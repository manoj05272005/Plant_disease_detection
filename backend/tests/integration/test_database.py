"""
Integration Tests for Database Operations
"""
import pytest
from datetime import datetime
from bson import ObjectId


@pytest.mark.integration
class TestDatabaseConnectivity:
    """Test database connectivity and operations"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self, test_db):
        """Test database connection is established"""
        # Perform simple operation
        result = await test_db.users.find_one({})
        
        # Should not raise error (might be None if empty)
        assert result is None or isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_insert_and_find(self, test_db):
        """Test insert and find operations"""
        doc = {
            "name": "Test",
            "value": 123,
            "created_at": datetime.utcnow()
        }
        
        result = await test_db.users.insert_one(doc)
        assert result.inserted_id is not None
        
        found = await test_db.users.find_one({"_id": result.inserted_id})
        assert found is not None
        assert found["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_update_operation(self, test_db):
        """Test update operations"""
        doc = {"name": "Original", "value": 1}
        result = await test_db.users.insert_one(doc)
        
        await test_db.users.update_one(
            {"_id": result.inserted_id},
            {"$set": {"name": "Updated"}}
        )
        
        updated = await test_db.users.find_one({"_id": result.inserted_id})
        assert updated["name"] == "Updated"
    
    @pytest.mark.asyncio
    async def test_delete_operation(self, test_db):
        """Test delete operations"""
        doc = {"name": "ToDelete"}
        result = await test_db.users.insert_one(doc)
        
        await test_db.users.delete_one({"_id": result.inserted_id})
        
        deleted = await test_db.users.find_one({"_id": result.inserted_id})
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, test_db):
        """Test bulk insert operations"""
        docs = [
            {"name": f"User{i}", "value": i}
            for i in range(5)
        ]
        
        result = await test_db.users.insert_many(docs)
        assert len(result.inserted_ids) == 5
        
        count = await test_db.users.count_documents({"name": {"$regex": "^User"}})
        assert count >= 5


@pytest.mark.integration
class TestDatabaseIndexing:
    """Test database indexing"""
    
    @pytest.mark.asyncio
    async def test_create_index(self, test_db):
        """Test index creation"""
        await test_db.users.create_index("email")
        
        indexes = await test_db.users.index_information()
        assert any("email" in str(idx) for idx in indexes.values())
    
    @pytest.mark.asyncio
    async def test_query_with_index(self, test_db):
        """Test query using indexed field"""
        await test_db.users.create_index("email")
        
        await test_db.users.insert_one({
            "email": "indexed@test.com",
            "name": "Test User"
        })
        
        result = await test_db.users.find_one({"email": "indexed@test.com"})
        assert result is not None
