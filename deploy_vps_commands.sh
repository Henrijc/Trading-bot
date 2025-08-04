#!/bin/bash
# CRITICAL VPS DEPLOYMENT COMMANDS
# Execute these commands on your VPS at 156.155.253.224

echo "=== CRYPTO COACH VPS DEPLOYMENT - CONSOLIDATED FIXES ==="
echo "These commands will apply all fixes to resolve ModuleNotFoundErrors"
echo

# Navigate to project directory
echo "1. Navigating to project directory..."
cd /opt/crypto-coach || { echo "ERROR: /opt/crypto-coach not found"; exit 1; }

echo "2. Creating critical __init__.py files..."
# Create all required __init__.py files
touch __init__.py
touch backend/__init__.py
touch backend/services/__init__.py
touch freqtrade/__init__.py
touch freqtrade/user_data/__init__.py
touch freqtrade/user_data/strategies/__init__.py

echo "3. Stopping all containers and cleaning up..."
# Stop containers and clean up
docker compose down -v
docker system prune -af --volumes

echo "4. Rebuilding with no cache..."
# Force rebuild from scratch
docker compose build --no-cache

echo "5. Starting services..."
# Start services
docker compose up -d

echo "6. Waiting for services to start..."
sleep 30

echo "7. Checking container status..."
docker compose ps

echo "8. Testing backend container imports..."
docker compose exec backend python -c "
import sys
sys.path.insert(0, '/app')
try:
    from backend.services.ai_service import AICoachService
    from backend.services.luno_service import LunoService
    print('✅ Backend imports working')
except Exception as e:
    print(f'❌ Backend imports failing: {e}')
"

echo "9. Testing freqtrade container imports..."
docker compose exec freqtrade python -c "
import sys
sys.path.insert(0, '/app')
try:
    import aiohttp
    from backend.services.luno_service import LunoService
    print('✅ Freqtrade imports working')
except Exception as e:
    print(f'❌ Freqtrade imports failing: {e}')
"

echo "10. Final container status..."
docker compose ps

echo
echo "=== DEPLOYMENT COMPLETE ==="
echo "If all tests passed, your application should now be running successfully!"
echo "Check the logs with: docker compose logs -f backend"
echo "Check the logs with: docker compose logs -f freqtrade"