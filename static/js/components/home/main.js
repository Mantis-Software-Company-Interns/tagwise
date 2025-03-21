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
    const bookmarkId = card.dataset.id;
    
    // Bookmark ID'sini image'ın data-id özelliğine kaydet
    const previewImage = modal.querySelector('.preview-image');
    previewImage.dataset.id = bookmarkId;
    
    // Kategori ve alt kategorileri al
    const mainCategories = card.getAttribute('data-main-categories');
    
    // Kategori container'ı güncelle
    const categoriesContainer = modal.querySelector('.bookmark-categories');
    categoriesContainer.innerHTML = mainCategories.split(',').map(cat => 
        `<a href="{% url 'tagwiseapp:categories' %}?category=${encodeURIComponent(cat)}" class="category-tag">${cat}</a>`
    ).join('');
    
    // Alt kategorileri al
    const subcategoriesContainer = modal.querySelector('.bookmark-subcategories');
    const subcategories = Array.from(card.querySelectorAll('.subcategory-tab'));
    subcategoriesContainer.innerHTML = '';
    
    subcategories.forEach(sub => {
        const link = document.createElement('a');
        link.href = sub.href;
        link.className = 'subcategory-tag';
        link.textContent = sub.textContent;
        subcategoriesContainer.appendChild(link);
    });
    
    // Genel bilgileri güncelle
    modal.querySelector('.bookmark-date').textContent = card.querySelector('.date').textContent;
    
    // İçerik bilgilerini güncelle
    modal.querySelector('.bookmark-title').textContent = card.querySelector('.title').textContent;
    modal.querySelector('.bookmark-description').textContent = card.querySelector('.description').textContent;
    
    // Tag'leri güncelle
    const tagsContainer = modal.querySelector('.bookmark-tags');
    const tags = Array.from(card.querySelectorAll('.tag'));
    tagsContainer.innerHTML = '';
    
    tags.forEach(tag => {
        const link = document.createElement('a');
        link.href = tag.href;
        link.className = 'tag';
        link.textContent = tag.textContent;
        tagsContainer.appendChild(link);
    });
    
    // Görsel ve link güncelle
    const visitLink = modal.querySelector('.visit-link');
    
    // Önizleme resmini ayarla - thumbnail'deki kaynak URL'yi kullan
    previewImage.src = card.querySelector('.thumbnail').src;
    
    // Ziyaret linkini ayarla
    const linkElem = card.querySelector('.title-link');
    if (linkElem) {
        visitLink.href = linkElem.href;
    }
}

