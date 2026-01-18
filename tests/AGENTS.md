<!-- Parent: ../AGENTS.md -->
# Test Suite

## Purpose
Pytest test suite for the gesture generation system. Contains unit tests for core modules, configuration validation, and API endpoints. Uses fixtures for Flask app and database setup.

## Key Files
- `conftest.py` - Pytest fixtures and configuration
  - `app` fixture - Creates Flask app with temporary SQLite database
  - `client` fixture - Test client for API testing
  - `base_url`, `api_key` fixtures for integration tests
- `__init__.py` - Package initialization

## Subdirectories
- `unit/` - Unit tests (see tests/unit/AGENTS.md)
  - `test_config.py` - Configuration schema validation tests
  - `test_rate_limiter.py` - TokenBucketLimiter tests
  - `test_optimizer.py` - ImageOptimizer tests
  - `test_history.py` - History API endpoint tests
  - `test_api.py` - Generation API tests

## For AI Agents

### Running Tests
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_rate_limiter.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=core --cov-report=term

# Run specific test function
python -m pytest tests/unit/test_config.py::test_valid_config -v
```

### Fixture Usage
```python
def test_api_endpoint(client):
    """Test with Flask test client."""
    response = client.get('/api/history')
    assert response.status_code == 200

def test_database(app):
    """Test with app context and database."""
    with app.app_context():
        from models import GenerationRecord
        record = GenerationRecord(mode='variation', ...)
        db.session.add(record)
        db.session.commit()
```

### Test Naming Conventions
- Test files: `test_<module>.py`
- Test functions: `test_<feature>_<scenario>()`
- Example: `test_rate_limiter_acquires_tokens()`

### Working in This Module

- **Adding new tests**: Create test file in `unit/`, import fixtures from `conftest.py`
- **Adding fixtures**: Add to `conftest.py` with `@pytest.fixture` decorator
- **Mocking**: Use `unittest.mock` or `pytest-mock` for external dependencies

## Dependencies
- **External**: pytest, pytest fixtures
- **Internal**: Tests import from main codebase modules
