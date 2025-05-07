document.addEventListener('DOMContentLoaded', () => {
    // Initialize edit collection modal
    initializeEditModal();
    
    // Initialize delete collection modal
    initializeDeleteModal();
    
    // Initialize add bookmark modal
    initializeAddBookmarkModal();
    
    // Initialize bookmark menu functionality
    initializeBookmarkMenus();

    // Initialize view toggle buttons (grid/list)
    initializeViewToggle();

    // Initialize share collection modal
    initializeShareModal();

    // Initialize action buttons (visit, copy)
    initializeActionButtons();
});

function initializeEditModal() {
    const editBtn = document.getElementById('editCollectionBtn');
    const modal = document.getElementById('editCollectionModal');
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const form = document.getElementById('editCollectionForm');
    const iconSelector = modal.querySelector('.selected-icon');
    const iconGrid = modal.querySelector('.icon-grid');
    
    // Open modal
    editBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });
    
    // Close modal
    [closeBtn, cancelBtn].forEach(btn => {
        btn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    });
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Icon selector
    iconSelector.addEventListener('click', () => {
        iconGrid.classList.toggle('active');
    });
    
    // Icon selection
    iconGrid.querySelectorAll('i').forEach(icon => {
        icon.addEventListener('click', () => {
            const selectedIcon = document.getElementById('selectedEditIcon');
            selectedIcon.textContent = icon.textContent;
            iconGrid.classList.remove('active');
        });
    });
    
    // Click outside check for icon grid
    document.addEventListener('click', (e) => {
        if (!iconSelector.contains(e.target)) {
            iconGrid.classList.remove('active');
        }
    });
    
    // Form submission
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        updateCollection();
    });
}

function updateCollection() {
    const collectionId = window.location.pathname.split('/').filter(Boolean).pop();
    const name = document.getElementById('editCollectionName').value;
    const description = document.getElementById('editCollectionDescription').value;
    const icon = document.getElementById('selectedEditIcon').textContent;
    
    if (!name) {
        showNotification('Please enter a collection name', 'error');
        return;
    }
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Prepare data
    const data = {
        id: collectionId,
        name,
        description,
        icon
    };
    
    // Send update request
    fetch('/api/update-collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Collection updated successfully', 'success');
            // Reload page to show updated collection
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('Error updating collection: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating collection', 'error');
    });
    
    // Close modal
    document.getElementById('editCollectionModal').classList.remove('active');
}

function initializeDeleteModal() {
    const deleteBtn = document.getElementById('deleteCollectionBtn');
    const modal = document.getElementById('deleteConfirmModal');
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const confirmBtn = modal.querySelector('.delete-confirm-btn');
    
    // Open modal
    deleteBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });
    
    // Close modal
    [closeBtn, cancelBtn].forEach(btn => {
        btn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    });
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Delete confirmation
    confirmBtn.addEventListener('click', () => {
        deleteCollection();
    });
}

function deleteCollection() {
    const collectionId = window.location.pathname.split('/').filter(Boolean).pop();
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Send delete request
    fetch('/api/delete-collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ id: collectionId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Collection deleted successfully', 'success');
            // Redirect to collections page
            setTimeout(() => {
                window.location.href = '/collections/';
            }, 1000);
        } else {
            showNotification('Error deleting collection: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error deleting collection', 'error');
    });
    
    // Close modal
    document.getElementById('deleteConfirmModal').classList.remove('active');
}

function initializeAddBookmarkModal() {
    const addBtn = document.getElementById('addBookmarkBtn');
    const emptyAddBtn = document.getElementById('emptyAddBookmarkBtn');
    const modal = document.getElementById('addBookmarkModal');
    
    if (!modal) {
        console.error('Add bookmark modal not found');
        return;
    }
    
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const addSelectedBtn = modal.querySelector('.add-selected-btn');
    const searchInput = document.getElementById('bookmarkSearch');
    
    console.log('Modal elements:', {
        addBtn: !!addBtn,
        emptyAddBtn: !!emptyAddBtn,
        modal: !!modal,
        closeBtn: !!closeBtn,
        cancelBtn: !!cancelBtn,
        addSelectedBtn: !!addSelectedBtn,
        searchInput: !!searchInput
    });
    
    // Open modal
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            console.log('Opening modal from add button');
            modal.classList.add('active');
        });
    }
    
    if (emptyAddBtn) {
        emptyAddBtn.addEventListener('click', () => {
            console.log('Opening modal from empty add button');
            modal.classList.add('active');
        });
    }
    
    // Close modal
    if (closeBtn && cancelBtn) {
        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        });
    }
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterBookmarks(e.target.value);
        });
    }
    
    // Add selected bookmarks
    if (addSelectedBtn) {
        addSelectedBtn.addEventListener('click', () => {
            addBookmarksToCollection();
        });
    }
    
    // Check if we have bookmarks
    const bookmarkItems = document.querySelectorAll('.available-bookmarks-grid .bookmark-item');
    console.log('Available bookmarks count:', bookmarkItems.length);
}

