# Deployment Guide - AI Crypto Trading Bot

Complete step-by-step deployment guide for the AI Crypto Trading Bot following the standard deployment framework.

## Prerequisites

- **VPS Server**: Ubuntu 20.04+ with Docker and Docker Compose
- **Domain**: DNS record pointing to your server IP
- **Luno Account**: API credentials for cryptocurrency trading
- **GitHub Account**: For repository management

## Step 1: Server Preparation

### Create Dedicated User and Directory

```bash
# Log in as your main user (e.g., zikhethele)
ssh zikhethele@156.155.253.224

# Create dedicated user for the crypto bot
sudo adduser cryptobotuser

# Add user to docker group
sudo usermod -aG docker cryptobotuser

# Create dedicated directory
sudo mkdir -p /opt/cryptobot
sudo chown -R cryptobotuser:cryptobotuser /opt/cryptobot
```

## Step 2: GitHub Access Setup

### Generate Deploy Key

```bash
# Switch to the crypto bot user
su - cryptobotuser

# Generate SSH key for GitHub access
ssh-keygen -t ed25519 -C "deploy-key-for-cryptobot"
# Press Enter three times (no passphrase)

# Display the public key
cat ~/.ssh/id_ed25519.pub
```

### Add Deploy Key to GitHub

1. Copy the public key output
2. Go to your GitHub repository
3. Navigate to Settings > Deploy keys
4. Click "Add deploy key"
5. Title: "Production Server - cryptobot.yourdomain.com"
6. Paste the key and save (do NOT check "Allow write access")

## Step 3: Code Deployment

### Clone Repository

```bash
# Navigate to the application directory
cd /opt/cryptobot

# Remove any existing files (ensure clean start)
rm -rf ./* .??*

# Clone the repository
git clone --branch main git@github.com:YourUsername/ai-crypto-trading-bot.git .
```

## Step 4: Application Configuration

### Create Environment Configuration

```bash
# Create .env file from template
cp .env.example .env

# Edit the environment file
nano .env
```

### Required Environment Variables

Fill in the following in your `.env` file:

```bash
# Database passwords (change these!)
MONGO_PASSWORD=your_secure_mongo_password_here
REDIS_PASSWORD=your_secure_redis_password_here

# Luno API credentials (from your Luno account)
LUNO_API_KEY=your_luno_api_key_here
LUNO_API_SECRET=your_luno_api_secret_here

# Security tokens (generate secure random strings)
API_TOKEN=your_secure_api_token_here
JWT_SECRET=your_secure_jwt_secret_here
FREQTRADE_JWT_SECRET=your_secure_freqtrade_secret_here

# Trading configuration (adjust as needed)
DAILY_TARGET_ZAR=1000
MAX_DAILY_RISK_PERCENT=2.0
MAX_OPEN_TRADES=5
CONFIDENCE_THRESHOLD=0.7

# Environment
ENVIRONMENT=production
```

### Configure Docker Ports

The application is configured to use:
- **Frontend**: Port 3003 (internally mapped from 3000)
- **Backend**: Port 8004 (internally from 8004)
- **MongoDB**: Port 27017 (internal only)
- **Redis**: Port 6379 (internal only)

These ports are correctly set for your deployment framework.

## Step 5: Launch Application

### Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Verify all services are running
docker-compose ps

# Check logs if needed
docker-compose logs -f backend
docker-compose logs -f frontend
```

Expected output from `docker-compose ps`:
```
NAME                    STATUS
cryptobot_backend       Up 30 seconds
cryptobot_frontend      Up 30 seconds  
cryptobot_mongodb       Up 45 seconds
cryptobot_redis         Up 45 seconds
```

## Step 6: Nginx Web Server Configuration

### Create Nginx Configuration

```bash
# Exit to main user
exit

# Create nginx configuration file
sudo nano /etc/nginx/sites-available/cryptobot.yourdomain.com
```

### Nginx Configuration Content

Paste the following configuration (replace `cryptobot.yourdomain.com` with your actual domain):

```nginx
server {
    server_name cryptobot.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 80;
}
```

### Enable Site and Reload Nginx

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/cryptobot.yourdomain.com /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Step 7: SSL Certificate Setup

### Install SSL Certificate

```bash
# Install SSL certificate with Certbot
sudo certbot --nginx -d cryptobot.yourdomain.com

# Follow the prompts to complete SSL setup
```

## Step 8: Verify Deployment

### Test Application Access

1. **Frontend**: Visit `https://cryptobot.yourdomain.com`
2. **API Health**: Visit `https://cryptobot.yourdomain.com/api/health`

Expected API health response:
```json
{
  "status": "healthy",
  "services": {
    "luno": "connected",
    "database": "connected",
    "freqtrade": "disabled"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### Verify Dashboard

The portfolio dashboard should display:
- Account balance information
- Market data for BTC/ZAR
- AI trading status controls
- Performance metrics

## Troubleshooting

### Common Issues

1. **Services not starting**:
```bash
docker-compose logs backend
docker-compose logs frontend
```

2. **Database connection issues**:
```bash
docker-compose logs mongodb
# Check MONGO_PASSWORD in .env file
```

3. **Nginx errors**:
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

4. **SSL certificate issues**:
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

### Application Logs

```bash
# Switch to crypto bot user
su - cryptobotuser
cd /opt/cryptobot

# View real-time logs
docker-compose logs -f backend
docker-compose logs -f frontend

# View specific service logs
docker-compose logs mongodb
docker-compose logs redis
```

## Maintenance

### Regular Updates

```bash
# Switch to crypto bot user
su - cryptobotuser
cd /opt/cryptobot

# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose up -d --build
```

### Backup Strategy

```bash
# Backup environment file
cp .env .env.backup.$(date +%Y%m%d)

# Backup database (run as cryptobotuser)
docker-compose exec mongodb mongodump --out /data/backup/$(date +%Y%m%d)
```

### Monitoring

```bash
# Check service status
docker-compose ps

# Check resource usage
docker stats

# Check application health
curl https://cryptobot.yourdomain.com/api/health
```

## Security Notes

1. **Change all default passwords** in the .env file
2. **Use strong JWT secrets** (generate with `openssl rand -hex 32`)
3. **Monitor API usage** to detect unusual activity
4. **Keep Docker images updated** regularly
5. **Enable firewall** to restrict access to necessary ports only

## Production Checklist

- [ ] Dedicated user created (`cryptobotuser`)
- [ ] SSH deploy key configured
- [ ] Repository cloned to `/opt/cryptobot`
- [ ] Environment variables configured with real credentials
- [ ] Docker services running (all 4 containers up)
- [ ] Nginx configuration created and enabled
- [ ] SSL certificate installed and working
- [ ] Frontend accessible via HTTPS
- [ ] API health endpoint responding
- [ ] Luno API credentials verified
- [ ] Database connection confirmed
- [ ] Application logs showing no errors

## Support

For issues during deployment:
1. Check the application logs
2. Verify all environment variables are set correctly
3. Ensure domain DNS is pointing to the correct server
4. Confirm all required ports are accessible
5. Test Luno API credentials separately if needed

The AI Crypto Trading Bot should now be fully deployed and operational!