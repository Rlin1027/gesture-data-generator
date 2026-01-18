<!-- Parent: ../AGENTS.md -->
# HTML Templates

## Purpose
Jinja2 HTML templates for the Flask web interface. Provides the user interface for image generation and history browsing. Uses custom CSS styling with dark theme.

## Key Files
- `index.html` - Main generation interface
  - API key input with secure password field
  - Mode selector: Variation vs Modification
  - Image upload for seed and reference images
  - Prompt textarea and batch size selector (1-4)
  - Generate button with loading states
  - Results display with AI analysis button
  - Download functionality
- `history.html` - History browsing page
  - Tailwind CSS styling
  - Search by prompt keywords
  - Filter by mode (variation/modification) and status (success/partial/failed)
  - Paginated grid view with thumbnails
  - Detail modal with full metadata
  - ZIP download for records
  - Delete functionality

## For AI Agents

### Template Structure

**index.html**
```html
├── Header
│   ├── Title: "Gesture Data Generator"
│   └── History link → /history
├── Controls Panel
│   ├── 1. System Config (API key, model)
│   ├── 2. Mode Selector (variation/modification)
│   ├── 3. Image Upload (seed, reference)
│   └── 4. Prompt & Batch Size
├── Generate Button
└── Results Section (dynamically populated)
```

**history.html**
```html
├── Header with home link
├── Filters (search, mode, status)
├── Stats (total count, pagination)
├── Gallery Grid (cards with thumbnails)
├── Detail Modal (metadata, images, actions)
└── JavaScript for API calls
```

### Key JavaScript Functions (index.html)
```javascript
setMode(mode)           // Switch variation/modification
previewImage(input, id) // Show image preview
generateImages()        // Submit generation request
analyzeImage(index)     // Request AI vision analysis
downloadImage(index)    // Download generated image
```

### Key JavaScript Functions (history.html)
```javascript
loadHistory(page)       // Load paginated history
showDetail(id)          // Show record detail modal
downloadRecord(id)      // Download ZIP archive
deleteRecord(id)        // Delete record and files
```

### Styling Notes
- **index.html**: Custom CSS from `/static/css/style.css`, dark theme
- **history.html**: Tailwind CSS via CDN, purple primary color (#bb86fc)
- Font: Inter from Google Fonts

### Working in This Module

- **Adding new UI elements**: Edit HTML, add CSS in `static/css/style.css` or Tailwind classes
- **Adding new API calls**: Add JavaScript functions, call appropriate `/api/` endpoints
- **Changing layout**: Modify grid/flex structures, update responsive breakpoints

## Dependencies
- **External**: Tailwind CSS (CDN, history.html only), Google Fonts (Inter)
- **Internal**: Served by Flask, uses `url_for()` for static assets
