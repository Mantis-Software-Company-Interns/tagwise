document.addEventListener('DOMContentLoaded', function() {
    // Main functions
    setupSearchAndFiltering();
    setupTabs();
    setupCollectionCardClicks();
    setupNewCollectionModal();
    setupIconSelection();
    setupDeleteConfirmationModal();
    setupEditCollectionModal();
    setupMoreButtons();
    setupEditActions();
    setupDeleteActions();
    setupBookmarkSelection();

    // Trigger initial load
    loadBookmarks(currentFilter, currentSort);
});

function setupCollectionCardClicks() {
    const collectionCards = document.querySelectorAll('.collection-card:not(.new-collection)');
    
    collectionCards.forEach(card => {
        card.addEventListener('click', (e) => {
            // Eğer tıklanan düğme veya menü ise, normal işlemi engelleme
            if (e.target.closest('.more-btn') || e.target.closest('.more-menu')) {
                e.stopPropagation();
                return;
            }
            
            const collectionId = card.dataset.id;
            // Yeni sekmede koleksiyon detay sayfasını aç
            window.open(`/collections/${collectionId}/`, '_blank');
        });
    });
}

// More butonlarını ve menülerini ayarlar
function setupMoreButtons() {
    const moreButtons = document.querySelectorAll('.more-btn');
    
    // Close all open menus function
    const closeAllMenus = () => {
        document.querySelectorAll('.more-menu.active').forEach(menu => {
            menu.classList.remove('active');
        });
    };
    
    moreButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            
            const menu = btn.nextElementSibling;
            
            // If this menu is already active, just close it
            if (menu.classList.contains('active')) {
                menu.classList.remove('active');
                return;
            }
            
            // Close all open menus
            closeAllMenus();
            
            // Open this menu
            menu.classList.add('active');
        });
    });
    
    // Close menus when clicking anywhere else on the page
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.more-btn') && !e.target.closest('.more-menu')) {
            closeAllMenus();
        }
    });
    
    // Close menus when pressing escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllMenus();
        }
    });
}

// Düzenleme alanı için olay dinleyicileri ekler
function setupEditActions() {
    const editButtons = document.querySelectorAll('.menu-item.edit-collection');
    
    editButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const collectionId = btn.dataset.id;
            openEditModal(collectionId);
            
            // Menüyü kapat
            const menu = btn.closest('.more-menu');
            if (menu) {
                menu.classList.remove('active');
            }
        });
    });
}

// Silme alanı için olay dinleyicileri ekler
function setupDeleteActions() {
    const deleteButtons = document.querySelectorAll('.menu-item.delete-collection');
    
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const collectionId = btn.dataset.id;
            openDeleteModal(collectionId);
            
            // Menüyü kapat
            const menu = btn.closest('.more-menu');
            if (menu) {
                menu.classList.remove('active');
            }
        });
    });
}

function setupDragAndDrop() {
    const availableList = document.getElementById('availableBookmarks');
    const selectedList = document.getElementById('selectedBookmarks');

    document.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('bookmark-item')) {
            e.target.classList.add('dragging');
        }
    });

    document.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('bookmark-item')) {
            e.target.classList.remove('dragging');
        }
    });

    [availableList, selectedList].forEach(list => {
        list.addEventListener('dragover', (e) => {
            e.preventDefault();
            list.classList.add('drag-over');
        });

        list.addEventListener('dragleave', () => {
            list.classList.remove('drag-over');
        });

        list.addEventListener('drop', (e) => {
            e.preventDefault();
            list.classList.remove('drag-over');
            
            const draggingItem = document.querySelector('.dragging');
            if (draggingItem) {
                const clone = draggingItem.cloneNode(true);
                if (list.id === 'selectedBookmarks') {
                    // Remove empty state
                    const emptyState = list.querySelector('.empty-state');
                    if (emptyState) {
                        emptyState.remove();
                    }
                }
                list.appendChild(clone);
                if (list.id === 'selectedBookmarks') {
                    draggingItem.remove();
                }
            }
        });
    });
}

