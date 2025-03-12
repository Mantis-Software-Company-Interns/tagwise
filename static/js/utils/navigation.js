// Navigation Utility
// Handles page navigation and URL management

const Navigation = {
    navigateToPage(page) {
        const pages = {
            'home': '/',
            'categories': '/categories',
            'tags': '/tags',
            'collections': '/collections'
        };
    
        // Convert page name to lowercase
        const cleanPage = page.toLowerCase();
    
        if (pages[cleanPage]) {
            // Compare current URL with target URL
            const currentPath = window.location.pathname;
            if (currentPath !== pages[cleanPage]) {
                window.location.href = pages[cleanPage];
            }
        } else {
            console.log('Page not found:', cleanPage);
        }
    },
    
    getQueryParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },
    
    setQueryParam(param, value) {
        const url = new URL(window.location);
        url.searchParams.set(param, value);
        window.history.pushState({}, '', url);
    },
    
    removeQueryParam(param) {
        const url = new URL(window.location);
        url.searchParams.delete(param);
        window.history.pushState({}, '', url);
    }
}; 