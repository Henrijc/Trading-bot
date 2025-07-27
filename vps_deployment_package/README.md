# AI Crypto Trading Coach - VPS CI/CD Deployment

**🌐 Your Private URL**: https://crypto-coach.zikhethele.properties  
**🔒 Access**: IP-restricted private deployment  
**🚀 CI/CD**: Automated deployment from GitHub  

## Quick Start

### 1. GitHub Repository Setup
1. Create **private** GitHub repository: `ai-crypto-trading-coach-vps`
2. Upload all files from this package to the repository
3. Add GitHub Secrets (Settings → Secrets and variables → Actions):
   - `VPS_HOST`: Your VPS IP address
   - `VPS_USER`: root
   - `VPS_SSH_KEY`: Your private SSH key content

### 2. VPS Server Setup
Follow the complete guide in `VPS_CICD_DEPLOYMENT_GUIDE.md`

### 3. Domain Configuration
Point `crypto-coach.zikhethele.properties` to your VPS IP address

### 4. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

### 5. Deploy
Push to GitHub main branch for automatic deployment!

## Package Contents

```
ai-crypto-trading-coach-vps/
├── .github/workflows/deploy.yml    # CI/CD pipeline
├── app/                           # Application code
│   ├── backend/                   # FastAPI backend
│   ├── frontend/                  # React frontend
│   └── freqtrade/                # Trading bot
├── docker/                        # Production Docker configs
├── scripts/                       # Deployment scripts
├── .env.example                   # Environment template
├── VPS_CICD_DEPLOYMENT_GUIDE.md   # Complete setup guide
└── README.md                      # This file
```

For detailed setup instructions, see `VPS_CICD_DEPLOYMENT_GUIDE.md`

---

**🎯 Result**: Private AI Crypto Trading Coach with automatic CI/CD deployment on your custom domain!