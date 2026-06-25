"""
Unit Tests for Notification Service
"""
import pytest
from datetime import datetime
from app.services.notification_service import NotificationService
from bson import ObjectId


@pytest.mark.unit
class TestNotificationService:
    """Test notification service"""
    
    @pytest.mark.asyncio
    async def test_create_notification(self, test_db):
        """Test create notification"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        notification = await service.create_notification(
            user_id=user_id,
            title="Test Notification",
            message="This is a test",
            notification_type="info"
        )
        
        assert notification is not None
        assert notification["title"] == "Test Notification"
        assert notification["user_id"] == user_id
        assert notification["read"] is False
    
    @pytest.mark.asyncio
    async def test_get_user_notifications(self, test_db):
        """Test get user notifications"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        # Create notifications
        await service.create_notification(user_id, "Title 1", "Message 1")
        await service.create_notification(user_id, "Title 2", "Message 2")
        
        notifications = await service.get_user_notifications(user_id)
        
        assert len(notifications) >= 2
    
    @pytest.mark.asyncio
    async def test_mark_as_read(self, test_db):
        """Test mark notification as read"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        notification = await service.create_notification(
            user_id, "Test", "Test message"
        )
        notification_id = str(notification["_id"])
        
        await service.mark_as_read(notification_id, user_id)
        
        # Verify marked as read
        updated = await test_db.notifications.find_one({"_id": notification["_id"]})
        assert updated["read"] is True
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, test_db):
        """Test mark all notifications as read"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        # Create multiple notifications
        await service.create_notification(user_id, "Title 1", "Message 1")
        await service.create_notification(user_id, "Title 2", "Message 2")
        
        await service.mark_all_as_read(user_id)
        
        # Verify all marked as read
        unread = await test_db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })
        assert unread == 0
    
    @pytest.mark.asyncio
    async def test_delete_notification(self, test_db):
        """Test delete notification"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        notification = await service.create_notification(
            user_id, "Test", "Test message"
        )
        notification_id = str(notification["_id"])
        
        await service.delete_notification(notification_id, user_id)
        
        # Verify deleted
        deleted = await test_db.notifications.find_one({"_id": notification["_id"]})
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, test_db):
        """Test get unread notification count"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        # Create notifications
        await service.create_notification(user_id, "Title 1", "Message 1")
        await service.create_notification(user_id, "Title 2", "Message 2")
        
        count = await service.get_unread_count(user_id)
        
        assert count >= 2


@pytest.mark.unit
class TestNotificationTypes:
    """Test different notification types"""
    
    @pytest.mark.asyncio
    async def test_diagnosis_notification(self, test_db):
        """Test diagnosis completion notification"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        notification = await service.create_notification(
            user_id=user_id,
            title="Diagnosis Complete",
            message="Your diagnosis is ready",
            notification_type="diagnosis"
        )
        
        assert notification["type"] == "diagnosis"
    
    @pytest.mark.asyncio
    async def test_alert_notification(self, test_db):
        """Test alert notification"""
        service = NotificationService(test_db)
        user_id = str(ObjectId())
        
        notification = await service.create_notification(
            user_id=user_id,
            title="Disease Alert",
            message="New disease detected in your area",
            notification_type="alert"
        )
        
        assert notification["type"] == "alert"
