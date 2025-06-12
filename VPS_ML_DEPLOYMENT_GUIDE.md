# 🚀 VPS ML Dependencies Deployment Guide

## 🎯 Objective
Install numpy, pandas, scikit-learn, matplotlib, and seaborn dependencies on VPS to fix the predictive analytics API crashes.

## 🔧 Current Issue
- **Problem**: API crashing with `ModuleNotFoundError: No module named 'numpy'`
- **Root Cause**: Predictive analytics feature requires ML packages not yet installed on VPS
- **Impact**: Main API service fails to start, frontend can't connect to backend

## 📝 Step-by-Step Instructions

### 1. Connect to VPS
```bash
ssh root@88.222.214.26
# Password: TimlesMon2024
```

### 2. Navigate to Project Directory
```bash
cd /var/www/dash-atm
```

### 3. Pull Latest Changes (includes updated requirements.txt)
```bash
git pull origin main
```

### 4. Run Automated Deployment Script
```bash
# Download and run the deployment script
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_ml_dependencies.sh
chmod +x deploy_ml_dependencies.sh
./deploy_ml_dependencies.sh
```

**OR Manual Installation:**

### 5. Manual Installation Steps
```bash
# Navigate to backend directory
cd /var/www/dash-atm/backend

# Activate virtual environment
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install ML dependencies (this may take 5-10 minutes)
pip install numpy>=1.24.0
pip install pandas>=2.0.0
pip install scikit-learn>=1.3.0
pip install matplotlib>=3.7.0
pip install seaborn>=0.12.0

# Install all requirements
pip install -r requirements.txt

# Verify installation
python3 -c "import numpy, pandas, sklearn, matplotlib, seaborn; print('✅ All ML packages imported successfully!')"
```

### 6. Restart Services
```bash
# Stop the main API
pm2 stop dash-atm-main-api

# Start the main API
pm2 start dash-atm-main-api

# Check status
pm2 status
pm2 logs dash-atm-main-api --lines 20
```

## ✅ Verification Steps

### 1. Check API Health
```bash
curl http://localhost:8000/api/v1/health
```

### 2. Test Predictive Analytics Endpoint
```bash
curl http://localhost:8000/api/v1/atm/147/predictive-analytics
```

### 3. Check PM2 Logs
```bash
pm2 logs dash-atm-main-api --lines 50
```

### 4. Monitor System Resources
```bash
htop
# Check CPU and memory usage during ML package installation
```

## 🔍 Expected Results

### ✅ Success Indicators:
- PM2 services show "online" status without restart loops
- API health endpoint returns 200 OK
- Predictive analytics endpoint returns JSON data
- No numpy import errors in PM2 logs
- Frontend can connect to backend successfully

### ❌ Troubleshooting:
- **If pip install fails**: Check disk space with `df -h`
- **If memory errors occur**: Temporarily stop other services
- **If virtual environment issues**: Recreate with `python3 -m venv venv`
- **If PM2 won't start**: Check logs with `pm2 logs dash-atm-main-api`

## 📦 Dependencies Being Installed

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | ≥1.24.0 | Numerical computing arrays |
| pandas | ≥2.0.0 | Data manipulation/analysis |
| scikit-learn | ≥1.3.0 | Machine learning algorithms |
| matplotlib | ≥3.7.0 | Plotting and visualization |
| seaborn | ≥0.12.0 | Statistical data visualization |

## 🎉 Final Verification

After successful installation, the predictive analytics features should work:

1. **Frontend**: Navigate to `/predictive-analytics` page
2. **Individual ATM Analysis**: Click "View Details" on any ATM
3. **Fleet Statistics**: View charts and risk distribution
4. **Real-time Updates**: Use refresh button for latest data

## 🚨 Emergency Rollback

If something goes wrong:
```bash
# Revert to previous commit
git log --oneline -5
git checkout <previous-commit-hash>

# Restart services
pm2 restart all
```

## 📞 Support

If issues persist:
1. Check error logs: `pm2 logs dash-atm-main-api`
2. Verify Python version: `python3 --version` (should be 3.8+)
3. Check virtual environment: `which python` (should point to venv)
4. Verify disk space: `df -h` (need at least 2GB free)

---

**Deployment Date**: December 6, 2024  
**Estimated Time**: 10-15 minutes  
**Dependencies Size**: ~500MB  
**Python Version Required**: 3.8+
