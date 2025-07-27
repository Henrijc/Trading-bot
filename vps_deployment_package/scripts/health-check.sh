#!/bin/bash
set -e

echo "🔍 Health Check - AI Crypto Trading Coach"
echo "========================================"

DOMAIN="crypto-coach.zikhethele.properties"
FAILED_CHECKS=0

# Function to check HTTP endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$url" 2>/dev/null); then
        if [ "$response" -eq "$expected_status" ]; then
            echo "✅ OK (HTTP $response)"
        else
            echo "❌ FAILED (HTTP $response, expected $expected_status)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        echo "❌ FAILED (Connection error)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Function to check Docker container
check_container() {
    local name=$1
    local container_name=$2
    
    echo -n "Checking $name container... "
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        echo "✅ OK (Running)"
    else
        echo "❌ FAILED (Not running or unhealthy)"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Check external endpoints
echo "🌐 External Endpoint Checks:"
check_endpoint "Frontend" "https://$DOMAIN/"
check_endpoint "Backend API" "https://$DOMAIN/api/"
check_endpoint "Backend Health" "https://$DOMAIN/api/"

echo ""

# Check Docker containers
echo "🐳 Container Health Checks:"
check_container "Frontend" "crypto-coach-frontend-prod"
check_container "Backend" "crypto-coach-backend-prod"
check_container "Database" "crypto-coach-mongo-prod"
check_container "Freqtrade" "crypto-coach-freqtrade-prod"

echo ""

# Check Docker container health status
echo "🏥 Container Health Status:"
for container in crypto-coach-frontend-prod crypto-coach-backend-prod crypto-coach-mongo-prod crypto-coach-freqtrade-prod; do
    echo -n "Health status for $container... "
    if docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null | grep -q "healthy"; then
        echo "✅ HEALTHY"
    else
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")
        echo "❌ $health_status"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
done

echo ""

# Check disk space
echo "💾 System Resource Checks:"
echo -n "Disk space check... "
disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 90 ]; then
    echo "✅ OK (${disk_usage}% used)"
else
    echo "⚠️ WARNING (${disk_usage}% used - getting full!)"
fi

# Check memory usage
echo -n "Memory usage check... "
memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
echo "📊 INFO (${memory_usage}% used)"

# Check Docker system resources
echo -n "Docker system check... "
if docker system df >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""

# Summary
echo "📊 Health Check Summary:"
echo "========================"
if [ $FAILED_CHECKS -eq 0 ]; then
    echo "🎉 All checks passed! System is healthy."
    echo "🌐 Application URL: https://$DOMAIN"
    exit 0
else
    echo "❌ $FAILED_CHECKS checks failed!"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "- Check container logs: docker-compose -f docker/docker-compose.prod.yml logs"
    echo "- Restart services: ./scripts/deploy.sh"
    echo "- Check system resources: df -h && free -h"
    exit 1
fi