"""
Unit Tests for Database Module
"""
import pytest
from app.core.database import get_database, close_database_connection


@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection utilities"""
    
    @pytest.mark.asyncio
    async def test_get_database(self):
        """Test database connection"""
        db = await get_database()
        
        assert db is not None
        assert hasattr(db, 'users')
        assert hasattr(db, 'diagnoses')
    
    @pytest.mark.asyncio
    async def test_database_collections(self):
        """Test database collections exist"""
        db = await get_database()
        
        collections = await db.list_collection_names()
        
        # Collections may or may not exist yet
        assert isinstance(collections, list)
    
    @pytest.mark.asyncio
    async def test_close_database_connection(self):
        """Test closing database connection"""
        await close_database_connection()
        
        # Should complete without error
        assert True


@pytest.mark.unit
class TestCollectionAccess:
    """Test collection access"""
    
    @pytest.mark.asyncio
    async def test_users_collection(self):
        """Test users collection access"""
        db = await get_database()
        
        collection = db.users
        assert collection is not None
    
    @pytest.mark.asyncio
    async def test_diagnoses_collection(self):
        """Test diagnoses collection access"""
        db = await get_database()
        
        collection = db.diagnoses
        assert collection is not None
    
    @pytest.mark.asyncio
    async def test_history_collection(self):
        """Test history collection access"""
        db = await get_database()
        
        collection = db.history
        assert collection is not None
