"""
Database Service for MongoDB operations
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for MongoDB operations"""
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'crypto_trading')
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            # Test connection
            await self.client.admin.command('ismaster')
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            if not self.db:
                await self.connect()
            user = await self.db.users.find_one({"username": username})
            return user
        except Exception as e:
            logger.error(f"Error getting user {username}: {e}")
            return None
    
    async def create_user(self, username: str, hashed_password: str) -> bool:
        """Create a new user"""
        try:
            if not self.db:
                await self.connect()
            result = await self.db.users.insert_one({
                "username": username,
                "hashed_password": hashed_password,
                "created_at": "2024-01-01T00:00:00"
            })
            logger.info(f"User {username} created with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database client instance
_db_service = None

async def get_database_client() -> DatabaseService:
    """Get database client instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.connect()
    return _db_service