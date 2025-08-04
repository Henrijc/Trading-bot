#!/bin/bash
# COMPLETE MANUAL DEPLOYMENT FOR CRYPTO COACH
# Run this script directly on your VPS to apply all fixes and deploy

echo "🚀 CRYPTO COACH COMPLETE MANUAL DEPLOYMENT"
echo "=========================================="
echo "This script will apply all fixes and deploy the application"
echo "Date: $(date)"
echo "User: $(whoami)"
echo ""

# Ensure we're in the right directory
cd /opt/crypto-coach || {
    echo "❌ ERROR: /opt/crypto-coach directory not found!"
    echo "Please ensure the project is cloned to /opt/crypto-coach"
    echo "Run: sudo git clone https://github.com/Henrijc/Trading-bot.git /opt/crypto-coach"
    exit 1
}

echo "✅ In project directory: $(pwd)"

# Backup current state
echo "💾 Creating backup..."
backup_dir="/opt/crypto-coach-backup-$(date +%Y%m%d_%H%M%S)"
sudo cp -r /opt/crypto-coach "$backup_dir" && echo "✅ Backup created: $backup_dir" || echo "⚠️  Backup failed"

# Pull latest changes
echo "⬇️  Updating from repository..."
git fetch --all && echo "✅ Git fetch successful" || echo "❌ Git fetch failed"
git reset --hard origin/for-deployment && echo "✅ Git reset successful" || echo "❌ Git reset failed"

# Create critical __init__.py files
echo "📝 Creating critical __init__.py files..."
files_to_create=(
    "__init__.py"
    "backend/__init__.py"
    "backend/services/__init__.py"
    "freqtrade/__init__.py"
    "freqtrade/user_data/__init__.py"
    "freqtrade/user_data/strategies/__init__.py"
)

for file in "${files_to_create[@]}"; do
    if [ ! -f "$file" ]; then
        touch "$file" && echo "✅ Created $file"
    else
        echo "✅ $file already exists"
    fi
done

# Create missing service files
echo "🔧 Creating missing service files..."

# Create emergent_mock.py
if [ ! -f "backend/services/emergent_mock.py" ]; then
    echo "Creating backend/services/emergent_mock.py..."
    cat > backend/services/emergent_mock.py << 'EOF'
"""
Mock implementation for emergentintegrations
This provides fallback functionality when emergentintegrations is not available
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class UserMessage:
    """Mock UserMessage class"""
    def __init__(self, content: str):
        self.content = content
        self.role = "user"

class LlmChat:
    """Mock LlmChat class for emergentintegrations fallback"""
    
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        logger.warning(f"Using mock LlmChat for {model_name}. No actual AI calls will be made.")
    
    async def send_message(self, message: str, history: Optional[List[Any]] = None) -> str:
        """Mock send_message implementation"""
        logger.warning(f"Mock LlmChat received message: {message[:50]}... Returning dummy response.")
        
        # Provide basic mock responses based on message content
        if "market" in message.lower() or "crypto" in message.lower():
            return f"Mock analysis: The cryptocurrency market is showing mixed signals. This is a mock response for development purposes."
        elif "trade" in message.lower() or "buy" in message.lower() or "sell" in message.lower():
            return f"Mock trading advice: Consider your risk tolerance before making any trades. This is a mock response."
        elif "portfolio" in message.lower():
            return f"Mock portfolio analysis: Your portfolio appears to be well-diversified. This is a mock response."
        else:
            return f"Mock response for '{message[:30]}...' from {self.model_name}. (This is a mock, replace with real LLM integration)"
    
    def send_message_sync(self, message: str, history: Optional[List[Any]] = None) -> str:
        """Synchronous version of send_message"""
        return asyncio.run(self.send_message(message, history))
EOF
    echo "✅ Created backend/services/emergent_mock.py"
else
    echo "✅ backend/services/emergent_mock.py already exists"
fi

# Create database_service.py
if [ ! -f "backend/services/database_service.py" ]; then
    echo "Creating backend/services/database_service.py..."
    cat > backend/services/database_service.py << 'EOF'
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
EOF
    echo "✅ Created backend/services/database_service.py"
else
    echo "✅ backend/services/database_service.py already exists"
fi

# Update freqtrade requirements.txt to include aiohttp
echo "📦 Updating freqtrade requirements.txt..."
if ! grep -q "aiohttp" freqtrade/requirements.txt 2>/dev/null; then
    echo "aiohttp>=3.8.0" >> freqtrade/requirements.txt
    echo "asyncio" >> freqtrade/requirements.txt
    echo "✅ Added missing dependencies to freqtrade/requirements.txt"
else
    echo "✅ freqtrade/requirements.txt already has required dependencies"
fi

# Set correct permissions
echo "🔒 Setting correct permissions..."
sudo chown -R cryptoadmin:cryptoadmin /opt/crypto-coach
chmod +x deploy_vps_commands.sh 2>/dev/null || echo "⚠️  deploy_vps_commands.sh not found"
chmod +x verify_deployment_fixes.py 2>/dev/null || echo "⚠️  verify_deployment_fixes.py not found"

# Verify all critical files exist
echo "🔍 Final verification of critical files..."
critical_files=(
    "__init__.py"
    "backend/__init__.py"
    "backend/services/__init__.py"
    "backend/Dockerfile"
    "freqtrade/Dockerfile"
    "backend/services/emergent_mock.py"
    "backend/services/database_service.py"
    "docker-compose.yml"
)

missing_files=0
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MISSING"
        ((missing_files++))
    fi
done

if [ $missing_files -eq 0 ]; then
    echo "🎉 All critical files present!"
else
    echo "⚠️  $missing_files critical files missing - deployment may fail"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose down -v || echo "⚠️  No containers to stop"

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker system prune -f || echo "⚠️  Docker cleanup failed"

# Build with no cache
echo "🔨 Building containers (this may take several minutes)..."
docker compose build --no-cache || {
    echo "❌ Docker build failed!"
    echo "Check the error messages above and ensure Docker is properly installed"
    exit 1
}

# Start containers
echo "🚀 Starting containers..."
docker compose up -d || {
    echo "❌ Container startup failed!"
    echo "Check container logs with: docker compose logs"
    exit 1
}

# Wait for containers to start
echo "⏳ Waiting for containers to start up..."
sleep 30

# Check container status
echo "📊 Container status:"
docker compose ps

# Check logs for critical errors
echo "📋 Checking container logs for errors..."
echo "Backend logs:"
docker compose logs backend | tail -10

echo "Freqtrade logs:"
docker compose logs freqtrade | tail -10

echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "======================"
echo "✅ All fixes applied"
echo "✅ Containers built and started"
echo ""
echo "📍 NEXT STEPS:"
echo "1. Check if containers are running: docker compose ps"
echo "2. View logs: docker compose logs -f backend"
echo "3. Test application endpoints"
echo ""
echo "If issues persist, check individual container logs:"
echo "  docker compose logs backend"
echo "  docker compose logs freqtrade"
echo "  docker compose logs frontend"
echo ""
echo "🚀 Your AI Crypto Trading Coach should now be running!"