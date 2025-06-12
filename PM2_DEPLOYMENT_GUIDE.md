# 🚀 PM2 Deployment Guide for ATM Dashboard

## 📋 Overview
This guide provides comprehensive step-by-step instructions for deploying the ATM Dashboard application using PM2 (Process Manager 2) as the process manager. PM2 ensures your applications run continuously, restart automatically on failure, and provide excellent monitoring capabilities.

## 🎯 Prerequisites
- Ubuntu VPS with sudo access
- Node.js v20.x installed
- Python 3.11+ with virtual environment
- PostgreSQL database running
- Domain configured (staging.luckymifta.dev)
- Application already cloned to `/var/www/dash-atm`

---

## 🔧 Phase 1: PM2 Installation and Setup

### 1.1 Install PM2 Globally
```bash
# Install PM2 globally with npm
sudo npm install -g pm2

# Verify installation
pm2 --version

# Update PM2 to latest version (if needed)
sudo npm update -g pm2
```

### 1.2 Verify System Requirements
```bash
# Check Node.js version (should be v20.x)
node --version

# Check npm version
npm --version

# Check Python version
python3 --version

# Check if application directory exists
ls -la /var/www/dash-atm
```

---

## 🏗️ Phase 2: Application Environment Setup

### 2.1 Backend Environment Configuration
```bash
cd /var/www/dash-atm/backend

# Ensure virtual environment is activated
source venv/bin/activate

# Verify environment file exists
ls -la .env

# If .env doesn't exist, create it
cat > .env << 'EOF'
# Production Environment Configuration for ATM Dashboard

# Database Configuration (PostgreSQL on VPS)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dash
DB_USER=timlesdev
DB_PASSWORD=timlesdev

# FastAPI Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_WORKERS=4

# User Management API Configuration
USER_API_HOST=0.0.0.0
USER_API_PORT=8001
USER_API_WORKERS=2

# CORS Configuration for Production
CORS_ORIGINS=["https://staging.luckymifta.dev", "http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# Security Settings
SECRET_KEY=2QNQK08xRdLElX4hT6zy61AqKdUFcGMT+r+XCzSEJIUV/WQYNcls8SBD3P8TKlqmG7pcl+VdwDhHU122/pbG7A==
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=
ENVIRONMENT=production

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/dash-atm/app.log
EOF
```

### 2.2 Frontend Environment Configuration
```bash
cd /var/www/dash-atm/frontend

# Generate secure NEXTAUTH_SECRET
NEXTAUTH_SECRET=$(openssl rand -base64 32)

# Create production environment file
cat > .env.production << EOF
# Production Environment Configuration for Frontend
# API Configuration - Production HTTPS URLs
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api/v1
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api

# Environment
NODE_ENV=production

# NextAuth Configuration
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=$NEXTAUTH_SECRET

# Application Configuration
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF

echo "Generated NEXTAUTH_SECRET: $NEXTAUTH_SECRET"
```

### 2.3 Build Frontend Application
```bash
cd /var/www/dash-atm/frontend

# Install dependencies if needed
npm install

# Clear previous build cache
rm -rf .next
rm -rf node_modules/.cache

# Build for production
NODE_ENV=production npm run build

# Verify build success
ls -la .next
```

---

## ⚙️ Phase 3: PM2 Configuration

### 3.1 Create PM2 Ecosystem Configuration
```bash
cd /var/www/dash-atm

# Create comprehensive PM2 configuration file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'dash-atm-main-api',
      script: '/var/www/dash-atm/backend/venv/bin/python',
      args: '-m uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000 --workers 4',
      cwd: '/var/www/dash-atm/backend',
      env: {
        NODE_ENV: 'production',
        PORT: 8000,
        PYTHONPATH: '/var/www/dash-atm/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      error_file: '/var/log/dash-atm/main-api-error.log',
      out_file: '/var/log/dash-atm/main-api-out.log',
      log_file: '/var/log/dash-atm/main-api-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'dash-atm-user-api',
      script: '/var/www/dash-atm/backend/venv/bin/python',
      args: '-m uvicorn user_management_api:app --host 0.0.0.0 --port 8001 --workers 2',
      cwd: '/var/www/dash-atm/backend',
      env: {
        NODE_ENV: 'production',
        PORT: 8001,
        PYTHONPATH: '/var/www/dash-atm/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      error_file: '/var/log/dash-atm/user-api-error.log',
      out_file: '/var/log/dash-atm/user-api-out.log',
      log_file: '/var/log/dash-atm/user-api-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'dash-atm-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/var/www/dash-atm/frontend',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      error_file: '/var/log/dash-atm/frontend-error.log',
      out_file: '/var/log/dash-atm/frontend-out.log',
      log_file: '/var/log/dash-atm/frontend-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
EOF

echo "✅ PM2 ecosystem configuration created"
```

