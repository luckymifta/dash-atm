# ATM Dashboard v2.0 Production Deployment Checklist

## 🚀 Pre-Deployment Requirements

### System Requirements
- [ ] Ubuntu 18.04+ or Ubuntu 20.04+ VPS
- [ ] Minimum 2GB RAM, 2 CPU cores
- [ ] 20GB+ disk space
- [ ] PostgreSQL database access (external)
- [ ] Domain name configured (staging.luckymifta.dev)
- [ ] SSL certificate ready (Let's Encrypt)

### Security Requirements
- [ ] Strong SSH key authentication
- [ ] Firewall configured (UFW)
- [ ] Non-root user with sudo privileges
- [ ] Database credentials secured
- [ ] JWT secret key generated

## 📦 Deployment Steps

### 1. Prepare VPS Environment
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Create deployment user if needed
sudo adduser deploy
sudo usermod -aG sudo deploy
```

### 2. Clone Repository
```bash
cd /tmp
git clone https://github.com/yourusername/dash-atm.git
sudo mv dash-atm /var/www/
sudo chown -R $USER:www-data /var/www/dash-atm
```

### 3. Run Deployment Script
```bash
cd /var/www/dash-atm
chmod +x deploy_production_v2.sh
./deploy_production_v2.sh
```

### 4. Configure Environment Variables

#### Backend Environment (.env)
```bash
cd /var/www/dash-atm/backend
sudo nano .env
```

**Required Changes:**
- [ ] `SECRET_KEY=` - Generate strong 32+ character secret
- [ ] `POSTGRES_HOST=` - Verify database host
- [ ] `POSTGRES_PASSWORD=` - Verify database password
- [ ] `CORS_ORIGINS=` - Update with your domain

#### Frontend Environment
```bash
cd /var/www/dash-atm/frontend
sudo nano .env.production
```

**Required Changes:**
- [ ] `NEXT_PUBLIC_USER_API_BASE_URL=` - Update with your domain

### 5. Database Setup
```bash
# Test database connection
psql -h 88.222.214.26 -U timlesdev -d development_db

# Verify required tables exist:
# - users
# - user_sessions  
# - user_audit_log
```

### 6. SSL Certificate Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate SSL certificate
sudo certbot --nginx -d staging.luckymifta.dev

# Test auto-renewal
sudo certbot renew --dry-run
```

### 7. Service Configuration

#### Start and Enable Services
```bash
# User Management API
sudo systemctl start atm-user-api
sudo systemctl enable atm-user-api
sudo systemctl status atm-user-api

# ATM Data API (if available)
sudo systemctl start atm-api
sudo systemctl enable atm-api
```

#### Frontend with PM2
```bash
cd /var/www/dash-atm/frontend
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 8. Nginx Configuration
```bash
# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Enable nginx
sudo systemctl enable nginx
```

### 9. Firewall Setup
```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## ✅ Post-Deployment Verification

### 1. Service Health Checks
```bash
# Run status check script
atm-dashboard-status

# Check individual services
systemctl status atm-user-api
systemctl status nginx
pm2 status
```

### 2. API Testing
```bash
# Test User Management API
curl -X GET https://staging.luckymifta.dev/user-api/

# Test API connectivity
curl -X POST https://staging.luckymifta.dev/user-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. Frontend Access
- [ ] Visit https://staging.luckymifta.dev
- [ ] Login with default admin credentials
- [ ] Test user management features
- [ ] Test audit log functionality
- [ ] Verify role-based access control

### 4. Security Verification
- [ ] Default admin password changed
- [ ] SSL certificate working
- [ ] HTTP redirects to HTTPS
- [ ] CORS headers configured
- [ ] Security headers present

## 🔧 Maintenance Commands

### Logs and Monitoring
```bash
# View API logs
sudo journalctl -f -u atm-user-api

# View frontend logs
pm2 logs atm-dashboard-frontend

# View nginx logs
sudo tail -f /var/log/nginx/atm-dashboard.access.log
sudo tail -f /var/log/nginx/atm-dashboard.error.log

# System status
atm-dashboard-status
```

### Service Management
```bash
# Restart services
sudo systemctl restart atm-user-api
pm2 restart atm-dashboard-frontend
sudo systemctl restart nginx

# Update application
cd /var/www/dash-atm
git pull origin main
cd backend && source venv/bin/activate && pip install -r requirements_fastapi.txt
cd ../frontend && npm install && npm run build
pm2 restart atm-dashboard-frontend
sudo systemctl restart atm-user-api
```

### Database Maintenance
```bash
# Backup audit logs
pg_dump -h 88.222.214.26 -U timlesdev -d development_db -t user_audit_log > audit_backup.sql

# Monitor database connections
psql -h 88.222.214.26 -U timlesdev -d development_db -c "SELECT * FROM pg_stat_activity;"
```

## 🚨 Troubleshooting

### Common Issues

#### User API Not Starting
```bash
# Check logs
sudo journalctl -u atm-user-api -n 50

# Check port availability
sudo netstat -tlnp | grep 8001

# Test database connection
cd /var/www/dash-atm/backend
source venv/bin/activate
python -c "import psycopg2; conn = psycopg2.connect(host='88.222.214.26', database='development_db', user='timlesdev', password='timlesdev'); print('Connected!')"
```

#### Frontend Build Issues
```bash
# Check Node.js version
node --version  # Should be 18.x

# Clear cache and rebuild
cd /var/www/dash-atm/frontend
rm -rf .next node_modules
npm install
npm run build
```

#### SSL Certificate Issues
```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

### Emergency Rollback
```bash
# Stop services
pm2 stop atm-dashboard-frontend
sudo systemctl stop atm-user-api

# Restore from backup (if needed)
# git checkout previous-working-commit

# Restart services
sudo systemctl start atm-user-api
pm2 start atm-dashboard-frontend
```

## 📊 Monitoring Endpoints

### Health Checks
- User API Health: `https://staging.luckymifta.dev/user-api/docs`
- Frontend: `https://staging.luckymifta.dev`
- Nginx Status: `sudo systemctl status nginx`

### Performance Monitoring
- PM2 Monitoring: `pm2 monit`
- System Resources: `htop`
- Disk Usage: `df -h`
- Memory Usage: `free -h`

## 🔐 Security Hardening Completed

- [x] Firewall configured (UFW)
- [x] SSL/TLS encryption enabled
- [x] Security headers configured
- [x] Service user isolation (www-data)
- [x] File permissions secured
- [x] Database connection encrypted
- [x] JWT token authentication
- [x] CORS properly configured
- [x] Audit logging enabled
- [x] Session management implemented

## 📝 Default Credentials (CHANGE IMMEDIATELY)

**Default Admin User:**
- Username: `admin`
- Password: `admin123`
- Role: `super_admin`

**⚠️ SECURITY WARNING: Change this password immediately after first login!**

## 🎯 Success Criteria

Your deployment is successful when:
- [x] All services are running (green status)
- [x] HTTPS website accessible
- [x] User authentication working
- [x] Audit logs capturing events
- [x] Role-based access control functional
- [x] Default admin password changed
- [x] SSL certificate valid
- [x] No security vulnerabilities detected
