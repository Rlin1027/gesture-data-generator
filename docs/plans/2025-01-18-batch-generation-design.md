# Batch Generation, Automation & Image Optimization Design

**Date**: 2025-01-18
**Status**: Approved
**Author**: Claude (with user collaboration)

## Overview

Enhance gesture_gen with bulk image generation, automation via config files, and image optimization capabilities.

## Requirements Summary

| Aspect | Decision |
|--------|----------|
| Primary Use Case | Large-scale dataset generation (quick iteration) |
| Batch Size | 100-500 images, complete within minutes |
| Environment | Local development machine |
| API Plan | Paid Gemini (60-100 RPM) |
| Storage | Files + JSON/CSV metadata |
| Image Optimization | Compression focused (PNG/WebP) |
| Interface | YAML/JSON config-driven |

## Architecture

### New File Structure

```
gesture_gen/
├── cli.py                    # Main entry: config parsing + task execution
├── config/
│   ├── schema.py             # Config validation rules
│   └── examples/
│       ├── variation.yaml    # Variation generation template
│       └── modification.yaml # Style modification template
├── core/
│   ├── batch_processor.py    # Batch processing engine (parallel + progress)
│   ├── rate_limiter.py       # Token bucket rate controller
│   └── optimizer.py          # Image compression (PNG/WebP)
├── output/                   # Default output directory
│   ├── images/
│   └── metadata.json
└── app.py                    # Existing Web UI (unchanged)
```

### Core Flow

```
YAML Config → cli.py parse/validate → batch_processor executes in batches
                                            ↓
                                    rate_limiter controls speed → gemini_client calls
                                            ↓
                                    optimizer compresses → output files + metadata.json
```

## Configuration Format

```yaml
job:
  name: "gesture_dataset_v1"
  mode: "variation"           # variation | modification

input:
  seed_image: "./seeds/hand_pose_01.png"

generation:
  count: 200                  # Total generation count
  batch_size: 4               # Per API call (1-4)
  prompt: "Generate variation with different lighting and background"
  model: "gemini-2.0-flash-exp-image-generation"

api:
  key_env: "GEMINI_API_KEY"   # Read from environment variable
  rate_limit: 60              # RPM limit
  retry_attempts: 3
  retry_delay: 5              # seconds

output:
  directory: "./output/dataset_v1"
  format: "png"               # png | webp | both
  compression:
    enabled: true
    png_level: 6              # 1-9
    webp_quality: 85          # 1-100
  naming: "{job_name}_{index:04d}_{timestamp}"

metadata:
  enabled: true
  format: "json"              # json | csv | both
  include_prompt: true
  include_generation_time: true
```

## Component Designs

### Rate Limiter (Token Bucket)

- Smooth request distribution
- Auto-adapt to different RPM settings
- Thread-safe implementation

### Image Optimizer

| Format | Original | Compressed | Space Saved |
|--------|----------|------------|-------------|
| PNG (level 6) | ~25 KB | ~18 KB | 28% |
| WebP (quality 85) | ~25 KB | ~8 KB | 68% |

### Metadata Structure

Per-image metadata includes:
- Generation parameters (mode, seed, prompt, model)
- Output info (format, size, dimensions)
- Timing (API latency, optimization time)

Output files:
- `metadata.json` - Full metadata array
- `metadata.csv` - Flattened version for Excel
- `summary.json` - Job summary with statistics

### CLI Interface

```bash
python cli.py run config/job.yaml           # Execute batch job
python cli.py validate config/job.yaml      # Validate config only
python cli.py init --mode variation          # Create template
python cli.py status                         # View last job status
```

Override options: `--count`, `--format`, `--output`, `--yes`, `--quiet`, `--dry-run`

## Error Handling

| Error Type | Strategy |
|------------|----------|
| API temporary failure (429/503) | Exponential backoff retry (max 3) |
| Single image failure | Log error, continue to next |
| Invalid API Key | Abort immediately with error |
| Network interruption | Pause and wait, auto-resume |

## Implementation Phases

1. **Phase 1**: Core foundation (rate_limiter, optimizer, schema)
2. **Phase 2**: Batch engine (batch_processor, metadata)
3. **Phase 3**: CLI integration (cli.py, config templates)
4. **Phase 4**: Testing and documentation

## New Dependencies

```
pyyaml>=6.0          # YAML config parsing
tqdm>=4.65           # Progress bar display
click>=8.0           # CLI framework
```

## Design Principles

1. **Backward compatible**: Existing app.py Web UI unchanged
2. **Single entry point**: All batch tasks via cli.py
3. **Config as documentation**: YAML files can be version controlled
