"""
MongoDB Database Connection and Management
Using Motor (async driver) for MongoDB operations
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls):
        """Initialize database connection"""
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
            
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                serverSelectionTimeoutMS=5000
            )
            
            
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DB_NAME}")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close database connection"""
        if cls.client:
            logger.info("Closing MongoDB connection")
            cls.client.close()
            cls.client = None
            cls.db = None
    
    @classmethod
 
    async def create_indexes(cls):
        """Create necessary database indexes"""
        try:
            # User indexes
            await cls.db.users.create_index("email", unique=True, sparse=True, name="email_1")  # Match existing index
            await cls.db.users.create_index("phone", unique=True, sparse=True, name="phone_1")  # sparse - phone is optional
            
            # Diagnosis indexes
            await cls.db.diagnoses.create_index("user_id")
            await cls.db.diagnoses.create_index("created_at")
            await cls.db.diagnoses.create_index([("user_id", 1), ("created_at", -1)])
            
            # History indexes
            await cls.db.history.create_index("user_id")
            await cls.db.history.create_index("created_at")
            
            # Notification indexes
            await cls.db.notifications.create_index("user_id")
            await cls.db.notifications.create_index("is_read")
            await cls.db.notifications.create_index([("user_id", 1), ("is_read", 1)])
            
            # Knowledge base indexes
            await cls.db.knowledge_base.create_index("disease_id", unique=True)
            await cls.db.knowledge_base.create_index("name")
            
            # Session indexes (for multi-device support)
            await cls.db.sessions.create_index("user_id")
            await cls.db.sessions.create_index("token")
            await cls.db.sessions.create_index("expires_at", expireAfterSeconds=0)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            # Don't raise - indexes might already exist
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if cls.db is None:
            raise Exception("Database not initialized. Call connect_db() first.")
        return cls.db


# Dependency for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency to get database instance"""
    return Database.get_db()
