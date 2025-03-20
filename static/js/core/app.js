// Core Application
// Main initialization and event handling

document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    ThemeManager.initialize();

    // Initialize layout
    LayoutManager.initialize();

    // Initialize modals
    ModalManager.initialize();

    // Initialize bookmark actions
    BookmarkActions.initialize();
    
    // Initialize bookmark manager
    BookmarkManager.initialize();

    // Close menus when clicking outside
    document.addEventListener('click', (e) => {
        // Close sort menu when clicking outside
        const sortMenu = document.querySelector('.sort-menu');
        if (sortMenu && !e.target.closest('.sort-btn')) {
            sortMenu.classList.remove('active');
        }
        
        // Close more menus when clicking outside
        if (!e.target.closest('.more-btn') && !e.target.closest('.more-menu')) {
            document.querySelectorAll('.more-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });

    initializeSearch();
});

/**
 * Initialize search functionality
 */
function initializeSearch() {
    // Arama formu boş gönderildiğinde engelle
    const searchForms = document.querySelectorAll('.search-container form');
    
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="query"]');
            if (!searchInput || !searchInput.value.trim()) {
                e.preventDefault();
                return false;
            }
            
            // Form action URL'sini kontrol et ve gerekiyorsa güncelle
            const path = window.location.pathname;
            if (path.includes('/categories/') && !this.action.includes('search_categories')) {
                this.action = '/search/categories/';
            } else if (path.includes('/tags/') && !this.action.includes('search_tags')) {
                this.action = '/search/tags/';
            } else if (!path.includes('/categories/') && !path.includes('/tags/') && !this.action.includes('search_bookmarks')) {
                this.action = '/search/bookmarks/';
            }
        });
    });

    // Filtre dropdown işlevselliği
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const filterOptions = this.closest('.filter-dropdown').querySelector('.filter-options');
            
            // Diğer açık filter-options'ları kapat
            document.querySelectorAll('.filter-options.show').forEach(dropdown => {
                if (dropdown !== filterOptions) {
                    dropdown.classList.remove('show');
                }
            });
            
            filterOptions.classList.toggle('show');
        });
    });
    
    // Sayfa herhangi bir yerine tıklandığında açık dropdown'ları kapat
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.filter-dropdown')) {
            document.querySelectorAll('.filter-options.show').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
    
    // Dropdown içine tıklandığında event'in yukarı çıkmasını engelle
    document.querySelectorAll('.filter-options').forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // Add URL butonları için modal açma işlemi
    const addUrlBtns = document.querySelectorAll('.add-url-btn');
    const urlModal = document.getElementById('urlModal');
    
    if (addUrlBtns.length > 0 && urlModal) {
        addUrlBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // ModalManager üzerinden modali açalım
                if (typeof ModalManager !== 'undefined' && ModalManager.openModal) {
                    ModalManager.openModal('urlModal');
                } else {
                    // ModalManager yoksa basit bir şekilde açalım
                    urlModal.style.display = 'flex';
                }
            });
        });
    }
} 