function filterBookmarks(searchTerm) {
    const bookmarkItems = document.querySelectorAll('.bookmark-item');
    const bookmarksContainer = document.querySelector('.bookmarks-list');
    searchTerm = searchTerm.toLowerCase();
    
    // Arama yapılıyor mu işaretliyoruz
    if (bookmarksContainer) {
        if (searchTerm) {
            bookmarksContainer.classList.add('searching');
        } else {
            bookmarksContainer.classList.remove('searching');
        }
    }
    
    bookmarkItems.forEach(item => {
        const title = item.querySelector('.bookmark-title').textContent.toLowerCase();
        const url = item.querySelector('.bookmark-url').textContent.toLowerCase();
        
        // CSS sınıflarıyla görünürlüğü kontrol ediyoruz
        item.classList.add('searching');
        if (title.includes(searchTerm) || url.includes(searchTerm)) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
}

// Setup bookmark selection functionality
function setupBookmarkSelection() {
    const bookmarks = document.querySelectorAll('.bookmark-selector');
    const checkboxes = document.querySelectorAll('.bookmark-check');
    const clearSelectionBtn = document.getElementById('clearSelection');
    const selectedCountElem = document.getElementById('selectedCount');
    const previewContent = document.querySelector('.preview-content');
    const collapsePreviewBtn = document.getElementById('collapsePreview');
    
    // Track selected bookmarks
    let selectedBookmarks = [];
    
    // Add click event to entire bookmark selector
    bookmarks.forEach(bookmark => {
        bookmark.addEventListener('click', (e) => {
            // Don't toggle if clicking on a link
            if (e.target.tagName === 'A') return;
            
            const checkbox = bookmark.querySelector('input[type="checkbox"]');
            // Don't process if clicking directly on checkbox (it handles its own state)
            if (e.target === checkbox) return;
            
            // Toggle checkbox state
            checkbox.checked = !checkbox.checked;
            
            // Manually trigger change event
            const changeEvent = new Event('change');
            checkbox.dispatchEvent(changeEvent);
        });
    });
    
    // Add change event to checkboxes
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const bookmark = checkbox.closest('.bookmark-selector');
            const bookmarkId = bookmark.dataset.id;
            const title = bookmark.dataset.title;
            const url = bookmark.dataset.url;
            
            if (checkbox.checked) {
                // Add selected class to parent
                bookmark.classList.add('selected');
                
                // Add to selected array if not already there
                if (!selectedBookmarks.some(bm => bm.id === bookmarkId)) {
                    selectedBookmarks.push({
                        id: bookmarkId,
                        title: title,
                        url: url
                    });
                }
            } else {
                // Remove selected class
                bookmark.classList.remove('selected');
                
                // Remove from selected array
                selectedBookmarks = selectedBookmarks.filter(bm => bm.id !== bookmarkId);
            }
            
            // Update the counter
            updateSelectionCount();
            
            // Update the preview
            updateSelectionPreview();
        });
    });
    
    // Clear selection button
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', () => {
            // Uncheck all checkboxes
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
                
                // Remove selected class from parent
                const bookmark = checkbox.closest('.bookmark-selector');
                bookmark.classList.remove('selected');
            });
            
            // Clear selected array
            selectedBookmarks = [];
            
            // Update counter and preview
            updateSelectionCount();
            updateSelectionPreview();
        });
    }
    
    // Collapse/expand preview
    if (collapsePreviewBtn) {
        collapsePreviewBtn.addEventListener('click', () => {
            const previewContent = document.querySelector('.preview-content');
            const icon = collapsePreviewBtn.querySelector('i');
            
            if (previewContent.style.display === 'none') {
                previewContent.style.display = 'block';
                icon.textContent = 'expand_less';
            } else {
                previewContent.style.display = 'none';
                icon.textContent = 'expand_more';
            }
        });
    }
    
    // Update the selection counter
    function updateSelectionCount() {
        if (selectedCountElem) {
            selectedCountElem.textContent = selectedBookmarks.length;
        }
    }
    
    // Update the selection preview
    function updateSelectionPreview() {
        if (!previewContent) return;
        
        if (selectedBookmarks.length === 0) {
            previewContent.innerHTML = '<p class="empty-preview-message">No bookmarks selected</p>';
            return;
        }
        
        let previewHTML = '';
        selectedBookmarks.forEach(bookmark => {
            previewHTML += `
                <div class="preview-item" data-id="${bookmark.id}">
                    <h5 class="preview-item-title">${bookmark.title}</h5>
                    <button class="remove-preview-item" data-id="${bookmark.id}">
                        <i class="material-icons">close</i>
                    </button>
                </div>
            `;
        });
        
        previewContent.innerHTML = previewHTML;
        
        // Add remove buttons functionality
        const removeButtons = previewContent.querySelectorAll('.remove-preview-item');
        removeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const bookmarkId = button.dataset.id;
                
                // Find the checkbox for this bookmark and uncheck it
                const checkbox = document.querySelector(`.bookmark-selector[data-id="${bookmarkId}"] input[type="checkbox"]`);
                if (checkbox) {
                    checkbox.checked = false;
                    
                    // Manually trigger change event
                    const changeEvent = new Event('change');
                    checkbox.dispatchEvent(changeEvent);
                }
            });
        });
    }
}

