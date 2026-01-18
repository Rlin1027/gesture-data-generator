<!-- Parent: ../AGENTS.md -->
# JavaScript Files

## Purpose
Client-side JavaScript for the Flask web interface. Handles user interactions, image previews, API calls for generation and analysis, and result display.

## Key Files
- `main.js` - Main JavaScript for index.html
  - Mode switching (variation/modification)
  - Image preview functionality
  - Form submission and API communication
  - Result display and download handling

## For AI Agents

### Global State
```javascript
let currentMode = 'variation';  // Current generation mode
```

### Key Functions

**Mode Management**
```javascript
setMode(mode)
// Switches between 'variation' and 'modification'
// Shows/hides reference image input
// Updates button states
```

**Image Preview**
```javascript
previewImage(input, previewId)
// Reads selected file and displays preview
// input: <input type="file"> element
// previewId: ID of preview container
```

**Form Submission** (event listener on generateForm)
```javascript
// Collects form data
// POSTs to /api/generate
// Displays results or error
```

**Result Handling**
```javascript
displayResults(data)
// Renders generated images in results section
// Creates cards with analyze/download buttons

analyzeImage(index)
// POSTs image to /api/analyze
// Displays AI vision QC results

downloadImage(index)
// Triggers image download with descriptive filename
```

### API Endpoints Used
```javascript
POST /api/generate   // Generate images
POST /api/analyze    // AI vision analysis
```

### DOM Element IDs
```javascript
// Inputs
'apiKey'          // API key input
'modelName'       // Model selector
'prompt'          // Prompt textarea
'batchSize'       // Batch size select
'seedImage'       // Seed image file input
'refImage'        // Reference image file input

// Containers
'refImageContainer'  // Reference image section
'seedPreview'        // Seed image preview
'refPreview'         // Reference image preview
'resultsSection'     // Generated results container
'generateBtn'        // Submit button
```

### Working in This File

- **Adding new API calls**: Follow existing fetch pattern with FormData
- **Adding UI interactions**: Add event listeners, update DOM
- **Error handling**: Display errors in alert or dedicated element

## Dependencies
- **External**: None (vanilla JavaScript)
- **Internal**: Calls Flask API endpoints
