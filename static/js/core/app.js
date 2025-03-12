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
}); 