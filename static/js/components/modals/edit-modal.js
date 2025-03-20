// Edit Modal
// Handles the bookmark edit modal functionality

const EditModal = {
    initialize() {
        this.setupEditFunctionality();
    },
    
    setupEditFunctionality() {
        console.log("Edit modal setup");
        const editModal = document.getElementById('editModal');
        if (!editModal) return;
        
        const closeBtn = editModal.querySelector('.close-btn');
        const cancelBtn = editModal.querySelector('.cancel-btn');
        const saveBtn = editModal.querySelector('.save-btn');
        const addCategoryBtn = editModal.querySelector('#editAddCategoryGroupBtn');
        const addTagBtn = editModal.querySelector('.add-tag-btn');
        
        // Edit button click
        document.querySelectorAll('.edit-bookmark').forEach(item => {
            item.addEventListener('click', (e) => {
                const card = e.target.closest('.bookmark-card');
                this.openEditModal(card);
            });
        });

        // Close buttons
        if (closeBtn && cancelBtn) {
            [closeBtn, cancelBtn].forEach(btn => {
                btn.addEventListener('click', () => {
                    editModal.classList.remove('active');
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
                            tagsList.insertAdjacentHTML('beforeend', this.createTagItem(tag));
                            input.value = '';
                        }
                    }
                }
            });
        }

        // Save changes
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveBookmarkChanges());
        }
    },
    
    openEditModal(card) {
        const modal = document.getElementById('editModal');
        if (!modal) return;
        
        const bookmarkId = card.dataset.id;
        const title = card.querySelector('.title')?.textContent || '';
        const description = card.querySelector('.description')?.textContent || '';
        const mainCategories = (card.dataset.mainCategories || '').split(',').filter(cat => cat.trim());
        const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => cat.textContent);
        const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);

        // Fill form fields
        const idField = modal.querySelector('#editBookmarkId');
        if (idField) idField.value = bookmarkId;
        
        const titleField = modal.querySelector('#editTitle');
        if (titleField) titleField.value = title;
        
        const descriptionField = modal.querySelector('#editDescription');
        if (descriptionField) descriptionField.value = description;

        // Add category groups
        const categoryGroupsList = modal.querySelector('#editCategoryGroupsList');
        if (categoryGroupsList) {
            categoryGroupsList.innerHTML = '';
            
            // Kategori-alt kategori ilişkilerini doğru şekilde göster
            if (mainCategories.length > 0 && subcategories.length > 0) {
                // Önce her ana kategori için alt kategorileri belirle
                const categorySubcategoryMap = {};
                
                // Backend'den gelen kategori-alt kategori ilişkilerini kullan
                // Eğer bu bilgi yoksa, mevcut alt kategorileri tüm ana kategorilere dağıt
                mainCategories.forEach(mainCategory => {
                    categorySubcategoryMap[mainCategory] = [];
                });
                
                // Her alt kategori için, ilişkili olduğu ana kategorileri bul
                subcategories.forEach(subcategory => {
                    let added = false;
                    
                    // Eğer bir alt kategori hiçbir ana kategoriye eklenmezse
                    // ilk ana kategoriye ekle (geriye dönük uyumluluk)
                    if (!added && mainCategories.length > 0) {
                        categorySubcategoryMap[mainCategories[0]].push(subcategory);
                    }
                });
                
                // Her ana kategori için ilişkili alt kategorileri göster
                mainCategories.forEach(mainCategory => {
                    // Eğer bu ana kategoriye ait alt kategori yoksa, ana kategoriyi tek başına göster
                    if (categorySubcategoryMap[mainCategory].length === 0) {
                        this.addCategoryGroup(mainCategory, '', categoryGroupsList);
                    } else {
                        // Bu ana kategoriye ait tüm alt kategorileri göster
                        categorySubcategoryMap[mainCategory].forEach(subcategory => {
                            this.addCategoryGroup(mainCategory, subcategory, categoryGroupsList);
                        });
                    }
                });
                
                // Eğer hiçbir ana kategoriye atanmamış alt kategoriler varsa, bunları da göster
                const assignedSubcategories = Object.values(categorySubcategoryMap).flat();
                const unassignedSubcategories = subcategories.filter(sub => !assignedSubcategories.includes(sub));
                
                if (unassignedSubcategories.length > 0 && mainCategories.length > 0) {
                    // Atanmamış alt kategorileri ilk ana kategoriye ekle
                    unassignedSubcategories.forEach(subcategory => {
                        this.addCategoryGroup(mainCategories[0], subcategory, categoryGroupsList);
                    });
                }
            } 
            // Eğer alt kategori yoksa, sadece ana kategorileri göster
            else if (mainCategories.length > 0) {
                for (let i = 0; i < mainCategories.length; i++) {
                    this.addCategoryGroup(mainCategories[i], '', categoryGroupsList);
                }
            }
            // Eğer ana kategori yoksa ama alt kategori varsa, varsayılan bir ana kategori ile göster
            else if (subcategories.length > 0) {
                for (let i = 0; i < subcategories.length; i++) {
                    this.addCategoryGroup('Uncategorized', subcategories[i], categoryGroupsList);
                }
            }
        }

        // Add tags
        const tagsList = modal.querySelector('#tagsList');
        if (tagsList) {
            tagsList.innerHTML = tags.map(tag => this.createTagItem(tag)).join('');
        }

        // Open modal
        modal.classList.add('active');
    },
    
    addCategoryGroup(mainCategory, subcategory, container) {
        if (!container) return;
        
        // Aynı kategori grubu var mı kontrol et
        const existingGroups = Array.from(container.querySelectorAll('.category-group'))
            .map(group => ({
                mainCategory: group.querySelector('.main-category-label').textContent,
                subcategory: group.querySelector('.subcategory-label').textContent
            }));
        
        const isDuplicate = existingGroups.some(group => 
            group.mainCategory === mainCategory && group.subcategory === subcategory);
        
        if (isDuplicate) return;
        
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
    },
    
    createTagItem(tag) {
        return `
            <div class="tag-item">
                ${tag}
                <button class="remove-btn" onclick="EditModal.removeItem(this, 'tag')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
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
        
        // Get tags
        const tags = Array.from(modal.querySelectorAll('#tagsList .tag-item'))
            .map(item => item.textContent.trim())
            .filter(tag => tag);
        
        // Prepare data
        const data = {
            id: bookmarkId,
            title: title,
            description: description,
            main_categories: mainCategories,
            subcategories: subcategories,
            tags: tags,
            category_subcategory_map: categorySubcategoryMap
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