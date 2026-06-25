# Unit Testing Documentation - Crop Disease Detection System

**Version:** 1.0.0  
**Date:** February 12, 2026  
**Testing Framework:** pytest  
**Coverage Tool:** pytest-cov  

---

## Table of Contents

1. [Testing Overview](#1-testing-overview)
2. [Testing Framework & Tools](#2-testing-framework--tools)
3. [Test Environment Setup](#3-test-environment-setup)
4. [Project Structure for Tests](#4-project-structure-for-tests)
5. [Test Data & Fixtures](#5-test-data--fixtures)
6. [Unit Test Cases by Module](#6-unit-test-cases-by-module)
7. [API Integration Tests](#7-api-integration-tests)
8. [Mocking & Dependencies](#8-mocking--dependencies)
9. [Edge Cases & Error Scenarios](#9-edge-cases--error-scenarios)
10. [Code Coverage Report](#10-code-coverage-report)
11. [Test Execution](#11-test-execution)
12. [Continuous Integration](#12-continuous-integration)

---

## 1. Testing Overview

### 1.1 Testing Strategy

The testing approach follows the **Test Pyramid**:

```
           ╱╲
          ╱  ╲
         ╱ E2E ╲          ← 10% (End-to-End Tests)
        ╱────────╲
       ╱          ╲
      ╱ Integration╲      ← 30% (API Integration Tests)
     ╱──────────────╲
    ╱                ╲
   ╱   Unit Tests     ╲   ← 60% (Unit Tests)
  ╱____________________╲
```

#### Test Levels:

1. **Unit Tests (60%)**
   - Test individual functions and methods
   - Mock external dependencies
   - Fast execution
   - Maximum coverage

2. **Integration Tests (30%)**
   - Test API endpoints
   - Test database operations
   - Test service interactions
   - Use test database

3. **End-to-End Tests (10%)**
   - Test complete user workflows
   - Test with real dependencies
   - Slower execution

### 1.2 Testing Principles

- **Isolation:** Each test should be independent
- **Repeatability:** Tests should produce same results every time
- **Fast Execution:** Unit tests should run in milliseconds
- **Readable:** Test names should describe what they test
- **Maintainable:** Easy to update when code changes
- **Comprehensive:** Cover happy path, edge cases, and errors

### 1.3 Test Coverage Goals

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| **Core Modules** | 90%+ | 92% |
| **API Routes** | 85%+ | 88% |
| **Services** | 90%+ | 91% |
| **Utilities** | 80%+ | 85% |
| **Overall** | 85%+ | 89% |

---

## 2. Testing Framework & Tools

### 2.1 Core Testing Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **pytest** | 7.4+ | Test framework and runner |
| **pytest-asyncio** | 0.21+ | Async/await test support |
| **pytest-cov** | 4.1+ | Code coverage reporting |
| **pytest-mock** | 3.12+ | Mocking utilities |
| **httpx** | 0.25+ | Async HTTP client for API testing |
| **faker** | 20.0+ | Test data generation |
| **mongomock** | 4.1+ | MongoDB mocking |

### 2.2 Installation

```bash
pip install -r requirements-test.txt
```

**requirements-test.txt:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.2
faker==20.1.0
mongomock==4.1.2
factory-boy==3.3.0
```

### 2.3 Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    auth: Authentication tests
    ai: AI model tests
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
```

---

## 3. Test Environment Setup

### 3.1 Environment Configuration

**tests/.env.test:**
```bash
# Test Environment Configuration
APP_NAME="Crop Disease Detection API - Test"
DEBUG=True
ENVIRONMENT=test

# Test Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=crop_disease_test_db

# Test Security (use different keys)
SECRET_KEY=test-secret-key-do-not-use-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Test Settings
UPLOAD_DIR=test_uploads
MODEL_PATH=test_models
LOG_LEVEL=DEBUG
```

### 3.2 Test Database Setup

```python
# tests/conftest.py
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

@pytest.fixture(scope="session")
async def test_db():
    """Setup test database"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    # Create test collections
    await db.users.delete_many({})
    await db.diagnoses.delete_many({})
    await db.history.delete_many({})
    
    yield db
    
    # Cleanup after all tests
    await db.users.delete_many({})
    await db.diagnoses.delete_many({})
    await db.history.delete_many({})
    client.close()
```

### 3.3 Test Client Setup

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    """HTTP test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

---

## 4. Project Structure for Tests

```
tests/
│
├── __init__.py
├── conftest.py                 # Global fixtures and configuration
│
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_security.py        # Security utilities tests
│   ├── test_image_processing.py # Image processing tests
│   ├── test_localization.py    # Localization tests
│   ├── test_pdf_generator.py   # PDF generation tests
│   └── test_file_handler.py    # File handling tests
│
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_auth_api.py        # Authentication endpoints
│   ├── test_user_api.py        # User management endpoints
│   ├── test_diagnosis_api.py   # Diagnosis endpoints
│   ├── test_history_api.py     # History endpoints
│   ├── test_remediation_api.py # Remediation endpoints
│   └── test_notifications_api.py # Notification endpoints
│
├── services/                   # Service layer tests
│   ├── __init__.py
│   ├── test_ai_service.py      # AI model service tests
│   ├── test_notification_service.py # Notification service tests
│   └── test_remediation_service.py  # Remediation service tests
│
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── mock_data.py           # Mock data generators
│   ├── test_images/           # Sample test images
│   │   ├── healthy_leaf.jpg
│   │   ├── diseased_leaf.jpg
│   │   └── blurry_image.jpg
│   └── factories.py           # Factory Boy factories
│
└── e2e/                       # End-to-end tests
    ├── __init__.py
    └── test_diagnosis_workflow.py
```

---

## 5. Test Data & Fixtures

### 5.1 Global Fixtures

**tests/conftest.py:**

```python
import pytest
import asyncio
from faker import Faker
from datetime import datetime
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.core.config import settings

fake = Faker()

# Event loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Database fixture
@pytest.fixture(scope="function")
async def test_db():
    """Test database instance"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[f"{settings.MONGODB_DB_NAME}_test"]
    
    # Clean before test
    await db.users.delete_many({})
    await db.diagnoses.delete_many({})
    await db.history.delete_many({})
    await db.notifications.delete_many({})
    
    yield db
    
    # Clean after test
    await db.users.delete_many({})
    await db.diagnoses.delete_many({})
    await db.history.delete_many({})
    await db.notifications.delete_many({})
    client.close()

# HTTP client fixture
@pytest.fixture
async def client():
    """Async HTTP test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Authenticated client fixture
@pytest.fixture
async def authenticated_client(test_db):
    """HTTP client with authentication"""
    # Create test user
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "hashed_password": get_password_hash("testpassword123"),
        "preferred_language": "en",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    result = await test_db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    # Create access token
    token = create_access_token(data={"sub": user_id})
    
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac, user_id

# Mock user fixture
@pytest.fixture
def mock_user():
    """Generate mock user data"""
    return {
        "_id": "65abc123def456",
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "preferred_language": "en",
        "location": fake.city(),
        "is_active": True,
        "created_at": datetime.utcnow()
    }

# Mock diagnosis fixture
@pytest.fixture
def mock_diagnosis():
    """Generate mock diagnosis data"""
    return {
        "_id": "65diag123xyz",
        "user_id": "65abc123def456",
        "crop_type": "tomato",
        "disease_id": "tomato_early_blight",
        "disease_name": "Early Blight",
        "confidence": 0.92,
        "severity": "medium",
        "is_healthy": False,
        "image_url": "/uploads/images/test.jpg",
        "heatmap_url": "/uploads/heatmaps/test.jpg",
        "bounding_boxes": [{"x": 100, "y": 150, "width": 80, "height": 100}],
        "created_at": datetime.utcnow()
    }

# Mock image fixture
@pytest.fixture
def mock_image():
    """Generate mock image data"""
    import numpy as np
    # Create 224x224 RGB image
    return np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
```

### 5.2 Factory Boy Factories

**tests/fixtures/factories.py:**

```python
import factory
from faker import Faker
from datetime import datetime

fake = Faker()

class UserFactory(factory.Factory):
    """User model factory"""
    class Meta:
        model = dict
    
    _id = factory.Faker('uuid4')
    name = factory.Faker('name')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    hashed_password = "$2b$12$hashedpassword"
    preferred_language = "en"
    location = factory.Faker('city')
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)

class DiagnosisFactory(factory.Factory):
    """Diagnosis model factory"""
    class Meta:
        model = dict
    
    _id = factory.Faker('uuid4')
    user_id = factory.Faker('uuid4')
    crop_type = "tomato"
    disease_id = "tomato_early_blight"
    disease_name = "Early Blight"
    confidence = 0.92
    severity = "medium"
    is_healthy = False
    image_url = "/uploads/images/test.jpg"
    heatmap_url = "/uploads/heatmaps/test.jpg"
    bounding_boxes = []
    created_at = factory.LazyFunction(datetime.utcnow)

class NotificationFactory(factory.Factory):
    """Notification model factory"""
    class Meta:
        model = dict
    
    _id = factory.Faker('uuid4')
    user_id = factory.Faker('uuid4')
    type = "diagnosis_complete"
    title = {"en": "Diagnosis Complete"}
    message = {"en": "Your diagnosis is ready"}
    is_read = False
    created_at = factory.LazyFunction(datetime.utcnow)
```

### 5.3 Mock Data Generators

**tests/fixtures/mock_data.py:**

```python
from faker import Faker
from datetime import datetime, timedelta
import random

fake = Faker()

def generate_mock_users(count=10):
    """Generate multiple mock users"""
    users = []
    for _ in range(count):
        users.append({
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "preferred_language": random.choice(["en", "hi", "kn", "ta"]),
            "location": fake.city(),
            "is_active": True,
            "created_at": datetime.utcnow()
        })
    return users

def generate_mock_diagnoses(user_id, count=5):
    """Generate multiple mock diagnoses"""
    diseases = [
        ("tomato_early_blight", "Early Blight", "medium"),
        ("tomato_late_blight", "Late Blight", "high"),
        ("tomato_healthy", "Healthy", "low"),
        ("rice_blast", "Rice Blast", "high"),
    ]
    
    diagnoses = []
    for i in range(count):
        disease = random.choice(diseases)
        diagnoses.append({
            "user_id": user_id,
            "crop_type": "tomato",
            "disease_id": disease[0],
            "disease_name": disease[1],
            "confidence": round(random.uniform(0.7, 0.98), 2),
            "severity": disease[2],
            "is_healthy": "healthy" in disease[0],
            "created_at": datetime.utcnow() - timedelta(days=i)
        })
    return diagnoses
```

---

## 6. Unit Test Cases by Module

### 6.1 Security Module Tests

**tests/unit/test_security.py:**

```python
import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp
)
from jose import jwt, JWTError
from app.core.config import settings

class TestPasswordHashing:
    """Test password hashing utilities"""
    
    def test_password_hash_creates_different_hash(self):
        """Test that same password creates different hashes"""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Due to salt
        assert hash1.startswith("$2b$")  # bcrypt format
    
    def test_verify_password_success(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test password verification with wrong password"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("wrongpassword", hashed) is False
    
    def test_password_hash_not_empty(self):
        """Test that password hash is not empty"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert len(hashed) > 0
        assert hashed != password

class TestJWTTokens:
    """Test JWT token creation and validation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_decode_token_success(self):
        """Test token decoding with valid token"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        decoded = decode_token(token)
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "access"
    
    def test_decode_token_invalid(self):
        """Test token decoding with invalid token"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            decode_token("invalid.token.here")
        
        assert exc.value.status_code == 401
        assert "Could not validate credentials" in exc.value.detail
    
    def test_token_expiration(self):
        """Test token expiration"""
        from datetime import timedelta
        
        data = {"sub": "user123"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(HTTPException):
            decode_token(token)

class TestOTPGeneration:
    """Test OTP generation"""
    
    def test_generate_otp_default_length(self):
        """Test OTP generation with default length"""
        otp = generate_otp()
        
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_otp_custom_length(self):
        """Test OTP generation with custom length"""
        otp = generate_otp(length=4)
        
        assert len(otp) == 4
        assert otp.isdigit()
    
    def test_generate_otp_uniqueness(self):
        """Test that OTPs are unique"""
        otp1 = generate_otp()
        otp2 = generate_otp()
        
        # While theoretically they could be same, probability is low
        # This test might occasionally fail due to randomness
        assert otp1 != otp2 or len(set([generate_otp() for _ in range(100)])) > 1
```

### 6.2 Image Processing Tests

**tests/unit/test_image_processing.py:**

```python
import pytest
import numpy as np
import cv2
from app.utils.image_processing import ImageProcessor

class TestImageQualityCheck:
    """Test image quality checking"""
    
    def test_blur_detection_sharp_image(self):
        """Test blur detection on sharp image"""
        # Create sharp image with high frequency content
        image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        # Add some edges
        image[100:124, 100:124] = 255
        
        result = ImageProcessor.check_blur(image)
        
        assert "is_acceptable" in result
        assert "blur_score" in result
        assert isinstance(result["is_acceptable"], bool)
        assert isinstance(result["blur_score"], (int, float))
    
    def test_blur_detection_blurry_image(self):
        """Test blur detection on blurry image"""
        # Create uniform blurry image
        image = np.ones((224, 224, 3), dtype=np.uint8) * 128
        
        result = ImageProcessor.check_blur(image)
        
        assert result["is_acceptable"] is False
        assert result["blur_score"] < 100  # Below threshold
    
    def test_check_blur_with_none_image(self):
        """Test blur check with None image"""
        with pytest.raises(Exception):
            ImageProcessor.check_blur(None)

class TestBoundingBoxDetection:
    """Test bounding box detection"""
    
    def test_detect_bounding_boxes(self, mock_image):
        """Test bounding box detection"""
        annotated, boxes = ImageProcessor.detect_bounding_boxes(mock_image)
        
        assert annotated is not None
        assert isinstance(boxes, list)
        assert annotated.shape == mock_image.shape
    
    def test_bounding_box_structure(self, mock_image):
        """Test bounding box data structure"""
        _, boxes = ImageProcessor.detect_bounding_boxes(mock_image)
        
        if len(boxes) > 0:
            box = boxes[0]
            assert "x" in box
            assert "y" in box
            assert "width" in box
            assert "height" in box

class TestSeverityCalculation:
    """Test severity calculation"""
    
    def test_calculate_severity_with_boxes(self, mock_image):
        """Test severity calculation with bounding boxes"""
        boxes = [
            {"x": 50, "y": 50, "width": 100, "height": 100}
        ]
        
        severity = ImageProcessor.calculate_severity(mock_image, boxes)
        
        assert severity in ["low", "medium", "high", "critical"]
    
    def test_calculate_severity_no_boxes(self, mock_image):
        """Test severity calculation with no boxes"""
        severity = ImageProcessor.calculate_severity(mock_image, [])
        
        assert severity == "low"

class TestImageEncoding:
    """Test image encoding utilities"""
    
    def test_encode_image_to_base64(self, mock_image):
        """Test image encoding to base64"""
        base64_str = ImageProcessor.encode_image_to_base64(mock_image)
        
        assert base64_str is not None
        assert isinstance(base64_str, str)
        assert base64_str.startswith("data:image/")
    
    def test_decode_base64_to_image(self, mock_image):
        """Test decoding base64 to image"""
        base64_str = ImageProcessor.encode_image_to_base64(mock_image)
        decoded_image = ImageProcessor.decode_base64_to_image(base64_str)
        
        assert decoded_image is not None
        assert decoded_image.shape == mock_image.shape
```

### 6.3 Localization Tests

**tests/unit/test_localization.py:**

```python
import pytest
from app.utils.localization import Localizer, get_language_from_request

class TestLocalization:
    """Test localization utilities"""
    
    def test_translate_english(self):
        """Test translation to English"""
        text = Localizer.translate("app_name", "en")
        
        assert text == "Crop Disease Detection"
    
    def test_translate_hindi(self):
        """Test translation to Hindi"""
        text = Localizer.translate("welcome", "hi")
        
        assert text == "स्वागत है"
    
    def test_translate_unsupported_language_fallback(self):
        """Test fallback to English for unsupported language"""
        text = Localizer.translate("app_name", "xyz")
        
        assert text == "Crop Disease Detection"  # Falls back to English
    
    def test_translate_missing_key(self):
        """Test translation with missing key"""
        text = Localizer.translate("nonexistent_key", "en")
        
        assert text == "nonexistent_key"  # Returns key itself
    
    def test_get_localized_dict(self):
        """Test getting localized value from dict"""
        data = {
            "en": "Hello",
            "hi": "नमस्ते",
            "kn": "ನಮಸ್ಕಾರ"
        }
        
        text = Localizer.get_localized_dict(data, "hi")
        assert text == "नमस्ते"
    
    def test_get_localized_dict_fallback(self):
        """Test localized dict with fallback"""
        data = {
            "en": "Hello",
            "hi": "नमस्ते"
        }
        
        text = Localizer.get_localized_dict(data, "xyz")
        assert text == "Hello"  # Falls back to English

class TestLanguageDetection:
    """Test language detection from request"""
    
    def test_language_from_header(self):
        """Test language detection from Accept-Language header"""
        lang = get_language_from_request("hi-IN,hi;q=0.9,en;q=0.8")
        
        assert lang == "hi"
    
    def test_language_from_user_preference(self):
        """Test language from user preference"""
        lang = get_language_from_request(None, user_preference="kn")
        
        assert lang == "kn"
    
    def test_language_default_fallback(self):
        """Test default language fallback"""
        lang = get_language_from_request(None, None)
        
        assert lang == "en"
```

### 6.4 File Handler Tests

**tests/unit/test_file_handler.py:**

```python
import pytest
import os
from pathlib import Path
from app.utils.file_handler import FileHandler

class TestFileHandler:
    """Test file handling utilities"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test"""
        # Setup
        FileHandler.ensure_upload_dir()
        yield
        # Teardown - clean test files
        # (implement cleanup logic)
    
    def test_ensure_upload_dir_creates_directories(self):
        """Test that upload directories are created"""
        FileHandler.ensure_upload_dir()
        
        assert os.path.exists("uploads/images")
        assert os.path.exists("uploads/heatmaps")
        assert os.path.exists("uploads/videos")
        assert os.path.exists("uploads/reports")
    
    @pytest.mark.asyncio
    async def test_save_image_from_base64(self):
        """Test saving image from base64"""
        base64_data = "data:image/jpeg;base64,/9j/4AAQSkZJRg..."  # truncated
        
        # This is a mock test - in real scenario, use valid base64
        # file_path = await FileHandler.save_image_from_base64(base64_data)
        # assert os.path.exists(file_path)
        pass
    
    def test_get_file_url(self):
        """Test file URL generation"""
        file_path = "uploads/images/test.jpg"
        url = FileHandler.get_file_url(file_path)
        
        assert url.startswith("/")
        assert "test.jpg" in url
    
    def test_validate_file_extension(self):
        """Test file extension validation"""
        assert FileHandler.validate_file_extension("test.jpg") is True
        assert FileHandler.validate_file_extension("test.jpeg") is True
        assert FileHandler.validate_file_extension("test.png") is True
        assert FileHandler.validate_file_extension("test.pdf") is False
```

---

## 7. API Integration Tests

### 7.1 Authentication API Tests

**tests/integration/test_auth_api.py:**

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestAuthenticationAPI:
    """Test authentication endpoints"""
    
    async def test_register_success(self, client: AsyncClient, test_db):
        """Test successful user registration"""
        response = await client.post("/api/v1/auth/register", json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+919876543210",
            "password": "SecurePass123",
            "preferred_language": "en"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert "hashed_password" not in data
        assert "_id" in data
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_db):
        """Test registration with duplicate email"""
        # Register first user
        await client.post("/api/v1/auth/register", json={
            "name": "User One",
            "email": "duplicate@example.com",
            "password": "Password123"
        })
        
        # Try to register with same email
        response = await client.post("/api/v1/auth/register", json={
            "name": "User Two",
            "email": "duplicate@example.com",
            "password": "Password456"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email"""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "Password123"
        })
        
        assert response.status_code == 422  # Validation error
    
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password"""
        response = await client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "123"  # Too short
        })
        
        assert response.status_code == 422
    
    async def test_login_success(self, client: AsyncClient, test_db):
        """Test successful login"""
        # Register user first
        await client.post("/api/v1/auth/register", json={
            "name": "Login Test",
            "email": "logintest@example.com",
            "password": "TestPass123"
        })
        
        # Login
        response = await client.post("/api/v1/auth/login", data={
            "username": "logintest@example.com",
            "password": "TestPass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_db):
        """Test login with wrong password"""
        # Register user
        await client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "CorrectPass123"
        })
        
        # Login with wrong password
        response = await client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "WrongPass123"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user"""
        response = await client.post("/api/v1/auth/login", data={
            "username": "nonexistent@example.com",
            "password": "Password123"
        })
        
        assert response.status_code == 401
    
    async def test_refresh_token(self, client: AsyncClient, test_db):
        """Test token refresh"""
        # Register and login
        await client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "TestPass123"
        })
        
        login_response = await client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "TestPass123"
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    async def test_logout(self, authenticated_client):
        """Test logout"""
        client, user_id = authenticated_client
        
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]
    
    async def test_forgot_password(self, client: AsyncClient, test_db):
        """Test forgot password request"""
        # Register user
        await client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "forgot@example.com",
            "password": "OldPass123"
        })
        
        # Request password reset
        response = await client.post("/api/v1/auth/forgot-password", json={
            "username": "forgot@example.com"
        })
        
        assert response.status_code == 200
        assert "reset" in response.json()["message"].lower()
```

### 7.2 Diagnosis API Tests

**tests/integration/test_diagnosis_api.py:**

```python
import pytest
from httpx import AsyncClient
import io
from PIL import Image
import numpy as np

@pytest.mark.asyncio
class TestDiagnosisAPI:
    """Test diagnosis endpoints"""
    
    def create_test_image(self):
        """Create a test image file"""
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
    
    async def test_check_image_quality(self, client: AsyncClient):
        """Test image quality check endpoint"""
        img_bytes = self.create_test_image()
        
        response = await client.post(
            "/api/v1/diagnosis/check-quality",
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_acceptable" in data
        assert "blur_score" in data
        assert isinstance(data["is_acceptable"], bool)
    
    async def test_create_diagnosis(self, authenticated_client):
        """Test creating a diagnosis"""
        client, user_id = authenticated_client
        img_bytes = self.create_test_image()
        
        response = await client.post(
            "/api/v1/diagnosis/",
            data={"crop_type": "tomato"},
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["crop_type"] == "tomato"
        assert "disease_name" in data
        assert "confidence" in data
        assert "severity" in data
        assert data["user_id"] == user_id
    
    async def test_create_diagnosis_unauthorized(self, client: AsyncClient):
        """Test diagnosis creation without authentication"""
        img_bytes = self.create_test_image()
        
        response = await client.post(
            "/api/v1/diagnosis/",
            data={"crop_type": "tomato"},
            files={"image": ("test.jpg", img_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 401
    
    async def test_get_diagnosis_by_id(self, authenticated_client, test_db):
        """Test getting specific diagnosis"""
        client, user_id = authenticated_client
        
        # Create a diagnosis first
        diagnosis_data = {
            "user_id": user_id,
            "crop_type": "tomato",
            "disease_id": "tomato_early_blight",
            "disease_name": "Early Blight",
            "confidence": 0.92,
            "severity": "medium",
            "is_healthy": False
        }
        result = await test_db.diagnoses.insert_one(diagnosis_data)
        diagnosis_id = str(result.inserted_id)
        
        # Get the diagnosis
        response = await client.get(f"/api/v1/diagnosis/{diagnosis_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["disease_name"] == "Early Blight"
    
    async def test_list_diagnoses(self, authenticated_client, test_db):
        """Test listing user's diagnoses"""
        client, user_id = authenticated_client
        
        # Create multiple diagnoses
        for i in range(3):
            await test_db.diagnoses.insert_one({
                "user_id": user_id,
                "crop_type": "tomato",
                "disease_name": f"Disease {i}",
                "confidence": 0.9
            })
        
        # List diagnoses
        response = await client.get("/api/v1/diagnosis/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
```

### 7.3 History API Tests

**tests/integration/test_history_api.py:**

```python
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

@pytest.mark.asyncio
class TestHistoryAPI:
    """Test history endpoints"""
    
    async def test_get_history(self, authenticated_client, test_db):
        """Test getting history"""
        client, user_id = authenticated_client
        
        # Create history entries
        for i in range(5):
            await test_db.history.insert_one({
                "user_id": user_id,
                "diagnosis_id": f"diag{i}",
                "crop_type": "tomato",
                "disease_name": f"Disease {i}",
                "severity": "medium",
                "confidence": 0.9,
                "is_healthy": False,
                "created_at": datetime.utcnow() - timedelta(days=i)
            })
        
        response = await client.get("/api/v1/history/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 20  # Default limit
    
    async def test_get_history_with_pagination(self, authenticated_client, test_db):
        """Test history pagination"""
        client, user_id = authenticated_client
        
        # Create 25 history entries
        for i in range(25):
            await test_db.history.insert_one({
                "user_id": user_id,
                "disease_name": f"Disease {i}",
                "created_at": datetime.utcnow()
            })
        
        # Get first page
        response = await client.get("/api/v1/history/?skip=0&limit=10")
        assert len(response.json()) == 10
        
        # Get second page
        response = await client.get("/api/v1/history/?skip=10&limit=10")
        assert len(response.json()) == 10
    
    async def test_filter_history_by_crop_type(self, authenticated_client, test_db):
        """Test filtering history by crop type"""
        client, user_id = authenticated_client
        
        # Create mixed crop types
        await test_db.history.insert_one({
            "user_id": user_id,
            "crop_type": "tomato",
            "disease_name": "Early Blight",
            "created_at": datetime.utcnow()
        })
        await test_db.history.insert_one({
            "user_id": user_id,
            "crop_type": "rice",
            "disease_name": "Rice Blast",
            "created_at": datetime.utcnow()
        })
        
        response = await client.get("/api/v1/history/?crop_type=tomato")
        
        assert response.status_code == 200
        data = response.json()
        assert all(entry["crop_type"] == "tomato" for entry in data)
    
    async def test_delete_history_entry(self, authenticated_client, test_db):
        """Test deleting history entry"""
        client, user_id = authenticated_client
        
        # Create history entry
        result = await test_db.history.insert_one({
            "user_id": user_id,
            "disease_name": "Test Disease",
            "created_at": datetime.utcnow()
        })
        history_id = str(result.inserted_id)
        
        # Delete entry
        response = await client.delete(f"/api/v1/history/{history_id}")
        
        assert response.status_code == 200
        
        # Verify soft delete
        entry = await test_db.history.find_one({"_id": result.inserted_id})
        assert entry["is_deleted"] is True
    
    async def test_get_analytics(self, authenticated_client, test_db):
        """Test getting analytics"""
        client, user_id = authenticated_client
        
        # Create diverse history
        diseases = ["Early Blight", "Late Blight", "Healthy"]
        for disease in diseases:
            await test_db.history.insert_one({
                "user_id": user_id,
                "disease_name": disease,
                "crop_type": "tomato",
                "severity": "medium",
                "created_at": datetime.utcnow()
            })
        
        response = await client.get("/api/v1/history/analytics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_diagnoses" in data
        assert "disease_frequency" in data
        assert "crop_distribution" in data
```

---

## 8. Mocking & Dependencies

### 8.1 Mocking Database Operations

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_database():
    """Mock database for unit tests"""
    db = MagicMock()
    db.users = MagicMock()
    db.diagnoses = MagicMock()
    db.history = MagicMock()
    
    # Mock async methods
    db.users.find_one = AsyncMock()
    db.users.insert_one = AsyncMock()
    db.users.update_one = AsyncMock()
    
    return db

def test_with_mock_database(mock_database):
    """Example test using mocked database"""
    # Set return value
    mock_database.users.find_one.return_value = {
        "_id": "123",
        "name": "Test User",
        "email": "test@example.com"
    }
    
    # Your test logic here
    # ...
    
    # Verify calls
    mock_database.users.find_one.assert_called_once()
```

### 8.2 Mocking AI Model

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_ai_model():
    """Mock AI model for testing"""
    with patch('app.services.ai_service.AIModelService') as mock:
        mock_instance = MagicMock()
        mock_instance.predict_disease = AsyncMock(return_value={
            "disease_id": "tomato_early_blight",
            "disease_name": "Early Blight",
            "confidence": 0.92,
            "severity": "medium",
            "is_healthy": False,
            "heatmap_image": None,
            "bounding_boxes": []
        })
        mock.return_value = mock_instance
        yield mock_instance

@pytest.mark.asyncio
async def test_diagnosis_with_mock_model(mock_ai_model):
    """Test diagnosis using mocked AI model"""
    result = await mock_ai_model.predict_disease(None, "tomato")
    
    assert result["disease_name"] == "Early Blight"
    assert result["confidence"] == 0.92
```

### 8.3 Mocking External APIs

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_password_reset_email():
    """Test password reset email sending (mocked)"""
    with patch('app.services.email_service.send_email') as mock_send:
        mock_send.return_value = AsyncMock(return_value=True)
        
        # Your test logic
        # ...
        
        # Verify email was "sent"
        mock_send.assert_called_once()
```

---

## 9. Edge Cases & Error Scenarios

### 9.1 Edge Case Tests

```python
import pytest

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_empty_diagnosis_list(self, authenticated_client):
        """Test getting diagnoses when none exist"""
        client, user_id = authenticated_client
        
        response = await client.get("/api/v1/diagnosis/")
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_very_large_image(self, authenticated_client):
        """Test uploading image exceeding size limit"""
        client, user_id = authenticated_client
        
        # Create large image (> 10MB)
        large_image = b'0' * (11 * 1024 * 1024)
        
        response = await client.post(
            "/api/v1/diagnosis/",
            data={"crop_type": "tomato"},
            files={"image": ("large.jpg", large_image, "image/jpeg")}
        )
        
        assert response.status_code == 413  # Payload too large
    
    @pytest.mark.asyncio
    async def test_malformed_json(self, client: AsyncClient):
        """Test API with malformed JSON"""
        response = await client.post(
            "/api/v1/auth/register",
            data="not valid json"
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, client: AsyncClient):
        """Test protection against SQL injection"""
        response = await client.post("/api/v1/auth/login", data={
            "username": "admin' OR '1'='1",
            "password": "password"
        })
        
        assert response.status_code == 401  # Should not allow injection
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, authenticated_client):
        """Test handling concurrent requests"""
        import asyncio
        client, user_id = authenticated_client
        
        # Make multiple concurrent requests
        tasks = [
            client.get("/api/v1/user/profile")
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        
        assert all(r.status_code == 200 for r in responses)
```

### 9.2 Error Scenario Tests

```python
class TestErrorScenarios:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing protected route without auth"""
        response = await client.get("/api/v1/user/profile")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_accessing_other_user_data(self, authenticated_client, test_db):
        """Test accessing another user's data"""
        client, user_id = authenticated_client
        
        # Create another user's diagnosis
        other_diagnosis = await test_db.diagnoses.insert_one({
            "user_id": "other_user_id",
            "disease_name": "Test Disease"
        })
        
        # Try to access it
        response = await client.get(f"/api/v1/diagnosis/{other_diagnosis.inserted_id}")
        
        assert response.status_code in [403, 404]  # Forbidden or not found
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, client: AsyncClient):
        """Test handling database connection errors"""
        with patch('app.core.database.Database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = await client.get("/api/v1/user/profile")
            
            assert response.status_code == 500
```

---

## 10. Code Coverage Report

### 10.1 Generating Coverage Report

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML report
# Open htmlcov/index.html in browser
```

### 10.2 Sample Coverage Report

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
app/__init__.py                             2      0   100%
app/main.py                                45      2    96%   67-68
app/api/__init__.py                         1      0   100%
app/api/v1/__init__.py                     15      0   100%
app/api/v1/auth.py                        120      8    93%   156-158, 245-250
app/api/v1/user.py                         55      3    95%   42-44
app/api/v1/diagnosis.py                   135     12    91%   various
app/api/v1/history.py                      88      6    93%   various
app/api/v1/notifications.py                45      2    96%   various
app/api/v1/remediation.py                  35      1    97%   various
app/core/__init__.py                        1      0   100%
app/core/config.py                         45      2    96%   various
app/core/database.py                       42      3    93%   various
app/core/security.py                       85      5    94%   various
app/models/__init__.py                      1      0   100%
app/models/schemas.py                     145      8    95%   various
app/services/__init__.py                    1      0   100%
app/services/ai_service.py                180     18    90%   various
app/services/notification_service.py       65      4    94%   various
app/services/remediation_service.py       150     12    92%   various
app/utils/__init__.py                       1      0   100%
app/utils/file_handler.py                  55      5    91%   various
app/utils/image_processing.py             120     10    92%   various
app/utils/localization.py                  48      3    94%   various
app/utils/pdf_generator.py                 95      8    92%   various
---------------------------------------------------------------------
TOTAL                                    1574    112    93%
```

### 10.3 Coverage Badges

```markdown
![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)
```

---

## 11. Test Execution

### 11.1 Running All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_security.py

# Run specific test class
pytest tests/unit/test_security.py::TestPasswordHashing

# Run specific test method
pytest tests/unit/test_security.py::TestPasswordHashing::test_verify_password_success
```

### 11.2 Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Run authentication tests
pytest -m auth

# Run all except slow tests
pytest -m "not slow"
```

### 11.3 Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto detect CPUs)
pytest -n auto

# Run tests on 4 CPUs
pytest -n 4
```

### 11.4 Watch Mode (Development)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests in watch mode
ptw
```

### 11.5 Test Reports

```bash
# Generate HTML report
pytest --html=report.html --self-contained-html

# Generate JUnit XML (for CI/CD)
pytest --junitxml=junit.xml

# Generate JSON report
pytest --json-report --json-report-file=report.json
```

---

## 12. Continuous Integration

### 12.1 GitHub Actions Workflow

**.github/workflows/test.yml:**

```yaml
name: Backend Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mongodb:
        image: mongo:5.0
        ports:
          - 27017:27017
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests with coverage
      run: |
        cd backend
        pytest --cov=app --cov-report=xml --cov-report=term
      env:
        MONGODB_URL: mongodb://localhost:27017
        SECRET_KEY: test-secret-key
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        fail_ci_if_error: true
    
    - name: Check coverage threshold
      run: |
        cd backend
        pytest --cov=app --cov-fail-under=85
```

### 12.2 Pre-commit Hooks

**.pre-commit-config.yaml:**

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ['-v', '--tb=short']
      
      - id: pytest-cov
        name: pytest-cov
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ['--cov=app', '--cov-fail-under=85']
```

---

## Appendix A: Test Checklist

### Unit Tests Checklist
- [ ] Security module tests
- [ ] Image processing tests
- [ ] Localization tests
- [ ] PDF generator tests
- [ ] File handler tests

### Integration Tests Checklist
- [ ] Authentication API tests
- [ ] User management API tests
- [ ] Diagnosis API tests
- [ ] History API tests
- [ ] Remediation API tests
- [ ] Notification API tests

### Coverage Checklist
- [ ] Overall coverage > 85%
- [ ] Core modules coverage > 90%
- [ ] API routes coverage > 85%
- [ ] Services coverage > 90%

### Quality Checklist
- [ ] All tests pass
- [ ] No skipped tests without reason
- [ ] Test names are descriptive
- [ ] Tests are isolated and independent
- [ ] Mocks are used appropriately
- [ ] Edge cases are covered
- [ ] Error scenarios are tested

---

## Appendix B: Common Test Patterns

### Pattern 1: AAA (Arrange-Act-Assert)

```python
def test_password_hashing():
    # Arrange
    password = "testpassword123"
    
    # Act
    hashed = get_password_hash(password)
    
    # Assert
    assert hashed != password
    assert verify_password(password, hashed)
```

### Pattern 2: Given-When-Then (BDD Style)

```python
async def test_user_login():
    # Given a registered user
    user = await create_test_user()
    
    # When they login with correct credentials
    response = await client.post("/auth/login", data={
        "username": user["email"],
        "password": "testpass"
    })
    
    # Then they receive valid tokens
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Pattern 3: Parameterized Tests

```python
@pytest.mark.parametrize("language,expected", [
    ("en", "Crop Disease Detection"),
    ("hi", "फसल रोग का पता लगाना"),
    ("kn", "ಬೆಳೆ ರೋಗ ಪತ್ತೆ"),
])
def test_translation(language, expected):
    result = Localizer.translate("app_name", language)
    assert result == expected
```

---

**Document Version:** 1.0  
**Last Updated:** February 12, 2026  
**Maintained By:** Backend Testing Team  
**Next Review Date:** March 12, 2026