function saveCollection() {
    const name = document.getElementById('collectionName').value;
    const description = document.getElementById('collectionDescription').value;
    const icon = document.getElementById('selectedIcon').textContent;
    
    // Get selected bookmarks from checkboxes
    const selectedBookmarks = Array.from(document.querySelectorAll('.bookmark-check:checked'))
        .map(checkbox => {
            const bookmarkSelector = checkbox.closest('.bookmark-selector');
            return parseInt(bookmarkSelector.dataset.id);
        });

    if (!name) {
        showNotification('Please enter a collection name', 'error');
        return;
    }
    
    if (selectedBookmarks.length === 0) {
        showNotification('Please select at least one bookmark for your collection', 'error');
        return;
    }

    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Save collection data (send to API)
    const collectionData = {
        name,
        description,
        icon,
        bookmarks: selectedBookmarks
    };

    // Show loading indication
    const saveBtn = document.querySelector('.save-collection-btn');
    const originalBtnText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="material-icons rotating">refresh</i> Creating...';
    saveBtn.disabled = true;

    // Make API call
    fetch('/api/create-collection/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(collectionData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification('Collection created successfully', 'success');
            // Reload page to show new collection
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            saveBtn.innerHTML = originalBtnText;
            saveBtn.disabled = false;
            showNotification('Error creating collection: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error creating collection:', error);
        saveBtn.innerHTML = originalBtnText;
        saveBtn.disabled = false;
        showNotification('Error creating collection. Please try again.', 'error');
    });
    
    // Close modal and reset form
    document.getElementById('newCollectionModal').classList.remove('active');
    resetForm();
}

function resetForm() {
    const form = document.getElementById('newCollectionForm');
    if (form) {
        form.reset();
    }
    
    // Reset selected bookmarks
    const selectedBookmarks = document.getElementById('selectedBookmarks');
    if (selectedBookmarks) {
        selectedBookmarks.innerHTML = '';
    }
    
    // Reset icon
    const selectedIcon = document.getElementById('selectedIcon');
    if (selectedIcon) {
        selectedIcon.textContent = 'folder';
    }
}

function setupEditCollectionModal() {
    const modal = document.getElementById('editCollectionModal');
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const saveBtn = document.getElementById('saveEditBtn');
    const iconSelector = modal.querySelector('.selected-icon');
    const iconGrid = modal.querySelector('.icon-grid');
    
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
    saveBtn.addEventListener('click', () => {
        updateCollection();
    });
}

