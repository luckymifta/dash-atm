# 🔔 Revised Bell Notification Feature - VPS Deployment Guide

## ⚠️ **Important Update: Database Tables Already Exist**

The notification database tables (`atm_notifications` and `atm_status_history`) **already exist** in your production database. This revised guide accounts for existing tables and simplifies the deployment process.

## 🚀 **Simplified Manual VPS Deployment Steps**

### 🔗 **Step 1: Connect to Your VPS**

```bash
ssh root@167.172.71.55
```

### 📁 **Step 2: Navigate to Project Directory & Update Code**

```bash
cd /var/www/dash-atm

# Pull latest changes with bell notification feature
git fetch origin
git checkout main
git pull origin main
```

**✅ Verify**: You should see new files including `notification_service.py`, `BellNotification.tsx`, etc.

### 🐍 **Step 3: Backend Dependencies Setup**

```bash
# Navigate to backend directory
cd /var/www/dash-atm/backend

# Activate virtual environment
source venv/bin/activate

# Install new Python dependencies for notification service
pip install asyncio asyncpg pytz

# Verify installation
python3 -c "import asyncpg, pytz; print('✅ Dependencies installed successfully')"
```

### 🗄️ **Step 4: Database Verification (Tables Already Exist)**

Since the notification tables already exist, we just need to verify they're accessible:

```bash
# Verify that notification tables exist and are accessible
psql -h 88.222.214.26 -U timlesdev -d development_db -c "
SELECT tablename FROM pg_tables WHERE tablename IN ('atm_notifications', 'atm_status_history');
"
```

**Expected output:**
```
     tablename      
--------------------
 atm_notifications
 atm_status_history
```

**Check current data (optional):**
```bash
# Check existing notification count
psql -h 88.222.214.26 -U timlesdev -d development_db -c "
SELECT COUNT(*) as notification_count FROM atm_notifications;
SELECT COUNT(*) as history_count FROM atm_status_history;
"
```

**✅ Verify connection successful**: The command should return the table names without errors.

### 🌐 **Step 5: Frontend Build**

```bash
# Navigate to frontend directory
cd /var/www/dash-atm/frontend

# Install any new dependencies
npm install

# Build the frontend with bell notification feature
npm run build
```

**✅ Verify build success:**
```bash
ls -la .next/
# Should show BUILD_ID file and other build artifacts
```

### 📄 **Step 6: Update Environment File (If Needed)**

Check if your `.env` file has the notification configurations:

```bash
# Navigate to project root
cd /var/www/dash-atm

# Check current .env file
cat .env | grep -E "(NOTIFICATION|DB_)"
```

**If missing**, add these lines to your `.env` file:
```bash
# Add notification configurations to .env
cat >> .env << 'EOF'

# Bell Notification Configuration
NOTIFICATION_CHECK_INTERVAL=300  # 5 minutes in seconds
NOTIFICATION_CLEANUP_DAYS=30     # Keep notifications for 30 days
NOTIFICATION_TIMEZONE=Asia/Dili  # Dili timezone for timestamps

# Notification Database Configuration (uses existing external DB)
NOTIFICATION_DB_HOST=88.222.214.26
NOTIFICATION_DB_PORT=5432
NOTIFICATION_DB_NAME=development_db
NOTIFICATION_DB_USER=timlesdev
NOTIFICATION_DB_PASSWORD=timlesdev
EOF
```

### 🔄 **Step 7: Restart Services**

```bash
# Restart the FastAPI service
sudo systemctl restart atm-api.service

# Wait for service to start
sleep 5

# Check service status
sudo systemctl status atm-api.service

# Restart Nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

### ✅ **Step 8: Verify Deployment**

**Test API endpoints:**
```bash
# Test unread count endpoint
curl http://localhost:8000/api/v1/notifications/unread-count

# Test notifications list
curl http://localhost:8000/api/v1/notifications?page=1&per_page=5

# Test manual status check
curl -X POST http://localhost:8000/api/v1/notifications/check-changes
```

**Expected API responses:**
- Unread count: `{"unread_count": 0, "timestamp": "..."}`
- Notifications list: JSON with notifications array
- Status check: `{"success": true, ...}`

### 🔍 **Step 9: Initialize Notifications (First Run)**

The notification service will automatically verify tables and create indexes on first run:

```bash
# Navigate to backend directory
cd /var/www/dash-atm/backend

# Activate virtual environment
source venv/bin/activate

# Run initial notification check to populate data
python3 -c "
import asyncio
import sys
sys.path.append('.')
from notification_service import run_status_check

async def main():
    try:
        changes = await run_status_check()
        print(f'✅ Initial notification check completed. Found {len(changes)} status changes.')
    except Exception as e:
        print(f'⚠️ Initial check failed: {e}')

asyncio.run(main())
"
```

### 📊 **Step 10: Verify Bell Notification Feature**

1. **Visit your website**: https://dash.luckymifta.dev
2. **Check for bell icon**: Should appear next to the refresh button
3. **Click the bell**: Should open dropdown with notifications
4. **Test functionality**: Try clicking a notification to see if it redirects

## 🎯 **Key Changes from Original Guide:**

### ✅ **What's Different:**
- **No manual table creation** - Tables already exist
- **Simplified database step** - Only verification needed
- **Automatic table validation** - Notification service handles table setup
- **Focus on service restart** - Main requirement for deployment

### ✅ **What the Notification Service Does Automatically:**
- Verifies table existence using `CREATE TABLE IF NOT EXISTS`
- Creates missing indexes automatically
- Initializes database connection pool
- Starts background monitoring task

## 🔍 **Quick Verification Commands:**

### **Database Verification:**
```bash
psql -h 88.222.214.26 -U timlesdev -d development_db -c "
SELECT COUNT(*) as notification_count FROM atm_notifications;
SELECT COUNT(*) as history_count FROM atm_status_history;
"
```

### **Service Status:**
```bash
sudo systemctl status atm-api.service
sudo systemctl status nginx
```

### **API Test:**
```bash
curl https://dash.luckymifta.dev/api/v1/notifications/unread-count
```

## 🚨 **Common Issues & Solutions:**

### **Issue: Tables not accessible**
```bash
# Test database connection
telnet 88.222.214.26 5432
# Should connect successfully
```

### **Issue: Service won't start**
```bash
sudo journalctl -u atm-api.service -n 50
sudo systemctl restart atm-api.service
```

### **Issue: Frontend not updating**
```bash
cd /var/www/dash-atm/frontend
rm -rf .next node_modules
npm install
npm run build
sudo systemctl restart nginx
```

---

## 🎉 **Success Criteria:**

Deployment is successful when:
- [x] Repository updated with latest code
- [x] Python dependencies installed
- [x] Database tables verified as accessible
- [x] Frontend built successfully
- [x] Services restarted without errors
- [x] API endpoints responding correctly
- [x] Bell icon visible and functional
- [x] Background monitoring active

**🔔 Your bell notification feature should now be fully functional!** 

**Repository**: https://github.com/luckymifta/dash-atm  
**Production URL**: https://dash.luckymifta.dev
