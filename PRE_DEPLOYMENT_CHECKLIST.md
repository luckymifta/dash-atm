# Pre-Deployment Checklist

## ✅ Prerequisites Verification

Before running the deployment script, verify these requirements:

### 1. Domain Configuration
- [ ] `dash.luckymifta.dev` DNS A record points to your VPS IP address
- [ ] Domain propagation is complete (test with `nslookup dash.luckymifta.dev`)

### 2. VPS Access
- [ ] SSH access to Ubuntu VPS as root
- [ ] VPS has at least 2GB RAM and 20GB storage
- [ ] VPS can access the internet (for package downloads)

### 3. Database Access
- [ ] PostgreSQL is installed and running on the VPS (`systemctl status postgresql`)
- [ ] Database `development_db` exists with user `timlesdev`
- [ ] Test connection: `sudo -u postgres psql -U timlesdev -d development_db`

### 4. Required Ports
- [ ] Port 80 (HTTP) - for initial Nginx setup
- [ ] Port 443 (HTTPS) - for SSL/TLS
- [ ] Port 3000 - for Next.js frontend
- [ ] Port 8000 - for FastAPI main API
- [ ] Port 8001 - for User Management API

### 5. Email for SSL Certificate
- [ ] Valid email address for Let's Encrypt certificate registration
- [ ] Currently set to: `admin@luckymifta.dev`

## 🚀 Deployment Options

### Option 1: Automated Script (Recommended)
```bash
# On your VPS as root:
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_to_vps.sh
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh
```

### Option 2: Manual Step-by-Step
Follow the commands in `VPS_DEPLOYMENT_GUIDE.md`

## 📋 Post-Deployment Verification

After deployment completes, verify these:

### 1. Services Running
```bash
pm2 status
systemctl status nginx
systemctl status postgresql
```

### 2. Application Health
- [ ] https://dash.luckymifta.dev (Frontend loads)
- [ ] https://dash.luckymifta.dev/health (Returns "Nginx working")
- [ ] https://dash.luckymifta.dev/api/v1/health (API health check)
- [ ] https://dash.luckymifta.dev/user-api/health (User API health)

### 3. SSL Certificate
- [ ] HTTPS works without certificate warnings
- [ ] Certificate is valid and trusted
- [ ] HTTP redirects to HTTPS

### 4. Dashboard Functionality
- [ ] Dashboard loads with data
- [ ] ATM status summary displays
- [ ] Regional data shows correctly
- [ ] Charts and visualizations work
- [ ] No console errors in browser developer tools

## 🔧 Configuration Summary

The deployment will configure:

- **Domain**: `dash.luckymifta.dev`
- **Frontend**: Next.js on port 3000 (via Nginx)
- **Main API**: FastAPI on port 8000 at `/api/*`
- **User API**: FastAPI on port 8001 at `/user-api/*`
- **Database**: `development_db` on localhost (PostgreSQL on VPS)
- **SSL**: Let's Encrypt certificate with auto-renewal
- **Process Manager**: PM2 with auto-startup
- **Web Server**: Nginx with gzip compression and security headers

## 🆘 Need Help?

### Quick Diagnostics
```bash
# Check all services
pm2 status
systemctl status nginx

# View logs
pm2 logs
tail -f /var/log/nginx/error.log

# Test connectivity
curl -I https://dash.luckymifta.dev
curl -I https://dash.luckymifta.dev/api/v1/health
```

### Common Issues
1. **DNS not propagated**: Wait 24-48 hours or use a DNS checker
2. **Firewall blocking**: Check `ufw status` and allow required ports
3. **Database connection**: Verify PostgreSQL is running locally on VPS (`systemctl status postgresql`)
4. **SSL certificate fails**: Ensure domain points to VPS and port 80 is accessible

### Get Support
- Check logs in `/var/log/dash-atm/`
- Review nginx logs in `/var/log/nginx/`
- Test individual components with curl commands
- Restart services if needed: `pm2 restart all && systemctl restart nginx`
