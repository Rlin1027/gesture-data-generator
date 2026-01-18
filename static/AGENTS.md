<!-- Parent: ../AGENTS.md -->
# Static Assets

## Purpose
Frontend static assets for the Flask web application. Contains CSS stylesheets and JavaScript for the generation interface.

## Subdirectories
- `css/` - Stylesheets (see static/css/AGENTS.md)
- `js/` - JavaScript files (see static/js/AGENTS.md)

## Key Files
- `css/style.css` - Main stylesheet for index.html
  - Dark theme with purple accent color
  - Custom styling for upload boxes, mode buttons, results
  - Responsive design with flexbox/grid
- `js/main.js` - JavaScript for index.html
  - Mode switching logic
  - Image preview functionality
  - API calls for generation and analysis
  - Download handling

## For AI Agents

### Design System
```css
/* Color Palette */
--bg-dark: #121212
--surface: #1e1e1e
--primary: #bb86fc (purple accent)
--text: #e0e0e0
--text-secondary: #a0a0a0
--border: #444
```

### Key CSS Classes
```css
.container          /* Main content wrapper */
.controls-panel     /* Settings form container */
.mode-btn           /* Variation/Modification buttons */
.upload-box         /* Image upload dropzone */
.preview-area       /* Image preview container */
.results-section    /* Generated images display */
.result-card        /* Individual result card */
```

### Working in This Directory

- **Styling changes**: Edit `css/style.css`, use existing color variables
- **JavaScript changes**: Edit `js/main.js`, follow existing patterns
- **Adding new assets**: Place in appropriate subdirectory, reference via `url_for('static', filename='...')`

## Dependencies
- **Internal**: Served by Flask static file handler at `/static/`
