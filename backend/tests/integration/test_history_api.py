"""
Integration Tests for History API
"""
import pytest
from datetime import datetime, timedelta


@pytest.mark.integration
class TestHistoryEndpoints:
    """Test history API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_diagnosis_history(self, authenticated_client, test_db):
        """Test get diagnosis history"""
        client, user_id = authenticated_client
        
        # Insert history records
        for i in range(3):
            await test_db.history.insert_one({
                "user_id": user_id,
                "diagnosis_id": f"diag_{i}",
                "action": "view",
                "created_at": datetime.utcnow()
            })
        
        response = await client.get("/api/v1/history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    @pytest.mark.asyncio
    async def test_filter_history_by_date(self, authenticated_client, test_db):
        """Test filter history by date range"""
        client, user_id = authenticated_client
        
        # Insert old and new records
        await test_db.history.insert_one({
            "user_id": user_id,
            "action": "view",
            "created_at": datetime.utcnow() - timedelta(days=10)
        })
        await test_db.history.insert_one({
            "user_id": user_id,
            "action": "view",
            "created_at": datetime.utcnow()
        })
        
        start_date = (datetime.utcnow() - timedelta(days=2)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        response = await client.get(f"/api/v1/history?start_date={start_date}&end_date={end_date}")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_delete_history(self, authenticated_client, test_db):
        """Test delete history record"""
        client, user_id = authenticated_client
        
        result = await test_db.history.insert_one({
            "user_id": user_id,
            "action": "view",
            "created_at": datetime.utcnow()
        })
        history_id = str(result.inserted_id)
        
        response = await client.delete(f"/api/v1/history/{history_id}")
        
        assert response.status_code == 200
