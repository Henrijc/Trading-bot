# AI Crypto Trading Bot

Professional AI-powered cryptocurrency trading platform with machine learning strategies, designed for automated trading on Luno exchange with intelligent goal tracking and probability-based decision making.

## Features

### Core Functionality
- **AI-Driven Trading**: Advanced machine learning models for price prediction and signal generation
- **Goal-Based Trading**: R1,000 daily profit target with probability tracking  
- **Dual Strategy**: Scalping for daily profits + accumulation for long-term wealth
- **Risk Management**: Comprehensive stop-loss, take-profit, and position sizing controls
- **Real-time Analytics**: Live performance monitoring and goal achievement probability

### Technical Features
- **Luno Integration**: Direct integration with Luno cryptocurrency exchange
- **FreqTrade Compatibility**: Hybrid approach using FreqTrade for strategy development
- **Machine Learning**: Ensemble ML models (Random Forest, Gradient Boosting, Linear Regression)
- **Real-time Dashboard**: React-based frontend with live updates
- **Probability Engine**: Statistical modeling for goal achievement predictions

## Architecture

### Backend (FastAPI + Python)
```
backend/
├── server.py                 # Main FastAPI application
├── luno_integration/          # Luno API client and integration
├── probability_engine/        # Goal probability calculations
├── ai_strategies/            # AI trading strategies and ML models
├── freqtrade/               # FreqTrade integration and control
└── requirements.txt         # Python dependencies
```

### Frontend (React)
```
frontend/
├── src/
│   ├── App.js               # Main portfolio dashboard
│   └── index.js             # React entry point
├── package.json             # Node.js dependencies
└── Dockerfile              # Frontend container
```

## Quick Deployment

### Prerequisites
- Docker and Docker Compose
- Domain configured (e.g., cryptobot.yourdomain.com)
- Luno API credentials

### Standard Deployment Procedure

1. **Create dedicated user and directory:**
```bash
sudo adduser cryptobotuser
sudo usermod -aG docker cryptobotuser
sudo mkdir -p /opt/cryptobot
sudo chown -R cryptobotuser:cryptobotuser /opt/cryptobot
```

2. **Setup SSH deploy key:**
```bash
su - cryptobotuser
ssh-keygen -t ed25519 -C "deploy-key-for-cryptobot"
cat ~/.ssh/id_ed25519.pub
# Add public key to GitHub repository deploy keys
```

3. **Clone repository:**
```bash
cd /opt/cryptobot
git clone --branch main git@github.com:YourUsername/ai-crypto-trading-bot.git .
```

4. **Configure environment:**
```bash
cp .env.example .env
nano .env
# Fill in all required credentials (see Environment Variables section)
```

5. **Launch application:**
```bash
docker-compose up -d --build
```

6. **Configure Nginx (exit to main user first):**
```bash
exit
sudo nano /etc/nginx/sites-available/cryptobot.yourdomain.com
```

Add the nginx configuration (see nginx.conf.example), then:

```bash
sudo ln -s /etc/nginx/sites-available/cryptobot.yourdomain.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

7. **Get SSL certificate:**
```bash
sudo certbot --nginx -d cryptobot.yourdomain.com
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LUNO_API_KEY` | Luno API Key from your account | `abc123...` |
| `LUNO_API_SECRET` | Luno API Secret | `def456...` |
| `MONGO_PASSWORD` | MongoDB root password | `secure_mongo_pass` |
| `REDIS_PASSWORD` | Redis password | `secure_redis_pass` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DAILY_TARGET_ZAR` | Daily profit target | `1000` |
| `MAX_DAILY_RISK_PERCENT` | Maximum daily risk exposure | `2.0` |
| `CONFIDENCE_THRESHOLD` | AI signal confidence threshold | `0.7` |
| `MAX_OPEN_TRADES` | Maximum concurrent trades | `5` |

### Security Variables

| Variable | Description |
|----------|-------------|
| `API_TOKEN` | Backend API authentication token |
| `JWT_SECRET` | JWT signing secret |
| `FREQTRADE_JWT_SECRET` | FreqTrade API JWT secret |

## API Endpoints

### Core Endpoints
- `GET /api/health` - System health check
- `GET /api/balance` - Account balance from Luno
- `GET /api/performance` - Performance metrics
- `GET /api/goals/probability` - Goal achievement probabilities
- `GET /api/market-data/{pair}` - Live market data
- `POST /api/trading/start` - Start AI trading
- `POST /api/trading/stop` - Stop AI trading

### Authentication
All protected endpoints require the API token:
```bash
Authorization: Bearer your_api_token
```

## Trading Configuration

### Default Settings
- **Daily Target**: R1,000 profit per day
- **Risk Management**: Maximum 2% daily risk exposure  
- **Strategy Allocation**: 60% scalping, 40% accumulation
- **Stop Loss**: 1.5% maximum loss per trade
- **Take Profit**: 3.0% target profit per trade

### AI Strategy Features
- Machine learning-based price prediction
- Technical analysis with 20+ indicators
- Real-time market condition analysis
- Dynamic position sizing based on confidence
- Automated risk management

## Monitoring & Troubleshooting

### Health Checks
```bash
# Check all services
docker-compose ps

# Check application health
curl https://cryptobot.yourdomain.com/api/health

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Common Issues

1. **Database Connection Failed**
```bash
docker-compose logs mongodb
# Check MongoDB container and credentials
```

2. **Luno API Errors**
```bash
# Verify API credentials in .env file
# Check Luno API status and rate limits
```

3. **Frontend Not Loading**
```bash
# Check Nginx configuration and SSL certificates
sudo nginx -t
sudo systemctl status nginx
```

## Security Considerations

### Production Security
- Change all default passwords in .env file
- Use strong JWT secrets
- Enable firewall on required ports only
- Regular security updates
- Monitor API usage and rate limits

### Network Security
- Application runs on isolated Docker network
- Database and Redis not exposed externally
- HTTPS enforced via Nginx and SSL certificates
- API rate limiting implemented

## Performance Targets

### Financial Goals
- **Daily Target**: R1,000 profit per day
- **Win Rate**: Target >65% successful trades  
- **Risk Control**: <2% daily account exposure
- **Drawdown**: <5% maximum drawdown

### Technical Performance
- **API Response**: <100ms average response time
- **Data Updates**: Real-time market data every 10 seconds
- **Model Accuracy**: >75% prediction accuracy target
- **Uptime**: 99.9% availability target

## Support & Maintenance

### Regular Maintenance
- Monitor system logs daily
- Review trading performance weekly
- Update dependencies monthly
- Backup database and configurations

### Scaling Considerations
- Database can handle millions of trade records
- Redis caching for high-frequency updates
- Horizontal scaling supported via Docker Swarm
- Load balancing ready for multiple instances

## Disclaimer

This trading bot is for educational and personal use. Cryptocurrency trading involves significant financial risk. Never invest more than you can afford to lose. Past performance does not guarantee future results. Always conduct thorough testing before live trading.

## License

Private project - All rights reserved.