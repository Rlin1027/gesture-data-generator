# Gesture Data Generator

## Purpose
A Flask web application and CLI tool for generating and analyzing 320×180 grayscale hand-gesture images using Google Gemini API. Designed for creating NPU model training datasets with features including variation generation, gesture modification, AI vision QC, batch processing, and persistent history tracking.

## Key Files
- `app.py` - Flask web server with REST API endpoints for generation, analysis, and history management
- `cli.py` - Command-line interface for batch generation with YAML configuration
- `gemini_client.py` - Google Gemini API wrapper for image generation and analysis
- `database.py` - SQLite database connection and initialization
- `utils.py` - Image processing utilities (grayscale conversion, resizing)
- `logger.py` - Logging configuration
- `requirements.txt` - Python dependencies (Flask, Pillow, google-generativeai, etc.)
- `README.md` - Project documentation and usage guide

## Subdirectories
- `config/` - Configuration management, schemas, and example YAML files (see config/AGENTS.md)
- `core/` - Core business logic: batch processor, rate limiter, optimizer, metadata (see core/AGENTS.md)
- `models/` - SQLAlchemy ORM models for database records (see models/AGENTS.md)
- `templates/` - Jinja2 HTML templates for web UI (see templates/AGENTS.md)
- `static/` - Frontend CSS and JavaScript assets (see static/AGENTS.md)
- `tests/` - Pytest test suite with unit tests (see tests/AGENTS.md)
- `data/` - Runtime data storage: SQLite database and generated images (see data/AGENTS.md)
- `docs/` - Project documentation and planning documents (see docs/AGENTS.md)

## For AI Agents

### Architecture Overview
```
┌─────────────────┐     ┌─────────────────┐
│   Web UI        │     │   CLI           │
│ (templates/)    │     │ (cli.py)        │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│            app.py / Flask               │
│    REST API: /api/generate, /api/history│
└────────────────────┬────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    ▼                ▼                ▼
┌─────────┐   ┌───────────┐   ┌───────────┐
│ gemini_ │   │  core/    │   │  models/  │
│ client  │   │batch_proc │   │generation │
└─────────┘   └───────────┘   └───────────┘
    │                │                │
    ▼                ▼                ▼
┌─────────────────────────────────────────┐
│         data/ (SQLite + images)         │
└─────────────────────────────────────────┘
```

### Key Workflows

1. **Web Generation Flow**: `index.html` → `POST /api/generate` → `GeminiClient` → save to `data/images/` → store record in SQLite

2. **CLI Batch Flow**: `cli.py run config.yaml` → `BatchProcessor` → rate-limited API calls → `ImageOptimizer` → metadata output

3. **History Flow**: `history.html` → `GET /api/history` → paginated query → display with filter/search

### Working in This Codebase

- **Adding API endpoints**: Edit `app.py`, follow existing pattern with try/catch and JSON responses
- **Modifying generation logic**: Edit `gemini_client.py` for API interaction, `core/batch_processor.py` for batch jobs
- **Database changes**: Update `models/generation.py` for schema, `database.py` for initialization
- **Frontend changes**: HTML in `templates/`, CSS in `static/css/`, JS in `static/js/`
- **Configuration**: Schema in `config/schema.py`, constants in `config/constants.py`

### Testing
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test
python -m pytest tests/unit/test_rate_limiter.py -v
```

### Development Setup
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
python app.py  # Web UI at http://127.0.0.1:5000
```

## Dependencies
- **External**: Google Gemini API for image generation/analysis
- **Python**: Flask 2.x, SQLAlchemy 3.x, Pillow, PyYAML, tqdm, click
- **Runtime**: Python 3.10+, SQLite (bundled)
