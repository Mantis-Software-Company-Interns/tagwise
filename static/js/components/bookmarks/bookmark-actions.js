// Bookmark Actions
// Handles bookmark operations (edit, delete, favorite, archive)

const BookmarkActions = {
    initialize() {
        this.setupDeleteFunctionality();
        this.setupBookmarkActions();
        this.setupMoreButtons();
        this.setupEditFunctionality();
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
    
    setupEditFunctionality() {
        document.querySelectorAll('.menu-item.edit-bookmark').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const card = e.target.closest('.bookmark-card');
                this.editBookmark(card);
            });
        });
    },
    
    setupBookmarkActions() {
        // Setup favorite toggle for favorite buttons
        document.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const card = e.target.closest('.bookmark-card');
                this.toggleFavorite(card);
            });
        });
        
        // Setup favorite toggle for menu items with star icon
        document.querySelectorAll('.menu-item').forEach(item => {
            const icon = item.querySelector('i.material-icons');
            if (icon && icon.textContent.trim() === 'star') {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const card = e.target.closest('.bookmark-card');
                    this.toggleFavorite(card);
                });
            }
        });
        
        // Setup archive action for archive buttons
        document.querySelectorAll('.archive-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const card = e.target.closest('.bookmark-card');
                this.archiveBookmark(card);
            });
        });
        
        // Setup archive action for menu items with archive icon
        document.querySelectorAll('.menu-item').forEach(item => {
            const icon = item.querySelector('i.material-icons');
            if (icon && icon.textContent.trim() === 'archive') {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const card = e.target.closest('.bookmark-card');
                    this.archiveBookmark(card);
                });
            }
        });
        
        // Setup edit tags action for menu items with tag icon
        document.querySelectorAll('.menu-item').forEach(item => {
            const icon = item.querySelector('i.material-icons');
            if (icon && icon.textContent.trim() === 'local_offer') {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const card = e.target.closest('.bookmark-card');
                    TagUtils.editTags(card);
                });
            }
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
        
        // Silme işlemini tekrar tekrar yapmamak için "deleting" sınıfı ekleyelim
        if (card.classList.contains('deleting')) {
            return; // Zaten silme işlemi devam ediyor
        }
        
        // İşlem devam ediyor olarak işaretle
        card.classList.add('deleting');

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
                // Add deleted class for animation
                card.classList.add('deleted');
                
                // Different animation duration based on layout
                const isCompact = card.closest('.grid') && card.closest('.grid').classList.contains('compact-view');
                const animationDuration = isCompact ? 200 : 300;
                
                // Remove card after animation
                setTimeout(() => {
                    card.remove();
                }, animationDuration);
            } else {
                card.classList.remove('deleting'); // İşlem durdu, işareti kaldır
                alert('Error deleting bookmark: ' + data.error);
            }
        })
        .catch(error => {
            card.classList.remove('deleting'); // İşlem durdu, işareti kaldır
            console.error('Error deleting bookmark:', error);
            alert('Error deleting bookmark. Please try again.');
        });
    },
    
    editBookmark(card) {
        // Open edit modal
        console.log('Edit bookmark:', card);
        
        // EditModal objesinin tanımlı olup olmadığını kontrol et
        if (typeof EditModal === 'undefined' || !EditModal) {
            console.error('EditModal objesi tanımlı değil!');
            return;
        }
        
        console.log('EditModal objesinin openEditModal fonksiyonu mevcut:', typeof EditModal.openEditModal === 'function');
        
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