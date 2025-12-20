# Gesture Data Generator

A lightweight Flask web tool that uses Google Gemini to generate and analyze 320×180 grayscale hand‑gesture images for NPU model training.

## Features
- **Variation generation** – keep the hand pose, change background, lighting, sensor noise.
- **Gesture modification** – transfer style from a seed image to a reference gesture.
- **AI Vision QC** – automatic quality check (finger count, realism score, lighting, issues).
- **Batch generation** – request up to 4 images per call.
- **Download & naming** – images saved with descriptive filenames.

## Prerequisites
- Python 3.10+ (tested on macOS)
- Google Gemini API key (set in the UI, never stored on the server)

## Installation
```bash
# Clone the repo
git clone <repo‑url>
cd gesture_gen

# Optional virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the app
```bash
python3 app.py
```
Open <http://127.0.0.1:5000> in a browser.

### Using the UI
1. Paste your Gemini API key.
2. Choose **Variation** or **Modification**.
3. Upload a seed image (and a reference image for modification).
4. Enter a prompt (optional).
5. Select **Batch size** (1‑4) and click **Generate**.
6. Use the **🔍 AI 分析** button on each result to view quality metrics.
7. Click **下載圖片** to download the generated file.

## Development & Tests
```bash
# Run unit tests
python -m unittest discover -s . -p "test_*.py"
```

## Preparing for GitHub
```bash
git add .
git commit -m "Initial commit – Gesture Data Generator with batch generation and AI analysis"
git branch -M main
# Replace <repo‑url> with your remote URL
git remote add origin <repo‑url>
git push -u origin main
```

## License
MIT – see `LICENSE` file.