### 3.2 Create Log Directory and Set Permissions
```bash
# Create log directory
sudo mkdir -p /var/log/dash-atm

# Set proper ownership and permissions
sudo chown -R www-data:www-data /var/log/dash-atm
sudo chmod -R 755 /var/log/dash-atm

# Set application directory permissions
sudo chown -R www-data:www-data /var/www/dash-atm
sudo chmod -R 755 /var/www/dash-atm

# Set specific permissions for environment files
sudo chmod 644 /var/www/dash-atm/backend/.env
sudo chmod 644 /var/www/dash-atm/frontend/.env.production

echo "✅ Permissions configured"
```

---

## 🚀 Phase 4: Starting Applications with PM2

### 4.1 Start All Applications
```bash
cd /var/www/dash-atm

# Start all applications using the ecosystem file
pm2 start ecosystem.config.js

# Wait a moment for startup
sleep 5

# Check status of all processes
pm2 status

# View startup logs
pm2 logs --lines 50
```

### 4.2 Save PM2 Configuration
```bash
# Save current PM2 process list for auto-restart
pm2 save

# Generate startup script (run the command it outputs)
pm2 startup

echo "✅ PM2 configuration saved and startup configured"
```

### 4.3 Verify Application Health
```bash
# Test main API health
curl -s http://localhost:8000/api/v1/health | jq .

# Test user API health
curl -s http://localhost:8001/health | jq .

# Test frontend (should return HTML)
curl -s -I http://localhost:3000

# Check if all ports are listening
sudo netstat -tlnp | grep -E ':(3000|8000|8001)'

echo "✅ Application health checks completed"
```

---

## 📊 Phase 5: PM2 Monitoring and Management

### 5.1 Basic PM2 Commands
```bash
# View all processes
pm2 list
pm2 status

# View specific process logs
pm2 logs dash-atm-main-api
pm2 logs dash-atm-user-api
pm2 logs dash-atm-frontend

# View logs with lines limit
pm2 logs --lines 100

# Clear all logs
pm2 flush

# Real-time monitoring
pm2 monit
```

### 5.2 Process Management Commands
```bash
# Restart all processes
pm2 restart all

# Restart specific process
pm2 restart dash-atm-main-api
pm2 restart dash-atm-user-api
pm2 restart dash-atm-frontend

# Stop all processes
pm2 stop all

# Stop specific process
pm2 stop dash-atm-main-api

# Delete a process
pm2 delete dash-atm-main-api

# Reload all processes (0-downtime restart)
pm2 reload all
```

### 5.3 Advanced Monitoring
```bash
# View detailed process information
pm2 describe dash-atm-main-api

# Show process statistics
pm2 show dash-atm-main-api

# View process logs in real-time
pm2 logs dash-atm-main-api --follow

# Memory usage monitoring
pm2 list --watch

# CPU and memory monitoring
pm2 monit
```

---

## 🔄 Phase 6: Application Updates and Deployment

### 6.1 Backend Updates
```bash
cd /var/www/dash-atm

# Pull latest changes
git pull origin main

# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate

# Update dependencies if requirements.txt changed
pip install -r requirements.txt

# Restart backend services
pm2 restart dash-atm-main-api
pm2 restart dash-atm-user-api

# Verify services are running
pm2 status
```

### 6.2 Frontend Updates
```bash
cd /var/www/dash-atm/frontend

# Install new dependencies if package.json changed
npm install

# Clear build cache
rm -rf .next
rm -rf node_modules/.cache

# Rebuild application
NODE_ENV=production npm run build

# Restart frontend service
pm2 restart dash-atm-frontend

# Verify service is running
pm2 status
```

### 6.3 Full Application Update
```bash
cd /var/www/dash-atm

# Stop all services
pm2 stop all

# Pull latest code
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Update frontend
cd ../frontend
npm install
NODE_ENV=production npm run build

# Restart all services
cd ..
pm2 restart all

# Check status
pm2 status
pm2 logs --lines 20
```

---

## 🛡️ Phase 7: PM2 Security and Best Practices

### 7.1 Security Configuration
```bash
# Set PM2 to run as www-data user
sudo pm2 startup systemd -u www-data --hp /var/www

# Update ecosystem file with security settings
cat >> ecosystem.config.js << 'EOF'

// Security and performance optimizations
const commonConfig = {
  autorestart: true,
  max_memory_restart: '1G',
  min_uptime: '10s',
  max_restarts: 10,
  restart_delay: 4000,
  kill_timeout: 10000,
  listen_timeout: 8000,
  exp_backoff_restart_delay: 100
};
EOF
```

