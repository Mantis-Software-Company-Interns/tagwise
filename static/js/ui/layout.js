// Layout Manager
// Handles grid layout, card alignment, and more button visibility

const LayoutManager = {
    initialize() {
        this.setupLayoutButtons();
        this.setupSortFunctionality();
        this.updateMoreButtonVisibility();
        this.alignCardFooters();
        
        // Update more button visibility on window resize
        window.addEventListener('resize', this.updateMoreButtonVisibility);
        
        // Add CSS animations
        this.addCssAnimations();
    },
    
    setupLayoutButtons() {
        const grid = document.querySelector('.grid');
        const layoutButtons = document.querySelectorAll('.layout-btn');
        
        if (!grid || !layoutButtons.length) return;

        layoutButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Update active button style
                layoutButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Update grid classes
                const newLayout = btn.getAttribute('data-layout');
                grid.classList.remove('list-view');
                
                if (newLayout === 'list') {
                    grid.classList.add('list-view');
                }
            });
        });
        
        // Setup more menu buttons
        const moreButtons = document.querySelectorAll('.more-btn');
        
        moreButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const menu = btn.nextElementSibling;
                if (menu && menu.classList.contains('more-menu')) {
                    // Close other menus
                    document.querySelectorAll('.more-menu.active').forEach(m => {
                        if (m !== menu) m.classList.remove('active');
                    });
                    
                    // Toggle this menu
                    menu.classList.toggle('active');
                }
            });
        });
    },
    
    setupSortFunctionality() {
        const sortBtn = document.querySelector('.sort-btn');
        const sortMenu = document.querySelector('.sort-menu');
        const sortItems = document.querySelectorAll('.sort-item');
        const grid = document.querySelector('.grid');

        if (!sortBtn || !sortMenu || !grid) return;

        sortBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sortMenu.classList.toggle('active');
        });

        sortItems.forEach(item => {
            item.addEventListener('click', () => {
                // Update active sort option
                sortItems.forEach(si => si.classList.remove('active'));
                item.classList.add('active');
                
                const cards = Array.from(grid.querySelectorAll('.bookmark-card'));
                if (cards.length === 0) return;

                // Compare dates and sort
                cards.sort((a, b) => {
                    const dateA = new Date(a.querySelector('.date').textContent);
                    const dateB = new Date(b.querySelector('.date').textContent);
                    
                    return item.dataset.sort === 'newest' ? 
                        dateB.getTime() - dateA.getTime() : 
                        dateA.getTime() - dateB.getTime();
                });

                // Place sorted cards in DOM
                cards.forEach(card => grid.appendChild(card));
                sortMenu.classList.remove('active');
            });
        });
    },
    
    updateMoreButtonVisibility() {
        const moreButtons = document.querySelectorAll('.more-btn');
        
        moreButtons.forEach(btn => {
            btn.style.display = 'flex'; // Make all more buttons visible
        });
        
        // Update more button visibility on page load and window resize
        window.addEventListener('load', () => {
            moreButtons.forEach(btn => {
                btn.style.display = 'flex';
            });
        });
    },
    
    alignCardFooters() {
        const cards = document.querySelectorAll('.bookmark-card');
        
        cards.forEach(card => {
            const content = card.querySelector('.card-content');
            const footer = card.querySelector('.card-footer');
            
            if (!content || !footer) return;
            
            // Reset any previously set styles
            content.style.position = '';
            content.style.paddingBottom = '';
            footer.style.position = '';
            footer.style.bottom = '';
            footer.style.left = '';
            footer.style.right = '';
            
            // Ensure content has enough space for the footer
            content.style.minHeight = '200px';
            content.style.display = 'flex';
            content.style.flexDirection = 'column';
        });
    },
    
    addCssAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideOut {
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            
            @keyframes fadeOut {
                to {
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}; 