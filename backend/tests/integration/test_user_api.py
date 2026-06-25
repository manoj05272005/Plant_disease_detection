"""
Integration Tests for User API
"""
import pytest
from datetime import datetime


@pytest.mark.integration
class TestUserProfile:
    """Test user profile endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client, test_db):
        """Test get current user profile"""
        client, user_id = authenticated_client
        
        response = await client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_update_profile(self, authenticated_client, test_db):
        """Test update user profile"""
        client, user_id = authenticated_client
        
        update_data = {
            "name": "Updated Name",
            "phone": "9876543210",
            "location": "New Delhi"
        }
        
        response = await client.put("/api/v1/users/me", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "9876543210"
    
    @pytest.mark.asyncio
    async def test_change_language_preference(self, authenticated_client, test_db):
        """Test change language preference"""
        client, user_id = authenticated_client
        
        response = await client.put("/api/v1/users/me", json={
            "preferred_language": "hi"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_language"] == "hi"
    
    @pytest.mark.asyncio
    async def test_delete_account(self, authenticated_client, test_db):
        """Test delete user account"""
        client, user_id = authenticated_client
        
        response = await client.delete("/api/v1/users/me")
        
        assert response.status_code == 200


@pytest.mark.integration
class TestUserStatistics:
    """Test user statistics endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_user_stats(self, authenticated_client, test_db):
        """Test get user statistics"""
        client, user_id = authenticated_client
        
        # Insert some diagnoses
        for i in range(5):
            await test_db.diagnoses.insert_one({
                "user_id": user_id,
                "crop_type": "tomato",
                "disease_name": "Early Blight",
                "confidence": 0.9,
                "created_at": datetime.utcnow()
            })
        
        response = await client.get("/api/v1/users/me/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_diagnoses" in data
        assert data["total_diagnoses"] >= 5
