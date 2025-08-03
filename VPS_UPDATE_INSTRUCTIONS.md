# 🚀 VPS Update Instructions for Security Improvements

## Overview
Your security improvements have been successfully pushed to GitHub! Here's what you need to do on your VPS to apply the updates.

## 📋 Critical VPS Environment Updates Needed

Your current VPS `.env` file is **missing several required variables** that the updated `user_management_api.py` now needs:

### ❌ Missing Required Variables:
- `JWT_SECRET_KEY` - For JWT token signing
- `PASSWORD_RESET_SECRET` - For password reset tokens
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration settings
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token settings
- `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` - Reset token expiration
- `REMEMBER_ME_DAYS` - Remember me functionality
- `MAX_FAILED_ATTEMPTS` - Account security
- `ACCOUNT_LOCKOUT_MINUTES` - Account lockout time
- `SESSION_TIMEOUT_WARNING_MINUTES` - Session warnings
- `TIMEZONE` - Timezone configuration
- `AUTO_LOGOUT_DILI_TIME` - Auto logout settings

### ⚠️ Format Issues to Fix:
- `CORS_ORIGINS` format needs to be changed from JSON array to comma-separated string
- Current: `CORS_ORIGINS=["https://dash.britimorleste.tl", "http://localhost:3000"]`
- Should be: `CORS_ORIGINS=https://dash.britimorleste.tl`

## 🔧 Quick VPS Update Steps

### Option 1: Automated Update (Recommended)

1. **Pull the latest code on your VPS:**
   ```bash
   ssh luckymifta@your-vps-ip
   cd /var/www/dash-atm
   git pull origin feature/docker-setup
   ```

2. **Run the automated update script:**
   ```bash
   chmod +x update_vps_security.sh
   ./update_vps_security.sh
   ```

3. **Follow the script instructions to update your VPS `.env` file**

### Option 2: Manual Update

1. **Backup your current `.env`:**
   ```bash
   sudo cp backend/.env backend/.env.backup.$(date +%Y%m%d)
   ```

2. **Add missing variables to your VPS `.env` file:**
   ```bash
   sudo nano backend/.env
   ```

3. **Add these lines to your existing `.env`:**
   ```env
   # Security Configuration (REQUIRED - ADD THESE)
   JWT_SECRET_KEY=GENERATE_NEW_32_CHAR_SECRET
   JWT_ALGORITHM=HS256
   PASSWORD_RESET_SECRET=GENERATE_DIFFERENT_32_CHAR_SECRET
   
   # Token Settings (ADD THESE)
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=30
   PASSWORD_RESET_TOKEN_EXPIRE_HOURS=24
   REMEMBER_ME_DAYS=30
   
   # Account Security (ADD THESE)
   MAX_FAILED_ATTEMPTS=5
   ACCOUNT_LOCKOUT_MINUTES=15
   SESSION_TIMEOUT_WARNING_MINUTES=5
   
   # Timezone (ADD THESE)
   TIMEZONE=Asia/Dili
   AUTO_LOGOUT_DILI_TIME=00:00
   ```

4. **Fix CORS_ORIGINS format:**
   ```env
   # Change this:
   CORS_ORIGINS=["https://dash.britimorleste.tl", "http://localhost:3000"]
   
   # To this:
   CORS_ORIGINS=https://dash.britimorleste.tl
   ```

5. **Generate secure secrets:**
   ```bash
   python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
   python3 -c "import secrets; print('PASSWORD_RESET_SECRET=' + secrets.token_urlsafe(32))"
   ```

## ✅ Verification Steps

1. **Test configuration:**
   ```bash
   cd /var/www/dash-atm
   python3 verify_security.py
   ```

2. **Test application import:**
   ```bash
   cd /var/www/dash-atm/backend
   python3 -c "from user_management_api import app; print('✅ App loads successfully')"
   ```

3. **Restart your services:**
   ```bash
   # If using systemd:
   sudo systemctl restart your-service-name
   
   # If using PM2:
   pm2 restart all
   
   # If using docker:
   docker-compose restart
   ```

## 🚨 What Will Happen If You Don't Update

If you try to run the updated `user_management_api.py` without updating your `.env` file, you'll get errors like:

```
ValueError: JWT_SECRET_KEY environment variable is required
ValueError: PASSWORD_RESET_SECRET environment variable is required
ValueError: Missing required database environment variables: ...
```

## 📁 Files Available on GitHub

After pulling the latest code, you'll have these new files:
- `verify_security.py` - Security verification script
- `update_vps_security.sh` - Automated VPS update script
- `vps.env.template` - Complete VPS environment template
- `SECURITY_IMPROVEMENTS.md` - Detailed documentation
- `DEPLOYMENT_SECURITY_CHECKLIST.md` - Deployment checklist

## 🔐 Security Benefits

Once updated, your VPS will have:
- ✅ No hardcoded secrets in code
- ✅ Strong JWT token security
- ✅ Proper password reset security
- ✅ Environment-based configuration
- ✅ Production security validation
- ✅ Comprehensive audit logging

## 📞 Need Help?

If you encounter any issues:
1. Check the logs: `sudo journalctl -u your-service-name -f`
2. Run the verification script: `python3 verify_security.py`
3. Check the detailed documentation in `SECURITY_IMPROVEMENTS.md`

## 🎯 Summary

**You MUST update your VPS `.env` file before the new code will work!**

The easiest way is to:
1. `git pull origin feature/docker-setup`
2. `./update_vps_security.sh`
3. Follow the script instructions
4. Restart your services

This ensures your production environment is secure and compatible with the new code! 🚀
