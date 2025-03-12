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
    
    if (tag && taggedBookmarksData[tag]) {
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
    const relatedTags = taggedBookmarksData[tag].bookmarks
        .flatMap(bookmark => bookmark.relatedTags)
        .filter((value, index, self) => self.indexOf(value) === index) // Tekrar edenleri kaldır
        .filter(relatedTag => relatedTag !== tag); // Mevcut etiketi kaldır

    relatedTagsContainer.innerHTML = `
        <div class="related-tags-header">
            <h3>Related Tags</h3>
        </div>
        <div class="related-tags-list">
            ${relatedTags.map(relatedTag => `
                <a href="/tagged-bookmarks/?tag=${relatedTag}" class="related-tag">
                    <i class="material-icons">local_offer</i>
                    ${relatedTag}
                </a>
            `).join('')}
        </div>
    `;
}

function loadBookmarks(tag) {
    const grid = document.getElementById('bookmarksGrid');
    const bookmarks = taggedBookmarksData[tag].bookmarks;

    grid.innerHTML = bookmarks.map(bookmark => `
        <div class="bookmark-card">
            <div class="card-header">
                <button class="more-btn">
                    <i class="material-icons">more_vert</i>
                </button>
                <div class="more-menu">
                    <div class="menu-item"><i class="material-icons">edit</i>Edit</div>
                    <div class="menu-item"><i class="material-icons">star</i>Favorite</div>
                    <div class="menu-item"><i class="material-icons">archive</i>Archive</div>
                    <div class="menu-item"><i class="material-icons">local_offer</i>Edit Tags</div>
                    <div class="menu-item delete"><i class="material-icons">delete</i>Delete</div>
                </div>
            </div>
            <a href="${bookmark.url}" target="_blank" class="thumbnail-link">
                <div class="thumbnail-container">
                    <img src="${bookmark.thumbnail}" alt="Thumbnail" class="thumbnail">
                </div>
            </a>
            <div class="card-content">
                <a href="${bookmark.url}" target="_blank" class="title-link">
                    <h3 class="title">${bookmark.title}</h3>
                </a>
                <p class="description">${bookmark.description}</p>
                <div class="tags">
                    ${bookmark.tags.map(tag => `
                        <a href="/tagged-bookmarks/?tag=${tag}" class="tag">${tag}</a>
                    `).join('')}
                </div>
                <div class="card-footer">
                    <button class="expand-btn">
                        <i class="material-icons">info_outline</i>
                    </button>
                    <div class="date">${formatDate(bookmark.date)}</div>
                </div>
            </div>
        </div>
    `).join('');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
} 