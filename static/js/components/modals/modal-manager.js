// Modal Manager
// Handles all modal operations (details, edit, URL)

const ModalManager = {
    initialize() {
        // Initialize details modal
        DetailsModal.initialize();
        
        // Initialize edit modal
        EditModal.initialize();
        
        // URL modal is handled by url-analyzer.js
        // this.initializeUrlModal();
    },

    setupDetailsModal() {
        const modal = document.getElementById('detailsModal');
        if (!modal) return;
        
        const closeBtn = modal.querySelector('.close-modal-btn');
        
        // Add event listeners to expand buttons
        document.querySelectorAll('.expand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const card = e.target.closest('.bookmark-card');
                this.updateModalContent(card);
                modal.classList.add('active');
            });
        });

        // Close button functionality
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }

        // Close when clicking outside modal content
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    },

    updateModalContent(card) {
        if (!card) return;
        
        const modal = document.getElementById('detailsModal');
        if (!modal) return;
        
        // Get main category
        const mainCategory = card.dataset.mainCategory;
        
        // Update main category link
        const mainCategoryLink = modal.querySelector('.main-category');
        if (mainCategoryLink) {
            mainCategoryLink.textContent = mainCategory;
            mainCategoryLink.href = `/categories/?category=${encodeURIComponent(mainCategory)}`;
        }
        
        // Get subcategories
        const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => ({
            name: cat.textContent,
            url: cat.href
        }));
        
        // Update subcategories
        const subcategoriesContainer = modal.querySelector('.subcategories');
        if (subcategoriesContainer) {
            subcategoriesContainer.innerHTML = subcategories.map(sub => 
                `<a href="${sub.url}" class="subcategory-tab">${sub.name}</a>`
            ).join('');
        }
        
        // Update general information
        const dateElement = modal.querySelector('.bookmark-date');
        if (dateElement) {
            const cardDate = card.querySelector('.date');
            if (cardDate) {
                dateElement.textContent = cardDate.textContent;
            }
        }
        
        // Update content information
        const titleElement = modal.querySelector('.bookmark-title');
        if (titleElement) {
            const cardTitle = card.querySelector('.title');
            if (cardTitle) {
                titleElement.textContent = cardTitle.textContent;
            }
        }
        
        const descriptionElement = modal.querySelector('.bookmark-description');
        if (descriptionElement) {
            const cardDescription = card.querySelector('.description');
            if (cardDescription) {
                descriptionElement.textContent = cardDescription.textContent;
            }
        }
        
        // Update tags
        const tags = Array.from(card.querySelectorAll('.tag')).map(tag => ({
            name: tag.textContent,
            url: tag.href
        }));
        
        const tagsContainer = modal.querySelector('.bookmark-tags');
        if (tagsContainer) {
            tagsContainer.innerHTML = tags.map(tag => 
                `<a href="${tag.url}" class="tag">${tag.name}</a>`
            ).join('');
        }
        
        // Update image and link
        const previewImage = modal.querySelector('.preview-image');
        const visitLink = modal.querySelector('.visit-link');
        
        if (previewImage) {
            const cardThumbnail = card.querySelector('.thumbnail');
            if (cardThumbnail) {
                previewImage.src = cardThumbnail.src;
            }
        }
        
        if (visitLink) {
            const cardLink = card.querySelector('.thumbnail-link');
            if (cardLink) {
                visitLink.href = cardLink.href;
            }
        }
    },

    setupEditModal() {
        const editButtons = document.querySelectorAll('.edit-btn');
        
        editButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const card = btn.closest('.bookmark-card');
                if (card) {
                    this.openEditModal(card);
                }
            });
        });
        
        // Close buttons
        const editModal = document.getElementById('editModal');
        if (editModal) {
            const closeBtn = editModal.querySelector('.close-btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    editModal.classList.remove('active');
                });
            }
            
            // Add subcategory button
            const addSubcategoryBtn = editModal.querySelector('.add-subcategory-btn');
            if (addSubcategoryBtn) {
                addSubcategoryBtn.addEventListener('click', () => {
                    const input = editModal.querySelector('#newSubcategory');
                    if (input && input.value.trim()) {
                        const subcategoriesList = editModal.querySelector('#subcategoriesList');
                        if (subcategoriesList) {
                            const subcategoryItem = this.createSubcategoryItem(input.value.trim());
                            subcategoriesList.insertAdjacentHTML('beforeend', subcategoryItem);
                            input.value = '';
                        }
                    }
                });
            }
            
            // Add tag button
            const addTagBtn = editModal.querySelector('.add-tag-btn');
            if (addTagBtn) {
                addTagBtn.addEventListener('click', () => {
                    const input = editModal.querySelector('#newTag');
                    if (input && input.value.trim()) {
                        const tagsList = editModal.querySelector('#tagsList');
                        if (tagsList) {
                            const tagItem = this.createTagItem(input.value.trim());
                            tagsList.insertAdjacentHTML('beforeend', tagItem);
                            input.value = '';
                        }
                    }
                });
            }
            
            // Save changes button
            const saveBtn = editModal.querySelector('.save-changes-btn');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => {
                    this.saveBookmarkChanges();
                });
            }
        }
    },

    openEditModal(card) {
        const modal = document.getElementById('editModal');
        if (!modal || !card) return;
        
        const bookmarkId = card.dataset.id;
        const title = card.querySelector('.title')?.textContent || '';
        const description = card.querySelector('.description')?.textContent || '';
        const mainCategory = card.dataset.mainCategory;
        const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => cat.textContent);
        const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);

        // Fill form fields
        const idField = modal.querySelector('#editBookmarkId');
        if (idField) idField.value = bookmarkId;
        
        const titleField = modal.querySelector('#editTitle');
        if (titleField) titleField.value = title;
        
        const descriptionField = modal.querySelector('#editDescription');
        if (descriptionField) descriptionField.value = description;
        
        // Select main category
        const mainCategorySelect = modal.querySelector('#mainCategory');
        if (mainCategorySelect && mainCategory) {
            for (let i = 0; i < mainCategorySelect.options.length; i++) {
                if (mainCategorySelect.options[i].value === mainCategory) {
                    mainCategorySelect.selectedIndex = i;
                    break;
                }
            }
        }

        // Add subcategories
        const subcategoriesList = modal.querySelector('#subcategoriesList');
        if (subcategoriesList) {
            subcategoriesList.innerHTML = subcategories.map(subcategory => 
                this.createSubcategoryItem(subcategory)
            ).join('');
        }

        // Add tags
        const tagsList = modal.querySelector('#tagsList');
        if (tagsList) {
            tagsList.innerHTML = tags.map(tag => 
                this.createTagItem(tag)
            ).join('');
        }

        // Open modal
        modal.classList.add('active');
    },

    createSubcategoryItem(subcategory) {
        return `
            <div class="item">
                <span>${subcategory}</span>
                <button class="remove-item-btn" onclick="ModalManager.removeItem(this, 'subcategory')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },

    createTagItem(tag) {
        return `
            <div class="item">
                <span>${tag}</span>
                <button class="remove-item-btn" onclick="ModalManager.removeItem(this, 'tag')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },

    removeItem(button, type) {
        const item = button.closest('.item');
        if (item) {
            item.remove();
        }
    },

    saveBookmarkChanges() {
        const modal = document.getElementById('editModal');
        if (!modal) return;
        
        const bookmarkId = modal.querySelector('#editBookmarkId')?.value;
        const title = modal.querySelector('#editTitle')?.value;
        const description = modal.querySelector('#editDescription')?.value;
        const mainCategory = modal.querySelector('#mainCategory')?.value;
        
        const subcategories = Array.from(modal.querySelectorAll('#subcategoriesList .item span')).map(span => span.textContent);
        const tags = Array.from(modal.querySelectorAll('#tagsList .item span')).map(span => span.textContent);
        
        // Validate required fields
        if (!title || !mainCategory) {
            alert('Title and main category are required!');
            return;
        }
        
        // Prepare data for submission
        const formData = new FormData();
        formData.append('id', bookmarkId);
        formData.append('title', title);
        formData.append('description', description || '');
        formData.append('main_category', mainCategory);
        formData.append('subcategories', JSON.stringify(subcategories));
        formData.append('tags', JSON.stringify(tags));
        
        // Send AJAX request
        fetch('/edit-bookmark/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                modal.classList.remove('active');
                
                // Update card in UI
                const card = document.querySelector(`.bookmark-card[data-id="${bookmarkId}"]`);
                if (card) {
                    card.querySelector('.title').textContent = title;
                    card.querySelector('.description').textContent = description || '';
                    
                    // Update subcategories
                    const subcategoriesContainer = card.querySelector('.subcategories');
                    if (subcategoriesContainer) {
                        subcategoriesContainer.innerHTML = subcategories.map(sub => 
                            `<a href="/subcategories/?subcategory=${encodeURIComponent(sub)}" class="subcategory-tab">${sub}</a>`
                        ).join('');
                    }
                    
                    // Update tags
                    const tagsContainer = card.querySelector('.card-tags');
                    if (tagsContainer) {
                        tagsContainer.innerHTML = tags.map(tag => 
                            `<a href="/tags/?tag=${encodeURIComponent(tag)}" class="tag">${tag}</a>`
                        ).join('');
                    }
                }
                
                // Show success message
                alert('Bookmark updated successfully!');
            } else {
                alert('Error updating bookmark: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating the bookmark.');
        });
    }
}; 