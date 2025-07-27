# 🚀 AI Crypto Trading Coach - VPS CI/CD Deployment Guide

**Domain**: zikhethele.properties
**Private URL**: https://crypto-coach.zikhethele.properties (restricted access)
**Deployment Type**: Standalone VPS with CI/CD Pipeline

---

## 📋 Prerequisites

### 1. VPS Server Requirements
- **OS**: Ubuntu 20.04+ LTS
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 50GB+ SSD
- **CPU**: 2+ cores
- **Network**: Public IP address

### 2. Required Accounts
- **GitHub Account** (for CI/CD)
- **Domain Access** (zikhethele.properties DNS management)
- **VPS Provider Access** (root/sudo access)

### 3. Required Software on VPS
- Docker & Docker Compose
- Nginx (reverse proxy)
- Certbot (SSL certificates)
- Git

---

## 🏗️ Step 1: VPS Server Initial Setup

### Connect to Your VPS
```bash
ssh root@YOUR_VPS_IP_ADDRESS
```

### Update System
```bash
apt update && apt upgrade -y
```

### Install Required Software
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Nginx
apt install nginx -y
systemctl enable nginx

# Install Certbot for SSL
apt install certbot python3-certbot-nginx -y

# Install Git
apt install git -y

# Install Node.js (for build processes)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
```

### Create Application Directory
```bash
mkdir -p /opt/crypto-coach
cd /opt/crypto-coach

