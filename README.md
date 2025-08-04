# 🚀 AI Crypto Trading Bot

An advanced AI-powered cryptocurrency trading bot with machine learning capabilities, designed for automated trading on Luno exchange with intelligent goal tracking and probability-based decision making.

## 🎯 Features

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
- **Real-time Dashboard**: React-based frontend with live WebSocket updates
- **Probability Engine**: Statistical modeling for goal achievement predictions

## 🏗️ Architecture

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

### Frontend (React + TailwindCSS)
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.js      # Main dashboard with KPIs
│   │   ├── TradingView.js    # Manual and AI trading interface
│   │   ├── GoalTracking.js   # Goal progress and probability tracking
│   │   ├── AIConfig.js       # AI strategy configuration
│   │   └── PerformanceAnalytics.js # Detailed performance analysis
│   └── App.js               # Main application component
└── package.json             # Node.js dependencies
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Luno API credentials
- Domain configured (cryptobot.zikhethele.properties)

### Deployment (Following Standard Framework)

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
# Add public key to GitHub repository
```

3. **Clone repository:**
```bash
cd /opt/cryptobot
git clone --branch main git@github.com:Henrijc/ai-crypto-trading-bot.git .
```

4. **Configure environment:**
```bash
cp .env.example .env
nano .env
# Fill in all required credentials and configuration
```

5. **Launch application:**
```bash
docker-compose up -d --build
```

6. **Configure Nginx:**
```bash
# Exit to main user
exit
sudo nano /etc/nginx/sites-available/cryptobot.zikhethele.properties
```

Nginx configuration:
```nginx
server {
    server_name cryptobot.zikhethele.properties;

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

7. **Enable site and get SSL:**
```bash
sudo ln -s /etc/nginx/sites-available/cryptobot.zikhethele.properties /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d cryptobot.zikhethele.properties
```

## 🎛️ Configuration

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `LUNO_API_KEY` | Luno API Key | Yes | `bg2r43ee5bn2t` |
| `LUNO_API_SECRET` | Luno API Secret | Yes | `GOvRCPBeCj...` |
| `DAILY_TARGET_ZAR` | Daily profit target | No | `1000` |
| `MAX_DAILY_RISK_PERCENT` | Maximum daily risk | No | `2.0` |
| `CONFIDENCE_THRESHOLD` | AI signal confidence threshold | No | `0.7` |

### Trading Parameters

- **Daily Target**: R1,000 profit per day
- **Risk Management**: Maximum 2% daily risk exposure
- **Strategy Allocation**: 60% scalping, 40% accumulation
- **Stop Loss**: 1.5% maximum loss per trade
- **Take Profit**: 3.0% target profit per trade

## 📊 AI Strategy

### Machine Learning Models
1. **Random Forest Regressor** (40% weight) - Robust ensemble method
2. **Gradient Boosting Regressor** (40% weight) - High accuracy boosting
3. **Linear Regression** (20% weight) - Simple linear relationship

### Features Used
- Technical indicators (RSI, MACD, Bollinger Bands)
- Price momentum and volatility
- Volume analysis
- Time-based features (hour, day of week)
- Support/resistance levels

### Trading Signals
- **Buy Signal**: Prediction > 0.5%, Confidence > 70%
- **Sell Signal**: Prediction < -0.5%, Confidence > 70%
- **Position Sizing**: Based on confidence and signal strength

## 📈 Goal Tracking

### Probability Calculations
- **Daily Goal (R1,000)**: Statistical analysis of recent performance
- **Weekly Goal (R7,000)**: Trend-adjusted probability estimation  
- **Monthly Goal (R30,000)**: Long-term projection with volatility factors

### Success Metrics
- Real-time progress tracking
- Confidence intervals
- Performance recommendations
- Risk-adjusted probability scores

## 🛡️ Risk Management

### Safety Features
- **Position Limits**: Maximum 5 open trades
- **Daily Limits**: Stop trading at risk threshold
- **Emergency Stop**: Manual override capabilities
- **Drawdown Protection**: Automatic position reduction

### Monitoring
- Real-time P&L tracking
- Risk exposure monitoring
- Performance alerts
- System health checks

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/health` - System health check
- `GET /api/balance` - Account balance from Luno
- `GET /api/performance` - Performance metrics
- `GET /api/goals/probability` - Goal achievement probabilities
- `POST /api/trade` - Execute manual trade
- `POST /api/trading/start` - Start AI trading
- `POST /api/trading/stop` - Stop AI trading

### WebSocket
- `WS /api/ws/live-data` - Real-time trading data and updates

## 📱 Frontend Features

### Dashboard
- Real-time account balance
- Daily P&L progress
- Goal achievement probability
- AI strategy status
- Recent trades overview

### Trading Interface
- Manual trade execution
- AI trading control
- Market data display
- Order management

### Analytics
- Performance charts
- Trade history
- Risk analysis
- AI insights and recommendations

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
```bash
docker-compose logs mongodb
# Check MongoDB container status and credentials
```

2. **Luno API Errors**
```bash
# Verify API credentials in .env file
# Check Luno API status and rate limits
```

3. **Frontend Not Loading**
```bash
docker-compose logs frontend
# Check Nginx configuration and SSL certificates
```

4. **AI Model Training Fails**
```bash
docker-compose logs backend
# Check market data availability and model parameters
```

### Health Checks
```bash
# Check all services
docker-compose ps

# Check application health
curl https://cryptobot.zikhethele.properties/api/health

# Check logs
docker-compose logs -f backend
```

## 🔒 Security

### Best Practices
- API keys stored as environment variables
- JWT tokens for authentication  
- HTTPS enforcement
- Rate limiting on API endpoints
- Input validation and sanitization

### Production Considerations
- Regular security updates
- Database backups
- API key rotation
- Monitoring and alerting
- Access control and audit logs

## 📊 Performance Targets

### Daily Goals
- **Primary**: R1,000 profit per day
- **Win Rate**: >65% successful trades
- **Risk**: <2% daily account exposure
- **Drawdown**: <5% maximum drawdown

### AI Performance
- **Model Accuracy**: >75% prediction accuracy
- **Signal Quality**: >70% confidence threshold
- **Response Time**: <100ms for trade decisions

## 🤝 Support

For issues and questions:
1. Check troubleshooting section
2. Review logs with `docker-compose logs`
3. Check system health endpoint
4. Verify environment configuration

## ⚠️ Disclaimer

This trading bot is for educational and personal use. Cryptocurrency trading involves significant financial risk. Never invest more than you can afford to lose. Past performance does not guarantee future results. Always conduct thorough testing before live trading.

## 📄 License

Private project - All rights reserved.