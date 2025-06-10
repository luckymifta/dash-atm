# 🔔 **SIMPLIFIED VPS DEPLOYMENT COMMANDS** 
## (Database Tables Already Exist)

Since the notification tables already exist in your database, here are the **simplified deployment steps**:

## 🚀 **Quick Deployment (Recommended)**

### **Option 1: Automated Script**
```bash
# Connect to VPS
ssh root@167.172.71.55

# Navigate to project directory
cd /var/www/dash-atm

# Download and run deployment script
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_bell_notification.sh
chmod +x deploy_bell_notification.sh
./deploy_bell_notification.sh
```

---

## 🛠️ **Option 2: Manual Steps (5 Minutes)**

### **Step 1: Update Code**
```bash
ssh root@167.172.71.55
cd /var/www/dash-atm
git pull origin main
```

### **Step 2: Install Python Dependencies**
```bash
cd /var/www/dash-atm/backend
source venv/bin/activate
pip install asyncpg pytz
```

### **Step 3: Build Frontend**
```bash
cd /var/www/dash-atm/frontend
npm install
npm run build
```

### **Step 4: Restart Services**
```bash
sudo systemctl restart atm-api.service
sudo systemctl restart nginx
```

### **Step 5: Verify Deployment**
```bash
# Test API
curl http://localhost:8000/api/v1/notifications/unread-count

# Check services
sudo systemctl status atm-api.service
sudo systemctl status nginx

# Visit website
curl -I https://dash.luckymifta.dev
```

---

## ✅ **Expected Results**
- **Bell icon** appears next to refresh button
- **Notification count** shows in badge
- **Click bell** → dropdown with notifications
- **Background monitoring** every 5 minutes
- **Real-time updates** every 30 seconds

---

## 🔍 **Troubleshooting Commands**
```bash
# Check logs
sudo journalctl -u atm-api.service -f

# Test database connection
psql -h 88.222.214.26 -U timlesdev -d development_db -c "SELECT COUNT(*) FROM atm_notifications;"

# Restart if needed
sudo systemctl restart atm-api.service nginx
```

---

## 📋 **Key Points**
✅ **Database tables already exist** - No table creation needed  
✅ **Code uses `IF NOT EXISTS`** - Safe to run deployment scripts  
✅ **All files committed** to GitHub main branch  
✅ **Deployment scripts updated** for existing infrastructure  

🚀 **Ready for immediate deployment!** 🔔

---

**Files Updated:**
- `BELL_NOTIFICATION_DEPLOYMENT_SUMMARY.md` 
- `REVISED_BELL_NOTIFICATION_DEPLOYMENT_GUIDE.md`
- `BELL_NOTIFICATION_VPS_DEPLOYMENT_CHECKLIST.md`
- `deploy_bell_notification.sh`

**Repository:** https://github.com/luckymifta/dash-atm
