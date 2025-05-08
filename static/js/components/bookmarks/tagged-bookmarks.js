// Örnek veri yapısı (gerçek uygulamada API'den gelecek)
const taggedBookmarksData = {
    javascript: {
        name: 'javascript',
        bookmarks: [
            {
                title: 'Modern JavaScript Tutorial',
                url: 'https://javascript.info',
                description: 'Modern JavaScript Tutorial: simple, but detailed explanations with examples and tasks.',
                thumbnail: 'images/js-tutorial.jpg',
                date: '2024-02-27',
                tags: ['javascript', 'tutorial', 'web'],
                relatedTags: ['frontend', 'web', 'programming']
            },
            // ... diğer yer imleri
        ]
    },
    // ... diğer etiketler
};

document.addEventListener('DOMContentLoaded', () => {
    // URL'den tag parametresini al
    const urlParams = new URLSearchParams(window.location.search);
    const tag = urlParams.get('tag');
    
    if (tag) {
        // Başlığı güncelle
        document.getElementById('currentTag').textContent = tag;
        
        // İlgili etiketleri ve yer imlerini yükle
        loadRelatedTags(tag);
        loadBookmarks(tag);
    } else {
        // Geçersiz etiket durumunda tags.html'e yönlendir
        window.location.href = '/tags/';
    }
});

function loadRelatedTags(tag) {
    const relatedTagsContainer = document.getElementById('relatedTags');
    
    // API'den ilgili etiketleri al
    fetch(`/api/related-tags/?tag=${encodeURIComponent(tag)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.related_tags && data.related_tags.length > 0) {
                relatedTagsContainer.innerHTML = `
                    <div class="related-tags-header">
                        <h3>Related Tags</h3>
                    </div>
                    <div class="related-tags-list">
                        ${data.related_tags.map(relatedTag => `
                            <a href="/tagged-bookmarks/?tag=${encodeURIComponent(relatedTag)}" class="related-tag">
                                <i class="material-icons">local_offer</i>
                                ${relatedTag}
                            </a>
                        `).join('')}
                    </div>
                `;
            } else {
                relatedTagsContainer.innerHTML = `
                    <div class="related-tags-header">
                        <h3>Related Tags</h3>
                    </div>
                    <div class="related-tags-list">
                        <p class="empty-message">No related tags found</p>
                    </div>
                `;
            }
        })
        .catch(err => {
            console.error('Error fetching related tags:', err);
            relatedTagsContainer.innerHTML = `
                <div class="related-tags-header">
                    <h3>Related Tags</h3>
                </div>
                <div class="related-tags-list">
                    <p class="empty-message">Failed to load related tags</p>
                </div>
            `;
        });
}

function loadBookmarks(tag) {
    const grid = document.getElementById('bookmarksGrid');
    
    // API'den yer imlerini al
    fetch(`/api/tagged-bookmarks/?tag=${encodeURIComponent(tag)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.bookmarks && data.bookmarks.length > 0) {
                grid.innerHTML = data.bookmarks.map(bookmark => `
                    <div class="grid-item bookmark-card" data-main-categories="${bookmark.main_categories || ''}" data-id="${bookmark.id}">
                        <div class="card-header">
                            <button class="more-btn">
                                <i class="material-icons">more_vert</i>
                            </button>
                            <div class="more-menu">
                                <div class="menu-item edit-bookmark"><i class="material-icons">edit</i>Edit</div>
                                <div class="menu-item"><i class="material-icons">star</i>Favorite</div>
                                <div class="menu-item"><i class="material-icons">archive</i>Archive</div>
                                <div class="menu-item"><i class="material-icons">local_offer</i>Edit Tags</div>
                                <div class="menu-item delete"><i class="material-icons">delete</i>Delete</div>
                            </div>
                        </div>
                        <a href="${bookmark.url}" target="_blank" class="thumbnail-link">
                            <div class="thumbnail-container">
                                ${bookmark.has_screenshot 
                                    ? (bookmark.screenshot_path && bookmark.screenshot_path.startsWith('http')
                                        ? `<img src="${bookmark.screenshot_path}" alt="${bookmark.title}" class="thumbnail">`
                                        : `<img src="/media/${bookmark.screenshot_path}" alt="${bookmark.title}" class="thumbnail">`)
                                    : `<img src="/static/images/default-thumbnail.png" alt="${bookmark.title}" class="thumbnail">`
                                }
                            </div>
                        </a>
                        <div class="card-content">
                            <a href="${bookmark.url}" target="_blank" class="title-link">
                                <h3 class="title">${bookmark.title}</h3>
                            </a>
                            <p class="description">${bookmark.description || ''}</p>
                            <div class="tags">
                                ${(bookmark.tags || []).map(tag => `
                                    <a href="/tagged-bookmarks/?tag=${encodeURIComponent(tag)}" class="tag">${tag}</a>
                                `).join('')}
                            </div>
                            <div class="card-footer">
                                <button class="expand-btn">
                                    <i class="material-icons">info_outline</i>
                                </button>
                                <div class="date">${formatDate(bookmark.created_at)}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
                
                // Expand butonlarına event listener ekle
                setupDetailsModal();
            } else {
                grid.innerHTML = `
                    <div class="empty-state">
                        <i class="material-icons">bookmark_border</i>
                        <h3>No bookmarks with this tag</h3>
                        <p>Try another tag or add new bookmarks with this tag.</p>
                        <button class="add-url-btn">
                            <i class="material-icons">add_link</i>
                            <span>Add URL</span>
                        </button>
                    </div>
                `;
            }
        })
        .catch(err => {
            console.error('Error fetching bookmarks:', err);
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="material-icons">error_outline</i>
                    <h3>Failed to load bookmarks</h3>
                    <p>Please try again later.</p>
                </div>
            `;
        });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

// Detay modalını ayarla
function setupDetailsModal() {
    const detailsModal = document.getElementById('detailsModal');
    if (!detailsModal) return;
    
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.bookmark-card');
            if (card) {
                const bookmarkId = card.dataset.id;
                updateModalContent(card);
                detailsModal.classList.add('active');
            }
        });
    });
    
    // Kapatma butonu
    const closeBtn = detailsModal.querySelector('.close-modal-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            detailsModal.classList.remove('active');
        });
    }
    
    // Modal dışına tıklama
    detailsModal.addEventListener('click', (e) => {
        if (e.target === detailsModal) {
            detailsModal.classList.remove('active');
        }
    });
}

