document.addEventListener('DOMContentLoaded', () => {
    // Dark mode işlemleri
    initializeDarkMode();

    // Layout işlemleri
    const grid = document.querySelector('.grid');
    const layoutButtons = document.querySelectorAll('.layout-btn');

    layoutButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Aktif buton stilini güncelle
            layoutButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Grid sınıflarını güncelle
            const newLayout = btn.getAttribute('data-layout');
            grid.classList.remove('list-view');
            
            if (newLayout === 'list') {
                grid.classList.add('list-view');
            }
        });
    });

    // More menü işlemleri
    const moreButtons = document.querySelectorAll('.more-btn');
    
    moreButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const menu = btn.nextElementSibling;
            if (menu && menu.classList.contains('more-menu')) {
                // Diğer menüleri kapat
                document.querySelectorAll('.more-menu.active').forEach(m => {
                    if (m !== menu) m.classList.remove('active');
                });
                
                // Bu menüyü aç/kapat
                menu.classList.toggle('active');
            }
        });
    });

    // Sayfa yüklendiğinde more butonlarının görünürlüğünü güncelle
    updateMoreButtonVisibility();
    
    // Pencere boyutu değiştiğinde more butonlarının görünürlüğünü güncelle
    window.addEventListener('resize', updateMoreButtonVisibility);

    // Sort işlemleri
    const sortBtn = document.querySelector('.sort-btn');
    const sortMenu = document.querySelector('.sort-menu');
    const sortItems = document.querySelectorAll('.sort-item');

    if (sortBtn && sortMenu) {
        sortBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sortMenu.classList.toggle('active');
        });

        sortItems.forEach(item => {
            item.addEventListener('click', () => {
                // Aktif sort seçeneğini güncelle
                sortItems.forEach(si => si.classList.remove('active'));
                item.classList.add('active');

                if (!grid) return;
                
                const cards = Array.from(grid.querySelectorAll('.bookmark-card'));
                if (cards.length === 0) return;

                // Tarihleri karşılaştır ve sırala
                cards.sort((a, b) => {
                    const dateA = new Date(a.querySelector('.date').textContent);
                    const dateB = new Date(b.querySelector('.date').textContent);
                    
                    return item.dataset.sort === 'newest' ? 
                        dateB.getTime() - dateA.getTime() : 
                        dateA.getTime() - dateB.getTime();
                });

                // Sıralanmış kartları DOM'a yerleştir
                cards.forEach(card => grid.appendChild(card));
                sortMenu.classList.remove('active');
            });
        });
    }

    // Add URL butonları - url-analyzer.js tarafından yönetiliyor
    // Bu kısmı devre dışı bırakıyoruz çünkü url-analyzer.js dosyasında zaten bu işlemler yapılıyor
    /*
    const addUrlBtns = document.querySelectorAll('.add-url-btn');
    const urlModal = document.getElementById('urlModal');
    
    addUrlBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            urlModal.classList.add('active');
            document.getElementById('url').focus();
        });
    });
    */

    // Details modal işlemleri
    setupDetailsModal();

    // Edit işlemleri
    setupEditFunctionality();

    // Delete işlemleri
    setupDeleteFunctionality();

    // Sayfa dışı tıklamalarda menüleri kapat
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.sort-btn')) {
            sortMenu?.classList.remove('active');
        }
        if (!e.target.closest('.more-btn') && !e.target.closest('.more-menu')) {
            document.querySelectorAll('.more-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
});

// Details modal işlemleri
function setupDetailsModal() {
    const modal = document.getElementById('detailsModal');
    if (!modal) return;
    
    const closeBtn = modal.querySelector('.close-modal-btn');
    
    // Expand butonlarına event listener ekle
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.bookmark-card');
            updateModalContent(card);
            modal.classList.add('active');
        });
    });

    // Kapatma işlemleri
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