### 7.2 Log Rotation Setup
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/dash-atm << 'EOF'
/var/log/dash-atm/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        pm2 reloadLogs
    endscript
}
EOF

# Test logrotate configuration
sudo logrotate -d /etc/logrotate.d/dash-atm
```

### 7.3 PM2 Configuration Backup
```bash
# Create PM2 configuration backup
mkdir -p /var/www/dash-atm/config-backup

# Backup PM2 dump
pm2 save
cp ~/.pm2/dump.pm2 /var/www/dash-atm/config-backup/

# Backup ecosystem configuration
cp /var/www/dash-atm/ecosystem.config.js /var/www/dash-atm/config-backup/

echo "✅ PM2 configuration backed up"
```

---

## 🔍 Phase 8: Health Checks and Verification

### 8.1 Automated Health Check Script
```bash
# Create health check script
cat > /var/www/dash-atm/health-check.sh << 'EOF'
#!/bin/bash

echo "=== ATM Dashboard Health Check ==="
echo "Timestamp: $(date)"
echo

# Check PM2 status
echo "📊 PM2 Process Status:"
pm2 jlist | jq -r '.[] | "\(.name): \(.pm2_env.status) (PID: \(.pid), Memory: \(.monit.memory / 1024 / 1024 | floor)MB, CPU: \(.monit.cpu)%)"'
echo

# Check API endpoints
echo "🔍 API Health Checks:"

