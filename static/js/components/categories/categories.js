document.addEventListener('DOMContentLoaded', () => {
    // Modal işlemleri
    const categoryModal = document.getElementById('categoryModal');
    const importModal = document.getElementById('importModal');
    const openModalBtn = document.getElementById('openCategoryModal');
    const openEmptyModalBtn = document.getElementById('openEmptyCategoryModal');
    const closeButtons = document.querySelectorAll('.close-btn');
    const categoryForm = document.getElementById('categoryForm');
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    const allCategoriesSection = document.querySelector('.all-categories-section');
    const recentCategoriesSection = document.querySelector('.recent-categories-section');
    
    // Icon seçici işlemleri
    const selectedIcon = document.querySelector('.selected-icon');
    const iconOptions = document.querySelectorAll('.icon-option');
    const hiddenIconInput = document.getElementById('selectedIcon');
    
    // Add URL button
    const addUrlButtons = document.querySelectorAll('.add-url-btn');
    
    // Initialize
    initializeFilters();
    initializeModals();
    initializeIconSelector();
    initializeSubcategoryInput();
    initializeImportCategories();
    initializeCategoryCards();
    
    // Add click event to category cards
    function initializeCategoryCards() {
        // Get all category cards
        const categoryCards = document.querySelectorAll('.category-card');
        
        categoryCards.forEach(card => {
            // Add click event to the "View All" link
            const viewAllLink = card.querySelector('.view-all-link');
            if (viewAllLink) {
                viewAllLink.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent the card click event from firing
                });
            }
            
            // Add click event to subcategory links
            const subcategoryLinks = card.querySelectorAll('.subcategory');
            subcategoryLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.stopPropagation(); // Prevent the card click event from firing
                });
            });
            
            // Add click event to the card itself
            card.addEventListener('click', () => {
                const categoryName = card.getAttribute('data-category');
                if (categoryName) {
                    // Use the correct URL pattern for Django
                    window.location.href = `/tagwise/subcategories/?category=${encodeURIComponent(categoryName)}`;
                }
            });
        });
    }
    
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
                    allCategoriesSection.style.display = 'block';
                    recentCategoriesSection.style.display = 'none';
                } else if (filter === 'recent') {
                    allCategoriesSection.style.display = 'none';
                    recentCategoriesSection.style.display = 'block';
                    
                    // If no recent categories, load them
                    if (!document.querySelector('.recent-card')) {
                        loadRecentCategories();
                    }
                }
            });
        });
    }
    
    // Modal initialization
    function initializeModals() {
        // Open category modal
        if (openModalBtn) {
            openModalBtn.addEventListener('click', () => {
                categoryModal.classList.add('active');
            });
        }
        
        if (openEmptyModalBtn) {
            openEmptyModalBtn.addEventListener('click', () => {
                categoryModal.classList.add('active');
            });
        }
        
        // Close modals
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const modal = btn.closest('.modal');
                if (modal) modal.classList.remove('active');
            });
        });
        
        // Close modal when clicking outside
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
        
        // Add URL buttons
        addUrlButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const urlModal = document.getElementById('urlModal');
                if (urlModal) {
                    urlModal.classList.add('active');
                    const urlInput = document.getElementById('url');
                    if (urlInput) urlInput.focus();
                }
            });
        });
    }
    
    // Icon selector initialization
    function initializeIconSelector() {
        if (!iconOptions.length || !selectedIcon || !hiddenIconInput) return;
        
        iconOptions.forEach(option => {
            option.addEventListener('click', () => {
                const icon = option.getAttribute('data-icon');
                selectedIcon.querySelector('i').textContent = icon;
                hiddenIconInput.value = icon;
                
                // Update active class
                iconOptions.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
            });
        });
    }
    
    // Subcategory input initialization
    function initializeSubcategoryInput() {
        const addSubcategoryBtn = document.querySelector('.add-subcategory-btn');
        const subcategoryInput = document.getElementById('subcategoryInput');
        const subcategoryTags = document.getElementById('subcategoryTags');
        const subcategoriesData = document.getElementById('subcategoriesData');
        
        if (!addSubcategoryBtn || !subcategoryInput || !subcategoryTags || !subcategoriesData) return;
        
        addSubcategoryBtn.addEventListener('click', addSubcategory);
        
        subcategoryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSubcategory();
            }
        });
        
        function addSubcategory() {
            const value = subcategoryInput.value.trim();
            if (value) {
                const tag = document.createElement('div');
                tag.className = 'subcategory-tag';
                tag.innerHTML = `
                    ${value}
                    <button type="button" class="remove-tag">
                        <i class="material-icons">close</i>
                    </button>
                `;
                
                // Remove button functionality
                const removeBtn = tag.querySelector('.remove-tag');
                removeBtn.addEventListener('click', () => {
                    tag.remove();
                    updateSubcategoriesData();
                });
                
                subcategoryTags.appendChild(tag);
                subcategoryInput.value = '';
                updateSubcategoriesData();
            }
        }
        
        function updateSubcategoriesData() {
            const subcategories = Array.from(subcategoryTags.querySelectorAll('.subcategory-tag'))
                .map(tag => tag.textContent.trim());
            subcategoriesData.value = JSON.stringify(subcategories);
        }
        
        // Form validation
        if (categoryForm) {
            categoryForm.addEventListener('submit', (e) => {
                // Update subcategories data before submitting
                updateSubcategoriesData();
                
                // Form validation
                const categoryName = document.getElementById('categoryName').value.trim();
                if (!categoryName) {
                    e.preventDefault();
                    alert('Please enter a category name');
                    return;
                }
            });
        }
    }
    
    // Load recent categories from bookmarks
    function loadRecentCategories() {
        const recentGrid = document.querySelector('.recent-grid');
        if (!recentGrid) return;
        
        // Get recent categories from localStorage
        const recentCategories = JSON.parse(localStorage.getItem('recentCategories') || '[]');
        
        if (recentCategories.length > 0) {
            // Clear grid
            recentGrid.innerHTML = '';
            
            // Add categories to grid
            recentCategories.forEach(category => {
                const card = createCategoryCard(category, true);
                recentGrid.appendChild(card);
            });
        } else {
            // If no categories in localStorage, try to fetch from API
            fetchRecentCategories(recentGrid);
        }
    }
    
    // Fetch recent categories from API
    function fetchRecentCategories(recentGrid) {
        // Show loading state
        recentGrid.innerHTML = '<div class="loading">Loading recent categories...</div>';
        
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        // Fetch recent categories
        fetch('/api/recent-categories/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.categories && data.categories.length > 0) {
                // Clear loading state
                recentGrid.innerHTML = '';
                
                // Add categories to grid
                data.categories.forEach(category => {
                    const card = createCategoryCard(category, true);
                    recentGrid.appendChild(card);
                });
                
                // Save to localStorage
                localStorage.setItem('recentCategories', JSON.stringify(data.categories));
            } else {
                showEmptyRecentState(recentGrid);
            }
        })
        .catch(error => {
            console.error('Error loading recent categories:', error);
            recentGrid.innerHTML = `
                <div class="error-message">
                    <i class="material-icons">error</i>
                    <p>Error loading recent categories. Please try again.</p>
                </div>
            `;
        });
    }
    
    // Show empty recent state
    function showEmptyRecentState(recentGrid) {
        recentGrid.innerHTML = `
            <div class="empty-recent">
                <i class="material-icons">access_time</i>
                <h3>No Recent Categories</h3>
                <p>Add a new bookmark to create categories</p>
                <button class="add-url-btn">
                    <i class="material-icons">add_link</i>
                    <span>Add URL</span>
                </button>
            </div>
        `;
        
        // Add event listener to Add URL button
        const addUrlBtn = recentGrid.querySelector('.add-url-btn');
        if (addUrlBtn) {
            addUrlBtn.addEventListener('click', () => {
                const urlModal = document.getElementById('urlModal');
                if (urlModal) {
                    urlModal.classList.add('active');
                    const urlInput = document.getElementById('url');
                    if (urlInput) urlInput.focus();
                }
            });
        }
    }
    
    // Create category card
    function createCategoryCard(category, isRecent = false) {
        const card = document.createElement('div');
        card.className = `category-card${isRecent ? ' recent-card' : ''}`;
        card.setAttribute('data-category', category.name);
        
        // Create subcategories HTML
        let subcategoriesHtml = '';
        if (category.subcategories && category.subcategories.length > 0) {
            const displaySubcategories = category.subcategories.slice(0, 3);
            const remainingCount = category.subcategories.length - 3;
            
            subcategoriesHtml = displaySubcategories.map(subcategory => 
                `<a href="/topics/?category=${encodeURIComponent(category.name)}&subcategory=${encodeURIComponent(subcategory)}" class="subcategory">${subcategory}</a>`
            ).join('');
            
            if (remainingCount > 0) {
                subcategoriesHtml += `<a href="/subcategories/?category=${encodeURIComponent(category.name)}" class="subcategory more">+${remainingCount} more</a>`;
            }
        }
        
        card.innerHTML = `
            <div class="category-header">
                <i class="material-icons">${category.icon || 'folder'}</i>
                <h3>${category.name}</h3>
                ${isRecent ? '<span class="new-badge">New</span>' : ''}
            </div>
            <div class="subcategories">
                ${subcategoriesHtml}
            </div>
            <div class="category-stats">
                <div class="stat">
                    <span class="stat-value">${category.bookmark_count || 0}</span>
                    <span class="stat-label">Bookmarks</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${category.subcategories?.length || 0}</span>
                    <span class="stat-label">Subcategories</span>
                </div>
            </div>
            <a href="/subcategories/?category=${encodeURIComponent(category.name)}" class="view-all-link">
                <span>View All</span>
                <i class="material-icons">arrow_forward</i>
            </a>
        `;
        
        // Add click event to navigate to subcategories
        card.addEventListener('click', (e) => {
            // If the clicked element is not a link or button, navigate to subcategories
            if (!e.target.closest('a') && !e.target.closest('button')) {
                window.location.href = `/subcategories/?category=${encodeURIComponent(category.name)}`;
            }
        });
        
        return card;
    }
    
    // Initialize import categories functionality
    function initializeImportCategories() {
        const importCategoriesList = document.getElementById('importCategoriesList');
        const importBtn = document.querySelector('.import-btn');
        const cancelBtn = document.querySelector('.cancel-btn');
        
        if (!importCategoriesList || !importBtn || !cancelBtn) return;
        
        // Cancel button
        cancelBtn.addEventListener('click', () => {
            importModal.classList.remove('active');
        });
        
        // Import button
        importBtn.addEventListener('click', () => {
            const selectedCategories = Array.from(importCategoriesList.querySelectorAll('.import-checkbox:checked'))
                .map(checkbox => {
                    const item = checkbox.closest('.import-category-item');
                    const categoryName = item.querySelector('.import-category-name').textContent;
                    const subcategories = Array.from(item.querySelectorAll('.import-subcategory'))
                        .map(sub => sub.textContent);
                    
                    return {
                        name: categoryName,
                        subcategories: subcategories
                    };
                });
            
            if (selectedCategories.length === 0) {
                alert('Please select at least one category to import');
                return;
            }
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            // Import categories
            fetch('/api/import-categories/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    categories: selectedCategories
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close modal
                    importModal.classList.remove('active');
                    
                    // Reload page
                    window.location.reload();
                } else {
                    alert('Error importing categories: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error importing categories:', error);
                alert('Error importing categories. Please try again.');
            });
        });
    }
}); 