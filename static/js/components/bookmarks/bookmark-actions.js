// Bookmark Actions
// Handles bookmark operations (edit, delete, favorite, archive)

const BookmarkActions = {
    initialize() {
        this.setupDeleteFunctionality();
        this.setupBookmarkActions();
        this.setupMoreButtons();
    },
    
    setupDeleteFunctionality() {
        document.querySelectorAll('.menu-item.delete').forEach(item => {
            item.addEventListener('click', (e) => {
                const card = e.target.closest('.bookmark-card');
                const bookmarkId = card.dataset.id;
                
                if (confirm('Are you sure you want to delete this bookmark?')) {
                    this.deleteBookmark(bookmarkId, card);
                }
            });
        });
    },
    
    setupBookmarkActions() {
        // Setup favorite toggle
        document.querySelectorAll('.favorite-btn, .menu-item:has(i.material-icons:contains("star"))').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const card = e.target.closest('.bookmark-card');
                this.toggleFavorite(card);
            });
        });
        
        // Setup archive action
        document.querySelectorAll('.archive-btn, .menu-item:has(i.material-icons:contains("archive"))').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const card = e.target.closest('.bookmark-card');
                this.archiveBookmark(card);
            });
        });
        
        // Setup edit tags action
        document.querySelectorAll('.menu-item:has(i.material-icons:contains("local_offer"))').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const card = e.target.closest('.bookmark-card');
                TagUtils.editTags(card);
            });
        });
    },
    
    setupMoreButtons() {
        // More button functionality
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
            
            // Make sure the button is visible
            btn.style.display = 'flex';
        });
    },
    
    deleteBookmark(bookmarkId, card) {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Make API call
        fetch('/api/delete-bookmark/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                id: bookmarkId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Remove card on success
                card.remove();
            } else {
                alert('Error deleting bookmark: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error deleting bookmark:', error);
            alert('Error deleting bookmark. Please try again.');
        });
    },
    
    editBookmark(card) {
        // Open edit modal
        console.log('Edit bookmark:', card);
        EditModal.openEditModal(card);
    },
    
    toggleFavorite(card) {
        card.classList.toggle('favorite');
        
        // Different visual effect based on layout
        const isListView = card.closest('.grid').classList.contains('list-view');
        if (isListView) {
            card.style.transition = 'background 0.3s ease';
        }
    },
    
    archiveBookmark(card) {
        card.classList.add('archived');
        
        // Different animation duration based on layout
        const isCompact = card.closest('.grid').classList.contains('compact-view');
        const animationDuration = isCompact ? 200 : 300;
        
        setTimeout(() => {
            card.style.display = 'none';
        }, animationDuration);
    }
}; 