function setupDeleteConfirmationModal() {
    const modal = document.getElementById('deleteConfirmModal');
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const confirmBtn = modal.querySelector('.delete-confirm-btn');
    
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

function openEditModal(collectionId) {
    const modal = document.getElementById('editCollectionModal');
    const nameInput = document.getElementById('editCollectionName');
    const descriptionInput = document.getElementById('editCollectionDescription');
    const iconElement = document.getElementById('selectedEditIcon');
    
    // Store the collection ID as a data attribute on the modal
    modal.dataset.collectionId = collectionId;
    
    // Find the collection card
    const collectionCard = document.querySelector(`.collection-card[data-id="${collectionId}"]`);
    
    // Get collection data from the card
    const name = collectionCard.querySelector('h3').textContent;
    const description = collectionCard.querySelector('.collection-description').textContent;
    const icon = collectionCard.querySelector('.collection-header i').textContent;
    
    // Populate the form
    nameInput.value = name;
    descriptionInput.value = description;
    iconElement.textContent = icon;
    
    // Show the modal
    modal.classList.add('active');
}

function openDeleteModal(collectionId) {
    const modal = document.getElementById('deleteConfirmModal');
    
    // Store the collection ID as a data attribute on the modal
    modal.dataset.collectionId = collectionId;
    
    // Show the modal
    modal.classList.add('active');
}

function updateCollection() {
    const modal = document.getElementById('editCollectionModal');
    const collectionId = modal.dataset.collectionId;
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
            // Update the collection card in the DOM
            const card = document.querySelector(`.collection-card[data-id="${collectionId}"]`);
            if (card) {
                card.querySelector('h3').textContent = name;
                card.querySelector('.collection-description').textContent = description;
                card.querySelector('.collection-header i').textContent = icon;
            }
            
            showNotification('Collection updated successfully', 'success');
        } else {
            showNotification('Error updating collection: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating collection. Please try again.', 'error');
    });
    
    // Close modal
    modal.classList.remove('active');
}

function deleteCollection() {
    const modal = document.getElementById('deleteConfirmModal');
    const collectionId = modal.dataset.collectionId;
    
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
            // Remove the collection card from the DOM
            const card = document.querySelector(`.collection-card[data-id="${collectionId}"]`);
            if (card) {
                card.remove();
            }
            
            showNotification('Collection deleted successfully', 'success');
        } else {
            showNotification('Error deleting collection: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error deleting collection. Please try again.', 'error');
    });
    
    // Close modal
    modal.classList.remove('active');
}

// Show notification function
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

// Set up the search and filtering functionality
function setupSearchAndFiltering() {
    const searchInput = document.querySelector('.bookmarks-search input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            filterBookmarks(e.target.value);
        });
    }
}

// Set up tabs if they exist
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    if (tabs.length) {
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelector('.tab.active').classList.remove('active');
                tab.classList.add('active');
                // Additional tab functionality
            });
        });
    }
}

// Set up new collection modal
function setupNewCollectionModal() {
    const newCollectionCard = document.querySelector('.new-collection');
    const modal = document.getElementById('newCollectionModal');
    
    if (!newCollectionCard || !modal) return;
    
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const saveBtn = modal.querySelector('.save-collection-btn');
    
    // Modal open/close
    newCollectionCard.addEventListener('click', () => {
        modal.classList.add('active');
    });

    [closeBtn, cancelBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                modal.classList.remove('active');
                resetForm();
            });
        }
    });
    
    // Collection saving
    if (saveBtn) {
        saveBtn.addEventListener('click', saveCollection);
    }
    
    // Setup drag and drop
    setupDragAndDrop();
}

// Set up icon selection
function setupIconSelection() {
    const iconSelectors = document.querySelectorAll('.icon-selector');
    
    iconSelectors.forEach(selector => {
        const selectedIcon = selector.querySelector('.selected-icon');
        const iconGrid = selector.querySelector('.icon-grid');
        const icons = iconGrid.querySelectorAll('i.material-icons');
        
        // Click on selected icon to show/hide grid
        selectedIcon.addEventListener('click', (e) => {
            e.preventDefault();
            iconGrid.classList.toggle('active');
        });
        
        // Click outside to close the icon grid
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.icon-selector') && iconGrid.classList.contains('active')) {
                iconGrid.classList.remove('active');
            }
        });
        
        // Click an icon to select it
        icons.forEach(icon => {
            icon.addEventListener('click', () => {
                // Update the selected icon
                const iconContent = icon.textContent;
                const iconToUpdate = selectedIcon.querySelector('i.material-icons');
                iconToUpdate.textContent = iconContent;
                
                // Close the grid
                iconGrid.classList.remove('active');
                
                // Add subtle animation
                selectedIcon.classList.add('icon-updated');
                setTimeout(() => {
                    selectedIcon.classList.remove('icon-updated');
                }, 300);
            });
        });
    });
    
    // Add CSS for animation
    const style = document.createElement('style');
    style.textContent = `
        .icon-updated {
            transform: scale(1.1);
            transition: transform 0.3s ease;
        }
    `;
    document.head.appendChild(style);
}

