// Category Utilities
// Handles category formatting and manipulation

const CategoryUtils = {
    createCategoryItem(category) {
        return `
            <div class="category-item">
                ${category}
                <button class="remove-btn" onclick="CategoryUtils.removeItem(this, 'category')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },
    
    createSubcategoryItem(subcategory) {
        return `
            <div class="subcategory-item">
                ${subcategory}
                <button class="remove-btn" onclick="CategoryUtils.removeItem(this, 'subcategory')">
                    <i class="material-icons">close</i>
                </button>
            </div>
        `;
    },
    
    createSubcategoryLink(category, subcategory) {
        return `
            <a href="topics.html?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}" 
               class="subcategory-tab">
                ${subcategory}
            </a>
        `;
    },
    
    addCategory() {
        const input = document.getElementById('categoryInput');
        const category = input.value.trim();
        
        if (category) {
            const categoriesList = document.getElementById('categoriesList');
            categoriesList.insertAdjacentHTML('beforeend', this.createCategoryItem(category));
            input.value = '';
        }
    },
    
    removeItem(button, type) {
        button.closest(`.${type}-item`).remove();
    }
}; 