# Main API health check
MAIN_API=$(curl -s -w "%{http_code}" http://localhost:8000/api/v1/health -o /dev/null)
if [ "$MAIN_API" = "200" ]; then
    echo "✅ Main API: Healthy (HTTP $MAIN_API)"
else
    echo "❌ Main API: Failed (HTTP $MAIN_API)"
fi

# User API health check
USER_API=$(curl -s -w "%{http_code}" http://localhost:8001/health -o /dev/null)
if [ "$USER_API" = "200" ]; then
    echo "✅ User API: Healthy (HTTP $USER_API)"
else
    echo "❌ User API: Failed (HTTP $USER_API)"
fi

# Frontend health check
FRONTEND=$(curl -s -w "%{http_code}" http://localhost:3000 -o /dev/null)
if [ "$FRONTEND" = "200" ]; then
    echo "✅ Frontend: Healthy (HTTP $FRONTEND)"
else
    echo "❌ Frontend: Failed (HTTP $FRONTEND)"
fi

echo
echo "📈 System Resources:"
echo "Memory Usage: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk Usage: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"

echo
echo "=== Health Check Complete ==="
EOF

# Make health check script executable
chmod +x /var/www/dash-atm/health-check.sh

# Run health check
/var/www/dash-atm/health-check.sh
```

### 8.2 Performance Monitoring
```bash
# Create performance monitoring script
cat > /var/www/dash-atm/performance-monitor.sh << 'EOF'
#!/bin/bash

echo "=== Performance Monitor ==="
echo "Timestamp: $(date)"

# PM2 process information
pm2 describe dash-atm-main-api | grep -E "(cpu|memory|uptime|restart)"
pm2 describe dash-atm-user-api | grep -E "(cpu|memory|uptime|restart)"
pm2 describe dash-atm-frontend | grep -E "(cpu|memory|uptime|restart)"

# Response time check
echo "API Response Times:"
time curl -s http://localhost:8000/api/v1/health > /dev/null
time curl -s http://localhost:8001/health > /dev/null
EOF

chmod +x /var/www/dash-atm/performance-monitor.sh
```

---

## 🚨 Phase 9: Troubleshooting and Emergency Procedures

### 9.1 Common Issues and Solutions

#### Application Won't Start
```bash
# Check PM2 logs for errors
pm2 logs dash-atm-main-api --lines 50

# Check if ports are already in use
sudo netstat -tlnp | grep -E ':(3000|8000|8001)'

# Check virtual environment
cd /var/www/dash-atm/backend
source venv/bin/activate
which python
python --version

# Verify environment files exist
ls -la .env
ls -la ../frontend/.env.production
```

#### High Memory Usage
```bash
# Check memory usage
pm2 monit

# Restart memory-heavy processes
pm2 restart dash-atm-main-api

# Set memory limits in ecosystem.config.js
# max_memory_restart: '500M'  # Adjust as needed
```

#### Database Connection Issues
```bash
# Test database connectivity
cd /var/www/dash-atm/backend
source venv/bin/activate
python -c "
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://timlesdev:timlesdev@localhost:5432/dash')
        result = await conn.fetchval('SELECT 1')
        print('✅ Database connection successful')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"
```

### 9.2 Emergency Recovery Procedures

#### Complete Service Recovery
```bash
# Stop all services
pm2 kill

# Remove PM2 processes
pm2 delete all

# Restart from ecosystem config
cd /var/www/dash-atm
pm2 start ecosystem.config.js

# Save new configuration
pm2 save
```

#### Rollback to Previous Version
```bash
# Stop services
pm2 stop all

# Show git history
git log --oneline -10

# Rollback to previous commit
git checkout <previous-commit-hash>

# Rebuild frontend
cd frontend
rm -rf .next
NODE_ENV=production npm run build

# Restart services
cd ..
pm2 restart all
```

### 9.3 Log Analysis
```bash
# Check for specific errors
pm2 logs | grep -i error

# Monitor real-time logs
pm2 logs --follow

# Check Nginx logs (if applicable)
sudo tail -f /var/log/nginx/error.log

# Search for specific patterns in logs
pm2 logs dash-atm-main-api | grep -i "database\|connection\|error"
```

---

## 📋 Phase 10: Maintenance and Best Practices

### 10.1 Regular Maintenance Tasks

#### Daily Tasks
```bash
# Check process status
pm2 status

# Quick health check
/var/www/dash-atm/health-check.sh

# Check log file sizes
du -sh /var/log/dash-atm/*
```

#### Weekly Tasks
```bash
# Update application
cd /var/www/dash-atm
git pull origin main

# Check for security updates
sudo apt update && sudo apt list --upgradable

# Rotate logs manually if needed
sudo logrotate -f /etc/logrotate.d/dash-atm

# Backup PM2 configuration
pm2 save
```

#### Monthly Tasks
```bash
# Update Node.js and npm if needed
sudo npm update -g pm2

# Review and analyze log files
pm2 logs --lines 1000 | grep -i error > error-analysis.log

# Performance review
/var/www/dash-atm/performance-monitor.sh
```

### 10.2 Performance Optimization

#### PM2 Configuration Tuning
```javascript
// Add to ecosystem.config.js for production optimization
module.exports = {
  apps: [
    {
      // ... existing config
      node_args: '--max-old-space-size=1024',
      instance_var: 'INSTANCE_ID',
      watch_delay: 1000,
      ignore_watch: [
        'node_modules',
        '.git',
        '*.log'
      ],
      env_production: {
        NODE_ENV: 'production',
        NODE_OPTIONS: '--max-old-space-size=1024'
      }
    }
  ]
};
```

#### Resource Monitoring
```bash
# Set up monitoring alerts (optional)
cat > /var/www/dash-atm/resource-alert.sh << 'EOF'
#!/bin/bash

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "⚠️ High memory usage: ${MEM_USAGE}%"
    pm2 restart all
fi

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️ High disk usage: ${DISK_USAGE}%"
    pm2 flush  # Clear logs
fi
EOF

chmod +x /var/www/dash-atm/resource-alert.sh
```

---

## ✅ Deployment Success Checklist

### Pre-Deployment Verification
- [ ] Node.js v20.x installed
- [ ] PM2 installed globally
- [ ] Python virtual environment created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Environment files configured
- [ ] Database connectivity verified

### PM2 Configuration
- [ ] ecosystem.config.js created
- [ ] Log directory created with proper permissions
- [ ] Application directories have correct ownership
- [ ] PM2 startup script configured

### Service Verification
- [ ] All PM2 processes show "online" status
- [ ] Main API responds at http://localhost:8000/api/v1/health
- [ ] User API responds at http://localhost:8001/health
- [ ] Frontend serves at http://localhost:3000
- [ ] No critical errors in PM2 logs

### Production Readiness
- [ ] PM2 configuration saved
- [ ] Startup script configured for auto-restart
- [ ] Log rotation configured
- [ ] Health check script functional
- [ ] Nginx reverse proxy configured (if needed)
- [ ] SSL certificate configured (if needed)

---

## 📞 Support and Additional Resources

### Quick Command Reference
```bash
# Essential PM2 commands
pm2 status                    # Check all processes
pm2 logs                      # View all logs
pm2 restart all               # Restart all processes
pm2 stop all                  # Stop all processes
pm2 reload all                # Zero-downtime restart
pm2 monit                     # Real-time monitoring

# Health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/health
curl http://localhost:3000

# Log management
pm2 logs --lines 100          # View recent logs
pm2 flush                     # Clear all logs
pm2 reloadLogs                # Reload log files
```

### Emergency Contact Commands
```bash
# Stop everything
pm2 kill

# Start fresh
cd /var/www/dash-atm && pm2 start ecosystem.config.js

# Check system resources
free -h && df -h && pm2 status
```

---

**🎉 Congratulations!** Your ATM Dashboard is now successfully deployed with PM2 process management. The application will automatically restart on failure, provide detailed logging, and can be easily monitored and managed through PM2's comprehensive toolset.

For ongoing support, refer to the troubleshooting section or run the health check script regularly to ensure optimal performance.
