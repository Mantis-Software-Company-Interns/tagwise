document.addEventListener('DOMContentLoaded', () => {
    // URL'den kategori ve alt kategori parametrelerini al
    const urlParams = new URLSearchParams(window.location.search);
    const category = urlParams.get('category');
    const subcategory = urlParams.get('subcategory');
    
    if (category && subcategory) {
        // Breadcrumb'ı güncelle
        document.getElementById('categoryLink').textContent = category;
        document.getElementById('categoryLink').href = `categories.html?category=${category}`;
        document.getElementById('currentSubcategory').textContent = subcategory;
        
        // İlgili bookmarkları yükle
        loadTopicBookmarks(category, subcategory);
    }
});

function loadTopicBookmarks(category, subcategory) {
    const grid = document.querySelector('.grid');
    
    // Örnek veri (gerçek uygulamada API'den gelecek)
    const bookmarks = [
        {
            title: 'React Performance Optimization Tips',
            url: 'https://react.dev/learn/performance',
            description: 'Learn advanced techniques for optimizing React applications...',
            thumbnail: 'images/react.png',
            date: '2024-03-14',
            mainCategory: 'Development',
            subcategories: ['React', 'Frontend'],
            tags: ['react', 'performance', 'optimization', 'hooks']
        },
        // Diğer bookmarklar...
    ];
    
    // Sadece seçili kategori ve alt kategoriye ait bookmarkları filtrele
    const filteredBookmarks = bookmarks.filter(bookmark => 
        bookmark.mainCategory.toLowerCase() === category.toLowerCase() &&
        bookmark.subcategories.some(sub => sub.toLowerCase() === subcategory.toLowerCase())
    );
    
    // Bookmarkları grid'e ekle
    grid.innerHTML = filteredBookmarks.map(bookmark => `
        <div class="grid-item bookmark-card" data-main-category="${bookmark.mainCategory}">
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
                    <div class="subcategory-container">
                        ${bookmark.subcategories.map(sub => 
                            `<a href="topics.html?category=${bookmark.mainCategory}&subcategory=${sub}" 
                                class="subcategory-tab">${sub}</a>`
                        ).join('')}
                    </div>
                </div>
            </a>
            <div class="card-content">
                <a href="${bookmark.url}" target="_blank" class="title-link">
                    <h3 class="title">${bookmark.title}</h3>
                </a>
                <p class="description">${bookmark.description}</p>
                <div class="tags">
                    ${bookmark.tags.map(tag => 
                        `<a href="tagged-bookmarks.html?tag=${tag}" class="tag">${tag}</a>`
                    ).join('')}
                </div>
                <div class="card-footer">
                    <button class="expand-btn">
                        <i class="material-icons">info_outline</i>
                    </button>
                    <div class="date">${bookmark.date}</div>
                </div>
            </div>
        </div>
    `).join('');
    
    // Event listener'ları yeniden ekle
    setupCardEventListeners();
}

function setupCardEventListeners() {
    // Expand butonları için event listener
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.bookmark-card');
            if (card) {
                updateModalContent(card);
                document.getElementById('detailsModal').classList.add('active');
            }
        });
    });
    
    // More menü butonları için event listener
    // ... diğer event listener'lar
} 