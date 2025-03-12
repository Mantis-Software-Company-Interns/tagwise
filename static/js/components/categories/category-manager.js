// Category Manager
// Handles category and subcategory operations

const CategoryManager = {
    initialize() {
        // Initialize category functionality
        this.setupCategoryNavigation();
    },

    setupCategoryNavigation() {
        // Handle category navigation
        document.querySelectorAll('.category-link, .subcategory-tab').forEach(link => {
            link.addEventListener('click', (e) => {
                // Let the default navigation happen, this is just for any additional functionality
                // that might be needed in the future
            });
        });
    },

    createCategoryItem(category) {
        return `
            <div class="item">
                <span>${category}</span>
                <button class="remove-item-btn" onclick="CategoryManager.removeItem(this, 'category')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },

    createSubcategoryLink(category, subcategory) {
        return `
            <a href="/subcategories/?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}" 
               class="subcategory-tab">
                ${subcategory}
            </a>
        `;
    },

    createTagLink(tag) {
        return `
            <a href="/tags/?tag=${encodeURIComponent(tag)}" class="tag">
                ${tag}
            </a>
        `;
    },

    addCategory() {
        const modal = document.getElementById('editModal');
        if (!modal) return;
        
        const input = modal.querySelector('#newCategory');
        if (!input || !input.value.trim()) return;
        
        const categoriesList = modal.querySelector('#categoriesList');
        if (!categoriesList) return;
        
        const categoryItem = this.createCategoryItem(input.value.trim());
        categoriesList.insertAdjacentHTML('beforeend', categoryItem);
        input.value = '';
    },

    removeItem(button, type) {
        const item = button.closest('.item');
        if (item) {
            item.remove();
        }
    }
}; 