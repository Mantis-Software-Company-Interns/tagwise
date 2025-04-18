// Bookmark Manager
// Handles bookmark operations (edit, delete, favorite, archive)

const BookmarkManager = {
    initialize() {
        // Initialize BookmarkActions
        BookmarkActions.initialize();
        
        // Setup additional bookmark functionality
        this.setupBookmarkFilters();
        this.setupBookmarkSearch();
    },
    
    setupBookmarkFilters() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        if (!filterButtons.length) return;
        
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active filter
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.dataset.filter;
                this.filterBookmarks(filter);
            });
        });
    },
    
    filterBookmarks(filter) {
        const cards = document.querySelectorAll('.bookmark-card');
        
        cards.forEach(card => {
            // Önce searching sınıfını kaldır
            card.classList.remove('searching');
            card.classList.remove('hidden');
            
            switch(filter) {
                case 'favorites':
                    if (!card.classList.contains('favorite')) {
                        card.classList.add('hidden');
                    }
                    break;
                case 'archived':
                    if (!card.classList.contains('archived')) {
                        card.classList.add('hidden');
                    }
                    break;
                // Add more filters as needed
            }
        });
    },
    
    setupBookmarkSearch() {
        const searchInput = document.querySelector('.search-input');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            this.searchBookmarks(query);
        });
    },
    
    searchBookmarks(query) {
        const cards = document.querySelectorAll('.bookmark-card');
        const grid = document.querySelector('.grid');
        
        // Arama yapılıyor mu?
        if (grid) {
            if (query) {
                grid.classList.add('searching');
            } else {
                grid.classList.remove('searching');
            }
        }
        
        if (!query) {
            // Arama yoksa tüm kartları göster ve arama sınıfını kaldır
            cards.forEach(card => {
                card.classList.remove('searching');
                card.classList.remove('hidden');
            });
            return;
        }
        
        cards.forEach(card => {
            const title = card.querySelector('.title').textContent.toLowerCase();
            const description = card.querySelector('.description').textContent.toLowerCase();
            const tags = Array.from(card.querySelectorAll('.tag'))
                .map(tag => tag.textContent.toLowerCase());
            
            const matchesQuery = 
                title.includes(query) || 
                description.includes(query) || 
                tags.some(tag => tag.includes(query));
            
            // display style kullanmak yerine class ekle/çıkar
            card.classList.add('searching');
            if (matchesQuery) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
}; 