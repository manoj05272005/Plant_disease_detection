"""
Integration Tests for Notifications API
"""
import pytest
from datetime import datetime


@pytest.mark.integration
class TestNotificationEndpoints:
    """Test notification API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_user_notifications(self, authenticated_client, test_db):
        """Test get user notifications"""
        client, user_id = authenticated_client
        
        # Insert notifications
        for i in range(3):
            await test_db.notifications.insert_one({
                "user_id": user_id,
                "title": f"Notification {i}",
                "message": "Test message",
                "type": "info",
                "read": False,
                "created_at": datetime.utcnow()
            })
        
        response = await client.get("/api/v1/notifications")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, authenticated_client, test_db):
        """Test mark notification as read"""
        client, user_id = authenticated_client
        
        result = await test_db.notifications.insert_one({
            "user_id": user_id,
            "title": "Test",
            "message": "Test",
            "type": "info",
            "read": False,
            "created_at": datetime.utcnow()
        })
        notification_id = str(result.inserted_id)
        
        response = await client.put(f"/api/v1/notifications/{notification_id}/read")
        
        assert response.status_code == 200
        
        # Verify marked as read
        notif = await test_db.notifications.find_one({"_id": result.inserted_id})
        assert notif["read"] is True
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, authenticated_client, test_db):
        """Test mark all notifications as read"""
        client, user_id = authenticated_client
        
        # Insert unread notifications
        for i in range(3):
            await test_db.notifications.insert_one({
                "user_id": user_id,
                "title": f"Notif {i}",
                "message": "Test",
                "read": False,
                "created_at": datetime.utcnow()
            })
        
        response = await client.put("/api/v1/notifications/mark-all-read")
        
        assert response.status_code == 200
        
        # Verify all marked as read
        unread_count = await test_db.notifications.count_documents({
            "user_id": user_id,
            "read": False
        })
        assert unread_count == 0
    
    @pytest.mark.asyncio
    async def test_delete_notification(self, authenticated_client, test_db):
        """Test delete notification"""
        client, user_id = authenticated_client
        
        result = await test_db.notifications.insert_one({
            "user_id": user_id,
            "title": "Test",
            "message": "Test",
            "created_at": datetime.utcnow()
        })
        notification_id = str(result.inserted_id)
        
        response = await client.delete(f"/api/v1/notifications/{notification_id}")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_unread_count(self, authenticated_client, test_db):
        """Test get unread notification count"""
        client, user_id = authenticated_client
        
        # Insert unread notifications
        for i in range(5):
            await test_db.notifications.insert_one({
                "user_id": user_id,
                "title": f"Notif {i}",
                "message": "Test",
                "read": False,
                "created_at": datetime.utcnow()
            })
        
        response = await client.get("/api/v1/notifications/unread-count")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] >= 5
