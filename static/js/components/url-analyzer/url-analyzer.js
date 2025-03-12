document.addEventListener('DOMContentLoaded', function() {
    // Get modal elements
    const urlModal = document.getElementById('urlModal');
    const urlReviewModal = document.getElementById('urlReviewModal');
    const addUrlBtns = document.querySelectorAll('.add-url-btn');
    const closeButtons = document.querySelectorAll('.close-btn');
    const submitUrlBtn = document.querySelector('.submit-url-btn');
    const saveBookmarkBtn = document.querySelector('.save-bookmark-btn');
    const cancelReviewBtn = document.querySelector('.cancel-review-btn');
    const loadingContainer = document.querySelector('.loading-container');
    
    // URL input
    const urlInput = document.getElementById('url');
    
    // Review form elements
    const reviewTitle = document.getElementById('reviewTitle');
    const reviewDescription = document.getElementById('reviewDescription');
    const categoryGroupsList = document.getElementById('categoryGroupsList');
    const reviewTagsList = document.getElementById('reviewTagsList');
    
    // New category group inputs
    const newMainCategoryInput = document.getElementById('newMainCategory');
    const newSubcategoryInput = document.getElementById('newSubcategory');
    const addCategoryGroupBtn = document.getElementById('addCategoryGroupBtn');
    
    // New tag input
    const newTagInput = document.getElementById('newTag');
    const addNewTagBtn = document.getElementById('addNewTagBtn');
    
    // Current URL data
    let currentUrlData = null;
    
    // URL input alanının değerini saklamak için bir değişken
    let savedUrl = '';
    
    // URL input alanı değiştiğinde değeri sakla
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            savedUrl = this.value;
        });
    }
    
    // Add URL butonuna tıklandığında modalı aç
    if (addUrlBtns.length > 0 && urlModal) {
        addUrlBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault(); // Formun gönderilmesini engelle
                console.log("Add URL button clicked");
                urlModal.classList.add('active');
                
                // Eğer daha önce bir URL girilmişse, onu geri yükle
                if (urlInput && savedUrl) {
                    urlInput.value = savedUrl;
                }
                
                // URL input alanına odaklan
                if (urlInput) {
                    urlInput.focus();
                }
            });
        });
    }
    
    // Close butonlarına tıklandığında modalları kapat
    if (closeButtons.length > 0) {
        closeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }
    
    // Modalın dışına tıklandığında modalı kapat
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal') && e.target.classList.contains('active')) {
            e.target.classList.remove('active');
        }
    });
    
    // Cancel review
    if (cancelReviewBtn && urlReviewModal && urlModal) {
        cancelReviewBtn.addEventListener('click', function() {
            urlReviewModal.classList.remove('active');
            urlModal.classList.add('active');
        });
    }
    
    // Yeni kategori grubu ekleme butonu
    if (addCategoryGroupBtn && newMainCategoryInput && newSubcategoryInput && categoryGroupsList) {
        addCategoryGroupBtn.addEventListener('click', function() {
            const mainCategory = newMainCategoryInput.value.trim();
            const subcategory = newSubcategoryInput.value.trim();
            
            if (mainCategory && subcategory) {
                // Aynı kategori grubu var mı kontrol et
                const existingGroups = Array.from(categoryGroupsList.querySelectorAll('.category-group'))
                    .map(group => ({
                        mainCategory: group.querySelector('.main-category-label').textContent,
                        subcategory: group.querySelector('.subcategory-label').textContent
                    }));
                
                const isDuplicate = existingGroups.some(group => 
                    group.mainCategory === mainCategory && group.subcategory === subcategory);
                
                if (!isDuplicate) {
                    addCategoryGroup(mainCategory, subcategory, categoryGroupsList);
                    newMainCategoryInput.value = '';
                    newSubcategoryInput.value = '';
                }
            }
        });
        
        // Enter tuşuna basıldığında da kategori grubu ekle
        newSubcategoryInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addCategoryGroupBtn.click();
            }
        });
    }
    
    // Yeni etiket ekleme butonu
    if (addNewTagBtn && newTagInput && reviewTagsList) {
        addNewTagBtn.addEventListener('click', function() {
            const tagText = newTagInput.value.trim();
            if (tagText) {
                // Aynı etiket var mı kontrol et
                const existingTags = Array.from(reviewTagsList.querySelectorAll('.tag'))
                    .map(tag => tag.childNodes[0].nodeValue.trim());
                
                if (!existingTags.includes(tagText)) {
                    addTagElement(tagText, reviewTagsList);
                    newTagInput.value = '';
                }
            }
        });
        
        // Enter tuşuna basıldığında da etiket ekle
        newTagInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addNewTagBtn.click();
            }
        });
    }
    
    // Submit URL for analysis
    if (submitUrlBtn && urlInput) {
        submitUrlBtn.addEventListener('click', function() {
            let url = urlInput.value.trim();
            
            console.log("Girilen URL:", url);
            
            if (!url) {
                alert('Lütfen bir URL girin');
                return; // URL boşsa işlemi durdur
            }
            
            // URL formatını kontrol et ve düzelt
            let processedUrl = url;
            if (!url.match(/^https?:\/\//i)) {
                processedUrl = 'https://' + url;
                urlInput.value = processedUrl; // Input alanını güncelle
            }
            
            console.log("İşlenen URL:", processedUrl);
            
            // Yükleniyor göstergesini göster
            if (loadingContainer) {
                loadingContainer.style.display = 'flex';
            }
            
            if (submitUrlBtn) {
                submitUrlBtn.disabled = true;
            }
            
            // CSRF token'ı al
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            if (!csrfToken) {
                console.error("CSRF token bulunamadı!");
                alert("İşlem güvenlik nedeniyle gerçekleştirilemiyor. Sayfayı yenileyin ve tekrar deneyin.");
                
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                
                if (submitUrlBtn) {
                    submitUrlBtn.disabled = false;
                }
                
                return;
            }
            
            // URL'yi analiz et
            fetch('/api/analyze-url/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ url: processedUrl }),
            })
            .then(response => {
                console.log("Sunucu yanıt durumu:", response.status);
                // Yanıt içeriğini text olarak al
                return response.text();
            })
            .then(textData => {
                console.log("Sunucu yanıtı (text):", textData);
                
                // Text'i JSON'a çevirmeyi dene
                let data;
                try {
                    data = JSON.parse(textData);
                    console.log("Sunucu yanıtı (parsed):", data);
                } catch (e) {
                    console.error("JSON parse hatası:", e);
                    data = { error: "Sunucu yanıtı işlenemedi" };
                }
                
                // Yükleniyor göstergesini gizle
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                
                if (submitUrlBtn) {
                    submitUrlBtn.disabled = false;
                }
                
                if (data.error) {
                    alert('Hata: ' + data.error);
                    return;
                }
                
                // Mevcut URL verisini sakla
                currentUrlData = data;
                
                // Form alanlarını doldur
                if (reviewTitle) reviewTitle.value = data.title || '';
                if (reviewDescription) reviewDescription.value = data.description || '';
                
                // Gemini 2.0 Flash modelinin yanıtını işle
                processGeminiResponse(data, categoryGroupsList, reviewTagsList);
                
                // URL modalını gizle ve inceleme modalını göster
                if (urlModal) urlModal.classList.remove('active');
                if (urlReviewModal) urlReviewModal.classList.add('active');
                
                // Input alanlarını temizle
                if (newMainCategoryInput) newMainCategoryInput.value = '';
                if (newSubcategoryInput) newSubcategoryInput.value = '';
                if (newTagInput) newTagInput.value = '';
            })
            .catch(error => {
                console.error("Fetch hatası:", error);
                
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                
                if (submitUrlBtn) {
                    submitUrlBtn.disabled = false;
                }
                
                alert('URL analiz edilirken bir hata oluştu. Lütfen tekrar deneyin.');
            });
        });
    }
    
    // Gemini 2.0 Flash modelinin yanıtını işleme fonksiyonu
    function processGeminiResponse(data, categoryGroupsList, reviewTagsList) {
        console.log("İşlenen veri:", data);
        
        // Yanıt formatını kontrol et
        if (!data) return;
        
        // Listeleri temizle (en başta)
        if (categoryGroupsList) {
            categoryGroupsList.innerHTML = '';
        }
        
        if (reviewTagsList) {
            reviewTagsList.innerHTML = '';
        }
        
        // Tüm etiketleri saklamak için dizi
        const allTags = new Set();
        
        // Yanıt formatını kontrol et ve uygun şekilde işle
        if (data.output && Array.isArray(data.output)) {
            // Gemini 2.0 Flash'ın output array formatı
            processOutputArray(data.output);
        } else if (data.categories && Array.isArray(data.categories)) {
            // Doğrudan categories array formatı
            processCategoriesArray(data.categories);
        } else {
            // Diğer olası formatları kontrol et
            try {
                // String olarak gelen JSON'ı parse etmeyi dene
                if (typeof data === 'string') {
                    const parsedData = JSON.parse(data);
                    if (parsedData.output) {
                        processOutputArray(parsedData.output);
                    } else if (parsedData.categories) {
                        processCategoriesArray(parsedData.categories);
                    }
                } else if (data.response) {
                    // response alanını kontrol et
                    try {
                        const parsedResponse = JSON.parse(data.response);
                        if (parsedResponse.output) {
                            processOutputArray(parsedResponse.output);
                        } else if (parsedResponse.categories) {
                            processCategoriesArray(parsedResponse.categories);
                        }
                    } catch (e) {
                        console.error("Response parsing error:", e);
                    }
                } else {
                    // Gemini'nin döndürdüğü JSON string'i bulmaya çalış
                    const responseText = JSON.stringify(data);
                    const jsonMatches = responseText.match(/\{[\s\S]*?"categories"[\s\S]*?\}/g);
                    
                    if (jsonMatches && jsonMatches.length > 0) {
                        console.log("JSON matches found:", jsonMatches);
                        
                        // Her bir JSON eşleşmesini işle
                        jsonMatches.forEach(jsonStr => {
                            try {
                                const parsedJson = JSON.parse(jsonStr);
                                if (parsedJson.categories) {
                                    processCategoriesArray(parsedJson.categories);
                                }
                            } catch (e) {
                                console.error("JSON parsing error:", e);
                            }
                        });
                    } else {
                        console.error("Beklenmeyen yanıt formatı:", data);
                    }
                }
            } catch (e) {
                console.error("Data parsing error:", e);
                console.error("Beklenmeyen yanıt formatı:", data);
            }
        }
        
        // Output array formatını işle
        function processOutputArray(outputArray) {
            console.log("Output array işleniyor:", outputArray);
            
            // Tüm output öğelerini döngüye al
            outputArray.forEach(item => {
                console.log("İşlenen output öğesi:", item);
                
                // Kategorileri işle
                if (item.categories && Array.isArray(item.categories)) {
                    item.categories.forEach(category => {
                        console.log("İşlenen kategori:", category);
                        
                        if (category.main_category && category.subcategory) {
                            addCategoryGroup(category.main_category, category.subcategory, categoryGroupsList);
                        }
                    });
                }
                
                // Etiketleri işle
                if (item.tags) {
                    console.log("İşlenen etiketler:", item.tags);
                    processTagsField(item.tags);
                }
            });
        }
        
        // Categories array formatını işle
        function processCategoriesArray(categoriesArray) {
            console.log("Categories array işleniyor:", categoriesArray);
            
            // Tüm kategorileri döngüye al
            categoriesArray.forEach(category => {
                console.log("İşlenen kategori:", category);
                
                // Kategori grubunu ekle
                if (category.main_category && category.subcategory) {
                    addCategoryGroup(category.main_category, category.subcategory, categoryGroupsList);
                }
                
                // Etiketleri işle
                if (category.tags) {
                    console.log("İşlenen etiketler:", category.tags);
                    processTagsField(category.tags);
                }
            });
        }
        
        // Etiketleri işle (string veya array olabilir)
        function processTagsField(tags) {
            let tagArray = tags;
            
            // Eğer tags bir string ise, parse et
            if (typeof tags === 'string') {
                try {
                    // Köşeli parantezli string'i diziye çevir
                    if (tags.startsWith('[') && tags.endsWith(']')) {
                        tagArray = JSON.parse(tags);
                    } else {
                        // Virgülle ayrılmış string'i diziye çevir
                        tagArray = tags.split(',').map(tag => tag.trim());
                    }
                } catch (e) {
                    console.error('Tag parsing error:', e);
                    tagArray = [tags]; // Parsing başarısız olursa string'i tek eleman olarak kullan
                }
            }
            
            console.log("İşlenen etiket dizisi:", tagArray);
            
            // Etiketleri ekle
            if (Array.isArray(tagArray)) {
                tagArray.forEach(tag => {
                    if (tag && !allTags.has(tag)) {
                        allTags.add(tag);
                        addTagElement(tag, reviewTagsList);
                    }
                });
            } else if (tagArray) {
                // Eğer dizi değilse ve değer varsa, doğrudan ekle
                if (!allTags.has(tagArray)) {
                    allTags.add(tagArray);
                    addTagElement(tagArray, reviewTagsList);
                }
            }
        }
        
        // Eğer hiç kategori grubu eklenmemişse, hata mesajı göster
        if (categoryGroupsList.children.length === 0) {
            const noDataMessage = document.createElement('div');
            noDataMessage.className = 'no-data-message';
            noDataMessage.textContent = 'No categories found. Please add categories manually.';
            categoryGroupsList.appendChild(noDataMessage);
        }
        
        // Eğer hiç etiket eklenmemişse, hata mesajı göster
        if (reviewTagsList.children.length === 0) {
            const noDataMessage = document.createElement('div');
            noDataMessage.className = 'no-data-message';
            noDataMessage.textContent = 'No tags found. Please add tags manually.';
            reviewTagsList.appendChild(noDataMessage);
        }
    }
    
    // Kategori grubu ekle
    function addCategoryGroup(mainCategory, subcategory, container) {
        if (!container) return;
        
        console.log("Kategori grubu ekleniyor:", mainCategory, subcategory);
        
        // Aynı kategori grubu var mı kontrol et
        const existingGroups = Array.from(container.querySelectorAll('.category-group'))
            .map(group => ({
                mainCategory: group.querySelector('.main-category-label').textContent,
                subcategory: group.querySelector('.subcategory-label').textContent
            }));
        
        const isDuplicate = existingGroups.some(group => 
            group.mainCategory === mainCategory && group.subcategory === subcategory);
        
        if (isDuplicate) {
            console.log("Bu kategori grubu zaten var, eklenmeyecek:", mainCategory, subcategory);
            return;
        }
        
        const categoryGroup = document.createElement('div');
        categoryGroup.className = 'category-group';
        
        const categoryGroupContent = document.createElement('div');
        categoryGroupContent.className = 'category-group-content';
        
        const mainCategoryLabel = document.createElement('span');
        mainCategoryLabel.className = 'main-category-label';
        mainCategoryLabel.textContent = mainCategory;
        
        const subcategoryLabel = document.createElement('span');
        subcategoryLabel.className = 'subcategory-label';
        subcategoryLabel.textContent = subcategory;
        
        categoryGroupContent.appendChild(mainCategoryLabel);
        categoryGroupContent.appendChild(document.createTextNode(' > '));
        categoryGroupContent.appendChild(subcategoryLabel);
        categoryGroup.appendChild(categoryGroupContent);
        
        // Silme butonu ekle
        const removeBtn = document.createElement('i');
        removeBtn.className = 'material-icons remove-category-group';
        removeBtn.textContent = 'close';
        removeBtn.addEventListener('click', function() {
            categoryGroup.remove();
        });
        
        categoryGroup.appendChild(removeBtn);
        container.appendChild(categoryGroup);
    }
    
    // Etiket elementi ekle
    function addTagElement(tag, container) {
        if (!container) return;
        
        console.log("Etiket ekleniyor:", tag);
        
        // Aynı etiket var mı kontrol et
        const existingTags = Array.from(container.querySelectorAll('.tag'))
            .map(tagEl => tagEl.childNodes[0].nodeValue.trim());
        
        if (existingTags.includes(tag)) {
            console.log("Bu etiket zaten var, eklenmeyecek:", tag);
            return;
        }
        
        const tagSpan = document.createElement('span');
        tagSpan.className = 'tag';
        tagSpan.textContent = tag;
        
        // Silme butonu ekle
        const removeBtn = document.createElement('i');
        removeBtn.className = 'material-icons remove-tag';
        removeBtn.textContent = 'close';
        removeBtn.addEventListener('click', function() {
            tagSpan.remove();
        });
        
        tagSpan.appendChild(removeBtn);
        container.appendChild(tagSpan);
    }
    
    // Save bookmark
    if (saveBookmarkBtn) {
        saveBookmarkBtn.addEventListener('click', function() {
            if (!currentUrlData) {
                alert('URL verisi mevcut değil');
                return;
            }
            
            // Butonları devre dışı bırak (çift tıklamayı önlemek için)
            saveBookmarkBtn.disabled = true;
            
            // Tüm kategori gruplarını al
            const categoryGroups = categoryGroupsList ? categoryGroupsList.querySelectorAll('.category-group') : [];
            
            // Ana kategorileri ve alt kategorileri topla
            const mainCategories = [];
            const subcategories = [];
            
            // Kategori-alt kategori ilişkilerini tutacak harita
            const categorySubcategoryMap = {};
            
            if (categoryGroups.length === 0) {
                // Manuel giriş varsa kullan
                const mainCategory = newMainCategoryInput.value.trim();
                const subcategory = newSubcategoryInput.value.trim();
                
                if (mainCategory) {
                    mainCategories.push(mainCategory);
                    
                    // Alt kategori varsa ilişkiyi kaydet
                    if (subcategory) {
                        categorySubcategoryMap[mainCategory] = [subcategory];
                    }
                } else {
                    mainCategories.push('Uncategorized');
                }
                
                if (subcategory) {
                    subcategories.push(subcategory);
                }
            } else {
                // Kategori gruplarından ana kategorileri ve alt kategorileri al
                categoryGroups.forEach(group => {
                    const mainCategory = group.querySelector('.main-category-label').textContent;
                    const subcategory = group.querySelector('.subcategory-label').textContent;
                    
                    if (mainCategory && !mainCategories.includes(mainCategory)) {
                        mainCategories.push(mainCategory);
                    }
                    
                    if (subcategory && !subcategories.includes(subcategory)) {
                        subcategories.push(subcategory);
                    }
                    
                    // Kategori-alt kategori ilişkisini kaydet
                    if (mainCategory && subcategory) {
                        if (!categorySubcategoryMap[mainCategory]) {
                            categorySubcategoryMap[mainCategory] = [];
                        }
                        if (!categorySubcategoryMap[mainCategory].includes(subcategory)) {
                            categorySubcategoryMap[mainCategory].push(subcategory);
                        }
                    }
                });
            }
            
            // Etiketleri al
            const tags = [];
            
            if (reviewTagsList) {
                const tagElements = reviewTagsList.querySelectorAll('.tag');
                
                // Eğer etiket yoksa ve newTag değeri varsa, onu ekle
                if (tagElements.length === 0 && newTagInput.value.trim()) {
                    tags.push(newTagInput.value.trim());
                } else {
                    // Etiketleri al
                    tagElements.forEach(tag => {
                        // Silme butonunu hariç tut ve sadece metin içeriğini al
                        if (tag.childNodes.length > 0 && tag.childNodes[0].nodeType === Node.TEXT_NODE) {
                            const tagText = tag.childNodes[0].nodeValue.trim();
                            if (tagText && !tags.includes(tagText)) {
                                tags.push(tagText);
                            }
                        }
                    });
                }
            }
            
            // Bookmark verilerini hazırla
            const bookmarkData = {
                url: currentUrlData.url,
                title: reviewTitle.value.trim() || currentUrlData.title,
                description: reviewDescription.value.trim() || currentUrlData.description,
                main_categories: mainCategories,
                subcategories: subcategories,
                tags: tags,
                category_subcategory_map: categorySubcategoryMap
            };
            
            console.log("Kaydedilen bookmark verisi:", bookmarkData);
            
            // CSRF token'ı al
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            if (!csrfToken) {
                console.error("CSRF token bulunamadı!");
                alert('CSRF token bulunamadı. Lütfen sayfayı yenileyip tekrar deneyin.');
                
                if (saveBookmarkBtn) {
                    saveBookmarkBtn.disabled = false;
                }
                
                return;
            }
            
            // Bookmark'u kaydet
            fetch('/api/save-bookmark/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(bookmarkData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Modalı kapat
                    if (urlReviewModal) {
                        urlReviewModal.classList.remove('active');
                    }
                    
                    // Başarılı mesajı göster
                    alert('Bookmark başarıyla kaydedildi.');
                    
                    // Sayfayı yenile
                    window.location.reload();
                } else {
                    alert('Bookmark kaydedilirken hata oluştu: ' + data.error);
                    // Hata durumunda butonu tekrar aktif et
                    if (saveBookmarkBtn) {
                        saveBookmarkBtn.disabled = false;
                    }
                }
            })
            .catch(error => {
                console.error('Fetch hatası:', error);
                alert('Bookmark kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.');
                // Hata durumunda butonu tekrar aktif et
                if (saveBookmarkBtn) {
                    saveBookmarkBtn.disabled = false;
                }
            });
        });
    }
}); 