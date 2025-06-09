# 🚀 Final VPS Deployment Commands

## Ready to Deploy!

Your ATM Dashboard is now configured for deployment to your Ubuntu VPS with local PostgreSQL database.

## 📋 Pre-Deployment Verification

**VPS Details:**
- **IP**: `88.222.214.26`
- **Domain**: `dash.luckymifta.dev`
- **Database**: PostgreSQL localhost:5432
- **Services**: Frontend (3000), Main API (8000), User API (8001)

**Before deploying, verify:**
1. ✅ Domain DNS: `dash.luckymifta.dev` → `88.222.214.26`
2. ✅ SSH Access: Can connect as root to your VPS
3. ✅ PostgreSQL: Running on VPS (script will handle this)

## 🎯 Single Command Deployment

SSH to your VPS and run:

```bash
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_to_vps.sh && chmod +x deploy_to_vps.sh && ./deploy_to_vps.sh
```

This single command will:
- Download the deployment script
- Install all dependencies (Node.js, Python, PM2, Nginx, SSL)
- Set up PostgreSQL database and user
- Deploy your 3 services with PM2
- Configure Nginx reverse proxy
- Install Let's Encrypt SSL certificate
- Run health checks

## 🧪 Optional Database Pre-Test

If you want to test the database setup first:

```bash
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/test_vps_database.sh && chmod +x test_vps_database.sh && ./test_vps_database.sh
```

## 📊 Expected Timeline

The deployment should take approximately:
- ⏱️ **5-10 minutes**: System updates and dependency installation
- ⏱️ **2-3 minutes**: Repository cloning and application setup  
- ⏱️ **1-2 minutes**: Database configuration
- ⏱️ **2-3 minutes**: Service startup and SSL certificate
- 🎉 **Total: ~10-18 minutes**

## ✅ Success Verification

After deployment completes, test these URLs:

1. **Main Application**: https://dash.luckymifta.dev
2. **Health Check**: https://dash.luckymifta.dev/health
3. **API Status**: https://dash.luckymifta.dev/api/v1/health
4. **User API**: https://dash.luckymifta.dev/user-api/health

All should show:
- ✅ Green SSL lock in browser
- ✅ HTTP 200 responses
- ✅ Application loads correctly

## 🛠️ Post-Deployment Management

### Check Service Status
```bash
pm2 status                    # All processes
systemctl status nginx        # Web server
systemctl status postgresql   # Database
```

### View Logs
```bash
pm2 logs                      # All application logs
pm2 logs dash-atm-main-api    # Main API logs
pm2 logs dash-atm-user-api    # User management logs
pm2 logs dash-atm-frontend    # Frontend logs
```

### Restart Services
```bash
pm2 restart all               # Restart everything
pm2 restart dash-atm-frontend # Frontend only
systemctl restart nginx       # Web server
```

## 🆘 If Something Goes Wrong

### Common Issues & Solutions

1. **Domain not working**
   ```bash
   nslookup dash.luckymifta.dev  # Check DNS
   ```

2. **SSL certificate issues**
   ```bash
   certbot certificates          # Check cert status
   certbot renew --dry-run      # Test renewal
   ```

3. **Database connection problems**
   ```bash
   ./test_vps_database.sh       # Run database test
   systemctl status postgresql  # Check PostgreSQL
   ```

4. **Services not starting**
   ```bash
   pm2 logs                     # Check error logs
   pm2 restart all              # Try restart
   ```

### Emergency Reset
If you need to start over:
```bash
pm2 delete all                 # Stop all processes
rm -rf /var/www/dash-atm       # Remove installation
./deploy_to_vps.sh             # Re-run deployment
```

## 🎉 You're All Set!

Your deployment configuration is complete and ready. The database is configured to use the local PostgreSQL instance on your VPS for optimal performance and security.

**Next step**: SSH to `88.222.214.26` and run the deployment command above!

---

**Files Updated for VPS Deployment:**
- ✅ `deploy_to_vps.sh` - Main deployment script
- ✅ `test_vps_database.sh` - Database verification script  
- ✅ `VPS_DEPLOYMENT_GUIDE.md` - Manual step-by-step guide
- ✅ `PRE_DEPLOYMENT_CHECKLIST.md` - Pre-deployment verification
- ✅ `VPS_DEPLOYMENT_SUMMARY.md` - Complete deployment summary
- ✅ All environment configurations updated for localhost database

Everything is committed and pushed to your GitHub repository at `https://github.com/luckymifta/dash-atm.git`
