// This file now handles additional functionality for the subcategories page
// The main rendering of subcategories is now handled by the Django template

document.addEventListener('DOMContentLoaded', () => {
    // Add search functionality
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', filterSubcategories);
    }
});

function filterSubcategories() {
    const searchInput = document.querySelector('input[type="search"]');
    const searchTerm = searchInput.value.toLowerCase();
    const subcategoryCards = document.querySelectorAll('.subcategory-card');
    
    subcategoryCards.forEach(card => {
        const subcategoryName = card.querySelector('h3').textContent.toLowerCase();
        const topics = Array.from(card.querySelectorAll('.topic')).map(topic => topic.textContent.toLowerCase());
        
        // Check if subcategory name or any topic contains the search term
        const matchesSearch = subcategoryName.includes(searchTerm) || 
                             topics.some(topic => topic.includes(searchTerm));
        
        card.style.display = matchesSearch ? 'flex' : 'none';
    });
    
    // Show empty state if no results
    const visibleCards = document.querySelectorAll('.subcategory-card[style="display: flex"]');
    const emptyState = document.querySelector('.empty-state') || createEmptySearchState();
    
    if (visibleCards.length === 0 && searchTerm !== '') {
        if (!document.querySelector('.empty-search-state')) {
            document.getElementById('subcategoriesGrid').appendChild(emptyState);
        }
        emptyState.style.display = 'flex';
    } else {
        emptyState.style.display = 'none';
    }
}

function createEmptySearchState() {
    const emptyState = document.createElement('div');
    emptyState.className = 'empty-state empty-search-state';
    emptyState.style.display = 'none';
    
    emptyState.innerHTML = `
        <i class="material-icons">search</i>
        <h3>No Results Found</h3>
        <p>Try a different search term</p>
    `;
    
    return emptyState;
} 