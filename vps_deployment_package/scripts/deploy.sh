#!/bin/bash
set -e

echo "🚀 Starting deployment process..."

# Set environment variables
export GITHUB_REPOSITORY="yourusername/ai-crypto-trading-coach-vps"

# Load environment variables
if [ -f .env ]; then
    echo "📋 Loading environment variables..."
    source .env
else
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Backup current deployment (optional)
BACKUP_DIR="/opt/crypto-coach-backups/$(date +%Y%m%d_%H%M%S)"
echo "💾 Creating backup at $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
docker-compose -f docker/docker-compose.prod.yml logs --no-color > "$BACKUP_DIR/logs.txt" 2>/dev/null || true

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose -f docker/docker-compose.prod.yml pull

# Stop existing containers gracefully
echo "⏹️ Stopping existing containers..."
docker-compose -f docker/docker-compose.prod.yml down --timeout 30

# Prune old images to save space
echo "🧹 Cleaning up old images..."
docker image prune -f

# Start new containers
echo "🚀 Starting new containers..."
docker-compose -f docker/docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 45

# Verify all containers are running
echo "🔍 Checking container status..."
if ! docker-compose -f docker/docker-compose.prod.yml ps | grep -q "Up"; then
    echo "❌ Some containers failed to start!"
    docker-compose -f docker/docker-compose.prod.yml logs
    exit 1
fi

echo "✅ Deployment completed successfully!"
echo "🌐 Application should be available at: https://crypto-coach.zikhethele.properties"