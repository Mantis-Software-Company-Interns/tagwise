// Edit Modal
// Handles the bookmark edit modal functionality

const EditModal = {
    initialize() {
        console.log("Edit modal setup başlatılıyor");
        this.setupEditFunctionality();
    },
    
    setupEditFunctionality() {
        console.log("Edit modal setup");
        const editModal = document.getElementById('editModal');
        if (!editModal) {
            console.error("editModal bulunamadı!");
            return;
        }
        
        const closeBtn = editModal.querySelector('.close-btn');
        const cancelBtn = editModal.querySelector('.cancel-btn');
        const saveBtn = editModal.querySelector('.save-btn');
        const addCategoryBtn = editModal.querySelector('#editAddCategoryGroupBtn');
        const addTagBtn = editModal.querySelector('.add-tag-btn');
        const screenshotInput = editModal.querySelector('#editScreenshotInput');
        
        // Edit button click
        document.querySelectorAll('.menu-item.edit-bookmark').forEach(item => {
            item.addEventListener('click', (e) => {
                console.log("Edit butonu tıklandı");
                const card = e.target.closest('.bookmark-card');
                this.openEditModal(card);
            });
        });

        // Close buttons
        if (closeBtn && cancelBtn) {
            [closeBtn, cancelBtn].forEach(btn => {
                btn.addEventListener('click', () => {
                    editModal.classList.remove('active');
                    // Reset modal state
                    this.resetModal(editModal);
                });
            });
        }

        // Add category group
        if (addCategoryBtn) {
            addCategoryBtn.addEventListener('click', () => {
                const mainCategoryInput = document.getElementById('editMainCategory');
                const subcategoryInput = document.getElementById('editSubcategory');
                
                const mainCategory = mainCategoryInput.value.trim();
                const subcategory = subcategoryInput.value.trim();
                
                if (mainCategory) {
                    const categoryGroupsList = document.getElementById('editCategoryGroupsList');
                    if (categoryGroupsList) {
                        this.addCategoryGroup(mainCategory, subcategory, categoryGroupsList);
                        mainCategoryInput.value = '';
                        subcategoryInput.value = '';
                    }
                }
            });
        }

        // Add tag
        if (addTagBtn) {
            addTagBtn.addEventListener('click', () => {
                const input = document.getElementById('tagInput');
                if (input) {
                    const tag = input.value.trim();
                    
                    if (tag) {
                        const tagsList = document.getElementById('tagsList');
                        if (tagsList) {
                            this.addTag(tag, tagsList);
                            input.value = '';
                        }
                    }
                }
            });
        }

        // Screenshot input change
        if (screenshotInput) {
            screenshotInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        // Display the selected image in the preview
                        const preview = editModal.querySelector('#editScreenshotPreview');
                        if (preview) preview.src = event.target.result;
                        
                        // Store the base64 image data
                        const screenshotField = editModal.querySelector('#editScreenshotData');
                        if (screenshotField) {
                            // Store only the base64 data (remove the data:image/... prefix)
                            const base64String = event.target.result.split(',')[1];
                            screenshotField.value = base64String;
                        }
                        
                        // Update status message
                        const statusElement = editModal.querySelector('#editScreenshotStatus span');
                        if (statusElement) statusElement.textContent = 'Custom screenshot selected';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        // Save changes
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveBookmarkChanges());
        }
    },
    
    resetModal(modal) {
        // Clear all input values and reset state
        modal.dataset.apiSuccess = 'false';
        modal.dataset.cardRef = '';
        
        // Clear input fields
        const inputs = modal.querySelectorAll('input:not([type="file"]), textarea');
        inputs.forEach(input => {
            input.value = '';
        });
        
        // Clear category groups and tags
        const categoryGroupsList = modal.querySelector('#editCategoryGroupsList');
        if (categoryGroupsList) categoryGroupsList.innerHTML = '';
        
        const tagsList = modal.querySelector('#tagsList');
        if (tagsList) tagsList.innerHTML = '';
        
        // Reset screenshot preview
        const screenshotPreview = modal.querySelector('#editScreenshotPreview');
        if (screenshotPreview) screenshotPreview.src = '';
        
        // Reset screenshot status
        const statusElement = modal.querySelector('#editScreenshotStatus span');
        if (statusElement) statusElement.textContent = 'Current screenshot';
    },
    
    openEditModal(card) {
        const modal = document.getElementById('editModal');
        if (!modal) return;
        
        console.log("Opening edit modal for bookmark:", card);
        
        // Set reference to the card for fallback method
        modal.dataset.cardRef = card.dataset.id;
        
        const bookmarkId = card.dataset.id;
        const title = card.querySelector('.title')?.textContent || '';
        const description = card.querySelector('.description')?.textContent || '';
        
        // Fill form fields
        const idField = modal.querySelector('#editBookmarkId');
        if (idField) idField.value = bookmarkId;
        
        const titleField = modal.querySelector('#editTitle');
        if (titleField) titleField.value = title;
        
        const descriptionField = modal.querySelector('#editDescription');
        if (descriptionField) descriptionField.value = description;

        // Clear existing categories and tags
        const categoryGroupsList = modal.querySelector('#editCategoryGroupsList');
        if (categoryGroupsList) {
            categoryGroupsList.innerHTML = '';
        }
        
        const tagsList = modal.querySelector('#tagsList');
        if (tagsList) {
            tagsList.innerHTML = '';
        }
        
        // Reset API success flag
        modal.dataset.apiSuccess = 'false';
        
        // Bookmark verisini API'dan alarak kategori-alt kategori ilişkisini doğru şekilde göster
        this.fetchBookmarkDetails(bookmarkId, modal, card);

        // Open modal
        modal.classList.add('active');
    },
    
    fetchBookmarkDetails(bookmarkId, modal, card) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (!csrfToken) {
            console.error('CSRF token not found');
            return;
        }
        
        // Kategori listesi konteynerı
        const categoryGroupsList = modal.querySelector('#editCategoryGroupsList');
        const tagsList = modal.querySelector('#tagsList');
        
        // API'dan bookmark detaylarını al
        fetch(`/api/get-bookmark-details/?id=${bookmarkId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log("Bookmark details:", data);
                
                // API'den gelen verileri kullan
                const mainCategories = data.bookmark.main_categories || [];
                const subcategories = data.bookmark.subcategories || [];
                const tags = data.bookmark.tags || [];
                const url = data.bookmark.url || '';
                
                // Kategori-alt kategori ilişkilerini ekle
                if (categoryGroupsList) {
                    // Clear existing categories first
                    categoryGroupsList.innerHTML = '';
                    
                    // Kategori-alt kategori ilişkileri varsa
                    if (data.bookmark.category_subcategory_map) {
                        const categoryMap = data.bookmark.category_subcategory_map;
                        
                        // Tüm ana kategorileri döngüyle işle
                        Object.keys(categoryMap).forEach(mainCategory => {
                            const subs = categoryMap[mainCategory];
                            
                            if (subs && subs.length > 0) {
                                // Ana kategoriye bağlı alt kategorileri göster
                                subs.forEach(subcategory => {
                                    this.addCategoryGroup(mainCategory, subcategory, categoryGroupsList);
                                });
                            } else {
                                // Alt kategorisi olmayan ana kategorileri tek başına göster
                                this.addCategoryGroup(mainCategory, '', categoryGroupsList);
                            }
                        });
                    } 
                    // Eğer ilişki bilgisi yoksa, alternatif mantık kullan
                    else {
                        // Ana kategorileri göster
                        mainCategories.forEach(category => {
                            const relatedSubs = subcategories.filter(sub => 
                                sub.parent_id === category.id || 
                                (category.name.toLowerCase() === sub.name.toLowerCase().split(' > ')[0])
                            );
                            
                            if (relatedSubs.length > 0) {
                                // İlişkili alt kategorileri göster
                                relatedSubs.forEach(sub => {
                                    this.addCategoryGroup(category.name, sub.name, categoryGroupsList);
                                });
                            } else {
                                // Alt kategorisi olmayan ana kategorileri göster
                                this.addCategoryGroup(category.name, '', categoryGroupsList);
                            }
                        });
                        
                        // Ana kategorisi olmayan alt kategorileri "Uncategorized" altında göster
                        const unassignedSubs = subcategories.filter(sub => 
                            !mainCategories.some(main => 
                                sub.parent_id === main.id || 
                                (main.name.toLowerCase() === sub.name.toLowerCase().split(' > ')[0])
                            )
                        );
                        
                        unassignedSubs.forEach(sub => {
                            this.addCategoryGroup("Uncategorized", sub.name, categoryGroupsList);
                        });
                    }
                }
                
                // Etiketleri ekle
                if (tagsList) {
                    // Mevcut tag'leri temizle ve API'den gelenleri ekle
                    tagsList.innerHTML = '';
                    const uniqueTags = new Set();
                    
                    tags.forEach(tag => {
                        const tagName = tag.name || tag;
                        if (!uniqueTags.has(tagName.toLowerCase())) {
                            uniqueTags.add(tagName.toLowerCase());
                            this.addTag(tagName, tagsList);
                        }
                    });
                }
                
                // Get and display the screenshot
                this.loadScreenshot(card, modal);
                
                // API başarılı olduğu için fallback method'a gerek yok
                // Bayrak değişkeni ekleyelim
                modal.dataset.apiSuccess = 'true';
                
            } else {
                console.error('Error fetching bookmark details:', data.error);
                // Hata durumunda alternatif yöntem - mevcut DOM elemanlarından kategori ve etiketleri al
                this.fallbackCategoryTagDisplay(card, modal);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Hata durumunda alternatif yöntem - mevcut DOM elemanlarından kategori ve etiketleri al
            this.fallbackCategoryTagDisplay(card, modal);
        });
    },
    
    loadScreenshot(card, modal) {
        // Get the screenshot from the card
        const thumbnail = card.querySelector('.thumbnail');
        if (!thumbnail || !thumbnail.src) {
            console.log("No thumbnail found in the card");
            return;
        }
        
        // Set the screenshot in the edit modal
        const screenshotPreview = modal.querySelector('#editScreenshotPreview');
        if (screenshotPreview) {
            screenshotPreview.src = thumbnail.src;
            console.log("Setting screenshot preview:", thumbnail.src);
        } else {
            console.log("Screenshot preview element not found");
        }
        
        // Store the screenshot path
        const screenshotDataField = modal.querySelector('#editScreenshotData');
        if (screenshotDataField) {
            // Extract the path from the src attribute
            const path = this.extractPathFromSrc(thumbnail.src);
            screenshotDataField.value = path;
            console.log("Setting screenshot data field:", path);
        }
    },
    
    extractPathFromSrc(src) {
        // Handle different formats of src attribute
        if (!src) return '';
        
        // For media URLs
        if (src.includes('/media/')) {
            const mediaIndex = src.indexOf('/media/');
            return src.substring(mediaIndex + 7); // +7 to skip '/media/'
        }
        
        // For relative paths
        if (src.includes('thumbnails/')) {
            const thumbIndex = src.indexOf('thumbnails/');
            return src.substring(thumbIndex);
        }
        
        return src;
    },
    
    fallbackCategoryTagDisplay(card, modal) {
        // API başarılı olduysa bu metodu çalıştırma
        if (modal.dataset.apiSuccess === 'true') {
            console.log("API successful, skipping fallback method");
            return;
        }
        
        console.log("Using fallback method with card:", card);
        
        const categoryGroupsList = modal.querySelector('#editCategoryGroupsList');
        const tagsList = modal.querySelector('#tagsList');
        
        // DOM'daki kategori ve alt kategorileri al
        const mainCategories = (card.dataset.mainCategories || '').split(',').filter(cat => cat.trim());
        const subcategories = Array.from(card.querySelectorAll('.subcategory-tab') || [])
            .map(cat => cat?.textContent || '')
            .filter(text => text);
        const tags = Array.from(card.querySelectorAll('.tag') || [])
            .map(tag => tag?.textContent || '')
            .filter(text => text);
        
        console.log("Fallback category display with:", {mainCategories, subcategories, tags});
        
        // Ana kategorileri göster
        if (categoryGroupsList && mainCategories.length > 0) {
            categoryGroupsList.innerHTML = ''; // Clear first
            mainCategories.forEach(mainCategory => {
                this.addCategoryGroup(mainCategory, '', categoryGroupsList);
            });
        }
        
        // Alt kategorileri göster
        if (categoryGroupsList && subcategories.length > 0 && mainCategories.length > 0) {
            subcategories.forEach(subcategory => {
                this.addCategoryGroup(mainCategories[0], subcategory, categoryGroupsList);
            });
        }
        
        // Etiketleri ekle
        if (tagsList && tags.length > 0) {
            tagsList.innerHTML = ''; // Clear first
            const uniqueTags = new Set();
            
            tags.forEach(tag => {
                if (!uniqueTags.has(tag.toLowerCase())) {
                    uniqueTags.add(tag.toLowerCase());
                    this.addTag(tag, tagsList);
                }
            });
        }
        
        // Load the screenshot
        this.loadScreenshot(card, modal);
    },
    
    addCategoryGroup(mainCategory, subcategory, container) {
        if (!container) return;
        
        console.log("Adding category group:", { mainCategory, subcategory });
        
        // Aynı kategori grubu var mı kontrol et
        const existingGroups = Array.from(container.querySelectorAll('.category-group'))
            .map(group => ({
                mainCategory: group.querySelector('.main-category-label')?.textContent || '',
                subcategory: group.querySelector('.subcategory-label')?.textContent || ''
            }));
        
        const isDuplicate = existingGroups.some(group => 
            group.mainCategory === mainCategory && group.subcategory === subcategory);
        
        if (isDuplicate) {
            console.log("Duplicate category group, skipping:", { mainCategory, subcategory });
            return;
        }
        
        const categoryGroup = document.createElement('div');
        categoryGroup.className = 'category-group';
        
        const categoryGroupContent = document.createElement('div');
        categoryGroupContent.className = 'category-group-content';
        
        const mainCategoryLabel = document.createElement('span');
        mainCategoryLabel.className = 'main-category-label category-label';
        mainCategoryLabel.textContent = mainCategory;
        
        categoryGroupContent.appendChild(mainCategoryLabel);
        
        // Alt kategori varsa ekle
        if (subcategory) {
            // ">" ayırıcı
            const separator = document.createElement('span');
            separator.className = 'category-separator';
            separator.textContent = ' > ';
            categoryGroupContent.appendChild(separator);
            
            // Alt kategori etiketi
            const subcategoryLabel = document.createElement('span');
            subcategoryLabel.className = 'subcategory-label category-label';
            subcategoryLabel.textContent = subcategory;
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
    },
    
    // Yeni bir addTag metodu ekledim
    addTag(tag, container) {
        if (!container) return;
        
        const safeTag = this.escapeHtml(String(tag).trim());
        if (!safeTag) return;
        
        // Etiket zaten mevcut mu kontrol et
        const existingTags = Array.from(container.querySelectorAll('.tag-item'))
            .map(item => this.getTagTextContent(item));
        
        if (existingTags.some(existingTag => 
            existingTag.toLowerCase() === safeTag.toLowerCase())) {
            console.log(`Tag '${safeTag}' already exists, skipping`);
            return;
        }
        
        container.insertAdjacentHTML('beforeend', this.createTagItem(safeTag));
    },
    
    getTagTextContent(tagElement) {
        // Get only the text content without the close button text
        const clone = tagElement.cloneNode(true);
        const button = clone.querySelector('.remove-btn');
        if (button) button.remove();
        return clone.textContent.trim();
    },
    
    createTagItem(tag) {
        // HTML içeren karakterleri escape et
        const safeTag = this.escapeHtml(String(tag).trim());
        
        return `
            <div class="tag-item">
                ${safeTag}
                <button class="remove-btn" onclick="EditModal.removeItem(this, 'tag')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },
    
    escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    },
    
    removeItem(button, type) {
        button.closest(`.${type}-item`).remove();
    },
    
    saveBookmarkChanges() {
        const modal = document.getElementById('editModal');
        if (!modal) return;
        
        const bookmarkId = modal.querySelector('#editBookmarkId')?.value;
        const title = modal.querySelector('#editTitle')?.value;
        const description = modal.querySelector('#editDescription')?.value;
        const screenshotData = modal.querySelector('#editScreenshotData')?.value;
        const customScreenshotBase64 = modal.querySelector('#editScreenshotInput').files.length > 0 ? 
            modal.querySelector('#editScreenshotPreview').src.split(',')[1] : null;
        
        // Get categories and subcategories
        const categoryGroups = Array.from(modal.querySelectorAll('#editCategoryGroupsList .category-group'));
        const mainCategories = [];
        const subcategories = [];
        
        // Kategori-alt kategori ilişkilerini tutacak harita
        const categorySubcategoryMap = {};
        
        categoryGroups.forEach(group => {
            const mainCategory = group.querySelector('.main-category-label')?.textContent;
            const subcategory = group.querySelector('.subcategory-label')?.textContent;
            
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
        
        // Get tags - use the getTagTextContent to exclude the close button text
        const tags = Array.from(modal.querySelectorAll('#tagsList .tag-item'))
            .map(item => this.getTagTextContent(item))
            .filter(tag => tag);
        
        // Prepare data
        const data = {
            id: bookmarkId,
            title: title,
            description: description,
            main_categories: mainCategories,
            subcategories: subcategories,
            tags: tags,
            category_subcategory_map: categorySubcategoryMap,
            screenshot_data: screenshotData,
            custom_screenshot: customScreenshotBase64
        };
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (!csrfToken) {
            alert('CSRF token not found. Please refresh the page and try again.');
            return;
        }
        
        // Send update request
        fetch('/api/update-bookmark/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                modal.classList.remove('active');
                
                // Reset modal
                this.resetModal(modal);
                
                // Reload page to show updated bookmark
                window.location.reload();
            } else {
                alert('Error updating bookmark: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error updating bookmark. Please try again.');
        });
    }
};

// DOM yüklendiğinde EditModal başlatılsın
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOMContentLoaded - Edit Modal başlatılıyor");
    EditModal.initialize();
}); 