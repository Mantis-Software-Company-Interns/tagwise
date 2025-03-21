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
    
    moreButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const menu = btn.nextElementSibling;
            
            // Diğer açık menüleri kapat
            document.querySelectorAll('.more-menu.active').forEach(m => {
                if (m !== menu) {
                    m.classList.remove('active');
                }
            });
            
            // Bu menüyü aç/kapat
            menu.classList.toggle('active');
        });
    });
    
    // Sayfa tıklamasında açık menüleri kapat
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.more-btn') && !e.target.closest('.more-menu')) {
            document.querySelectorAll('.more-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
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
    searchTerm = searchTerm.toLowerCase();
    
    bookmarkItems.forEach(item => {
        const title = item.querySelector('.bookmark-title').textContent.toLowerCase();
        const url = item.querySelector('.bookmark-url').textContent.toLowerCase();
        
        if (title.includes(searchTerm) || url.includes(searchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

function saveCollection() {
    const name = document.getElementById('collectionName').value;
    const description = document.getElementById('collectionDescription').value;
    const icon = document.getElementById('selectedIcon').textContent;
    const selectedBookmarks = Array.from(document.querySelectorAll('#selectedBookmarks .bookmark-item'))
        .map(item => parseInt(item.dataset.id));

    if (!name) {
        showNotification('Please enter a collection name', 'error');
        return;
    }
    
    if (selectedBookmarks.length === 0) {
        showNotification('Please add at least one bookmark to your collection', 'error');
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
            showNotification('Error creating collection: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error creating collection:', error);
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
    const modal = document.getElementById('newCollectionModal');
    if (!modal) return;
    
    const iconSelector = modal.querySelector('.selected-icon');
    const iconGrid = modal.querySelector('.icon-grid');
    
    if (!iconSelector || !iconGrid) return;
    
    // Icon selector
    iconSelector.addEventListener('click', () => {
        iconGrid.classList.toggle('active');
    });

    iconGrid.querySelectorAll('i').forEach(icon => {
        icon.addEventListener('click', () => {
            const selectedIcon = document.getElementById('selectedIcon');
            if (selectedIcon) {
                selectedIcon.textContent = icon.textContent;
                iconGrid.classList.remove('active');
            }
        });
    });

    // Click outside check
    document.addEventListener('click', (e) => {
        if (iconSelector && !iconSelector.contains(e.target)) {
            iconGrid.classList.remove('active');
        }
    });
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