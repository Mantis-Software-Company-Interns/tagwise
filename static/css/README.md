# TagWise CSS Architecture

This document outlines the modular CSS architecture for the TagWise application.

## Directory Structure

The CSS code is organized into the following directories:

- **base/**: Base styles (reset, typography, general elements)
- **layout/**: Layout styles (containers, sidebar, grid)
- **Components/**: Component styles (cards, buttons, modals, tags, menus, chatbot)
- **themes/**: Theme styles (dark mode, light mode)
- **utilities/**: Utility styles (animations, helpers)
- **responsive/**: Responsive styles (media queries)

## Module Overview

### Base

- **reset.css**: Basic reset styles and general element styling

### Layout

- **container.css**: Main container and content area styles
- **sidebar.css**: Sidebar and navigation styles
- **grid.css**: Grid layout styles for different views (grid, list, compact)

### Components

- **cards.css**: Bookmark card styles
- **buttons.css**: Button styles (add URL, layout, theme toggle, etc.)
- **modals.css**: Modal dialog styles (details, edit, URL)
- **tags.css**: Tag and category styles
- **menus.css**: Dropdown menu styles
- **chatbot.css**: Chatbot styles

### Themes

- **dark-mode.css**: Dark theme styles

### Utilities

- **animations.css**: Animation styles (falling cat, slide out, fade, etc.)
- **helpers.css**: Helper utility classes (spacing, display, flex, text, etc.)

### Responsive

- **media-queries.css**: Responsive styles for different screen sizes

## Usage

The main.css file imports all the modular CSS files in the correct order. This ensures that the styles are applied correctly and that there are no conflicts.

```css
/* Base Styles */
@import url('base/reset.css');

/* Layout */
@import url('layout/container.css');
@import url('layout/sidebar.css');
@import url('layout/grid.css');

/* Components */
@import url('Components/cards.css');
@import url('Components/buttons.css');
@import url('Components/modals.css');
@import url('Components/tags.css');
@import url('Components/menus.css');
@import url('Components/chatbot.css');

/* Themes */
@import url('themes/dark-mode.css');

/* Utilities */
@import url('utilities/animations.css');
@import url('utilities/helpers.css');

/* Responsive */
@import url('responsive/media-queries.css');
```

## Extending the Architecture

When adding new styles:

1. Determine which module they belong to
2. If they don't fit in an existing module, create a new one
3. Update main.css to import the new module
4. Follow the existing naming conventions and coding style

## Note on Styling

The CSS has been adjusted to closely match the original appearance of the application. The color scheme primarily uses:
- Primary color: #2196F3 (blue)
- Secondary colors: Various shades of gray
- Text colors: #333 (dark gray) for headings, #666 (medium gray) for body text
- Background colors: #f5f5f5 (light gray) for page background, white for cards and containers

The styling maintains the original layout while providing a more modular and maintainable structure. 