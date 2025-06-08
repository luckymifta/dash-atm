# VPS Deployment Summary - Updated for Local Database

## 🎯 Deployment Configuration

**VPS IP**: `88.222.214.26`  
**Domain**: `dash.luckymifta.dev`  
**Database**: PostgreSQL on localhost (same VPS)  
**Database Name**: `development_db`  

## 🚀 Quick Deployment Commands

SSH to your VPS and run these commands:

### Option 1: Automated Deployment (Recommended)
```bash
# Download and run the deployment script
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_to_vps.sh
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh
```

### Option 2: Test Database First (Optional)
```bash
# Test PostgreSQL setup before deployment
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/test_vps_database.sh
chmod +x test_vps_database.sh
./test_vps_database.sh
```

## 📋 Pre-Deployment Checklist

Before running the deployment, ensure:

1. **Domain DNS**: `dash.luckymifta.dev` points to `88.222.214.26`
2. **VPS Access**: SSH access as root to `88.222.214.26`
3. **PostgreSQL**: Running on the VPS (will be verified/configured by script)
4. **Ports**: 80, 443, 3000, 8000, 8001 available

## 🔧 What Gets Deployed

### Services Configuration
- **Frontend**: Next.js on port 3000
- **Main API**: FastAPI on port 8000 (handles ATM data)
- **User API**: FastAPI on port 8001 (handles authentication)
- **Database**: PostgreSQL on localhost:5432
- **Web Server**: Nginx with SSL (Let's Encrypt)

### Process Management
All services managed by PM2:
- `dash-atm-frontend`
- `dash-atm-main-api` 
- `dash-atm-user-api`

### Database Configuration
```bash
# Local connection on VPS
DB_HOST=localhost
DB_PORT=5432
DB_NAME=development_db
DB_USER=timlesdev
DB_PASSWORD=timlesdev
```

## 🌐 Application URLs (After Deployment)

- **Main Dashboard**: https://dash.luckymifta.dev
- **Health Check**: https://dash.luckymifta.dev/health
- **API Health**: https://dash.luckymifta.dev/api/v1/health
- **User API Health**: https://dash.luckymifta.dev/user-api/health

## 🔍 Post-Deployment Verification

### 1. Check Services
```bash
# Check PM2 processes
pm2 status

# Check Nginx
systemctl status nginx

# Check PostgreSQL
systemctl status postgresql
```

### 2. Test Endpoints
```bash
# Test health endpoint
curl -I https://dash.luckymifta.dev/health

# Test main API
curl -I https://dash.luckymifta.dev/api/v1/health

# Test user API  
curl -I https://dash.luckymifta.dev/user-api/health
```

### 3. Database Connection Test
```bash
# Run the database test script
./test_vps_database.sh
```

## 🛠️ Management Commands

### Restart Services
```bash
pm2 restart all                    # Restart all services
pm2 restart dash-atm-frontend      # Frontend only
pm2 restart dash-atm-main-api      # Main API only
pm2 restart dash-atm-user-api      # User API only
systemctl restart nginx            # Restart Nginx
```

### View Logs
```bash
pm2 logs                           # All PM2 logs
pm2 logs dash-atm-main-api         # Main API logs
tail -f /var/log/nginx/error.log   # Nginx error logs
```

### Update Application
```bash
cd /var/www/dash-atm
git pull origin main

# Rebuild frontend
cd frontend
NODE_ENV=production npm run build
pm2 restart dash-atm-frontend

# Restart backend APIs
pm2 restart dash-atm-main-api
pm2 restart dash-atm-user-api
```

## 🔒 Security Features

- **SSL Certificate**: Let's Encrypt with auto-renewal
- **Firewall**: UFW configured for essential ports only
- **Process Isolation**: Each service runs in its own PM2 process
- **Secure Headers**: Nginx configured with security headers
- **Database Security**: Local PostgreSQL connection (no external exposure)

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection**: Use `./test_vps_database.sh` to diagnose
2. **Domain Not Working**: Check DNS propagation with `nslookup dash.luckymifta.dev`
3. **SSL Issues**: Check certificate with `certbot certificates`
4. **Service Down**: Check with `pm2 status` and restart if needed

### Quick Health Check
```bash
# Create and run health check
cat > /tmp/health_check.sh << 'EOF'
#!/bin/bash
echo "=== ATM Dashboard Health Check ==="
echo "Services:"
pm2 list | grep -E "(online|stopped|errored)"
echo "Database:"
systemctl is-active postgresql
echo "Web Server:"
systemctl is-active nginx
echo "Endpoints:"
curl -s -o /dev/null -w "Frontend: %{http_code}\n" https://dash.luckymifta.dev
curl -s -o /dev/null -w "API: %{http_code}\n" https://dash.luckymifta.dev/api/v1/health
EOF
chmod +x /tmp/health_check.sh
/tmp/health_check.sh
```

## 📊 Expected Results

After successful deployment:

1. ✅ **Website Live**: https://dash.luckymifta.dev loads the ATM dashboard
2. ✅ **SSL Active**: Green lock icon in browser
3. ✅ **Data Loading**: Dashboard shows ATM status data from your database
4. ✅ **APIs Working**: All health endpoints return 200 OK
5. ✅ **Auto-Startup**: Services restart automatically if VPS reboots

## 🎉 You're Ready!

Your VPS deployment is configured to use the local PostgreSQL database on the same server, which is more efficient and secure than external database connections.

**Next Step**: SSH to your VPS at `88.222.214.26` and run the deployment script!