function updateModalContent(card) {
    const modal = document.getElementById('detailsModal');
    
    // Ana kategoriyi al
    const mainCategory = card.dataset.mainCategory;
    
    // Ana kategori linkini güncelle
    const mainCategoryLink = modal.querySelector('.main-category');
    mainCategoryLink.textContent = mainCategory;
    mainCategoryLink.href = `/categories/?category=${encodeURIComponent(mainCategory)}`;
    
    // Alt kategorileri al
    const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => ({
        name: cat.textContent,
        url: cat.href
    }));
    
    // Alt kategorileri güncelle
    const subcategoriesContainer = modal.querySelector('.subcategories');
    subcategoriesContainer.innerHTML = subcategories.map(sub => 
        `<a href="${sub.url}" class="subcategory-tab">${sub.name}</a>`
    ).join('');
    
    // Genel bilgileri güncelle
    modal.querySelector('.bookmark-date').textContent = card.querySelector('.date').textContent;
    
    // İçerik bilgilerini güncelle
    modal.querySelector('.bookmark-title').textContent = card.querySelector('.title').textContent;
    modal.querySelector('.bookmark-description').textContent = card.querySelector('.description').textContent;
    
    // Tag'leri güncelle
    const tags = Array.from(card.querySelectorAll('.tag')).map(tag => ({
        name: tag.textContent,
        url: tag.href
    }));
    
    const tagsContainer = modal.querySelector('.bookmark-tags');
    tagsContainer.innerHTML = tags.map(tag => 
        `<a href="${tag.url}" class="tag">${tag.name}</a>`
    ).join('');
    
    // Görsel ve link güncelle
    const previewImage = modal.querySelector('.preview-image');
    const visitLink = modal.querySelector('.visit-link');
    
    previewImage.src = card.querySelector('.thumbnail').src;
    visitLink.href = card.querySelector('.thumbnail-link').href;
}

// Edit işlemleri
function setupEditFunctionality() {
    const editModal = document.getElementById('editModal');
    if (!editModal) return;
    
    const closeBtn = editModal.querySelector('.close-btn');
    const cancelBtn = editModal.querySelector('.cancel-btn');
    const saveBtn = editModal.querySelector('.save-btn');
    const addSubcategoryBtn = editModal.querySelector('.add-subcategory-btn');
    const addTagBtn = editModal.querySelector('.add-tag-btn');
    
    // Edit butonlarına tıklama
    document.querySelectorAll('.edit-bookmark').forEach(item => {
        item.addEventListener('click', (e) => {
            const card = e.target.closest('.bookmark-card');
            openEditModal(card);
        });
    });

    // Kapatma butonları
    [closeBtn, cancelBtn].forEach(btn => {
        btn.addEventListener('click', () => {
            editModal.classList.remove('active');
        });
    });

    // Alt kategori ekleme
    addSubcategoryBtn.addEventListener('click', () => {
        const input = document.getElementById('subcategoryInput');
        const subcategory = input.value.trim();
        
        if (subcategory) {
            const subcategoriesList = document.getElementById('subcategoriesList');
            subcategoriesList.insertAdjacentHTML('beforeend', createSubcategoryItem(subcategory));
            input.value = '';
        }
    });

    // Tag ekleme
    addTagBtn.addEventListener('click', () => {
        const input = document.getElementById('tagInput');
        const tag = input.value.trim();
        
        if (tag) {
            const tagsList = document.getElementById('tagsList');
            tagsList.insertAdjacentHTML('beforeend', createTagItem(tag));
            input.value = '';
        }
    });

    // Değişiklikleri kaydetme
    saveBtn.addEventListener('click', saveBookmarkChanges);
}

