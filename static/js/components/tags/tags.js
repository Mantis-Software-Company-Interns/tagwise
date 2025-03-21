document.addEventListener('DOMContentLoaded', () => {
    const tagCards = document.querySelectorAll('.tag-card');
    const overlay = document.getElementById('taggedBookmarksOverlay');
    const backBtn = overlay.querySelector('.back-btn');
    const searchInput = overlay.querySelector('.search-container input');
    const backdrop = overlay.querySelector('.overlay-backdrop');
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    const allTagsSection = document.querySelector('.all-tags-section');
    const recentTagsSection = document.querySelector('.recent-tags-section');
    
    // Add URL buttons
    const addUrlButtons = document.querySelectorAll('.add-url-btn');
    
    // Initialize
    initializeFilters();
    initializeTagCards();
    initializeAddUrlButtons();
    
    // Filter functionality
    function initializeFilters() {
        if (!filterButtons.length) return;
        
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active filter
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.getAttribute('data-filter');
                
                if (filter === 'all') {
                    allTagsSection.style.display = 'block';
                    recentTagsSection.style.display = 'none';
                } else if (filter === 'recent') {
                    allTagsSection.style.display = 'none';
                    recentTagsSection.style.display = 'block';
                }
            });
        });
    }
    
    // Initialize tag cards
    function initializeTagCards() {
        // Tag kartlarına tıklama olayı
        tagCards.forEach(card => {
            card.addEventListener('click', (e) => {
                // Prevent default only if it's not an anchor tag click
                if (e.target.tagName !== 'A') {
                    e.preventDefault();
                    const tag = card.dataset.tag;
                    const count = card.querySelector('.tag-count').textContent;
                    showTaggedBookmarks(tag, count);
                }
            });
        });
    }
    
    // Initialize Add URL buttons
    function initializeAddUrlButtons() {
        addUrlButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Check if URL modal exists in the DOM
                let urlModal = document.getElementById('urlModal');
                
                // If it doesn't exist, create it
                if (!urlModal) {
                    createUrlModal();
                    urlModal = document.getElementById('urlModal');
                }
                
                // Show the modal
                urlModal.classList.add('active');
                
                // Focus on the URL input
                const urlInput = document.getElementById('url');
                if (urlInput) urlInput.focus();
            });
        });
    }
    
    // Create URL Modal if it doesn't exist
    function createUrlModal() {
        const modalHTML = `
            <div class="modal" id="urlModal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Add New URL</h2>
                        <button class="close-btn">
                            <i class="material-icons">close</i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="url">Enter URL</label>
                            <input type="text" id="url" placeholder="https://example.com" autocomplete="off">
                        </div>
                        <div class="url-preview" id="urlPreview" style="display: none;">
                            <!-- Preview content will be loaded here -->
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="cancel-btn">Cancel</button>
                        <button class="analyze-btn" id="analyzeUrlBtn">
                            <i class="material-icons">search</i>
                            Analyze
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add event listeners to the new modal
        const modal = document.getElementById('urlModal');
        const closeBtn = modal.querySelector('.close-btn');
        const cancelBtn = modal.querySelector('.cancel-btn');
        const analyzeBtn = document.getElementById('analyzeUrlBtn');
        const urlInput = document.getElementById('url');
        
        // Close modal events
        closeBtn.addEventListener('click', () => modal.classList.remove('active'));
        cancelBtn.addEventListener('click', () => modal.classList.remove('active'));
        
        // Close when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
        
        // Analyze URL
        analyzeBtn.addEventListener('click', () => {
            const url = urlInput.value.trim();
            if (url) {
                analyzeUrl(url);
            } else {
                alert('Please enter a valid URL');
            }
        });
        
        // Enter key to analyze
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const url = urlInput.value.trim();
                if (url) {
                    analyzeUrl(url);
                } else {
                    alert('Please enter a valid URL');
                }
            }
        });
    }
    
    // Analyze URL function
    function analyzeUrl(url) {
        const preview = document.getElementById('urlPreview');
        preview.innerHTML = `
            <div class="loading-spinner">
                <i class="material-icons rotating">refresh</i>
                <span>Analyzing URL...</span>
            </div>
        `;
        preview.style.display = 'block';
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        // Make API call to analyze URL
        fetch('/tagwise/analyze-url/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ url })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Redirect to the URL analyzer page with the analyzed data
                window.location.href = `/tagwise/url-analyzer/?url=${encodeURIComponent(url)}`;
            } else {
                preview.innerHTML = `
                    <div class="error-message">
                        <i class="material-icons">error</i>
                        <p>${data.error || 'Error analyzing URL. Please try again.'}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error analyzing URL:', error);
            preview.innerHTML = `
                <div class="error-message">
                    <i class="material-icons">error</i>
                    <p>Error analyzing URL. Please try again.</p>
                </div>
            `;
        });
    }
    
    // Geri butonuna tıklama olayı
    backBtn.addEventListener('click', () => {
        closeOverlay();
    });

    // Backdrop'a tıklama olayı
    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
            closeOverlay();
        }
    });

    // Escape tuşu ile kapatma
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
            closeOverlay();
        }
    });

    // Arama işlevi
    searchInput.addEventListener('input', debounce((e) => {
        filterBookmarks(e.target.value);
    }, 300));
});

