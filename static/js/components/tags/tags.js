document.addEventListener('DOMContentLoaded', () => {
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    const allTagsSection = document.querySelector('.all-tags-section');
    const recentTagsSection = document.querySelector('.recent-tags-section');
    
    // Initialize
    initializeFilters();
    
    // Filter functionality
    function initializeFilters() {
        if (!filterButtons.length) return;
        
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active filter
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.getAttribute('data-filter');
                
                if (filter === 'all') {
                    allTagsSection.style.display = 'block';
                    recentTagsSection.style.display = 'none';
                } else if (filter === 'recent') {
                    allTagsSection.style.display = 'none';
                    recentTagsSection.style.display = 'block';
                }
            });
        });
    }
    
    // Add search functionality for tags
    const searchInput = document.querySelector('.search-container input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            filterTags(searchTerm);
        }, 300));
    }
    
    // Filter tags based on search input
    function filterTags(searchTerm) {
        const tagCards = document.querySelectorAll('.tag-card');
        
        tagCards.forEach(card => {
            const tagName = card.querySelector('.tag-name').textContent.toLowerCase();
            
            if (tagName.includes(searchTerm) || searchTerm === '') {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
        
        // Check if any tags are visible in each group
        const tagGroups = document.querySelectorAll('.tag-group');
        tagGroups.forEach(group => {
            const visibleTags = Array.from(group.querySelectorAll('.tag-card')).filter(card => {
                return card.style.display !== 'none';
            });
            
            // Show/hide the group heading based on if there are visible tags
            const heading = group.querySelector('h3');
            if (heading) {
                heading.style.display = visibleTags.length > 0 ? 'block' : 'none';
            }
            
            // Show/hide the entire group
            group.style.display = visibleTags.length > 0 ? 'block' : 'none';
        });
        
        // Show empty state if no tags are found
        const allTags = document.querySelectorAll('.tag-card');
        const visibleTags = Array.from(allTags).filter(tag => tag.style.display !== 'none');
        
        // Find or create empty state
        let emptyState = document.querySelector('.no-results');
        if (!emptyState && visibleTags.length === 0 && searchTerm !== '') {
            emptyState = document.createElement('div');
            emptyState.className = 'empty-state no-results';
            emptyState.innerHTML = `
                <i class="material-icons">search_off</i>
                <h3>No Tags Found</h3>
                <p>No tags match your search for "${searchTerm}"</p>
            `;
            
            // Append to the correct section
            if (allTagsSection.style.display !== 'none') {
                allTagsSection.appendChild(emptyState);
            } else if (recentTagsSection.style.display !== 'none') {
                recentTagsSection.appendChild(emptyState);
            }
        } else if (emptyState) {
            // Update or remove the empty state
            if (visibleTags.length === 0 && searchTerm !== '') {
                emptyState.querySelector('p').textContent = `No tags match your search for "${searchTerm}"`;
            } else {
                emptyState.remove();
            }
        }
    }
});

// Helper function: Debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
} 