# Create application user
useradd -r -s /bin/false crypto-coach
usermod -aG docker crypto-coach
chown -R crypto-coach:crypto-coach /opt/crypto-coach
```

---

## 🌐 Step 2: Domain Configuration

### Add DNS Record
Add the following DNS record to your zikhethele.properties domain:

**DNS Record:**
```
Type: A
Name: crypto-coach
Value: YOUR_VPS_IP_ADDRESS
TTL: 300
```

**Result**: `crypto-coach.zikhethele.properties` → Your VPS IP

### Verify DNS Resolution
```bash
nslookup crypto-coach.zikhethele.properties
```

---

## 🔐 Step 3: SSL Certificate & Nginx Configuration

### Create Nginx Configuration
```bash
cat > /etc/nginx/sites-available/crypto-coach << 'EOF'
server {
    listen 80;
    server_name crypto-coach.zikhethele.properties;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name crypto-coach.zikhethele.properties;
    
    # SSL Configuration (will be added by certbot)
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # IP Restriction - PRIVATE ACCESS ONLY
    # Add your IP addresses here
    allow YOUR_HOME_IP_ADDRESS;
    allow YOUR_OFFICE_IP_ADDRESS;
    deny all;
    
    # Frontend (React App)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

### Enable Site
```bash
ln -s /etc/nginx/sites-available/crypto-coach /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Get SSL Certificate
```bash
certbot --nginx -d crypto-coach.zikhethele.properties
```

---

## 🔑 Step 4: GitHub Repository Setup

### Create Repository Structure
Create a new **private** GitHub repository named `ai-crypto-trading-coach-vps`

### Repository Structure:
```
ai-crypto-trading-coach-vps/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── app/
│   ├── backend/
│   ├── frontend/
│   └── freqtrade/
├── docker/
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.backend.prod
│   ├── Dockerfile.frontend.prod
│   └── Dockerfile.freqtrade.prod
├── scripts/
│   ├── deploy.sh
│   └── health-check.sh
├── .env.example
└── README.md
```

---

## 🤖 Step 5: GitHub Actions CI/CD Pipeline

### Create `.github/workflows/deploy.yml`
```yaml
name: CI/CD Pipeline - AI Crypto Trading Coach

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ai-crypto-trading-coach

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: app/frontend/package-lock.json
    
    - name: Install Frontend Dependencies
      run: |
        cd app/frontend
        npm ci
    
    - name: Run Frontend Tests
      run: |
        cd app/frontend
        npm test -- --coverage --watchAll=false
    
    - name: Frontend Build Test
      run: |
        cd app/frontend
        npm run build
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Backend Dependencies
      run: |
        cd app/backend
        pip install -r requirements.txt
    
    - name: Run Backend Tests
      run: |
        cd app/backend
        python -m pytest tests/ -v

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Login to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and Push Docker Images
      run: |
        # Build Backend
        docker build -f docker/Dockerfile.backend.prod -t ${{ env.REGISTRY }}/${{ github.repository }}/backend:latest app/backend
        docker push ${{ env.REGISTRY }}/${{ github.repository }}/backend:latest
        
        # Build Frontend
        docker build -f docker/Dockerfile.frontend.prod -t ${{ env.REGISTRY }}/${{ github.repository }}/frontend:latest app/frontend
        docker push ${{ env.REGISTRY }}/${{ github.repository }}/frontend:latest
        
        # Build Freqtrade
        docker build -f docker/Dockerfile.freqtrade.prod -t ${{ env.REGISTRY }}/${{ github.repository }}/freqtrade:latest app/freqtrade
        docker push ${{ env.REGISTRY }}/${{ github.repository }}/freqtrade:latest
    
    - name: Deploy to VPS
      uses: appleboy/ssh-action@v0.1.7
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /opt/crypto-coach
          
          # Pull latest code
          git pull origin main
          
          # Login to registry
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          
          # Pull latest images
          docker-compose -f docker/docker-compose.prod.yml pull
          
          # Stop existing containers
          docker-compose -f docker/docker-compose.prod.yml down
          
          # Start new containers
          docker-compose -f docker/docker-compose.prod.yml up -d
          
          # Health check
          sleep 30
          ./scripts/health-check.sh
          
          # Cleanup old images
          docker image prune -f
```

---

## 🐳 Step 6: Production Docker Configuration

### Create `docker/docker-compose.prod.yml`
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: crypto-coach-mongo-prod
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGO_DB_NAME}
    volumes:
      - mongodb_data:/data/db
      - mongodb_logs:/var/log/mongodb
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:27017:27017"

  backend:
    image: ghcr.io/yourusername/ai-crypto-trading-coach/backend:latest
    container_name: crypto-coach-backend-prod
    restart: unless-stopped
    environment:
      - MONGO_URL=mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@mongodb:27017/${MONGO_DB_NAME}?authSource=admin
      - LUNO_API_KEY=${LUNO_API_KEY}
      - LUNO_SECRET=${LUNO_SECRET}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - mongodb
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:8001:8001"
    volumes:
      - backend_logs:/app/logs

  frontend:
    image: ghcr.io/yourusername/ai-crypto-trading-coach/frontend:latest
    container_name: crypto-coach-frontend-prod
    restart: unless-stopped
    environment:
      - REACT_APP_BACKEND_URL=https://crypto-coach.zikhethele.properties/api
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:3000:3000"

  freqtrade:
    image: ghcr.io/yourusername/ai-crypto-trading-coach/freqtrade:latest
    container_name: crypto-coach-freqtrade-prod
    restart: unless-stopped
    environment:
      - LUNO_API_KEY=${LUNO_API_KEY}
      - LUNO_SECRET=${LUNO_SECRET}
    depends_on:
      - backend
    networks:
      - crypto-coach-network
    ports:
      - "127.0.0.1:8082:8082"
    volumes:
      - freqtrade_data:/freqtrade/user_data
      - freqtrade_logs:/freqtrade/logs

networks:
  crypto-coach-network:
    driver: bridge

volumes:
  mongodb_data:
    driver: local
  mongodb_logs:
    driver: local
  backend_logs:
    driver: local
  freqtrade_data:
    driver: local
  freqtrade_logs:
    driver: local
```

### Create Production Dockerfiles

**`docker/Dockerfile.backend.prod`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/ || exit 1

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

**`docker/Dockerfile.frontend.prod`**
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

---

## ⚙️ Step 7: VPS Deployment Setup

### Clone Repository on VPS
```bash
cd /opt/crypto-coach
git clone https://github.com/YOURUSERNAME/ai-crypto-trading-coach-vps.git .
chown -R crypto-coach:crypto-coach /opt/crypto-coach
```

### Create Environment File
```bash
cat > /opt/crypto-coach/.env << 'EOF'
# Database Configuration
MONGO_ROOT_USER=cryptoadmin
MONGO_ROOT_PASSWORD=YOUR_SECURE_MONGO_PASSWORD
MONGO_DB_NAME=crypto_trader_coach

# API Keys
LUNO_API_KEY=your_luno_api_key
LUNO_SECRET=your_luno_secret_key
GEMINI_API_KEY=your_gemini_api_key

# Security
JWT_SECRET_KEY=your_64_character_jwt_secret_key

# Admin Credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_admin_password
EOF

chmod 600 /opt/crypto-coach/.env
chown crypto-coach:crypto-coach /opt/crypto-coach/.env
```

### Create Deployment Script
```bash
cat > /opt/crypto-coach/scripts/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest code
git pull origin main

# Pull latest Docker images
docker-compose -f docker/docker-compose.prod.yml pull

# Stop existing containers
docker-compose -f docker/docker-compose.prod.yml down

# Start new containers
docker-compose -f docker/docker-compose.prod.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🔍 Running health checks..."
./scripts/health-check.sh

echo "✅ Deployment completed successfully!"
EOF

chmod +x /opt/crypto-coach/scripts/deploy.sh
```

### Create Health Check Script
```bash
cat > /opt/crypto-coach/scripts/health-check.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Health Check - AI Crypto Trading Coach"

# Check Frontend
echo "Checking Frontend..."
if curl -f -s https://crypto-coach.zikhethele.properties/ > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAILED"
    exit 1
fi

# Check Backend API
echo "Checking Backend API..."
if curl -f -s https://crypto-coach.zikhethele.properties/api/ > /dev/null; then
    echo "✅ Backend API: OK"
else
    echo "❌ Backend API: FAILED"
    exit 1
fi

# Check Database
echo "Checking Database..."
if docker exec crypto-coach-mongo-prod mongosh --eval "db.adminCommand('ping')" > /dev/null; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAILED"
    exit 1
fi

echo "🎉 All services are healthy!"
EOF

chmod +x /opt/crypto-coach/scripts/health-check.sh
```

---

## 🔐 Step 8: GitHub Secrets Configuration

In your GitHub repository, add these secrets (Settings → Secrets and variables → Actions):

```
VPS_HOST: YOUR_VPS_IP_ADDRESS
VPS_USER: root
VPS_SSH_KEY: YOUR_PRIVATE_SSH_KEY
```

---

## 🚀 Step 9: Initial Deployment

### Manual First Deployment
```bash
cd /opt/crypto-coach
./scripts/deploy.sh
```

### Verify Deployment
```bash
# Check running containers
docker ps

# Check logs
docker-compose -f docker/docker-compose.prod.yml logs -f

# Run health check
./scripts/health-check.sh
```

---

## 🔒 Step 10: Security & Access Restriction

### Update IP Restrictions in Nginx
Edit `/etc/nginx/sites-available/crypto-coach` and replace:
```nginx
# IP Restriction - PRIVATE ACCESS ONLY
allow YOUR_HOME_IP_ADDRESS;      # Replace with your home IP
allow YOUR_OFFICE_IP_ADDRESS;    # Replace with your office IP
deny all;
```

### Find Your IP Address
```bash
curl https://ipinfo.io/ip
```

### Reload Nginx
```bash
nginx -t
systemctl reload nginx
```

---

## 📊 Step 11: Monitoring & Maintenance

### Set Up Log Rotation
```bash
cat > /etc/logrotate.d/crypto-coach << 'EOF'
/opt/crypto-coach/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 crypto-coach crypto-coach
}
EOF
```

### Set Up Automatic Updates
```bash
# Add to crontab
crontab -e

# Add this line for weekly updates (Sundays at 2 AM)
0 2 * * 0 cd /opt/crypto-coach && ./scripts/deploy.sh >> /var/log/crypto-coach-deploy.log 2>&1
```

---

## 🎯 Final Access Information

### Your Private URLs:
- **Main Application**: https://crypto-coach.zikhethele.properties
- **API Documentation**: https://crypto-coach.zikhethele.properties/api/docs
- **Health Status**: https://crypto-coach.zikhethele.properties/api/

### Access Restrictions:
- ✅ **SSL Encrypted** (HTTPS only)
- ✅ **IP Restricted** (Only your IPs allowed)
- ✅ **Private Repository** (Source code not public)
- ✅ **Secure Environment Variables** (API keys protected)

### CI/CD Workflow:
1. **Push code** to GitHub main branch
2. **Automated tests** run on GitHub Actions
3. **Docker images** built and pushed to registry
4. **Automatic deployment** to your VPS
5. **Health checks** verify successful deployment

---

## 🎉 Deployment Complete!

Your AI Crypto Trading Coach is now deployed with:
- ✅ **Private Access**: Only visible to your IP addresses
- ✅ **Custom Domain**: crypto-coach.zikhethele.properties
- ✅ **CI/CD Pipeline**: Automated deployment on code changes
- ✅ **SSL Security**: Full HTTPS encryption
- ✅ **Production Ready**: Scalable, monitored, and maintained

**You can now access your private AI Crypto Trading Coach at:**
**https://crypto-coach.zikhethele.properties**

**Default Login**: Use the credentials you set in the .env file.