function filterBookmarks(searchTerm) {
    const bookmarks = document.querySelectorAll('.available-bookmarks-grid .bookmark-item');
    const bookmarksGrid = document.querySelector('.available-bookmarks-grid');
    searchTerm = searchTerm.toLowerCase();
    
    // Arama yapılıyor mu işaretliyoruz
    if (bookmarksGrid) {
        if (searchTerm) {
            bookmarksGrid.classList.add('searching');
        } else {
            bookmarksGrid.classList.remove('searching');
        }
    }
    
    bookmarks.forEach(bookmark => {
        const title = bookmark.querySelector('h4').textContent.toLowerCase();
        const url = bookmark.querySelector('p').textContent.toLowerCase();
        
        // CSS sınıflarıyla görünürlüğü kontrol ediyoruz
        bookmark.classList.add('searching');
        if (title.includes(searchTerm) || url.includes(searchTerm)) {
            bookmark.classList.remove('hidden');
        } else {
            bookmark.classList.add('hidden');
        }
    });
}

function addBookmarksToCollection() {
    const collectionId = window.location.pathname.split('/').filter(Boolean).pop();
    const selectedBookmarks = Array.from(
        document.querySelectorAll('.available-bookmarks-grid input[type="checkbox"]:checked')
    ).map(checkbox => parseInt(checkbox.value));
    
    if (selectedBookmarks.length === 0) {
        showNotification('Please select at least one bookmark', 'error');
        return;
    }
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Prepare data
    const data = {
        collection_id: collectionId,
        bookmark_ids: selectedBookmarks
    };
    
    // Send request
    fetch('/api/add-bookmarks-to-collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`${selectedBookmarks.length} bookmark(s) added to collection`, 'success');
            // Reload page to show updated bookmarks
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification('Error adding bookmarks: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error adding bookmarks', 'error');
    });
    
    // Close modal
    document.getElementById('addBookmarkModal').classList.remove('active');
}

function initializeBookmarkMenus() {
    // Add click event to bookmark menu buttons
    document.querySelectorAll('.bookmark-menu-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Find the existing menu element
            const menu = btn.nextElementSibling;
            
            // If menu doesn't exist, return
            if (!menu || !menu.classList.contains('bookmark-menu')) {
                console.error('Bookmark menu not found');
                return;
            }
            
            // Close any other open menus
            document.querySelectorAll('.bookmark-menu.active').forEach(m => {
                if (m !== menu) {
                    m.classList.remove('active');
                }
            });
            
            // Toggle this menu
            menu.classList.toggle('active');
            
            // Get bookmark ID and collection ID
            const bookmarkId = btn.getAttribute('data-id');
            const collectionId = window.location.pathname.split('/').filter(Boolean).pop();
            
            // Add click event to menu items if not already added
            if (!menu.dataset.initialized) {
                // View details menu item
                const viewDetailsBtn = menu.querySelector('.menu-item.view-details');
                if (viewDetailsBtn) {
                    viewDetailsBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        // Implement view details functionality if needed
                        showNotification('View details functionality will be implemented soon', 'info');
                        menu.classList.remove('active');
                    });
                }
                
                // Edit menu item
                const editBookmarkBtn = menu.querySelector('.menu-item.edit-bookmark');
                if (editBookmarkBtn) {
                    editBookmarkBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        // Redirect to edit page
                        window.location.href = `/tagwise/?edit=${bookmarkId}`;
                    });
                }
                
                // Remove from collection menu item
                const removeBookmarkBtn = menu.querySelector('.menu-item.remove-from-collection');
                if (removeBookmarkBtn) {
                    removeBookmarkBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        if (confirm('Are you sure you want to remove this bookmark from the collection?')) {
                            removeBookmarkFromCollection(bookmarkId, collectionId);
                        }
                        menu.classList.remove('active');
                    });
                }
                
                // Delete menu item
                const deleteBookmarkBtn = menu.querySelector('.menu-item.delete-bookmark');
                if (deleteBookmarkBtn) {
                    deleteBookmarkBtn.addEventListener('click', (e) => {
                        e.preventDefault();
                        if (confirm('Are you sure you want to delete this bookmark? This will remove it from all collections.')) {
                            deleteBookmark(bookmarkId);
                        }
                        menu.classList.remove('active');
                    });
                }
                
                // Mark as initialized
                menu.dataset.initialized = 'true';
            }
            
            // Close menu when clicking outside
            const closeMenu = (e) => {
                if (!menu.contains(e.target) && e.target !== btn) {
                    menu.classList.remove('active');
                    document.removeEventListener('click', closeMenu);
                }
            };
            
            // Add event listener with a slight delay to prevent immediate closing
            setTimeout(() => {
                document.addEventListener('click', closeMenu);
            }, 10);
        });
    });
    
    // Close menus when pressing escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.bookmark-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
}

