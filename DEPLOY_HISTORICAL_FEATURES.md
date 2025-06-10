# 🚀 Deploy ATM Historical Features to VPS

## Overview
This guide will deploy your new ATM Individual Historical Chart features to your VPS at `dash.luckymifta.dev`.

## 🎯 New Features Being Deployed
- ✅ Individual ATM Historical Data API endpoints
- ✅ ATM Historical Chart component with line visualization
- ✅ 30-minute auto-refresh intervals (reduced from 30 seconds)
- ✅ Comprehensive testing and documentation

## 📋 Pre-Deployment Checklist

### Verify Current Setup
- **VPS**: `88.222.214.26`
- **Domain**: `dash.luckymifta.dev`
- **Database**: PostgreSQL localhost (development_db)
- **Services**: Frontend (3000), Main API (8000), User API (8001)

### Check VPS Access
```bash
# Test SSH connection
ssh root@88.222.214.26

# Check if domain resolves
nslookup dash.luckymifta.dev
```

## 🚀 Deployment Steps

### Step 1: Connect to VPS
```bash
ssh root@88.222.214.26
```

### Step 2: Navigate to Application Directory
```bash
cd /var/www/dash-atm
```

### Step 3: Pull Latest Changes from Main Branch
```bash
# Ensure we're on main branch
git checkout main

# Pull the latest changes (includes your ATM historical features)
git pull origin main

# Verify the new files are present
ls -la frontend/src/components/ATMIndividualChart.tsx
ls -la backend/ATM_HISTORICAL_API_GUIDE.md
ls -la INDIVIDUAL_ATM_CHART_IMPLEMENTATION_COMPLETE.md
```

### Step 4: Update Backend Dependencies
```bash
cd backend
source venv/bin/activate

# Install any new dependencies (if added)
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Update Frontend Dependencies and Rebuild
```bash
cd ../frontend

# Install any new dependencies
npm install

# Clear build cache to ensure fresh build with new components
rm -rf .next
rm -rf node_modules/.cache

# Build with new features
NODE_ENV=production npm run build
```

### Step 6: Update PM2 Services
```bash
cd /var/www/dash-atm

# Restart all services to pick up changes
pm2 restart all

# Check service status
pm2 status
```

### Step 7: Verify Deployment
```bash
# Test individual ATM historical endpoints
echo "Testing new historical endpoints..."

# Test ATM list endpoint
curl -s "https://dash.luckymifta.dev/api/v1/atm/list" | jq '.success'

# Test individual ATM historical data (using ATM 147 as example)
curl -s "https://dash.luckymifta.dev/api/v1/atm/147/history?hours=24" | jq '.atm_data.terminal_id'

# Test health endpoints
curl -s "https://dash.luckymifta.dev/api/v1/health" | jq '.status'
curl -s "https://dash.luckymifta.dev/user-api/health" | jq '.status'
```

## 🔍 Verification Steps

### 1. Check PM2 Process Status
```bash
pm2 status
# Expected: All services should be "online"
```

### 2. Check Service Logs
```bash
# Check for any errors in the logs
pm2 logs dash-atm-main-api --lines 20
pm2 logs dash-atm-frontend --lines 20
```

### 3. Test Web Application
Open your browser and visit:
- **Main Dashboard**: https://dash.luckymifta.dev
- **Look for**: New "Individual ATM Chart" section below the main dashboard
- **Test**: Select different ATMs from the dropdown
- **Verify**: Line chart shows status transitions over time

### 4. Test New API Endpoints
```bash
# Test all 14 ATMs are available
curl -s "https://dash.luckymifta.dev/api/v1/atm/list" | jq '.total_atms'