function openEditModal(card) {
    const modal = document.getElementById('editModal');
    const bookmarkId = card.dataset.id;
    const title = card.querySelector('.title').textContent;
    const description = card.querySelector('.description').textContent;
    const mainCategory = card.dataset.mainCategory;
    const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => cat.textContent);
    const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);

    // Form alanlarını doldur
    modal.querySelector('#editBookmarkId').value = bookmarkId;
    modal.querySelector('#editTitle').value = title;
    modal.querySelector('#editDescription').value = description;
    
    // Ana kategoriyi seç
    const mainCategorySelect = modal.querySelector('#mainCategory');
    for (let i = 0; i < mainCategorySelect.options.length; i++) {
        if (mainCategorySelect.options[i].value === mainCategory) {
            mainCategorySelect.selectedIndex = i;
            break;
        }
    }

    // Alt kategorileri ekle
    const subcategoriesList = modal.querySelector('#subcategoriesList');
    subcategoriesList.innerHTML = subcategories.map(subcategory => createSubcategoryItem(subcategory)).join('');

    // Etiketleri ekle
    const tagsList = modal.querySelector('#tagsList');
    tagsList.innerHTML = tags.map(tag => createTagItem(tag)).join('');

    // Modalı aç
    modal.classList.add('active');
}

function createSubcategoryItem(subcategory) {
    return `
        <div class="subcategory-item">
            ${subcategory}
            <button class="remove-btn" onclick="removeItem(this, 'subcategory')">
                <i class="material-icons">close</i>
            </button>
        </div>
    `;
}

function createTagItem(tag) {
    return `
        <div class="tag-item">
            ${tag}
            <button class="remove-btn" onclick="removeItem(this, 'tag')">
                <i class="material-icons">close</i>
            </button>
        </div>
    `;
}

function removeItem(button, type) {
    button.closest(`.${type}-item`).remove();
}

function saveBookmarkChanges() {
    const modal = document.getElementById('editModal');
    const bookmarkId = modal.querySelector('#editBookmarkId').value;
    const title = modal.querySelector('#editTitle').value;
    const description = modal.querySelector('#editDescription').value;
    const mainCategory = modal.querySelector('#mainCategory').value;
    const subcategories = Array.from(modal.querySelectorAll('.subcategory-item')).map(item => item.textContent.trim());
    const tags = Array.from(modal.querySelectorAll('.tag-item')).map(item => item.textContent.trim());

    // CSRF token'ı al
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // API çağrısı yap
    fetch('/api/update-bookmark/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            id: bookmarkId,
            title: title,
            description: description,
            main_category: mainCategory,
            subcategories: subcategories,
            tags: tags
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Başarılı olduğunda sayfayı yenile
            window.location.reload();
        } else {
            alert('Error updating bookmark: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error updating bookmark:', error);
        alert('Error updating bookmark. Please try again.');
    });

    // Modalı kapat
    modal.classList.remove('active');
}

// Delete işlemleri
function setupDeleteFunctionality() {
    document.querySelectorAll('.menu-item.delete').forEach(item => {
        item.addEventListener('click', (e) => {
            const card = e.target.closest('.bookmark-card');
            const bookmarkId = card.dataset.id;
            
            if (confirm('Are you sure you want to delete this bookmark?')) {
                deleteBookmark(bookmarkId, card);
            }
        });
    });
}

function deleteBookmark(bookmarkId, card) {
    // CSRF token'ı al
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // API çağrısı yap
    fetch('/api/delete-bookmark/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            id: bookmarkId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Başarılı olduğunda kartı kaldır
            card.remove();
        } else {
            alert('Error deleting bookmark: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error deleting bookmark:', error);
        alert('Error deleting bookmark. Please try again.');
    });
}

// Dark mode initialization function
function initializeDarkMode() {
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;
    
    // Sayfa yüklendiğinde localStorage'dan tema tercihini al
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        updateThemeIcon('dark_mode');
    }

    // Tema değiştirme butonu işlevi
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            
            // Yeni tema durumunu belirle
            const isDarkMode = body.classList.contains('dark-mode');
            
            // Icon'u güncelle
            updateThemeIcon(isDarkMode ? 'dark_mode' : 'light_mode');
            
            // Tercihi localStorage'a kaydet
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        });
    }
}

// Theme icon update function
function updateThemeIcon(iconName) {
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.textContent = iconName;
        }
    }
}

// Bookmark işlemleri için fonksiyonlar
function editBookmark(card) {
    // Düzenleme modalını aç
    console.log('Edit bookmark:', card);
}

