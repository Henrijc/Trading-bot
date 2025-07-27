# 🚀 QUICK START GUIDE

## Prerequisites ✅
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Make sure Docker Desktop is running

## Setup (5 minutes) ⚙️

### Method 1: Automatic Setup (Recommended)
**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

### Method 2: Manual Setup
1. **Copy environment files:**
   ```bash
   cp .env.backend.example .env
   cp .env.frontend.example app/frontend/.env
   cp config.luno.example.json app/freqtrade/config.json
   ```

2. **Edit .env file with your API keys:**
   - `LUNO_API_KEY` - Get from [Luno API Settings](https://www.luno.com/wallet/security/api_keys)
   - `LUNO_SECRET` - Your Luno secret key
   - `GEMINI_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. **Start the system:**
   ```bash
   docker-compose up --build
   ```

## Access Your Trading Coach 🎯
- **Dashboard:** http://localhost:3000
- **API Documentation:** http://localhost:8001/docs

## First Steps 👶
1. **Login** with configured credentials
2. **Set up 2FA** for security
3. **Check Portfolio** tab (verify Luno connection)
4. **Start Bot** in **Dry Run mode** (safe testing)
5. **Monitor AI Log** tab to see decision making

## Important Safety Notes ⚠️
- **Always start with Dry Run mode**
- **Verify your settings before Live Trading**
- **Monitor the Decision Log for transparency**
- **Keep your API keys secure**

## Stop the System 🛑
Press `Ctrl+C` in terminal, then:
```bash
docker-compose down
```

## Need Help? 🆘
- Check the full `README.md` for detailed instructions
- Review logs: `docker-compose logs [service-name]`
- Ensure API keys are correct in `.env` file

---
*🎉 You're ready to start AI-powered crypto trading!*