function showTaggedBookmarks(tag, count) {
    const overlay = document.getElementById('taggedBookmarksOverlay');
    const currentTag = overlay.querySelector('#currentTag');
    const bookmarkCount = overlay.querySelector('.bookmark-count');
    
    // Tag bilgilerini güncelle
    currentTag.textContent = tag;
    bookmarkCount.textContent = `${count} bookmarks`;
    
    // İlgili etiketleri yükle
    loadRelatedTags(tag);
    
    // Yer imlerini yükle
    loadTaggedBookmarks(tag);
    
    // Overlay'i göster
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeOverlay() {
    const overlay = document.getElementById('taggedBookmarksOverlay');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
}

function loadRelatedTags(tag) {
    const container = document.getElementById('relatedTags');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Show loading state
    container.innerHTML = `<div class="loading">Loading related tags...</div>`;
    
    // Fetch related tags from API
    fetch(`/tagwise/api/related-tags/?tag=${encodeURIComponent(tag)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.related_tags && data.related_tags.length > 0) {
            container.innerHTML = data.related_tags.map(relatedTag => `
                <button class="related-tag" onclick="showTaggedBookmarks('${relatedTag}')">
                    <i class="material-icons">local_offer</i>
                    ${relatedTag}
                </button>
            `).join('');
        } else {
            container.innerHTML = `<div class="no-related-tags">No related tags found</div>`;
        }
    })
    .catch(error => {
        console.error('Error loading related tags:', error);
        container.innerHTML = `<div class="error">Error loading related tags</div>`;
    });
}

function loadTaggedBookmarks(tag) {
    const grid = document.getElementById('taggedBookmarksGrid');
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Show loading state
    grid.innerHTML = `<div class="loading">Loading bookmarks...</div>`;
    
    // Fetch bookmarks from API
    fetch(`/tagwise/api/tagged-bookmarks/?tag=${encodeURIComponent(tag)}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.bookmarks && data.bookmarks.length > 0) {
            grid.innerHTML = data.bookmarks.map(bookmark => `
                <div class="bookmark-card">
                    <div class="card-header">
                        <button class="more-btn">
                            <i class="material-icons">more_vert</i>
                        </button>
                    </div>
                    <a href="${bookmark.url}" target="_blank" class="thumbnail-container">
                        <img src="${bookmark.thumbnail || '/media/placeholder.jpg'}" alt="Thumbnail" class="thumbnail">
                    </a>
                    <div class="card-content">
                        <a href="${bookmark.url}" target="_blank" class="title-link">
                            <h3 class="title">${bookmark.title}</h3>
                        </a>
                        <p class="description">${bookmark.description || 'No description available'}</p>
                        <div class="tags">
                            ${bookmark.tags.map(t => `
                                <span class="tag" onclick="showTaggedBookmarks('${t}')">${t}</span>
                            `).join('')}
                        </div>
                        <div class="card-footer">
                            <span class="date">${formatDate(bookmark.created_at)}</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            grid.innerHTML = `
                <div class="empty-bookmarks">
                    <i class="material-icons">bookmark_border</i>
                    <h3>No bookmarks found</h3>
                    <p>No bookmarks with the tag "${tag}" were found.</p>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error loading bookmarks:', error);
        grid.innerHTML = `
            <div class="error-message">
                <i class="material-icons">error</i>
                <p>Error loading bookmarks. Please try again.</p>
            </div>
        `;
    });
}

function filterBookmarks(searchTerm) {
    const cards = document.querySelectorAll('.bookmark-card');
    searchTerm = searchTerm.toLowerCase();

    cards.forEach(card => {
        const title = card.querySelector('.title').textContent.toLowerCase();
        const description = card.querySelector('.description').textContent.toLowerCase();
        
        if (title.includes(searchTerm) || description.includes(searchTerm)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

// Debounce yardımcı fonksiyonu
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