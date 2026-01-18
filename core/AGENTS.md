<!-- Parent: ../AGENTS.md -->
# Core Business Logic

## Purpose
Core business logic modules for batch image generation. Contains the batch processing engine, rate limiting, image optimization, and metadata collection systems. These modules power the CLI batch generation feature and can be used programmatically.

## Key Files
- `batch_processor.py` - Main batch generation engine
  - `BatchProcessor` - Orchestrates parallel generation with progress tracking
  - `BatchResult` - Dataclass for job results and statistics
  - Handles retry logic, error collection, and metadata output
- `rate_limiter.py` - Token bucket rate limiter for API throttling
  - `TokenBucketLimiter` - Thread-safe rate limiting with configurable RPM
  - Supports blocking/non-blocking acquisition, burst handling
- `optimizer.py` - Image compression and format conversion
  - `ImageOptimizer` - PNG compression and WebP conversion
  - `CompressionConfig` - Compression settings (png_level, webp_quality)
  - `OptimizationResult` - Tracks compression ratios and space savings
- `metadata.py` - Metadata collection and output
  - `MetadataCollector` - Collects per-image and job-level metadata
  - `ImageMetadata` - Per-image metadata with timing and dimensions
  - `JobSummary` - Aggregate statistics for batch jobs
  - Outputs JSON, CSV, and summary files
- `__init__.py` - Module exports

## For AI Agents

### Batch Processing Flow
```
cli.py run config.yaml
    │
    ▼
BatchProcessor(config)
    ├── TokenBucketLimiter(rpm)    # Rate limiting
    ├── ImageOptimizer(config)     # Compression
    └── MetadataCollector(name)    # Statistics
    │
    ▼
processor.run(show_progress=True)
    │
    ├── _load_images()             # Load seed/reference
    ├── _create_client()           # GeminiClient
    │
    └── for batch in batches:
        │
        └── _process_batch()
            ├── rate_limiter.acquire()    # Wait for token
            ├── _generate_single()        # API call + retry
            ├── optimizer.optimize()      # Compress image
            └── metadata.add_image()      # Record stats
    │
    ▼
metadata.save_all(output_dir)
    ├── metadata.json
    ├── metadata.csv
    └── summary.json
```

### Key Classes

**TokenBucketLimiter**
```python
limiter = TokenBucketLimiter(rpm=60, burst_size=60)
limiter.acquire()  # Blocks until token available
limiter.try_acquire()  # Non-blocking, returns bool
limiter.wait_time_for(tokens=2)  # Calculate wait time
```

**ImageOptimizer**
```python
optimizer = ImageOptimizer(CompressionConfig(png_level=6, webp_quality=85))
results = optimizer.optimize(image, OutputFormat.BOTH)
# results = {"png": OptimizationResult, "webp": OptimizationResult}
```

**MetadataCollector**
```python
collector = MetadataCollector("job_name", "config.yaml")
collector.add_image(filename="img_001.png", mode="variation", ...)
collector.add_error(batch_index=0, error="API timeout", ...)
collector.save_all(output_dir, output_format="png", metadata_format="json")
```

### Working in This Module

- **Adding new optimization formats**: Extend `OutputFormat` enum, add `_compress_X()` method in `optimizer.py`
- **Modifying rate limiting**: Adjust `TokenBucketLimiter` parameters or algorithm
- **Adding metadata fields**: Update `ImageMetadata` dataclass, `to_dict()`, and `to_flat_dict()` methods
- **Batch processing changes**: Modify `_process_batch()` or `_generate_single()` in `batch_processor.py`

## Dependencies
- **External**: PIL/Pillow for image processing, tqdm for progress bars
- **Internal**:
  - Uses `config.schema.JobConfig` for configuration
  - Uses `gemini_client.GeminiClient` for API calls
  - Uses `utils.process_image` for image preprocessing
