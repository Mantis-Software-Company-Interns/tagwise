# TagWise JavaScript Code Organization

This directory contains the JavaScript code for the TagWise application. The code is organized into modules based on functionality.

## Directory Structure

- **core/**: Core application initialization
  - `app.js`: Main application initialization

- **ui/**: User interface components
  - `layout.js`: Layout management (grid/list views, card alignment)
  - `theme.js`: Theme management (dark/light mode)

- **modals/**: Modal dialogs
  - `details-modal.js`: Bookmark details modal
  - `edit-modal.js`: Bookmark edit modal
  - `modal-manager.js`: Modal initialization and management

- **bookmarks/**: Bookmark management
  - `bookmark-actions.js`: Bookmark actions (edit, delete, favorite, archive)
  - `bookmark-manager.js`: Bookmark management (filtering, searching)

- **utils/**: Utility functions
  - `date-formatter.js`: Date formatting utilities
  - `navigation.js`: Navigation utilities
  - `tag-utils.js`: Tag-related utilities
  - `category-utils.js`: Category-related utilities

## Module Dependencies

The modules should be loaded in the following order:

1. Utilities (date-formatter.js, navigation.js, tag-utils.js, category-utils.js)
2. UI Components (layout.js, theme.js)
3. Modals (details-modal.js, edit-modal.js, modal-manager.js)
4. Bookmarks (bookmark-actions.js, bookmark-manager.js)
5. Core (app.js)

## Usage

The application is initialized when the DOM is loaded. The initialization is handled by the `app.js` file, which initializes all the other modules.

```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    ThemeManager.initialize();

    // Initialize layout
    LayoutManager.initialize();

    // Initialize modals
    ModalManager.initialize();

    // Initialize bookmark actions
    BookmarkManager.initialize();
});
```

## Adding New Features

When adding new features, follow these guidelines:

1. Create a new module in the appropriate directory
2. Add the module to the base.html file in the correct order
3. Initialize the module in app.js if necessary
4. Use existing utilities and modules when possible
5. Follow the existing code style and naming conventions 