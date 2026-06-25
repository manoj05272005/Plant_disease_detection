"""
Global Test Fixtures and Configuration
"""
import pytest
import asyncio
import sys
from pathlib import Path
from faker import Faker
from datetime import datetime
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    await db.sessions.delete_many({})
    await db.password_resets.delete_many({})
    
    yield db
    
    # Clean after test
    await db.users.delete_many({})
    await db.diagnoses.delete_many({})
    await db.history.delete_many({})
    await db.notifications.delete_many({})
    await db.sessions.delete_many({})
    await db.password_resets.delete_many({})
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
        "_id": ObjectId(),
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
        "_id": ObjectId(),
        "user_id": str(ObjectId()),
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
