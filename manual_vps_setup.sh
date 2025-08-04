#!/bin/bash
# MANUAL VPS SETUP SCRIPT
# Run this script directly on your VPS to apply all fixes

echo "=== MANUAL CRYPTO COACH FIXES ==="
cd /opt/crypto-coach

# Create __init__.py files
echo "Creating __init__.py files..."
touch __init__.py
touch backend/__init__.py
touch backend/services/__init__.py
touch freqtrade/__init__.py
touch freqtrade/user_data/__init__.py
touch freqtrade/user_data/strategies/__init__.py

# Create emergent_mock.py
echo "Creating backend/services/emergent_mock.py..."
cat > backend/services/emergent_mock.py << 'EOF'
"""Mock implementation for emergentintegrations"""
import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class UserMessage:
    def __init__(self, content: str):
        self.content = content
        self.role = "user"

class LlmChat:
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        logger.warning(f"Using mock LlmChat for {model_name}")
    
    async def send_message(self, message: str, history: Optional[List[Any]] = None) -> str:
        return f"Mock response for '{message[:30]}...' from {self.model_name}"
EOF

# Create database_service.py
echo "Creating backend/services/database_service.py..."
cat > backend/services/database_service.py << 'EOF'
"""Database Service for MongoDB operations"""
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.environ.get('DB_NAME', 'crypto_trading')
        self.client = None
        self.db = None
        
    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(self.mongo_url)
            self.db = self.client[self.db_name]
            await self.client.admin.command('ismaster')
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        if not self.db:
            await self.connect()
        return await self.db.users.find_one({"username": username})
    
    async def create_user(self, username: str, hashed_password: str) -> bool:
        if not self.db:
            await self.connect()
        result = await self.db.users.insert_one({
            "username": username,
            "hashed_password": hashed_password,
            "created_at": "2024-01-01T00:00:00"
        })
        return True

async def get_database_client() -> DatabaseService:
    return DatabaseService()
EOF

# Update freqtrade requirements.txt
echo "Updating freqtrade/requirements.txt..."
if ! grep -q "aiohttp" freqtrade/requirements.txt; then
    echo "aiohttp>=3.8.0" >> freqtrade/requirements.txt
fi

echo "✅ All manual fixes applied!"
echo "Now run: docker compose down -v && docker compose build --no-cache && docker compose up -d"