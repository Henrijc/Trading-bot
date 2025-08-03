# 🚀 Manual Deployment Guide

## ✅ **AUTOMATIC DEPLOYMENT IS NOW DISABLED**

The CI/CD workflow will **NO LONGER** automatically deploy when you push changes to the `for-deployment` branch.

## 🎯 **HOW TO MANUALLY DEPLOY CHANGES:**

### **Option 1: Manual GitHub Actions Trigger (Recommended)**

1. **Push your changes** to the `for-deployment` branch as usual:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin for-deployment
   ```

2. **Go to GitHub Actions**:
   - Visit: https://github.com/Henrijc/Trading-bot/actions
   - Click on "Build and Deploy to VPS" workflow
   - Click "Run workflow" button

3. **Confirm deployment**:
   - In the dropdown, type exactly: `DEPLOY`
   - Click "Run workflow"

### **Option 2: Direct Server Deployment**

If you prefer to deploy directly on the server:

```bash
# SSH into your server
ssh cryptoadmin@156.155.253.224

# Navigate to app directory
cd /opt/crypto-coach

# Pull latest changes
git pull origin for-deployment

# Rebuild and restart containers
docker-compose down
docker-compose up -d --build
```

## 🔒 **SAFETY FEATURES:**

- **Manual confirmation required**: You must type "DEPLOY" to trigger deployment
- **No accidental deployments**: Pushing code won't automatically deploy
- **Full control**: You decide when changes go live

## 📝 **WORKFLOW SUMMARY:**

1. **Develop**: Make changes in your development environment
2. **Commit**: Push changes to `for-deployment` branch
3. **Deploy**: Manually trigger deployment when ready
4. **Verify**: Check that your app works at `https://crypto.zikhethele.properties`

## ⚠️ **IMPORTANT NOTES:**

- Your local docker-compose setup will continue working normally
- The production deployment is now completely under your control
- No more surprise deployments breaking your website
- You can test changes locally before deploying to production

**AUTOMATIC DEPLOYMENT NIGHTMARE IS OVER! 🎉**