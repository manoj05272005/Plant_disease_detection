# Backend Testing Suite

## Overview
This directory contains comprehensive unit and integration tests for the Crop Disease Detection backend application.

## Test Structure

```
tests/
├── conftest.py              # Global test fixtures and configuration
├── fixtures/                # Test data factories and fixtures
├── unit/                    # Unit tests for individual modules
├── integration/             # Integration tests for API endpoints
└── services/                # Service layer tests
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run All Tests
```bash
pytest -v
```

### 3. Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### 4. View Coverage Report
```bash
# Open in browser
start htmlcov/index.html  # Windows
```

## Test Categories

### Unit Tests (`-m unit`)
Tests for individual functions and classes in isolation:
- Security (password hashing, JWT, OTP)
- Localization (translations, language detection)
- Image processing (quality checks, bounding boxes)
- Configuration validation
- Schema validation
- File operations
- PDF generation

### Integration Tests (`-m integration`)
Tests for API endpoints and database operations:
- Authentication flow
- Diagnosis API
- User management
- History tracking
- Notifications
- Remediation queries
- Database CRUD operations

### Service Tests
Tests for service layer:
- AI Service (model predictions, Grad-CAM)
- Remediation Service
- Notification Service

## Running Specific Tests

### By Marker
```bash
pytest -m unit                # Unit tests only
pytest -m integration         # Integration tests only
pytest -m auth                # Authentication tests
pytest -m ai                  # AI-related tests
```

### By File
```bash
pytest tests/unit/test_security.py
pytest tests/integration/test_auth_api.py
```

### By Pattern
```bash
pytest -k "test_password"     # All password-related tests
pytest -k "test_login"        # All login tests
```

## Using Test Runner

The `run_tests.py` script provides convenient shortcuts:

```bash
python run_tests.py                # All tests
python run_tests.py --unit         # Unit tests only
python run_tests.py --integration  # Integration tests only
python run_tests.py --coverage     # With detailed coverage
```

## Test Fixtures

### Global Fixtures (in conftest.py)
- `event_loop`: Event loop for async tests
- `test_db`: Clean test database instance
- `client`: HTTP test client
- `authenticated_client`: Authenticated HTTP client
- `mock_user`: Mock user data
- `mock_diagnosis`: Mock diagnosis data
- `mock_image`: Mock image for testing

### Factory Fixtures (in fixtures/factories.py)
- `UserFactory`: Create test users
- `DiagnosisFactory`: Create test diagnoses
- `NotificationFactory`: Create test notifications
- `HistoryFactory`: Create test history records

## Writing New Tests

### Unit Test Example
```python
import pytest
from app.utils.some_module import some_function

@pytest.mark.unit
def test_some_function():
    """Test some_function does what it should"""
    result = some_function("input")
    assert result == "expected_output"
```

### Integration Test Example
```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_endpoint(authenticated_client):
    """Test API endpoint returns correct data"""
    client, user_id = authenticated_client
    
    response = await client.get("/api/v1/endpoint")
    
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

### Async Test Example
```python
import pytest

@pytest.mark.asyncio
async def test_async_function(test_db):
    """Test async database operation"""
    await test_db.collection.insert_one({"key": "value"})
    
    result = await test_db.collection.find_one({"key": "value"})
    assert result is not None
```

## Coverage Goals

- Overall: 85%+
- Core modules: 90%+
- API endpoints: 85%+
- Services: 85%+

## Configuration

### pytest.ini
- Test discovery patterns
- Async mode configuration
- Custom markers
- Coverage settings
- Report formats

### Environment Variables
Tests use a separate test database:
- `MONGODB_DB_NAME_test` for test data
- Automatic cleanup before/after each test

## Best Practices

1. **Test Independence**: Each test should be able to run independently
2. **Database Cleanup**: Use fixtures for automatic cleanup
3. **Mocking**: Mock external dependencies (AI models, external APIs)
4. **Descriptive Names**: Use clear, descriptive test function names
5. **Assert Messages**: Include helpful assertion messages
6. **test Isolation**: Don't rely on test execution order

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml
```

## Troubleshooting

### Tests Failing
1. Ensure MongoDB is running
2. Check environment variables
3. Install all dependencies: `pip install -r requirements.txt`
4. Clear pytest cache: `pytest --cache-clear`

### Coverage Not Generated
1. Ensure pytest-cov is installed: `pip install pytest-cov`
2. Check pytest.ini configuration
3. Verify app module is in Python path

### Async Tests Failing
1. Ensure pytest-asyncio is installed
2. Check event loop configuration in conftest.py
3. Verify `@pytest.mark.asyncio` decorator is used

## Test Statistics

- **Total Tests**: 185+
- **Unit Tests**: 115+
- **Integration Tests**: 48+
- **Service Tests**: 22+

## Maintainers

For questions or issues with tests, refer to:
- UNIT_TESTING_DOCUMENTATION.md (detailed testing guide)
- TESTING_IMPLEMENTATION_SUMMARY.md (implementation details)
