document.addEventListener('DOMContentLoaded', () => {
    const newCollectionCard = document.querySelector('.new-collection');
    const modal = document.getElementById('newCollectionModal');
    const closeBtn = modal.querySelector('.close-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const saveBtn = modal.querySelector('.save-collection-btn');
    const iconSelector = modal.querySelector('.selected-icon');
    const iconGrid = modal.querySelector('.icon-grid');
    const searchInput = modal.querySelector('.bookmarks-search input');
    
    // Modal open/close
    newCollectionCard.addEventListener('click', () => {
        modal.classList.add('active');
    });

    [closeBtn, cancelBtn].forEach(btn => {
        btn.addEventListener('click', () => {
            modal.classList.remove('active');
            resetForm();
        });
    });

    // Icon selector
    iconSelector.addEventListener('click', () => {
        iconGrid.classList.toggle('active');
    });

    iconGrid.querySelectorAll('i').forEach(icon => {
        icon.addEventListener('click', () => {
            const selectedIcon = document.getElementById('selectedIcon');
            selectedIcon.textContent = icon.textContent;
            iconGrid.classList.remove('active');
        });
    });

    // Click outside check
    document.addEventListener('click', (e) => {
        if (!iconSelector.contains(e.target)) {
            iconGrid.classList.remove('active');
        }
    });

    // Drag and drop operations
    setupDragAndDrop();

    // Search functionality
    searchInput.addEventListener('input', (e) => {
        filterBookmarks(e.target.value);
    });

    // Collection saving
    saveBtn.addEventListener('click', saveCollection);
    
    // Collection card click
    setupCollectionCardClicks();
});

function setupCollectionCardClicks() {
    const collectionCards = document.querySelectorAll('.collection-card:not(.new-collection)');
    
    collectionCards.forEach(card => {
        card.addEventListener('click', () => {
            const collectionId = card.dataset.id;
            // Redirect to collection detail page or open a modal with collection details
            window.location.href = `/tagwise/collections/${collectionId}/`;
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
    const bookmarks = document.querySelectorAll('#availableBookmarks .bookmark-item');
    searchTerm = searchTerm.toLowerCase();

    bookmarks.forEach(bookmark => {
        const title = bookmark.querySelector('h4').textContent.toLowerCase();
        const url = bookmark.querySelector('p').textContent.toLowerCase();
        
        if (title.includes(searchTerm) || url.includes(searchTerm)) {
            bookmark.style.display = '';
        } else {
            bookmark.style.display = 'none';
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
        alert('Please enter a collection name');
        return;
    }
    
    if (selectedBookmarks.length === 0) {
        alert('Please add at least one bookmark to your collection');
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
    fetch('/tagwise/api/create-collection/', {
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
            // Reload page to show new collection
            window.location.reload();
        } else {
            alert('Error creating collection: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error creating collection:', error);
        alert('Error creating collection. Please try again.');
    });
    
    // Close modal and reset form
    document.getElementById('newCollectionModal').classList.remove('active');
    resetForm();
}

function resetForm() {
    document.getElementById('collectionName').value = '';
    document.getElementById('collectionDescription').value = '';
    document.getElementById('selectedIcon').textContent = 'collections_bookmark';
    document.getElementById('selectedBookmarks').innerHTML = `
        <div class="empty-state">
            <i class="material-icons">drag_indicator</i>
            <p>Drag bookmarks here</p>
        </div>
    `;
} 