// Load bookmarks with current filter and sort options
function loadBookmarks(filter, sort) {
    // This is a placeholder function for loading bookmarks with filters
    console.log(`Loading bookmarks with filter: ${filter} and sort: ${sort}`);
    // Implementation would depend on your backend API
}

// Global variables for current filter and sort
let currentFilter = 'all';
let currentSort = 'date';

// Setup search and filtering for bookmarks in the new collection modal
function setupSearchAndFiltering() {
    const searchInput = document.getElementById('bookmarkSearch');
    const filterButtons = document.querySelectorAll('.filter-buttons .filter-btn');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            const searchTerm = e.target.value.toLowerCase().trim();
            filterBookmarkSelectors(searchTerm);
        }, 300));
    }
    
    if (filterButtons.length) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active button
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Apply filter
                const filter = btn.getAttribute('data-filter');
                applyBookmarkFilter(filter);
            });
        });
    }
    
    // Function to filter bookmarks based on search term
    function filterBookmarkSelectors(searchTerm) {
        const bookmarks = document.querySelectorAll('.bookmark-selector');
        
        bookmarks.forEach(bookmark => {
            const title = bookmark.querySelector('.bookmark-title').textContent.toLowerCase();
            const url = bookmark.querySelector('.bookmark-url').textContent.toLowerCase();
            
            if (title.includes(searchTerm) || url.includes(searchTerm) || searchTerm === '') {
                bookmark.style.display = 'flex';
            } else {
                bookmark.style.display = 'none';
            }
        });
        
        // Show no results message if needed
        const visibleBookmarks = Array.from(bookmarks).filter(b => b.style.display !== 'none');
        const container = document.querySelector('.bookmarks-selection-area');
        
        if (visibleBookmarks.length === 0 && container) {
            // Check if message already exists
            if (!document.querySelector('.no-search-results')) {
                const noResults = document.createElement('div');
                noResults.className = 'empty-state no-search-results';
                noResults.innerHTML = `
                    <i class="material-icons">search_off</i>
                    <h3>No Results</h3>
                    <p>No bookmarks match your search for "${searchTerm}"</p>
                `;
                container.appendChild(noResults);
            }
        } else {
            // Remove message if it exists
            const noResults = document.querySelector('.no-search-results');
            if (noResults) {
                noResults.remove();
            }
        }
    }
    
    // Function to apply filter (all, recent, popular)
    function applyBookmarkFilter(filter) {
        const bookmarks = document.querySelectorAll('.bookmark-selector');
        const now = new Date();
        
        switch(filter) {
            case 'recent':
                // Show only bookmarks added in the last 7 days
                // This is a simplified example - you would need to have date data in your bookmarks
                bookmarks.forEach(bookmark => {
                    // Example: Assuming you have a data-date attribute with ISO date string
                    const dateStr = bookmark.dataset.date;
                    if (dateStr) {
                        const date = new Date(dateStr);
                        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
                        bookmark.style.display = diffDays <= 7 ? 'flex' : 'none';
                    } else {
                        // If no date info, just show it
                        bookmark.style.display = 'flex';
                    }
                });
                break;
                
            case 'popular':
                // Show bookmarks sorted by popularity (visits, etc.)
                // This is a simplified example - you would need visit count data
                bookmarks.forEach(bookmark => {
                    // Example: Assuming you have a data-popularity attribute
                    const popularity = parseInt(bookmark.dataset.popularity || 0);
                    bookmark.style.display = popularity >= 5 ? 'flex' : 'none';
                });
                break;
                
            case 'all':
            default:
                // Show all bookmarks
                bookmarks.forEach(bookmark => {
                    bookmark.style.display = 'flex';
                });
                break;
        }
    }
}

// Helper function for debouncing
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