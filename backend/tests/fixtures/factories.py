"""
Test Data Fixtures and Factories
"""
import pytest
from faker import Faker
from datetime import datetime, timedelta
from bson import ObjectId

fake = Faker()


class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create(**kwargs):
        """Create a test user with optional overrides"""
        default_data = {
            "_id": ObjectId(),
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "preferred_language": "en",
            "location": fake.city(),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data


class DiagnosisFactory:
    """Factory for creating test diagnoses"""
    
    @staticmethod
    def create(**kwargs):
        """Create a test diagnosis with optional overrides"""
        default_data = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "crop_type": fake.random_element(["tomato", "potato", "wheat", "rice"]),
            "disease_id": "tomato_early_blight",
            "disease_name": "Early Blight",
            "confidence": fake.random.uniform(0.7, 0.99),
            "severity": fake.random_element(["low", "medium", "high"]),
            "is_healthy": False,
            "image_url": f"/uploads/images/{fake.uuid4()}.jpg",
            "heatmap_url": f"/uploads/heatmaps/{fake.uuid4()}.jpg",
            "bounding_boxes": [],
            "created_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data


class NotificationFactory:
    """Factory for creating test notifications"""
    
    @staticmethod
    def create(**kwargs):
        """Create a test notification with optional overrides"""
        default_data = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "title": fake.sentence(nb_words=5),
            "message": fake.text(max_nb_chars=200),
            "type": fake.random_element(["info", "alert", "diagnosis", "system"]),
            "read": False,
            "created_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data


class HistoryFactory:
    """Factory for creating test history records"""
    
    @staticmethod
    def create(**kwargs):
        """Create a test history record with optional overrides"""
        default_data = {
            "_id": ObjectId(),
            "user_id": str(ObjectId()),
            "diagnosis_id": str(ObjectId()),
            "action": fake.random_element(["view", "download", "share", "delete"]),
            "created_at": datetime.utcnow()
        }
        default_data.update(kwargs)
        return default_data


# Pytest fixtures using factories
@pytest.fixture
def user_factory():
    """Provide user factory"""
    return UserFactory


@pytest.fixture
def diagnosis_factory():
    """Provide diagnosis factory"""
    return DiagnosisFactory


@pytest.fixture
def notification_factory():
    """Provide notification factory"""
    return NotificationFactory


@pytest.fixture
def history_factory():
    """Provide history factory"""
    return HistoryFactory
