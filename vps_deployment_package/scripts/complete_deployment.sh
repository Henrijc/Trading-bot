#!/bin/bash

# AI Crypto Trading Coach - Complete VPS Deployment Script
# Run as cryptoadmin user on Ubuntu VPS (156.155.253.224)

set -e  # Exit on any error

echo "🚀 Starting AI Crypto Trading Coach deployment..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Configuration
DEPLOY_USER="cryptoadmin"
DEPLOY_DIR="/opt/crypto-coach"
REPO_URL="https://github.com/Henrijc/Trading-bot.git"
BRANCH="for-deployment"

# Check if running as correct user
if [ "$(whoami)" != "$DEPLOY_USER" ]; then
    error "This script must be run as $DEPLOY_USER user"
fi

# Check if directory exists
if [ ! -d "$DEPLOY_DIR" ]; then
    log "Creating deployment directory..."
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
fi

# Navigate to deployment directory
cd "$DEPLOY_DIR"

# Clone or update repository
if [ -d ".git" ]; then
    log "Updating existing repository..."
    git fetch --all
    git reset --hard origin/"$BRANCH"
else
    log "Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" .
fi

# Check if environment file exists
if [ ! -f ".env" ]; then
    warn "Environment file not found!"
    echo "Please copy the environment template and configure it:"
    echo "cp vps_deployment_package/.env.production.example .env"
    echo "nano .env  # Configure with your actual credentials"
    error "Environment file required for deployment"
fi

log "Environment file found ✅"

# Validate critical environment variables
log "Validating environment configuration..."
source .env 2>/dev/null || error "Failed to source .env file"

critical_vars=("MONGO_URL" "LUNO_API_KEY" "LUNO_SECRET")
missing_vars=()

for var in "${critical_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    error "Missing or unconfigured environment variables: ${missing_vars[*]}"
fi

log "Environment validation passed ✅"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    error "Docker not installed. Please install Docker first."
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose not installed. Please install Docker Compose first."
fi

log "Docker installation verified ✅"

# Stop existing containers if running
log "Stopping existing containers..."
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# Clean up old containers and images
log "Cleaning up old Docker resources..."
sudo docker system prune -f --volumes

# Ensure proper permissions
log "Setting file permissions..."
chmod 600 .env
sudo chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"

# Pull latest Docker images
log "Pulling latest Docker images..."
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml pull

# Start all services
log "Starting all services..."
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml --env-file .env up -d --remove-orphans --force-recreate

# Wait for services to initialize
log "Waiting for services to initialize..."
sleep 45

# Check service status
log "Checking service status..."
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml ps

# Test service health
log "Testing service health..."
services=("backend:8001/api/health" "frontend:3000" "freqtrade:8082")
all_healthy=true

for service in "${services[@]}"; do
    name="${service%%:*}"
    endpoint="${service##*:}"
    
    log "Testing $name service..."
    if curl -f -s "http://localhost:$endpoint" >/dev/null 2>&1; then
        log "$name service is healthy ✅"
    else
        warn "$name service may not be ready yet"
        all_healthy=false
    fi
done

# Final status
echo
if [ "$all_healthy" = true ]; then
    log "🎉 Deployment completed successfully!"
    log "All services are running and healthy"
else
    warn "Deployment completed but some services may need more time to initialize"
    log "Check logs with: sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml logs"
fi

# Display useful commands
echo
log "Useful commands:"
echo "  Status: sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml ps"
echo "  Logs:   sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml logs -f"
echo "  Stop:   sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml down"
echo "  Restart: sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml restart"

echo
log "Deployment script completed!"