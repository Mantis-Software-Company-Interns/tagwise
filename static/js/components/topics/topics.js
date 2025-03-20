document.addEventListener('DOMContentLoaded', function() {
    // Initialize bookmark cards
    initializeBookmarkCards();
    
    // Initialize URL modal
    initializeUrlModal();
    
    // Initialize details modal
    initializeDetailsModal();
    
    // Initialize subcategory navigation
    initializeSubcategoryNav();
});

function initializeBookmarkCards() {
    // More menu functionality
    document.querySelectorAll('.more-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const menu = this.nextElementSibling;
            const allMenus = document.querySelectorAll('.more-menu');
            allMenus.forEach(m => {
                if (m !== menu) m.classList.remove('show');
            });
            menu.classList.toggle('show');
        });
    });

    // Close more menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.more-btn') && !e.target.closest('.more-menu')) {
            document.querySelectorAll('.more-menu').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });

    // Menu item actions
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.bookmark-card');
            const bookmarkId = card.dataset.id;
            const action = this.textContent.trim().toLowerCase();

            switch(action) {
                case 'edit':
                    // Handle edit action
                    break;
                case 'favorite':
                    // Handle favorite action
                    break;
                case 'archive':
                    // Handle archive action
                    break;
                case 'edit tags':
                    // Handle edit tags action
                    break;
                case 'delete':
                    if (confirm('Are you sure you want to delete this bookmark?')) {
                        deleteBookmark(bookmarkId);
                    }
                    break;
            }
        });
    });

    // Expand button functionality
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.bookmark-card');
            const bookmarkId = card.dataset.id;
            showBookmarkDetails(bookmarkId);
        });
    });
}

function initializeUrlModal() {
    const modal = document.getElementById('urlModal');
    const addUrlBtn = document.getElementById('addUrlBtn');
    const emptyAddUrlBtn = document.getElementById('emptyAddUrlBtn');
    const closeBtn = modal.querySelector('.close-btn');
    const urlForm = document.getElementById('urlForm');

    function openModal() {
        modal.classList.add('show');
    }

    function closeModal() {
        modal.classList.remove('show');
    }

    addUrlBtn.addEventListener('click', openModal);
    emptyAddUrlBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);

    urlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const url = document.getElementById('url').value;
        
        try {
            const response = await fetch('/api/bookmarks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    url: url,
                    category: getUrlParameter('category'),
                    subcategory: getUrlParameter('subcategory')
                })
            });

            if (response.ok) {
                window.location.reload();
            } else {
                const data = await response.json();
                alert(data.error || 'Failed to add bookmark');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add bookmark');
        }
    });
}

function initializeDetailsModal() {
    const modal = document.getElementById('detailsModal');
    const closeBtn = modal.querySelector('.close-modal-btn');

    closeBtn.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    });
}

function initializeSubcategoryNav() {
    const navItems = document.querySelectorAll('.subcategory-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

async function showBookmarkDetails(bookmarkId) {
    try {
        const response = await fetch(`/api/bookmarks/${bookmarkId}/`);
        const bookmark = await response.json();
        
        const modal = document.getElementById('detailsModal');
        modal.querySelector('.bookmark-title').textContent = bookmark.title;
        modal.querySelector('.bookmark-url').href = bookmark.url;
        modal.querySelector('.bookmark-url').textContent = bookmark.url;
        modal.querySelector('.bookmark-description').textContent = bookmark.description;
        modal.querySelector('.bookmark-date').textContent = new Date(bookmark.created_at).toLocaleString();
        
        const categoriesContainer = modal.querySelector('.bookmark-categories');
        categoriesContainer.innerHTML = bookmark.subcategories.map(sub => 
            `<a href="/topics/?category=${encodeURIComponent(bookmark.category)}&subcategory=${encodeURIComponent(sub.name)}" class="subcategory-tab">${sub.name}</a>`
        ).join('');
        
        const tagsContainer = modal.querySelector('.bookmark-tags');
        tagsContainer.innerHTML = bookmark.tags.map(tag => 
            `<a href="/tagged_bookmarks/?tag=${encodeURIComponent(tag.name)}" class="tag">${tag.name}</a>`
        ).join('');
        
        modal.classList.add('show');
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to load bookmark details');
    }
}

async function deleteBookmark(bookmarkId) {
    try {
        const response = await fetch(`/api/bookmarks/${bookmarkId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            const card = document.querySelector(`.bookmark-card[data-id="${bookmarkId}"]`);
            card.remove();
        } else {
            alert('Failed to delete bookmark');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to delete bookmark');
    }
}

// Utility functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
} 