# Test historical data for multiple ATMs
curl -s "https://dash.luckymifta.dev/api/v1/atm/147/history?hours=168" | jq '.atm_data.summary_stats'
curl -s "https://dash.luckymifta.dev/api/v1/atm/89/history?hours=48" | jq '.atm_data.summary_stats'
```

## 🎯 Expected Results

After successful deployment, you should see:

### 1. Dashboard Features
- ✅ **Individual ATM Chart**: New component below availability chart
- ✅ **ATM Selector**: Dropdown with 14+ ATMs
- ✅ **Status Indicators**: Color-coded current status in dropdown
- ✅ **Time Period Controls**: 24H, 7D, 30D buttons
- ✅ **Line Chart**: Step-after visualization showing status transitions
- ✅ **Auto-Refresh**: 30-minute intervals (check timer in header)

### 2. API Responses
```json
// /api/v1/atm/list
{
  "success": true,
  "total_atms": 14,
  "atms": [...]
}

// /api/v1/atm/147/history
{
  "atm_data": {
    "terminal_id": "147",
    "historical_points": [...],
    "summary_stats": {
      "data_points": 48,
      "uptime_percentage": 100.0
    }
  },
  "chart_config": {...}
}
```

### 3. Performance
- ✅ **Response Times**: < 1 second for all endpoints
- ✅ **Chart Rendering**: Smooth line chart with status transitions
- ✅ **Data Volume**: 24-168 data points per ATM
- ✅ **Memory Usage**: No memory leaks or excessive usage

## 🛠️ Troubleshooting

### If Services Don't Start
```bash
# Check logs for specific errors
pm2 logs --lines 50

# Restart individual services
pm2 restart dash-atm-frontend
pm2 restart dash-atm-main-api

# Check if ports are available
netstat -tlnp | grep :3000
netstat -tlnp | grep :8000
```

### If API Endpoints Return Errors
```bash
# Check backend logs
pm2 logs dash-atm-main-api --lines 30

# Test database connectivity
cd /var/www/dash-atm/backend
source venv/bin/activate
python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://timlesdev:timlesdev@localhost/development_db')
    result = await conn.fetchval('SELECT COUNT(*) FROM terminals')
    print(f'Terminals in DB: {result}')
    await conn.close()
asyncio.run(test())
"
```

### If Frontend Doesn't Show New Features
```bash
# Clear cache and rebuild
cd /var/www/dash-atm/frontend
rm -rf .next
npm run build
pm2 restart dash-atm-frontend

# Check if new component exists
ls -la src/components/ATMIndividualChart.tsx
```

## 🔄 Rollback Plan (If Needed)

If something goes wrong, you can rollback:

```bash
cd /var/www/dash-atm

# Rollback to previous commit (change COMMIT_HASH to previous working commit)
git log --oneline -5  # Find previous working commit
git checkout PREVIOUS_COMMIT_HASH

# Rebuild and restart
cd frontend && npm run build
cd .. && pm2 restart all
```

## 📊 Success Verification Checklist

- [ ] All PM2 services are "online" status
- [ ] Main dashboard loads at https://dash.luckymifta.dev
- [ ] Individual ATM Chart component is visible
- [ ] ATM dropdown shows 14+ ATMs with status indicators
- [ ] Line chart displays status transitions
- [ ] API endpoints return expected JSON responses
- [ ] Auto-refresh timer shows 30-minute intervals
- [ ] CSV export works from the chart
- [ ] No console errors in browser developer tools

## 🎉 Deployment Complete!

Once all verification steps pass, your ATM Historical Data features are successfully deployed!

## 📋 Next Steps

1. **Monitor**: Check logs periodically for any issues
2. **Performance**: Monitor response times and memory usage
3. **Data**: Verify historical data collection is working
4. **Users**: Share the new features with your team
5. **Documentation**: Update any user guides if needed

## 🆘 Support

If you encounter issues:
1. Check the logs: `pm2 logs --lines 50`
2. Verify service status: `pm2 status`
3. Test endpoints: Use the curl commands above
4. Check database connectivity
5. Review nginx configuration: `nginx -t`

Your ATM Dashboard now includes comprehensive individual ATM historical tracking! 🎊