function toggleFavorite(card) {
    card.classList.toggle('favorite');
    
    // Layout'a göre farklı görsel efekt
    const isListView = card.closest('.grid').classList.contains('list-view');
    if (isListView) {
        card.style.transition = 'background 0.3s ease';
    }
}

function archiveBookmark(card) {
    card.classList.add('archived');
    
    // Layout'a göre farklı animasyon süresi
    const isCompact = card.closest('.grid').classList.contains('compact-view');
    const animationDuration = isCompact ? 200 : 300;
    
    setTimeout(() => {
        card.style.display = 'none';
    }, animationDuration);
}

// Tag işlemleri için yardımcı fonksiyon
function formatTag(tagText) {
    // Tag'i küçük harfe çevir ve başındaki # işaretini kaldır
    return tagText.toLowerCase().replace(/^#/, '');
}

// Yeni tag ekleme örneği
function addTag(container, tagText) {
    const formattedTag = formatTag(tagText);
    const tagElement = document.createElement('span');
    tagElement.className = 'tag';
    tagElement.textContent = formattedTag;
    container.appendChild(tagElement);
}

// Tag düzenleme modalı için
function editTags(card) {
    const tagsContainer = card.querySelector('.tags');
    const currentTags = Array.from(tagsContainer.querySelectorAll('.tag'))
        .map(tag => tag.textContent);
    
    // Mevcut tag'leri düzenleme modalında göster
    console.log('Current tags:', currentTags);
    
    // Tag'leri düzenlerken formatTag fonksiyonunu kullan
    // Modal implementation...
}

function deleteBookmark(card) {
    if (confirm('Are you sure you want to delete this bookmark?')) {
        card.classList.add('deleted');
        
        // Layout'a göre farklı animasyon süresi
        const isCompact = card.closest('.grid').classList.contains('compact-view');
        const animationDuration = isCompact ? 200 : 300;
        
        setTimeout(() => {
            card.remove();
        }, animationDuration);
    }
}

// More butonlarının görünürlüğünü güncelleme fonksiyonu
function updateMoreButtonVisibility() {
    const moreButtons = document.querySelectorAll('.more-btn');
    
    moreButtons.forEach(btn => {
        btn.style.display = 'flex'; // Tüm more butonlarını görünür yap
    });
    
    // Sayfa yüklendiğinde ve pencere boyutu değiştiğinde more butonlarının görünürlüğünü güncelle
    window.addEventListener('load', () => {
        moreButtons.forEach(btn => {
            btn.style.display = 'flex';
        });
    });
}

// CSS Animasyonları için keyframes ekle
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fadeOut {
        to {
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Kartların alt bilgilerini hizalama fonksiyonu
function alignCardFooters() {
    const grid = document.querySelector('.grid');
    const cards = document.querySelectorAll('.bookmark-card');
    
    cards.forEach(card => {
        const content = card.querySelector('.card-content');
        const footer = card.querySelector('.card-footer');
        
        // Reset any previously set styles
        content.style.position = '';
        content.style.paddingBottom = '';
        footer.style.position = '';
        footer.style.bottom = '';
        footer.style.left = '';
        footer.style.right = '';
        
        // Ensure content has enough space for the footer
        content.style.minHeight = '200px';
        content.style.display = 'flex';
        content.style.flexDirection = 'column';
    });
}

// Navigation function
function navigateToPage(page) {
    const pages = {
        'home': '/',
        'categories': '/categories',
        'tags': '/tags',
        'collections': '/collections'
    };

    // Sayfanın adını küçük harfe çevir
    const cleanPage = page.toLowerCase();

    if (pages[cleanPage]) {
        // Geçerli URL ile hedef URL'i karşılaştır
        const currentPath = window.location.pathname;
        if (currentPath !== pages[cleanPage]) {
            window.location.href = pages[cleanPage];
        }
    } else {
        console.log('Page not found:', cleanPage);
    }
}

// Cat Rain Easter Egg
function createCatRain() {
    const catEmoji = '🐱';
    const numberOfCats = 50;

    for (let i = 0; i < numberOfCats; i++) {
        const cat = document.createElement('div');
        cat.className = 'falling-cat';
        cat.style.left = `${Math.random() * 100}vw`;
        cat.style.animationDuration = `${Math.random() * 2 + 1}s`;
        cat.style.opacity = Math.random();
        cat.innerHTML = catEmoji;
        document.body.appendChild(cat);

        // Kedileri bir süre sonra temizle
        setTimeout(() => {
            cat.remove();
        }, 3000);
    }
}

// URL Modal işlemleri
function initializeUrlModal() {
    // Bu fonksiyonu devre dışı bırakalım çünkü url-analyzer.js dosyasında zaten bu işlemler yapılıyor
    console.log("URL modal işlemleri url-analyzer.js tarafından yönetiliyor");
    return;
}

function openEditModal(card) {
    const modal = document.getElementById('editModal');
    const title = card.querySelector('.title').textContent;
    const description = card.querySelector('.description').textContent;
    const categories = Array.from(card.querySelectorAll('.subcategory-tab')).map(cat => cat.textContent);
    const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);

    // Form alanlarını doldur
    modal.querySelector('#editTitle').value = title;
    modal.querySelector('#editDescription').value = description;

    // Kategorileri ekle
    const categoriesList = modal.querySelector('#categoriesList');
    categoriesList.innerHTML = categories.map(category => createCategoryItem(category)).join('');

    // Etiketleri ekle
    const tagsList = modal.querySelector('#tagsList');
    tagsList.innerHTML = tags.map(tag => createTagItem(tag)).join('');

    // Modalı aç
    modal.classList.add('active');
}

function createCategoryItem(category) {
    return `
        <div class="category-item">
            ${category}
            <button class="remove-btn" onclick="removeItem(this, 'category')">
                <i class="material-icons">close</i>
            </button>
        </div>
    `;
}

function createTagItem(tag) {
    return `
        <div class="tag-item">
            ${tag}
            <button class="remove-btn" onclick="removeItem(this, 'tag')">
                <i class="material-icons">close</i>
            </button>
        </div>
    `;
}

function addCategory() {
    const input = document.getElementById('categoryInput');
    const category = input.value.trim();
    
    if (category) {
        const categoriesList = document.getElementById('categoriesList');
        categoriesList.insertAdjacentHTML('beforeend', createCategoryItem(category));
        input.value = '';
    }
}

function addTag() {
    const input = document.getElementById('tagInput');
    const tag = input.value.trim();
    
    if (tag) {
        const tagsList = document.getElementById('tagsList');
        tagsList.insertAdjacentHTML('beforeend', createTagItem(tag));
        input.value = '';
    }
}

function removeItem(button, type) {
    button.closest(`.${type}-item`).remove();
}

function saveChanges() {
    const modal = document.getElementById('editModal');
    const title = modal.querySelector('#editTitle').value;
    const description = modal.querySelector('#editDescription').value;
    const categories = Array.from(modal.querySelectorAll('.category-item')).map(item => item.textContent.trim());
    const tags = Array.from(modal.querySelectorAll('.tag-item')).map(item => item.textContent.trim());

    // Burada API çağrısı yapılacak
    console.log('Saving changes:', { title, description, categories, tags });

    // Modalı kapat
    modal.classList.remove('active');
}

function formatRelativeDate(dateString) {
    // T ve saniye bilgisini kaldır
    dateString = dateString.replace('T', ' ').split('.')[0].slice(0, -3);
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInSeconds < 60) {
        return 'just now';
    } else if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    } else if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    } else if (diffInDays < 7) {
        return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    } else {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
    }
}

function createSubcategoryLink(category, subcategory) {
    return `
        <a href="topics.html?category=${encodeURIComponent(category)}&subcategory=${encodeURIComponent(subcategory)}" 
           class="subcategory-tab">
            ${subcategory}
        </a>
    `;
}

function createTagLink(tag) {
    return `
        <a href="tagged-bookmarks.html?tag=${encodeURIComponent(tag)}" 
           class="tag">
            ${tag}
        </a>
    `;
} 