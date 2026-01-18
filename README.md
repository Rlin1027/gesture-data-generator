# Gesture Data Generator

A Flask web tool and CLI for generating and analyzing 320×180 grayscale hand-gesture images using Google Gemini, designed for NPU model training datasets.

## Features

### Web UI
- **Variation generation** – keep the hand pose, change background, lighting, sensor noise.
- **Gesture modification** – transfer style from a seed image to a reference gesture.
- **AI Vision QC** – automatic quality check (finger count, realism score, lighting, issues).
- **Batch generation** – request up to 4 images per call.
- **Download & naming** – images saved with descriptive filenames.
- **History tracking** – persistent history of all generations with search, filter, and download.

### CLI Batch Generation (New!)
- **Config-driven** – YAML configuration files for reproducible experiments.
- **Bulk processing** – generate 100-500+ images in a single run.
- **Rate limiting** – automatic API throttling with token bucket algorithm.
- **Image optimization** – PNG compression and WebP conversion.
- **Metadata tracking** – JSON/CSV output with generation parameters and statistics.
- **Progress display** – real-time progress bar with success/failure counts.

## Prerequisites
- Python 3.10+ (tested on macOS)
- Google Gemini API key

## Installation
```bash
# Clone the repo
git clone <repo-url>
cd gesture_gen

# Optional virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Web UI Usage
```bash
python3 app.py
```
Open <http://127.0.0.1:5000> in a browser.

1. Paste your Gemini API key.
2. Choose **Variation** or **Modification**.
3. Upload a seed image (and a reference image for modification).
4. Enter a prompt (optional).
5. Select **Batch size** (1-4) and click **Generate**.
6. Use the **🔍 AI 分析** button on each result to view quality metrics.
7. Click **下載圖片** to download the generated file.
8. Click **📜 歷史記錄** to browse past generations.

### History Page
Access `/history` to view all past generations with:
- **Search** – filter by prompt keywords.
- **Filter** – by mode (variation/modification) or status (success/partial/failed).
- **Detail view** – click any card to see full metadata and all images.
- **Download ZIP** – download all images and metadata from a generation.
- **Delete** – remove unwanted records and their associated files.

## CLI Batch Generation

### Quick Start
```bash
# Set your API key
export GEMINI_API_KEY="your-api-key"

# Create a config template
python cli.py init --mode variation --output config/my_job.yaml

# Edit the config file with your parameters
# Then validate it
python cli.py validate config/my_job.yaml

# Run the batch generation
python cli.py run config/my_job.yaml
```

### Configuration Example
```yaml
job:
  name: "gesture_dataset_v1"
  mode: "variation"

input:
  seed_image: "./seeds/hand_pose_01.png"

generation:
  count: 200                  # Total images to generate
  batch_size: 4               # Images per API call (1-4)
  prompt: "Generate variation with different lighting and background"
  model: "gemini-2.0-flash-exp-image-generation"

api:
  key_env: "GEMINI_API_KEY"   # Environment variable name
  rate_limit: 60              # Requests per minute

output:
  directory: "./output/dataset_v1"
  format: "png"               # png | webp | both
  compression:
    enabled: true
    png_level: 6              # 0-9
    webp_quality: 85          # 1-100

metadata:
  enabled: true
  format: "json"              # json | csv | both
```

### CLI Commands
```bash
# Execute batch job
python cli.py run config/job.yaml

# With overrides
python cli.py run config/job.yaml --count 50 --format webp

# Skip confirmation
python cli.py run config/job.yaml --yes

# Validate config only
python cli.py validate config/job.yaml

# Create config template
python cli.py init --mode variation

# View last job status
python cli.py status --directory ./output
```

### Output Structure
```
output/dataset_v1/
├── images/
│   ├── gesture_dataset_v1_0001_20250118.png
│   └── ...
├── metadata.json      # Full generation metadata
├── metadata.csv       # Flattened for spreadsheets
└── summary.json       # Job statistics
```

## Development & Tests
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_rate_limiter.py -v
```

## Project Structure
```
gesture_gen/
├── app.py                    # Flask web server
├── database.py               # SQLite database initialization
├── cli.py                    # CLI entry point
├── gemini_client.py          # Gemini API wrapper
├── utils.py                  # Image processing utilities
├── models/
│   └── generation.py         # GenerationRecord ORM model
├── core/
│   ├── batch_processor.py    # Batch generation engine
│   ├── rate_limiter.py       # Token bucket rate limiter
│   ├── optimizer.py          # Image compression
│   └── metadata.py           # Metadata collection
├── config/
│   ├── schema.py             # Config validation
│   └── examples/             # Example configs
├── data/
│   ├── gesture_gen.db        # SQLite database (auto-created)
│   └── images/               # Generated images storage
├── templates/                # Web UI templates
├── static/                   # CSS/JS assets
└── tests/                    # Unit tests
```

## License
MIT – see `LICENSE` file.