function removeBookmarkFromCollection(bookmarkId, collectionId) {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Send request
    fetch('/api/remove-bookmark-from-collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            bookmark_id: bookmarkId,
            collection_id: collectionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove bookmark card from DOM
            const card = document.querySelector(`.bookmark-card[data-id="${bookmarkId}"]`);
            if (card) {
                card.remove();
            }
            
            showNotification('Bookmark removed from collection', 'success');
            
            // If no bookmarks left, show empty state
            const bookmarkCards = document.querySelectorAll('.bookmark-card');
            if (bookmarkCards.length === 0) {
                const bookmarksGrid = document.querySelector('.bookmarks-grid');
                bookmarksGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="material-icons">bookmark_border</i>
                        <h3>No Bookmarks Yet</h3>
                        <p>This collection doesn't have any bookmarks yet.</p>
                        <button class="add-bookmark-btn" id="emptyAddBookmarkBtn">
                            <i class="material-icons">add_link</i>
                            <span>Add Your First Bookmark</span>
                        </button>
                    </div>
                `;
                
                // Reinitialize add bookmark modal for the new button
                document.getElementById('emptyAddBookmarkBtn').addEventListener('click', () => {
                    document.getElementById('addBookmarkModal').classList.add('active');
                });
            }
        } else {
            showNotification('Error removing bookmark: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error removing bookmark', 'error');
    });
}

function deleteBookmark(bookmarkId) {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Send delete request
    fetch('/api/delete-bookmark/', {
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
            
            showNotification('Bookmark deleted successfully', 'success');
            
            // If no bookmarks left, show empty state
            const bookmarkCards = document.querySelectorAll('.bookmark-card');
            if (bookmarkCards.length === 0) {
                const bookmarksGrid = document.querySelector('.bookmarks-grid');
                bookmarksGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="material-icons">bookmark_border</i>
                        <h3>No Bookmarks Yet</h3>
                        <p>This collection doesn't have any bookmarks yet.</p>
                        <button class="add-bookmark-btn" id="emptyAddBookmarkBtn">
                            <i class="material-icons">add_link</i>
                            <span>Add Your First Bookmark</span>
                        </button>
                    </div>
                `;
                
                // Reinitialize add bookmark modal for the new button
                document.getElementById('emptyAddBookmarkBtn').addEventListener('click', () => {
                    document.getElementById('addBookmarkModal').classList.add('active');
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

function initializeViewToggle() {
    const viewButtons = document.querySelectorAll('.view-btn');
    const bookmarksContainer = document.getElementById('bookmarksContainer');
    
    if (!viewButtons.length || !bookmarksContainer) return;
    
    viewButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            viewButtons.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Get view type
            const viewType = btn.getAttribute('data-view');
            
            // Update container class
            if (viewType === 'grid') {
                bookmarksContainer.classList.remove('list-view');
            } else if (viewType === 'list') {
                bookmarksContainer.classList.add('list-view');
            }
        });
    });
}

function initializeShareModal() {
    const shareBtn = document.getElementById('shareCollectionBtn');
    const modal = document.getElementById('shareCollectionModal');
    
    if (!shareBtn || !modal) return;
    
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.close-modal-btn');
    const copyLinkBtn = document.getElementById('copyShareLink');
    const socialButtons = modal.querySelectorAll('.social-btn');
    
    // Open modal
    shareBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });
    
    // Close modal
    [closeBtn, cancelBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                modal.classList.remove('active');
            });
        }
    });
    
    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Copy link button
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', () => {
            const linkInput = document.getElementById('shareLink');
            if (linkInput) {
                linkInput.select();
                document.execCommand('copy');
                showNotification('Link copied to clipboard', 'success');
            }
        });
    }
    
    // Social share buttons
    socialButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const platform = btn.getAttribute('data-platform');
            const url = encodeURIComponent(document.getElementById('shareLink').value);
            const title = encodeURIComponent(`Check out my collection: ${document.querySelector('.collection-details h1').textContent}`);
            
            let shareUrl = '';
            switch (platform) {
                case 'twitter':
                    shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                    break;
                case 'facebook':
                    shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                    break;
                case 'linkedin':
                    shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
                    break;
            }
            
            if (shareUrl) {
                window.open(shareUrl, '_blank', 'width=600,height=400');
            }
        });
    });
}

function initializeActionButtons() {
    // Visit buttons
    document.querySelectorAll('.action-btn.visit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const url = btn.getAttribute('data-url');
            if (url) {
                window.open(url, '_blank');
            }
        });
    });
    
    // Copy buttons
    document.querySelectorAll('.action-btn.copy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const url = btn.getAttribute('data-url');
            if (url) {
                // Create a temporary input element
                const temp = document.createElement('input');
                temp.value = url;
                document.body.appendChild(temp);
                
                // Select and copy
                temp.select();
                document.execCommand('copy');
                
                // Remove the temporary element
                document.body.removeChild(temp);
                
                showNotification('URL copied to clipboard', 'success');
            }
        });
    });
}