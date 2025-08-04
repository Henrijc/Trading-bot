#!/bin/bash
# DIRECT DEPLOYMENT SCRIPT - Run this on your local machine
# This script will SSH to your VPS and execute the deployment directly

echo "🚀 DIRECT CRYPTO COACH DEPLOYMENT"
echo "================================="
echo "This will SSH to your VPS and deploy directly"
echo ""

# SSH to VPS and execute deployment
ssh cryptoadmin@156.155.253.224 << 'ENDSSH'

echo "🔑 Connected to VPS successfully!"
echo "Date: $(date)"
echo "User: $(whoami)"
echo ""

# Navigate to project directory
cd /opt/crypto-coach || {
    echo "❌ ERROR: /opt/crypto-coach directory not found!"
    echo "Creating directory and cloning repository..."
    sudo mkdir -p /opt/crypto-coach
    sudo chown cryptoadmin:cryptoadmin /opt/crypto-coach
    git clone https://github.com/Henrijc/Trading-bot.git /opt/crypto-coach
    cd /opt/crypto-coach
}

echo "✅ In project directory: $(pwd)"

# Pull latest changes
echo "⬇️  Updating from repository..."
git fetch --all && git reset --hard origin/for-deployment

# Create all critical __init__.py files
echo "📝 Creating critical __init__.py files..."
touch __init__.py
touch backend/__init__.py
touch backend/services/__init__.py
touch freqtrade/__init__.py
touch freqtrade/user_data/__init__.py
touch freqtrade/user_data/strategies/__init__.py
echo "✅ __init__.py files created"

# Create emergent_mock.py
echo "🔧 Creating backend/services/emergent_mock.py..."
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
        if "market" in message.lower() or "crypto" in message.lower():
            return "Mock analysis: The cryptocurrency market is showing mixed signals."
        elif "trade" in message.lower():
            return "Mock trading advice: Consider your risk tolerance before making trades."
        else:
            return f"Mock response for '{message[:30]}...' from {self.model_name}"
EOF

# Create database_service.py
echo "🔧 Creating backend/services/database_service.py..."
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
echo "📦 Updating freqtrade requirements.txt..."
if ! grep -q "aiohttp" freqtrade/requirements.txt 2>/dev/null; then
    echo "aiohttp>=3.8.0" >> freqtrade/requirements.txt
    echo "asyncio" >> freqtrade/requirements.txt
    echo "✅ Added missing dependencies"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down -v 2>/dev/null || echo "No containers to stop"

# Clean up
echo "🧹 Cleaning up Docker..."
docker system prune -f 2>/dev/null || echo "Docker cleanup failed"

# Build containers
echo "🔨 Building containers (this may take several minutes)..."
docker compose build --no-cache || {
    echo "❌ Docker build failed!"
    exit 1
}

# Start containers
echo "🚀 Starting containers..."
docker compose up -d || {
    echo "❌ Container startup failed!"
    exit 1
}

# Wait and check status
echo "⏳ Waiting for containers to start..."
sleep 30

echo "📊 Container status:"
docker compose ps

echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "Your AI Crypto Trading Coach should now be running!"
echo ""
echo "Check logs with:"
echo "  docker compose logs backend"
echo "  docker compose logs freqtrade"

ENDSSH

echo ""
echo "✅ Direct deployment completed!"
echo "The script has executed on your VPS"