// Modal içeriğini güncelle
function updateModalContent(card) {
    const modal = document.getElementById('detailsModal');
    const bookmarkId = card.dataset.id;
    
    // Önizleme resmini ayarla
    const previewImage = modal.querySelector('.preview-image');
    const thumbnail = card.querySelector('.thumbnail');
    previewImage.src = thumbnail.src;
    
    // Ziyaret linkini ayarla
    const visitLink = modal.querySelector('.visit-link');
    const linkElem = card.querySelector('.title-link');
    if (linkElem) {
        visitLink.href = linkElem.href;
    }
    
    // Diğer bilgileri güncelle
    modal.querySelector('.bookmark-date').textContent = card.querySelector('.date').textContent;
    modal.querySelector('.bookmark-title').textContent = card.querySelector('.title').textContent;
    const description = card.querySelector('.description').textContent;
    modal.querySelector('.bookmark-description').textContent = description || 'No description';
    
    // Kategori ve alt kategorileri güncelle
    const mainCategories = card.getAttribute('data-main-categories');
    const categoriesContainer = modal.querySelector('.bookmark-categories');
    if (mainCategories) {
        categoriesContainer.innerHTML = mainCategories.split(',').map(cat => 
            `<a href="/categories/?category=${encodeURIComponent(cat)}" class="category-tag">${cat}</a>`
        ).join('');
    } else {
        categoriesContainer.innerHTML = '<span class="empty-message">No categories</span>';
    }
    
    // Alt kategorileri güncelle
    const subcategoriesContainer = modal.querySelector('.bookmark-subcategories');
    const subcategories = Array.from(card.querySelectorAll('.subcategory-tab'));
    subcategoriesContainer.innerHTML = '';
    
    if (subcategories.length > 0) {
        subcategories.forEach(sub => {
            const link = document.createElement('a');
            link.href = sub.href;
            link.className = 'subcategory-tag';
            link.textContent = sub.textContent;
            subcategoriesContainer.appendChild(link);
        });
    } else {
        subcategoriesContainer.innerHTML = '<span class="empty-message">No subcategories</span>';
    }
    
    // Tag'leri güncelle
    const tagsContainer = modal.querySelector('.bookmark-tags');
    const tags = Array.from(card.querySelectorAll('.tag'));
    tagsContainer.innerHTML = '';
    
    if (tags.length > 0) {
        tags.forEach(tag => {
            const link = document.createElement('a');
            link.href = tag.href;
            link.className = 'tag';
            link.textContent = tag.textContent;
            tagsContainer.appendChild(link);
        });
    } else {
        tagsContainer.innerHTML = '<span class="empty-message">No tags</span>';
    }
} 