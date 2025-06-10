# Bell Notification Feature - VPS Deployment Checklist

## 🎯 Pre-Deployment Requirements

### ✅ Code Repository Status
- [x] Bell notification feature code committed to main branch
- [x] All files pushed to GitHub repository
- [x] No compilation errors or warnings
- [x] Backend and frontend integration tested locally

### ✅ Dependencies Verified
- [x] Python dependencies: `asyncio`, `asyncpg`, `pytz`
- [x] Frontend dependencies: All existing packages compatible
- [x] Database requirements: PostgreSQL with UUID support

## 🚀 VPS Deployment Steps

### Step 1: Connect to VPS
```bash
ssh root@167.172.71.55
# or 
ssh your_user@dash.luckymifta.dev
```

### Step 2: Navigate to Project Directory
```bash
cd /var/www/dash-atm
```

### Step 3: Run Bell Notification Deployment Script
```bash
# Download the new deployment script
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_bell_notification.sh

# Make executable
chmod +x deploy_bell_notification.sh

# Run deployment
./deploy_bell_notification.sh
```

### Alternative: Manual Deployment Steps

If the script fails, follow these manual steps:

#### 1. Update Repository
```bash
cd /var/www/dash-atm
git fetch origin
git checkout main
git pull origin main
```

#### 2. Backend Setup
```bash
cd /var/www/dash-atm/backend
source venv/bin/activate
pip install asyncio asyncpg pytz
```

#### 3. Database Setup
```bash
# Connect to PostgreSQL and run:
psql -h 88.222.214.26 -U timlesdev -d development_db

# Run these SQL commands:
CREATE TABLE IF NOT EXISTS atm_notifications (
    id SERIAL PRIMARY KEY,
    notification_id UUID NOT NULL DEFAULT gen_random_uuid(),
    terminal_id VARCHAR(50) NOT NULL,
    location TEXT,
    previous_status VARCHAR(20),
    current_status VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS atm_status_history (
    id SERIAL PRIMARY KEY,
    terminal_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    location TEXT,
    issue_state_name VARCHAR(50),
    serial_number VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fetched_status VARCHAR(50),
    raw_data JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_notifications_terminal_created 
ON atm_notifications(terminal_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_unread 
ON atm_notifications(is_read, created_at DESC) WHERE is_read = FALSE;

CREATE INDEX IF NOT EXISTS idx_status_history_terminal 
ON atm_status_history(terminal_id, updated_at DESC);
```

#### 4. Frontend Build
```bash
cd /var/www/dash-atm/frontend
npm install
npm run build
```

#### 5. Restart Services
```bash
sudo systemctl restart atm-api.service
sudo systemctl restart nginx
```

## 🔍 Post-Deployment Verification

### 1. Check Service Status
```bash
sudo systemctl status atm-api.service
sudo systemctl status nginx
```

### 2. Test API Endpoints
```bash
# Test unread count
curl http://localhost:8000/api/v1/notifications/unread-count

# Test notifications list
curl http://localhost:8000/api/v1/notifications?page=1&per_page=5

# Test manual status check
curl -X POST http://localhost:8000/api/v1/notifications/check-changes
```

### 3. Check Frontend
- Visit https://dash.luckymifta.dev
- Verify bell icon appears next to refresh button
- Check that notifications load properly
- Test click-to-redirect functionality

### 4. Monitor Logs
```bash
# Backend logs
tail -f /var/log/atm-dashboard/api.log

# System service logs
sudo journalctl -u atm-api.service -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## 🎛️ Configuration Verification

### Environment Variables
Ensure these are set in production:
```bash
# Check if environment variables are set
echo $DB_HOST
echo $DB_NAME
echo $DB_USER
# (Password should not be echoed)
```

### Database Connection
```bash
# Test database connection
cd /var/www/dash-atm/backend
source venv/bin/activate
python3 -c "
import asyncio
import asyncpg

async def test_db():
    try:
        conn = await asyncpg.connect(
            host='88.222.214.26',
            port=5432,
            database='development_db',
            user='timlesdev',
            password='timlesdev'
        )
        result = await conn.fetchval('SELECT COUNT(*) FROM atm_notifications')
        print(f'✅ Database connected. Notifications count: {result}')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"
```

## 🔔 Feature Testing Checklist

### Frontend Tests
- [ ] Bell icon visible in dashboard header
- [ ] Unread count badge displays correctly
- [ ] Dropdown opens when bell is clicked
- [ ] Notifications list displays properly
- [ ] "Mark all read" functionality works
- [ ] Click notification redirects to ATM Information page
- [ ] Real-time polling updates unread count

### Backend Tests
- [ ] All 5 notification endpoints respond correctly
- [ ] Status change detection working
- [ ] Database tables created with proper structure
- [ ] Background task monitoring every 5 minutes
- [ ] Timezone handling (Asia/Dili) working correctly
- [ ] Notification severity mapping correct

### Database Tests
- [ ] Tables exist: `atm_notifications`, `atm_status_history`
- [ ] Indexes created for performance
- [ ] Initial notifications populated
- [ ] Status history tracking working

## 🚨 Troubleshooting Common Issues

### Issue: Service Won't Start
```bash
# Check service logs
sudo journalctl -u atm-api.service -n 50

# Check if port is in use
sudo netstat -tulpn | grep :8000

# Restart service
sudo systemctl restart atm-api.service
```

### Issue: Database Connection Failed
```bash
# Test database connectivity
telnet 88.222.214.26 5432

# Check credentials
psql -h 88.222.214.26 -U timlesdev -d development_db -c "SELECT 1"
```

### Issue: Frontend Build Failed
```bash
# Check Node.js version (should be 18+)
node --version

# Clear cache and rebuild
cd /var/www/dash-atm/frontend
rm -rf .next node_modules
npm install
npm run build
```

### Issue: Notifications Not Appearing
```bash
# Manual trigger status check
curl -X POST http://localhost:8000/api/v1/notifications/check-changes

# Check if tables exist
psql -h 88.222.214.26 -U timlesdev -d development_db -c "
SELECT COUNT(*) as notification_count FROM atm_notifications;
SELECT COUNT(*) as history_count FROM atm_status_history;
"
```

## 📈 Performance Monitoring

### Key Metrics to Monitor
- Notification API response times
- Database query performance
- Frontend bell icon loading time
- Background task execution frequency

### Log Analysis
```bash
# Monitor notification creation
grep "Created notification" /var/log/atm-dashboard/api.log

# Monitor status changes
grep "status changes" /var/log/atm-dashboard/api.log

# Monitor API requests
grep "notifications" /var/log/nginx/access.log
```

## ✅ Success Criteria

Deployment is successful when:
- [ ] All services running without errors
- [ ] All API endpoints responding correctly
- [ ] Frontend displays bell notification properly
- [ ] Database tables populated with initial data
- [ ] Background monitoring detecting status changes
- [ ] Users can interact with notifications as expected

## 🎉 Post-Deployment Tasks

1. **Monitor for 24 hours** to ensure stability
2. **Test notification generation** by simulating ATM status changes
3. **Verify performance** under normal load
4. **Document any issues** and resolutions
5. **Update monitoring dashboards** to include notification metrics

---

**Deployment Script**: `deploy_bell_notification.sh`  
**Documentation**: `BELL_NOTIFICATION_IMPLEMENTATION_COMPLETE.md`  
**Repository**: https://github.com/luckymifta/dash-atm  
**Production URL**: https://dash.luckymifta.dev
