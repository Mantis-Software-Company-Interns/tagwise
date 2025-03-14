document.addEventListener('DOMContentLoaded', () => {
    // Initialize bookmark menu functionality
    initializeBookmarkMenus();
    
    // Initialize URL modal
    initializeUrlModal();
});

function initializeBookmarkMenus() {
    // Add click event to bookmark menu buttons
    document.querySelectorAll('.bookmark-menu-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Create menu element
            const menu = document.createElement('div');
            menu.className = 'bookmark-menu';
            
            // Get bookmark ID
            const bookmarkId = btn.getAttribute('data-id');
            
            // Add menu items
            menu.innerHTML = `
                <a href="#" class="menu-item edit-bookmark" data-id="${bookmarkId}">
                    <i class="material-icons">edit</i>
                    <span>Edit</span>
                </a>
                <a href="#" class="menu-item delete-bookmark" data-id="${bookmarkId}">
                    <i class="material-icons">delete</i>
                    <span>Delete</span>
                </a>
            `;
            
            // Position menu
            const rect = btn.getBoundingClientRect();
            menu.style.top = `${rect.bottom + window.scrollY}px`;
            menu.style.right = `${window.innerWidth - rect.right}px`;
            
            // Add to document
            document.body.appendChild(menu);
            
            // Add click event to edit menu item
            menu.querySelector('.edit-bookmark').addEventListener('click', (e) => {
                e.preventDefault();
                // Redirect to edit page
                window.location.href = `/tagwise/?edit=${bookmarkId}`;
            });
            
            // Add click event to delete menu item
            menu.querySelector('.delete-bookmark').addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to delete this bookmark?')) {
                    deleteBookmark(bookmarkId);
                }
            });
            
            // Close menu when clicking outside
            const closeMenu = (e) => {
                if (!menu.contains(e.target) && e.target !== btn) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            };
            
            // Add event listener with a slight delay to prevent immediate closing
            setTimeout(() => {
                document.addEventListener('click', closeMenu);
            }, 10);
        });
    });
}

function deleteBookmark(bookmarkId) {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Send delete request
    fetch('/tagwise/api/delete-bookmark/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ id: bookmarkId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove bookmark card from DOM
            const card = document.querySelector(`.bookmark-card[data-id="${bookmarkId}"]`);
            if (card) {
                card.remove();
            }
            
            // Show success message
            showNotification('Bookmark deleted successfully', 'success');
            
            // If no bookmarks left, show empty state
            const bookmarkCards = document.querySelectorAll('.bookmark-card');
            if (bookmarkCards.length === 0) {
                const topicsGrid = document.querySelector('.topics-grid');
                topicsGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="material-icons">bookmark_border</i>
                        <h3>No Bookmarks Left</h3>
                        <p>This subcategory doesn't have any bookmarks yet.</p>
                        <button class="add-url-btn" id="emptyAddUrlBtn">
                            <i class="material-icons">add_link</i>
                            <span>Add Your First Bookmark</span>
                </button>
                    </div>
                `;
                
                // Reinitialize URL modal for the new button
                document.getElementById('emptyAddUrlBtn').addEventListener('click', () => {
                    document.getElementById('urlModal').classList.add('active');
                });
            }
        } else {
            showNotification('Error deleting bookmark: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error deleting bookmark', 'error');
    });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="material-icons">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</i>
        <span>${message}</span>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide and remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

function initializeUrlModal() {
    // Add URL button functionality
    const addUrlBtn = document.getElementById('addUrlBtn');
    const emptyAddUrlBtn = document.getElementById('emptyAddUrlBtn');
    const urlModal = document.getElementById('urlModal');
    
    if (!urlModal) return;
    
    const closeBtn = urlModal.querySelector('.close-btn');
    
    function openUrlModal() {
        urlModal.classList.add('active');
        document.getElementById('url').focus();
    }
    
    if (addUrlBtn) {
        addUrlBtn.addEventListener('click', openUrlModal);
    }
    
    if (emptyAddUrlBtn) {
        emptyAddUrlBtn.addEventListener('click', openUrlModal);
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            urlModal.classList.remove('active');
        });
    }
    
    // Close modal when clicking outside
    urlModal.addEventListener('click', function(e) {
        if (e.target === urlModal) {
            urlModal.classList.remove('active');
        }
    });
    
    // URL form submission
    const urlForm = document.getElementById('urlForm');
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const url = document.getElementById('url').value.trim();
            if (url) {
                // Redirect to the main page with the URL in the query string
                window.location.href = `/tagwise/?url=${encodeURIComponent(url)}`;
            }
        });
    }
} 