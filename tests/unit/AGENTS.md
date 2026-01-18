<!-- Parent: ../AGENTS.md -->
# Unit Tests

## Purpose
Unit tests for the gesture generation system core modules. Tests configuration validation, rate limiting, image optimization, and API endpoints.

## Key Files
- `test_config.py` - Configuration schema validation tests
  - Valid/invalid config parsing
  - Validation error messages
  - Config loading from YAML
- `test_rate_limiter.py` - TokenBucketLimiter tests
  - Token acquisition and blocking
  - Rate limiting accuracy
  - Burst handling
- `test_optimizer.py` - ImageOptimizer tests
  - PNG compression
  - WebP conversion
  - Format detection
- `test_history.py` - History API endpoint tests
  - Pagination
  - Filtering (mode, status)
  - Search functionality
- `test_api.py` - Generation API tests
  - Form validation
  - Response formats
- `__init__.py` - Package initialization

## For AI Agents

### Test Examples

**test_rate_limiter.py**
```python
def test_limiter_blocks_when_exhausted():
    limiter = TokenBucketLimiter(rpm=1, burst_size=1)
    assert limiter.try_acquire() == True   # First succeeds
    assert limiter.try_acquire() == False  # Second fails immediately

def test_limiter_refills_tokens():
    limiter = TokenBucketLimiter(rpm=60, burst_size=1)
    limiter.try_acquire()
    time.sleep(1.1)  # Wait for refill
    assert limiter.try_acquire() == True
```

**test_optimizer.py**
```python
def test_png_compression():
    img = Image.new('L', (320, 180), color=128)
    optimizer = ImageOptimizer(CompressionConfig(png_level=6))
    results = optimizer.optimize(img, OutputFormat.PNG)
    assert 'png' in results
    assert results['png'].optimized_size < results['png'].original_size
```

**test_history.py** (uses fixtures)
```python
def test_history_pagination(client, app):
    with app.app_context():
        # Create test records...
        response = client.get('/api/history?page=1&per_page=10')
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert 'total' in data
```

### Running Specific Tests
```bash
# All unit tests
pytest tests/unit/ -v

# Single file
pytest tests/unit/test_rate_limiter.py -v

# Single test function
pytest tests/unit/test_config.py::test_valid_config_loads -v

# With print output
pytest tests/unit/ -v -s

# With coverage
pytest tests/unit/ --cov=core --cov=config
```

### Adding New Tests
1. Create `test_<module>.py` in this directory
2. Import fixtures from `conftest.py` as needed
3. Use descriptive test names: `test_<feature>_<scenario>`
4. Add assertions with clear failure messages

## Dependencies
- **External**: pytest
- **Internal**: Imports from main codebase, uses fixtures from `../conftest.py`
