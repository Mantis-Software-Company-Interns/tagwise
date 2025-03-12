// Details Modal
// Handles the bookmark details modal functionality

const DetailsModal = {
    initialize() {
        this.setupDetailsModal();
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
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });

        // Close when clicking outside modal content
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    },
    
    updateModalContent(card) {
        const modal = document.getElementById('detailsModal');
        
        // Get main categories
        const mainCategoriesStr = card.dataset.mainCategories || '';
        const mainCategories = mainCategoriesStr.split(',').filter(cat => cat.trim());
        
        // Update categories
        const categoriesContainer = modal.querySelector('.bookmark-categories');
        if (categoriesContainer) {
            categoriesContainer.innerHTML = mainCategories.map(category => 
                `<span class="category-badge">${category}</span>`
            ).join('');
            
            if (mainCategories.length === 0) {
                categoriesContainer.innerHTML = '<span class="no-data">No categories</span>';
            }
        }
        
        // Get subcategories
        const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => cat.textContent);
        
        // Update subcategories
        const subcategoriesContainer = modal.querySelector('.bookmark-subcategories');
        if (subcategoriesContainer) {
            subcategoriesContainer.innerHTML = subcategories.map(subcategory => 
                `<span class="subcategory-badge">${subcategory}</span>`
            ).join('');
            
            if (subcategories.length === 0) {
                subcategoriesContainer.innerHTML = '<span class="no-data">No subcategories</span>';
            }
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
        const tagsContainer = modal.querySelector('.bookmark-tags');
        if (tagsContainer) {
            const tags = Array.from(card.querySelectorAll('.tag')).map(tag => ({
                name: tag.textContent,
                url: tag.href
            }));
            
            tagsContainer.innerHTML = tags.map(tag => 
                `<a href="${tag.url}" class="tag">${tag.name}</a>`
            ).join('');
            
            if (tags.length === 0) {
                tagsContainer.innerHTML = '<span class="no-data">No tags</span>';
            }
        }
        
        // Update image and link
        const previewImage = modal.querySelector('.preview-image');
        if (previewImage) {
            const thumbnail = card.querySelector('.thumbnail');
            if (thumbnail) {
                previewImage.src = thumbnail.src;
            }
        }
        
        const visitLink = modal.querySelector('.visit-link');
        if (visitLink) {
            const thumbnailLink = card.querySelector('.thumbnail-link');
            if (thumbnailLink) {
                visitLink.href = thumbnailLink.href;
            }
        }
    }
}; 