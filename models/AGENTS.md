<!-- Parent: ../AGENTS.md -->
# Database Models

## Purpose
SQLAlchemy ORM models for the gesture generation system. Defines the database schema for persistent storage of generation history, including images, prompts, and analysis results.

## Key Files
- `generation.py` - GenerationRecord model for history tracking
  - Stores mode, prompt, model, batch size, status
  - References to seed, reference, and output images
  - API latency and analysis results
  - `to_dict()` method for JSON serialization
- `__init__.py` - Module exports (exports `GenerationRecord`)

## For AI Agents

### GenerationRecord Schema
```python
class GenerationRecord(db.Model):
    __tablename__ = 'generations'

    id = Integer, primary_key
    mode = String(20)              # 'variation' | 'modification'
    prompt = Text, nullable
    model = String(100)            # e.g., 'gemini-2.5-flash-image'
    batch_size = Integer           # 1-4
    seed_image_path = String(500)  # 'images/seed_xxx.png'
    reference_image_path = String(500)  # For modification mode
    output_images = JSON           # ['images/gen_001.png', ...]
    created_at = DateTime, indexed
    status = String(20), indexed   # 'success' | 'partial' | 'failed'
    success_count = Integer
    api_latency_ms = Integer
    analysis_results = JSON        # AI vision QC results
```

### Usage Examples
```python
from models import GenerationRecord
from database import db

# Create new record
record = GenerationRecord(
    mode='variation',
    prompt='Generate with different lighting',
    model='gemini-2.5-flash-image',
    batch_size=4,
    seed_image_path='images/seed_001.png',
    output_images=['images/gen_001.png', 'images/gen_002.png'],
    status='partial',
    success_count=2,
    api_latency_ms=2500
)
db.session.add(record)
db.session.commit()

# Query with filters
records = GenerationRecord.query\
    .filter(GenerationRecord.status == 'success')\
    .filter(GenerationRecord.mode == 'variation')\
    .order_by(GenerationRecord.created_at.desc())\
    .paginate(page=1, per_page=12)

# Convert to dict for API response
data = record.to_dict()
```

### Working in This Module

- **Adding new fields**: Add column to `GenerationRecord`, update `to_dict()`, may require migration
- **Adding new models**: Create new file in `models/`, add to `__init__.py` exports
- **Database migrations**: Currently no migration system; schema changes require manual DB updates or recreation

### Image Path Convention
- Seed images: `images/seed_YYYYMMDD_HHMMSS_XXXXXXXX.png`
- Reference images: `images/ref_YYYYMMDD_HHMMSS_XXXXXXXX.png`
- Generated images: `images/gen_YYYYMMDD_HHMMSS_XXXXXXXX.png`

## Dependencies
- **External**: Flask-SQLAlchemy
- **Internal**: Uses `database.db` from `database.py`
