<!-- Parent: ../AGENTS.md -->
# CSS Stylesheets

## Purpose
CSS stylesheets for the Flask web interface. Provides dark theme styling with purple accent colors for the image generation UI.

## Key Files
- `style.css` - Main stylesheet for index.html
  - CSS custom properties (variables) for theming
  - Layout with CSS Grid (sidebar + main content)
  - Component styles: buttons, inputs, upload boxes, cards
  - Responsive design considerations

## For AI Agents

### CSS Variables (Theme)
```css
:root {
    --bg-color: #121212;        /* Page background */
    --surface-color: #1e1e1e;   /* Card/panel background */
    --primary-color: #bb86fc;   /* Purple accent */
    --primary-hover: #a370db;   /* Darker purple for hover */
    --text-color: #e0e0e0;      /* Primary text */
    --secondary-text: #a0a0a0;  /* Muted text */
    --border-color: #333;       /* Borders */
    --input-bg: #2c2c2c;        /* Input backgrounds */
    --success-color: #03dac6;   /* Success/teal accent */
}
```

### Key Components
```css
.container         /* Max-width wrapper (1400px) */
.controls-panel    /* Left sidebar with settings */
.mode-btn          /* Variation/Modification toggle buttons */
.upload-box        /* Image upload dropzone */
.preview-area      /* Image preview container */
.results-section   /* Grid of generated results */
.result-card       /* Individual result with actions */
.generate-btn      /* Primary action button */
```

### Layout Structure
```
┌─────────────────────────────────────────┐
│                 Header                   │
├──────────────┬──────────────────────────┤
│              │                          │
│  Controls    │      Results Section     │
│  Panel       │      (Grid of cards)     │
│  (400px)     │                          │
│              │                          │
└──────────────┴──────────────────────────┘
```

### Working in This File

- **Changing colors**: Update CSS variables in `:root`
- **Adding components**: Follow BEM-like naming, use existing variables
- **Responsive changes**: Add media queries, modify grid template

## Dependencies
- **External**: Google Fonts (Inter)
- **Internal**: Used by `templates/index.html`
