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
    const reviewLoadingContainer = document.querySelector('.review-loading');
    const reviewUrl = document.getElementById('reviewUrl');
    const reviewScreenshotData = document.getElementById('reviewScreenshotData');
    
    // Screenshot elements
    const screenshotPreview = document.getElementById('screenshotPreview');
    const customScreenshotInput = document.getElementById('customScreenshotInput');
    
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
    
    // Retry analysis button
    const retryAnalysisBtn = document.querySelector('.retry-analysis-btn');
    if (retryAnalysisBtn && urlReviewModal) {
        retryAnalysisBtn.addEventListener('click', function() {
            if (currentUrlData && currentUrlData.url) {
                // Show loading indicator
                if (reviewLoadingContainer) {
                    reviewLoadingContainer.style.display = 'flex';
                }
                
                // Disable the retry button
                retryAnalysisBtn.disabled = true;
                
                // Get CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                if (!csrfToken) {
                    showNotification('CSRF token bulunamadı. Sayfayı yenileyin ve tekrar deneyin.', 'error');
                    if (reviewLoadingContainer) {
                        reviewLoadingContainer.style.display = 'none';
                    }
                    retryAnalysisBtn.disabled = false;
                    return;
                }
                
                // Call the API
                fetch('/api/analyze-url/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ 
                        url: currentUrlData.url,
                        format: 'json'
                    }),
                    credentials: 'same-origin'
                })
                .then(response => response.text())
                .then(textData => {
                    // Parse the response
                    let data;
                    try {
                        data = JSON.parse(textData);
                    } catch (e) {
                        throw new Error('Sunucu yanıtı işlenemedi');
                    }
                    
                    // Hide loading indicator
                    if (reviewLoadingContainer) {
                        reviewLoadingContainer.style.display = 'none';
                    }
                    
                    // Re-enable the retry button
                    retryAnalysisBtn.disabled = false;
                    
                    if (data.error) {
                        showNotification('Hata: ' + data.error, 'error');
                        return;
                    }
                    
                    // Update current URL data
                    currentUrlData = data;
                    
                    // Update form fields
                    if (reviewTitle) reviewTitle.value = data.title || '';
                    if (reviewDescription) reviewDescription.value = data.description || '';
                    
                    // Clear and update categories and tags
                    if (categoryGroupsList) categoryGroupsList.innerHTML = '';
                    if (reviewTagsList) reviewTagsList.innerHTML = '';
                    
                    // Process the Gemini response
                    processGeminiResponse(data, categoryGroupsList, reviewTagsList);
                })
                .catch(error => {
                    console.error("Fetch hatası:", error);
                    
                    if (reviewLoadingContainer) {
                        reviewLoadingContainer.style.display = 'none';
                    }
                    
                    retryAnalysisBtn.disabled = false;
                    
                    showNotification('URL analiz edilirken bir hata oluştu: ' + error.message, 'error');
                });
            } else {
                showNotification('Analiz edilecek URL verisi bulunamadı', 'error');
            }
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

            reviewUrl.value = processedUrl;
            
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
                    'X-CSRFToken': csrfToken,
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    url: processedUrl,
                    format: 'json'
                }),
                credentials: 'same-origin'
            })
            .then(response => {
                console.log("Sunucu yanıt durumu:", response.status);
                console.log("Yanıt başlıkları:", response.headers);
                
                // Önce response.text() ile ham yanıtı al
                return response.text().then(text => {
                    console.log("Ham yanıt:", text);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                    }
                    
                    try {
                        // Text'i JSON'a çevirmeyi dene
                        return JSON.parse(text);
                    } catch (e) {
                        console.error("JSON parse hatası:", e);
                        throw new Error(`JSON parse hatası: ${text}`);
                    }
                });
            })
            .then(data => {
                console.log("İşlenmiş yanıt:", data);
                
                // Yükleniyor göstergesini gizle
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                
                if (submitUrlBtn) {
                    submitUrlBtn.disabled = false;
                }
                
                if (data.error) {
                    showNotification('Hata: ' + data.error, 'error');
                    return;
                }
                
                // Mevcut URL verisini sakla
                currentUrlData = data;
                
                // Form alanlarını doldur
                if (reviewTitle) reviewTitle.value = data.title || '';
                if (reviewDescription) reviewDescription.value = data.description || '';
                
                // URL modalını gizle ve inceleme modalını göster
                if (urlModal) urlModal.classList.remove('active');
                if (urlReviewModal) urlReviewModal.classList.add('active');
                
                // Input alanlarını temizle
                if (newMainCategoryInput) newMainCategoryInput.value = '';
                if (newSubcategoryInput) newSubcategoryInput.value = '';
                if (newTagInput) newTagInput.value = '';
                
                // Gemini yanıtını işle
                if (data.gemini_response) {
                    try {
                        let categories = [];
                        let geminiData = data.gemini_response;
                        
                        // Eğer string ise ve JSON formatında değilse, düzelt
                        if (typeof geminiData === 'string') {
                            // Markdown formatını temizle
                            geminiData = geminiData
                                .replace(/^```json\s*/, '')
                                .replace(/```\s*$/, '')
                                .trim();
                            
                            // Escape karakterlerini düzelt
                            geminiData = geminiData
                                .replace(/\\"/g, '"')
                                .replace(/\\\\/g, '\\');
                            
                            console.log("Temizlenmiş Gemini yanıtı:", geminiData);
                            
                            try {
                                const parsedData = JSON.parse(geminiData);
                                
                                // Eğer categories array olarak varsa kullan
                                if (parsedData.categories && Array.isArray(parsedData.categories)) {
                                    categories = parsedData.categories;
                                } 
                                // Eğer main_category ve subcategory varsa, bunları bir kategori olarak ekle
                                else if (parsedData.main_category) {
                                    categories = [{
                                        main_category: parsedData.main_category,
                                        subcategory: parsedData.subcategory || ""
                                    }];
                                }
                            } catch (e) {
                                console.error("Gemini yanıtı parse hatası:", e);
                                // Alternatif parse yöntemi
                                const match = geminiData.match(/{[\s\S]*?categories[\s\S]*?\[([\s\S]*?)\][\s\S]*?}/);
                                if (match) {
                                    try {
                                        categories = JSON.parse(`[${match[1]}]`);
                                    } catch (e2) {
                                        console.error("Alternatif parse hatası:", e2);
                                        
                                        // Alternatif olarak main_category ve subcategory'yi ara
                                        const mainCategoryMatch = geminiData.match(/"main_category"\s*:\s*"([^"]*)"/);
                                        const subcategoryMatch = geminiData.match(/"subcategory"\s*:\s*"([^"]*)"/);
                                        
                                        if (mainCategoryMatch && mainCategoryMatch[1]) {
                                            const mainCategory = mainCategoryMatch[1];
                                            const subcategory = subcategoryMatch && subcategoryMatch[1] ? subcategoryMatch[1] : "";
                                            
                                            categories = [{
                                                main_category: mainCategory,
                                                subcategory: subcategory
                                            }];
                                        } else {
                                            throw new Error("Gemini yanıtı işlenemedi");
                                        }
                                    }
                                } else {
                                    // Alternatif olarak main_category ve subcategory'yi ara
                                    const mainCategoryMatch = geminiData.match(/"main_category"\s*:\s*"([^"]*)"/);
                                    const subcategoryMatch = geminiData.match(/"subcategory"\s*:\s*"([^"]*)"/);
                                    
                                    if (mainCategoryMatch && mainCategoryMatch[1]) {
                                        const mainCategory = mainCategoryMatch[1];
                                        const subcategory = subcategoryMatch && subcategoryMatch[1] ? subcategoryMatch[1] : "";
                                        
                                        categories = [{
                                            main_category: mainCategory,
                                            subcategory: subcategory
                                        }];
                                    } else {
                                        throw new Error("Gemini yanıtı işlenemedi");
                                    }
                                }
                            }
                        } else if (geminiData && typeof geminiData === 'object') {
                            // Eğer categories array olarak varsa kullan
                            if (geminiData.categories && Array.isArray(geminiData.categories)) {
                                categories = geminiData.categories;
                            } 
                            // Eğer main_category ve subcategory varsa, bunları bir kategori olarak ekle
                            else if (geminiData.main_category) {
                                categories = [{
                                    main_category: geminiData.main_category,
                                    subcategory: geminiData.subcategory || ""
                                }];
                            }
                        }
                        
                        console.log("İşlenmiş kategoriler:", categories);
                        
                        if (!categories || !Array.isArray(categories) || categories.length === 0) {
                            throw new Error("Geçerli kategori verisi bulunamadı");
                        }
                        
                        // Kategori listesini temizle
                        if (categoryGroupsList) categoryGroupsList.innerHTML = '';
                        if (reviewTagsList) reviewTagsList.innerHTML = '';
                        
                        // Her kategoriyi işle
                        categories.forEach(category => {
                            console.log("Kategori:", category);
                            if (category.main_category) {
                                addCategoryGroup(
                                    category.main_category.trim(),
                                    (category.subcategory || "").trim(),
                                    categoryGroupsList
                                );
                                
                                // Etiketleri işle
                                if (category.tags) {
                                    let tags = category.tags;
                                    if (typeof tags === 'string') {
                                        tags = tags.split(',').map(t => t.trim());
                                    }
                                    if (Array.isArray(tags)) {
                                        tags.forEach(tag => {
                                            if (tag && typeof tag === 'string') {
                                                addTagElement(tag.trim(), reviewTagsList);
                                            }
                                        });
                                    }
                                }
                            }
                        });
                        
                        // Eğer ana JSON'da etiketler varsa onları da ekle
                        if (data.tags && Array.isArray(data.tags)) {
                            console.log("Ana JSON'dan etiketler işleniyor:", data.tags);
                            data.tags.forEach(tag => {
                                if (tag && typeof tag === 'string') {
                                    addTagElement(tag.trim(), reviewTagsList);
                                }
                            });
                        } else {
                            console.log("Ana JSON'da etiket dizisi bulunamadı:", data);
                        }
                        
                        showNotification('URL başarıyla analiz edildi', 'success');
                    } catch (e) {
                        console.error("Gemini yanıtı işleme hatası:", e);
                        console.error("Ham Gemini yanıtı:", data.gemini_response);
                        showNotification('Kategoriler işlenirken hata oluştu. Lütfen manuel olarak ekleyin.', 'warning');
                    }
                } else {
                    console.log("Gemini yanıtı bulunamadı, ham veriyi kullanmaya çalışıyorum:", data);
                    processGeminiResponse(data, categoryGroupsList, reviewTagsList);
                }
            })
            .catch(error => {
                console.error("Fetch hatası:", error);
                
                if (loadingContainer) {
                    loadingContainer.style.display = 'none';
                }
                
                if (submitUrlBtn) {
                    submitUrlBtn.disabled = false;
                }
                
                showNotification('URL analiz edilirken bir hata oluştu: ' + error.message, 'error');
            });
        });
    }
    
    // URL form submission

    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const url = urlInput.value.trim();
            if (url) {
                processUrlAnalysis(url);
            }
        });
    }
        
    
    // Gemini 2.0 Flash modelinin yanıtını işleme fonksiyonu
    function processGeminiResponse(data, categoryGroupsList, reviewTagsList) {
        console.log("İşlenen veri:", data);
        
        if (!data) {
            console.error("Veri bulunamadı");
            return;
        }
        
        // Listeleri temizle
        if (categoryGroupsList) categoryGroupsList.innerHTML = '';
        if (reviewTagsList) reviewTagsList.innerHTML = '';
        
        try {
            let categories = [];
            let tags = [];
            
            // Veri formatını kontrol et
            if (typeof data === 'string') {
                // String'i temizle ve parse et
                let cleanData = data
                    .replace(/^```json\s*/, '')
                    .replace(/```\s*$/, '')
                    .trim()
                    .replace(/\\"/g, '"');
                
                try {
                    const parsedData = JSON.parse(cleanData);
                    
                    // Eğer categories array olarak varsa kullan
                    if (parsedData.categories && Array.isArray(parsedData.categories)) {
                        categories = parsedData.categories;
                    } 
                    // Eğer main_category ve subcategory varsa, bunları bir kategori olarak ekle
                    else if (parsedData.main_category) {
                        categories = [{
                            main_category: parsedData.main_category,
                            subcategory: parsedData.subcategory || ""
                        }];
                    }
                    
                    tags = parsedData.tags || [];
                } catch (e) {
                    console.error("JSON parse hatası:", e);
                    
                    // Categories kısmını bulmaya çalış
                    const categoriesMatch = cleanData.match(/"categories"\s*:\s*(\[[\s\S]*?\])/);
                    if (categoriesMatch && categoriesMatch[1]) {
                        categories = JSON.parse(categoriesMatch[1]);
                    }
                    
                    // Alternatif olarak main_category ve subcategory'yi ara
                    const mainCategoryMatch = cleanData.match(/"main_category"\s*:\s*"([^"]*)"/);
                    const subcategoryMatch = cleanData.match(/"subcategory"\s*:\s*"([^"]*)"/);
                    
                    if (mainCategoryMatch && mainCategoryMatch[1]) {
                        const mainCategory = mainCategoryMatch[1];
                        const subcategory = subcategoryMatch && subcategoryMatch[1] ? subcategoryMatch[1] : "";
                        
                        categories = [{
                            main_category: mainCategory,
                            subcategory: subcategory
                        }];
                    }
                    
                    // Tags kısmını bulmaya çalış
                    const tagsMatch = cleanData.match(/"tags"\s*:\s*(\[[\s\S]*?\])/);
                    if (tagsMatch && tagsMatch[1]) {
                        tags = JSON.parse(tagsMatch[1]);
                    }
                }
            } else {
                // Doğrudan JSON nesnesi
                
                // Eğer categories array olarak varsa kullan
                if (data.categories && Array.isArray(data.categories)) {
                    categories = data.categories;
                } 
                // Eğer main_category ve subcategory varsa, bunları bir kategori olarak ekle
                else if (data.main_category) {
                    categories = [{
                        main_category: data.main_category,
                        subcategory: data.subcategory || ""
                    }];
                }
                
                tags = data.tags || [];
            }
            
            console.log("İşlenmiş kategoriler:", categories);
            console.log("İşlenmiş etiketler:", tags);
            
            // Kategorileri işle
            if (categories && Array.isArray(categories) && categories.length > 0) {
                categories.forEach(category => {
                    if (category.main_category) {
                        addCategoryGroup(
                            category.main_category.trim(),
                            (category.subcategory || "").trim(),
                            categoryGroupsList
                        );
                    }
                });
            }
            
            // Etiketleri doğrudan JSON'dan al
            if (tags && Array.isArray(tags)) {
                console.log("Etiketler dizisi işleniyor:", tags);
                tags.forEach(tag => {
                    if (tag && typeof tag === 'string') {
                        addTagElement(tag.trim(), reviewTagsList);
                    } else {
                        console.log("Geçersiz etiket formatı:", tag);
                    }
                });
            } else if (data.tags && Array.isArray(data.tags)) {
                console.log("data.tags dizisi işleniyor:", data.tags);
                data.tags.forEach(tag => {
                    if (tag && typeof tag === 'string') {
                        addTagElement(tag.trim(), reviewTagsList);
                    } else {
                        console.log("Geçersiz etiket formatı:", tag);
                    }
                });
            } else {
                console.log("Hiçbir etiket dizisi bulunamadı:", data);
            }
            
            // Eğer hiç kategori veya etiket yoksa hata fırlat
            if ((!categories || !categories.length) && (!tags || !tags.length)) {
                throw new Error("Geçerli kategori veya etiket verisi bulunamadı");
            }
        } catch (e) {
            console.error("Veri işleme hatası:", e);
            console.error("Ham veri:", data);
            showNotification('Kategoriler işlenirken hata oluştu. Lütfen manuel olarak ekleyin.', 'warning');
            
            // Boş kategori ve etiket listeleri göster
            if (categoryGroupsList.children.length === 0) {
                const noDataMessage = document.createElement('div');
                noDataMessage.className = 'no-data-message';
                noDataMessage.textContent = 'Kategori bulunamadı. Lütfen manuel olarak ekleyin.';
                categoryGroupsList.appendChild(noDataMessage);
            }
            
            if (reviewTagsList.children.length === 0) {
                const noDataMessage = document.createElement('div');
                noDataMessage.className = 'no-data-message';
                noDataMessage.textContent = 'Etiket bulunamadı. Lütfen manuel olarak ekleyin.';
                reviewTagsList.appendChild(noDataMessage);
            }
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
        
        // Alt kategori varsa ekle, yoksa sadece ana kategoriyi göster
        if (subcategory) {
            categoryGroupContent.appendChild(document.createTextNode(' > '));
            categoryGroupContent.appendChild(subcategoryLabel);
        }
        
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
    
    // Handle custom screenshot upload
    if (customScreenshotInput && screenshotPreview) {
        customScreenshotInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                // Check if file is an image
                if (!file.type.match('image.*')) {
                    showNotification('Please select an image file', 'error');
                    return;
                }
                
                // Check if file size is less than 5MB
                if (file.size > 5 * 1024 * 1024) {
                    showNotification('Image size should be less than 5MB', 'error');
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Display the image
                    screenshotPreview.src = e.target.result;
                    
                    // Update status message
                    const statusEl = document.getElementById('screenshotStatus');
                    if (statusEl) {
                        statusEl.innerHTML = `
                            <i class="material-icons" style="color: #ff9800;">image</i>
                            <span>Custom screenshot selected</span>
                        `;
                    }
                    
                    // Store the base64 image data
                    if (reviewScreenshotData) {
                        // Extract the base64 data without the prefix
                        const base64data = e.target.result.split(',')[1];
                        // Store the file path prefix and filename for backend processing
                        reviewScreenshotData.value = `custom_${Date.now()}.png`;
                        // Store the actual data in a data attribute for submission
                        reviewScreenshotData.dataset.content = base64data;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Save bookmark
    if (saveBookmarkBtn) {
        saveBookmarkBtn.addEventListener('click', function() {
            if (!currentUrlData) {
                showNotification('No data available to save', 'error');
                return;
            }

            const url = currentUrlData.url || reviewUrl.value;
            const title = reviewTitle.value;
            const description = reviewDescription.value;
            
            // Kategori gruplarını topla
            const categoryGroups = Array.from(categoryGroupsList.querySelectorAll('.category-group'))
                .map(group => ({
                    mainCategory: group.querySelector('.main-category-label').textContent,
                    subcategory: group.querySelector('.subcategory-label').textContent
                }));
            
            // Ana kategorileri listeye dönüştür
            const mainCategories = [...new Set(categoryGroups.map(group => group.mainCategory))];
            
            // Alt kategorileri listeye dönüştür
            const subcategories = categoryGroups.map(group => group.subcategory);
            
            // Her alt kategori için hangi ana kategoriye ait olduğunu belirle
            const categorySubcategoryMap = {};
            categoryGroups.forEach(group => {
                if (!categorySubcategoryMap[group.mainCategory]) {
                    categorySubcategoryMap[group.mainCategory] = [];
                }
                categorySubcategoryMap[group.mainCategory].push(group.subcategory);
            });
            
            // Etiketleri topla
            const tags = Array.from(reviewTagsList.querySelectorAll('.tag'))
                .map(tag => tag.childNodes[0].nodeValue.trim());
            
            // Screenshot data
            let screenshotData = currentUrlData.screenshot_data;
            if (reviewScreenshotData && reviewScreenshotData.value) {
                screenshotData = reviewScreenshotData.value;
            }
            
            // Check required fields
            if (!url || !title || mainCategories.length === 0) {
                showNotification('URL, title, and at least one category are required', 'error');
                return;
            }
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            if (!csrfToken) {
                showNotification('CSRF token bulunamadı', 'error');
                return;
            }
            
            // Prepare data for the API
            const bookmarkData = {
                url,
                title,
                description,
                main_categories: mainCategories,
                subcategories,
                category_subcategory_map: categorySubcategoryMap,
                tags,
                screenshot_data: screenshotData
            };
            
            // If we have custom screenshot base64 data, include it
            if (reviewScreenshotData && reviewScreenshotData.dataset.content) {
                bookmarkData.custom_screenshot = reviewScreenshotData.dataset.content;
            }
            
            // Call the API
            fetch('/api/save-bookmark/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(bookmarkData),
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Close modal
                if (urlReviewModal) {
                    urlReviewModal.classList.remove('active');
                }
                
                // Show success message
                showNotification('Bookmark saved successfully', 'success');
                
                // Reload page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            })
            .catch(error => {
                console.error('Error saving bookmark:', error);
                showNotification('Error saving bookmark: ' + error.message, 'error');
            });
        });
    }
});

function processUrlAnalysis(url) {
    // Show loading animation
    loadingContainer.classList.add('active');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Send URL to backend for analysis
    fetch('/api/analyze-url/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ url: url })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Hide loading animation
        loadingContainer.classList.remove('active');
        
        // Check if screenshot was used
        if (data.screenshot_used) {
            // Show notification that screenshot was used
            showNotification('HTML içeriği alınamadı, ekran görüntüsü kullanıldı.', 'info');
        }
        
        // Process the response data
        showUrlReviewModal(data, url);
    })
    .catch(error => {
        // Hide loading animation
        loadingContainer.classList.remove('active');
        
        console.error('Error:', error);
        alert('URL analiz edilirken bir hata oluştu. Lütfen tekrar deneyin.');
    });
}

// Notification function
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="material-icons">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</i>
        <span>${message}</span>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide and remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function showUrlReviewModal(data, url) {
    const urlReviewModal = document.getElementById('urlReviewModal');
    if (!urlReviewModal) return;
    
    const urlModal = document.getElementById('urlModal');
    if (urlModal) {
        urlModal.classList.remove('active');
    }
    
    // Hide previous loading
    const reviewLoadingContainer = document.querySelector('.review-loading');
    if (reviewLoadingContainer) {
        reviewLoadingContainer.style.display = 'none';
    }
    
    // Update current URL data
    currentUrlData = data;
    
    // Update form fields
    const reviewUrl = document.getElementById('reviewUrl');
    const reviewTitle = document.getElementById('reviewTitle');
    const reviewDescription = document.getElementById('reviewDescription');
    const reviewScreenshotData = document.getElementById('reviewScreenshotData');
    const screenshotPreview = document.getElementById('screenshotPreview');
    const categoryGroupsList = document.getElementById('categoryGroupsList');
    const reviewTagsList = document.getElementById('reviewTagsList');
    
    if (reviewUrl) reviewUrl.value = url;
    if (reviewTitle) reviewTitle.value = data.title || '';
    if (reviewDescription) reviewDescription.value = data.description || '';
    
    // Update the screenshot preview and field
    if (reviewScreenshotData && screenshotPreview) {
        const screenshotData = data.screenshot_data;
        reviewScreenshotData.value = screenshotData || '';
        
        // Clear any previous custom data
        reviewScreenshotData.dataset.content = '';
        
        // Update the screenshot preview
        if (screenshotData) {
            screenshotPreview.src = `/static/${screenshotData}`;
            
            // Update status message based on screenshot source
            const statusEl = document.getElementById('screenshotStatus');
            if (statusEl) {
                if (data.screenshot_used) {
                    statusEl.innerHTML = `
                        <i class="material-icons" style="color: #4caf50;">check_circle</i>
                        <span>Screenshot captured automatically</span>
                    `;
                } else {
                    statusEl.innerHTML = `
                        <i class="material-icons" style="color: #2196f3;">image</i>
                        <span>Screenshot available</span>
                    `;
                }
            }
        } else {
            // No screenshot available
            screenshotPreview.src = '/static/images/default-thumbnail.png';
            const statusEl = document.getElementById('screenshotStatus');
            if (statusEl) {
                statusEl.innerHTML = `
                    <i class="material-icons" style="color: #f44336;">error_outline</i>
                    <span>No screenshot available</span>
                `;
            }
        }
    }
    
    // Clear previous data
    if (categoryGroupsList) categoryGroupsList.innerHTML = '';
    if (reviewTagsList) reviewTagsList.innerHTML = '';
    
    // Process the Gemini response
    processGeminiResponse(data, categoryGroupsList, reviewTagsList);
    
    // Show the review modal
    urlReviewModal.classList.add('active');
} 