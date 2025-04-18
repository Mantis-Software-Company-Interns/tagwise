// Theme Manager
// Handles dark mode and theme switching

const ThemeManager = {
    initialize() {
        this.initializeDarkMode();
        this.initializeSearchEasterEgg();
    },

    initializeDarkMode() {
        const themeToggle = document.querySelector('.theme-toggle');
        const body = document.body;
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            body.classList.add('dark-mode');
            this.updateThemeIcon('dark_mode');
        }

        // Toggle theme on button click
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                body.classList.toggle('dark-mode');
                
                // Determine new theme state
                const isDarkMode = body.classList.contains('dark-mode');
                
                // Update icon
                this.updateThemeIcon(isDarkMode ? 'dark_mode' : 'light_mode');
                
                // Save preference to localStorage
                localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
                
                // Removed cat rain Easter egg from dark mode toggle
            });
        }
    },

    initializeSearchEasterEgg() {
        // Get the main search input in the top bar
        const searchInput = document.querySelector('.search-container input');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase().trim();
                
                // Check if the search term is "loki"
                if (searchTerm === 'loki') {
                    this.createCatRain();
                }
            });
        }
    },

    updateThemeIcon(iconName) {
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.textContent = iconName;
            }
        }
    },
    
    createCatRain() {
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

            // Clean up cats after animation
            setTimeout(() => {
                cat.remove();
            }, 3000);
        }
    }
}; 