// Edit işlemleri
function setupEditFunctionality() {
    const editModal = document.getElementById('editModal');
    if (!editModal) return;
    
    const closeBtn = editModal.querySelector('.close-btn');
    const cancelBtn = editModal.querySelector('.cancel-btn');
    const saveBtn = editModal.querySelector('.save-btn');
    const editScreenshotInput = document.getElementById('editScreenshotInput');
    const editScreenshotPreview = document.getElementById('editScreenshotPreview');
    
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

    // Handle screenshot upload
    if (editScreenshotInput && editScreenshotPreview) {
        editScreenshotInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                // Check if file is an image
                if (!file.type.match('image.*')) {
                    alert('Please select an image file');
                    return;
                }
                
                // Check if file size is less than 5MB
                if (file.size > 5 * 1024 * 1024) {
                    alert('Image size should be less than 5MB');
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Display the image
                    editScreenshotPreview.src = e.target.result;
                    
                    // Update status message
                    const statusEl = document.getElementById('editScreenshotStatus');
                    if (statusEl) {
                        statusEl.innerHTML = `
                            <i class="material-icons" style="color: #ff9800;">image</i>
                            <span>Custom screenshot selected</span>
                        `;
                    }
                    
                    // Store the base64 image data
                    const editScreenshotData = document.getElementById('editScreenshotData');
                    if (editScreenshotData) {
                        // Extract the base64 data without the prefix
                        const base64data = e.target.result.split(',')[1];
                        // Store the file path prefix and filename for backend processing
                        editScreenshotData.value = `custom_${Date.now()}.png`;
                        // Store the actual data in a data attribute for submission
                        editScreenshotData.dataset.content = base64data;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Değişiklikleri kaydetme
    saveBtn.addEventListener('click', saveBookmarkChanges);
}

function openEditModal(card) {
    const modal = document.getElementById('editModal');
    const bookmarkId = card.dataset.id;
    const title = card.querySelector('.title').textContent;
    const description = card.querySelector('.description').textContent;
    
    // Screenshot elements
    const editScreenshotData = document.getElementById('editScreenshotData');
    const editScreenshotPreview = document.getElementById('editScreenshotPreview');
    const editScreenshotStatus = document.getElementById('editScreenshotStatus');
    
    // Form alanlarını doldur
    modal.querySelector('#editBookmarkId').value = bookmarkId;
    modal.querySelector('#editTitle').value = title;
    modal.querySelector('#editDescription').value = description;
    
    // Screenshot'ı ayarla
    if (editScreenshotPreview && editScreenshotData) {
        const thumbnail = card.querySelector('.thumbnail');
        if (thumbnail && thumbnail.src) {
            editScreenshotPreview.src = thumbnail.src;
            // Extract the path from src
            const srcPath = thumbnail.src.split('/static/')[1];
            if (srcPath) {
                editScreenshotData.value = srcPath;
                // Clear any previous custom data
                editScreenshotData.dataset.content = '';
                
                // Update status message
                if (editScreenshotStatus) {
                    editScreenshotStatus.innerHTML = `
                        <i class="material-icons" style="color: #2196f3;">image</i>
                        <span>Current screenshot</span>
                    `;
                }
            } else {
                editScreenshotPreview.src = '/static/images/default-thumbnail.png';
                editScreenshotData.value = '';
                
                // Update status message
                if (editScreenshotStatus) {
                    editScreenshotStatus.innerHTML = `
                        <i class="material-icons" style="color: #f44336;">error_outline</i>
                        <span>No screenshot available</span>
                    `;
                }
            }
        } else {
            editScreenshotPreview.src = '/media/default-thumbnail.png';
            editScreenshotData.value = '';
            
            // Update status message
            if (editScreenshotStatus) {
                editScreenshotStatus.innerHTML = `
                    <i class="material-icons" style="color: #f44336;">error_outline</i>
                    <span>No screenshot available</span>
                `;
            }
        }
    }
    
    const mainCategories = (card.dataset.mainCategories || '').split(',').filter(cat => cat.trim());
    const subcategories = Array.from(card.querySelectorAll('.subcategory-tab')).map(sub => sub.textContent);
    
    // Kategori gruplarını ekle
    const editCategoryGroupsList = modal.querySelector('#editCategoryGroupsList');
    editCategoryGroupsList.innerHTML = '';
    
    if (mainCategories.length > 0 && subcategories.length > 0) {
        // Her ana kategori için tüm alt kategorileri göster
        mainCategories.forEach(mainCategory => {
            // Bu ana kategoriye ait alt kategorileri bul
            const relatedSubcategories = subcategories.filter(sub => {
                // Burada alt kategorinin ana kategoriye ait olup olmadığını kontrol etmek gerekir
                // Basit bir çözüm olarak tüm alt kategorileri gösteriyoruz
                return true;
            });
            
            if (relatedSubcategories.length === 0) {
                // Eğer ilişkili alt kategori yoksa, ana kategoriyi tek başına göster
                addCategoryGroupToEdit(mainCategory, '', editCategoryGroupsList);
            } else {
                // Bu ana kategoriye ait tüm alt kategorileri göster
                relatedSubcategories.forEach(subcategory => {
                    addCategoryGroupToEdit(mainCategory, subcategory, editCategoryGroupsList);
                });
            }
        });
    } else if (mainCategories.length > 0) {
        // Sadece ana kategorileri göster
        mainCategories.forEach(mainCategory => {
            addCategoryGroupToEdit(mainCategory, '', editCategoryGroupsList);
        });
    } else if (subcategories.length > 0) {
        // Sadece alt kategorileri göster (varsayılan ana kategori ile)
        subcategories.forEach(subcategory => {
            addCategoryGroupToEdit('Uncategorized', subcategory, editCategoryGroupsList);
        });
    }
    
    // Etiketleri ekle
    const tagsList = modal.querySelector('#tagsList');
    const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);
    tagsList.innerHTML = '';
    
    tags.forEach(tag => {
        addTagToEdit(tag, tagsList);
    });
    
    // Modalı aç
    modal.classList.add('active');
}

function addCategoryGroupToEdit(mainCategory, subcategory, container) {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'category-group';
    
    groupDiv.innerHTML = `
        <div class="group-header">
            <span class="main-category-label">${mainCategory}</span>
            <span class="separator">›</span>
            <span class="subcategory-label">${subcategory}</span>
            <button class="remove-group-btn">
                <i class="material-icons">close</i>
            </button>
        </div>
    `;
    
    // Remove button functionality
    const removeBtn = groupDiv.querySelector('.remove-group-btn');
    removeBtn.addEventListener('click', () => {
        groupDiv.remove();
    });
    
    container.appendChild(groupDiv);
}

function addTagToEdit(tag, container) {
    const tagSpan = document.createElement('span');
    tagSpan.className = 'tag';
    tagSpan.textContent = tag;
    
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-tag-btn';
    removeBtn.innerHTML = '<i class="material-icons">close</i>';
    
    // Remove button functionality
    removeBtn.addEventListener('click', () => {
        tagSpan.remove();
    });
    
    tagSpan.appendChild(removeBtn);
    container.appendChild(tagSpan);
}

function saveBookmarkChanges() {
    const modal = document.getElementById('editModal');
    const bookmarkId = modal.querySelector('#editBookmarkId').value;
    const title = modal.querySelector('#editTitle').value;
    const description = modal.querySelector('#editDescription').value;
    
    // Get all category groups
    const categoryGroups = Array.from(modal.querySelectorAll('.category-group'))
        .map(group => ({
            mainCategory: group.querySelector('.main-category-label').textContent,
            subcategory: group.querySelector('.subcategory-label').textContent
        }));
    
    // Extract main categories and subcategories
    const mainCategories = [...new Set(categoryGroups.map(group => group.mainCategory))];
    const subcategories = categoryGroups.map(group => group.subcategory);
    
    // Create category-subcategory map
    const categorySubcategoryMap = {};
    categoryGroups.forEach(group => {
        if (!categorySubcategoryMap[group.mainCategory]) {
            categorySubcategoryMap[group.mainCategory] = [];
        }
        categorySubcategoryMap[group.mainCategory].push(group.subcategory);
    });
    
    // Get tags
    const tags = Array.from(modal.querySelectorAll('.tags-list .tag'))
        .map(tag => tag.childNodes[0].nodeValue.trim());
    
    // Get screenshot data
    const editScreenshotData = document.getElementById('editScreenshotData');
    let screenshotData = editScreenshotData ? editScreenshotData.value : null;
    
    // CSRF token al
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // Prepare the data for API call
    const bookmarkData = {
        id: bookmarkId,
        title: title,
        description: description,
        main_categories: mainCategories,
        subcategories: subcategories,
        category_subcategory_map: categorySubcategoryMap,
        tags: tags,
        screenshot_data: screenshotData
    };
    
    // Add custom screenshot if available
    if (editScreenshotData && editScreenshotData.dataset.content) {
        bookmarkData.custom_screenshot = editScreenshotData.dataset.content;
    }
    
    // API çağrısı yap
    fetch('/api/update-bookmark/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(bookmarkData)
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
                BookmarkActions.deleteBookmark(bookmarkId, card);
            }
        });
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