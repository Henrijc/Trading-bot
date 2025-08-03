# 🎯 HOW TO ACCESS YOUR AI CRYPTO TRADING COACH

## 🌐 **YOUR APP URLs:**

### **Option 1: Via Domain (Recommended)**
```
https://crypto-coach.zikhethele.properties
```

### **Option 2: Direct IP Access** 
```
http://156.155.253.224:3000  (if nginx is configured)
```

### **Option 3: SSH Tunnel (Development)**
```bash
ssh -L 3000:localhost:3000 -L 8001:localhost:8001 cryptoadmin@156.155.253.224
# Then access: http://localhost:3000
```

---

## 🔧 **SETUP REQUIRED ON YOUR VPS:**

### **1. Setup Nginx Reverse Proxy** 
```bash
# SSH into your VPS
ssh cryptoadmin@156.155.253.224

# Copy the nginx config
sudo cp /opt/crypto-coach/vps_deployment_package/nginx-reverse-proxy.conf /etc/nginx/sites-available/crypto-coach

# Enable the site
sudo ln -s /etc/nginx/sites-available/crypto-coach /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### **2. Make Sure Your Domain Points to VPS**
```bash
# Check DNS
dig crypto-coach.zikhethele.properties
# Should show: 156.155.253.224
```

### **3. Start Your App**
```bash
cd /opt/crypto-coach
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml up -d
```

---

## 🚀 **WHAT YOU'LL SEE:**

### **Main App Interface:**
- **Login Page**: First thing you'll see
- **Dashboard**: Your portfolio overview
- **Chat**: Talk to your AI trading coach
- **Technical Analysis**: Market insights and signals
- **Trading Campaigns**: Manage your trades

### **API Endpoints (for testing):**
```
GET https://crypto-coach.zikhethele.properties/api/
GET https://crypto-coach.zikhethele.properties/api/health
GET https://crypto-coach.zikhethele.properties/api/portfolio
```

---

## 🔍 **TROUBLESHOOTING:**

### **If you can't access the app:**

1. **Check if containers are running:**
```bash
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml ps
```

2. **Check nginx status:**
```bash
sudo systemctl status nginx
```

3. **Check if ports are open:**
```bash
sudo netstat -tulpn | grep -E ":80|:443|:3000|:8001"
```

4. **Check container logs:**
```bash
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml logs frontend
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml logs backend
```

### **If you see errors:**

1. **Backend not responding:**
```bash
curl http://localhost:8001/api/health
```

2. **Frontend not loading:**
```bash
curl http://localhost:3000
```

3. **Database connection issues:**
```bash
sudo docker compose -f vps_deployment_package/docker/docker-compose.prod.yml logs mongodb
```

---

## 🎮 **USING YOUR APP:**

1. **Go to**: `https://crypto-coach.zikhethele.properties`
2. **Login** with your credentials
3. **Dashboard**: See your portfolio value and performance
4. **Chat**: Ask your AI coach questions like:
   - "What's my portfolio status?"
   - "Should I buy Bitcoin now?"
   - "Show me technical analysis for ETH"
5. **Technical Analysis**: View market signals and indicators
6. **Trading**: Execute trades through the interface

---

## ⚠️ **IMPORTANT NOTES:**

- Your app runs on **ports 3000 (frontend) and 8001 (backend)**
- **Nginx** proxies external traffic to these internal ports
- **MongoDB** runs on port 27017 (internal only)
- **Domain**: crypto-coach.zikhethele.properties should point to 156.155.253.224
- **SSL**: Optional but recommended for production

---

**NOW GO MAKE SOME MONEY WITH YOUR AI TRADING COACH! 💰**