# VPS Deployment Guide - dash.luckymifta.dev

## Quick Start Commands

Copy and paste these commands on your Ubuntu VPS as root:

### 1. Download and Run Deployment Script

```bash
# Download the deployment script
wget https://raw.githubusercontent.com/luckymifta/dash-atm/main/deploy_to_vps.sh

# Make it executable
chmod +x deploy_to_vps.sh

# Run the deployment
./deploy_to_vps.sh
```

### 2. Manual Step-by-Step (Alternative)

If you prefer manual deployment:

#### ⚠️ CRITICAL: Node.js v20 Required for Next.js 15

**Your current Node.js v12.22.9 is incompatible. Upgrade to v20 first:**

```bash
# Check current Node.js version
node --version

# Complete Node.js removal and upgrade (if v12.x.x or lower):
sudo apt remove -y nodejs npm nodejs-doc libnode-dev libnode72
sudo apt autoremove -y
sudo rm -rf /usr/local/bin/npm /usr/local/share/man/man1/node* ~/.npm
sudo rm -rf /usr/local/lib/node* /usr/local/bin/node* /usr/local/include/node*
sudo rm -rf /etc/apt/sources.list.d/nodesource.list*

# Add NodeSource repository and install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt update
sudo apt install -y nodejs

# Install PM2 globally
sudo npm install -g pm2

# Verify successful upgrade
node --version   # Should show v20.19.x
npm --version    # Should show 10.x.x
pm2 --version    # Should show 5.x.x
```

**If you encounter package conflicts, force the installation:**
```bash
# If apt install fails due to conflicts, force it:
sudo dpkg --configure -a
sudo apt --fix-broken install
sudo apt install -y nodejs --fix-missing
```

#### A. Initial Setup
```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y curl wget unzip git nginx python3.11 python3.11-venv python3-pip libpq-dev python3-dev build-essential gcc certbot python3-certbot-nginx ufw

# CRITICAL: Install Node.js 20 (Required for Next.js 15)
# Remove old Node.js if present
apt remove -y nodejs npm
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt install -y nodejs

# Verify Node.js version (should be v20.x.x)
node --version
npm --version

# Install PM2
npm install -g pm2

# Configure firewall
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

#### B. Clone Repository
```bash
mkdir -p /var/www/dash-atm
cd /var/www/dash-atm
git clone https://github.com/luckymifta/dash-atm.git .
```

#### C. Backend Setup
```bash
cd /var/www/dash-atm/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create environment file
cat > .env << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=development_db
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

# CORS Configuration
CORS_ORIGINS=["https://dash.luckymifta.dev", "http://localhost:3000"]
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

#### D. Frontend Setup
```bash
# Exit Python virtual environment (we're done with backend)
deactivate

# Move to frontend directory
cd /var/www/dash-atm/frontend

# Install dependencies
npm install

# Create production environment
cat > .env.production << 'EOF'
# API Configuration
NEXT_PUBLIC_API_BASE_URL=https://dash.luckymifta.dev/api
NEXT_PUBLIC_USER_API_BASE_URL=https://dash.luckymifta.dev/user-api

# Environment
NODE_ENV=production

# NextAuth Configuration
NEXTAUTH_URL=https://dash.luckymifta.dev
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=

# Application Configuration
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF

# Build frontend
NODE_ENV=production npm run build
```

#### E. PM2 Process Management
```bash
cd /var/www/dash-atm

# Create PM2 configuration
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
        PORT: 8000
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/dash-atm/main-api-error.log',
      out_file: '/var/log/dash-atm/main-api-out.log',
      log_file: '/var/log/dash-atm/main-api-combined.log',
      time: true
    },
    {
      name: 'dash-atm-user-api',
      script: '/var/www/dash-atm/backend/venv/bin/python',
      args: '-m uvicorn user_management_api:app --host 0.0.0.0 --port 8001 --workers 2',
      cwd: '/var/www/dash-atm/backend',
      env: {
        NODE_ENV: 'production',
        PORT: 8001
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/dash-atm/user-api-error.log',
      out_file: '/var/log/dash-atm/user-api-out.log',
      log_file: '/var/log/dash-atm/user-api-combined.log',
      time: true
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
      error_file: '/var/log/dash-atm/frontend-error.log',
      out_file: '/var/log/dash-atm/frontend-out.log',
      log_file: '/var/log/dash-atm/frontend-combined.log',
      time: true
    }
  ]
};
EOF

# Create log directory
mkdir -p /var/log/dash-atm
chown -R www-data:www-data /var/log/dash-atm

# Start applications
pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd -u root --hp /root
```

#### F. Nginx Configuration
```bash
# Create Nginx site configuration
cat > /etc/nginx/sites-available/dash.luckymifta.dev << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name dash.luckymifta.dev;

    # Test endpoint
    location /health {
        return 200 "Nginx working\n";
        add_header Content-Type text/plain;
    }

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # User Management API routes (port 8001)
    location /user-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/dash.luckymifta.dev /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
nginx -t
systemctl restart nginx
```

#### G. SSL Certificate Setup
```bash
# Install SSL certificate
certbot --nginx -d dash.luckymifta.dev --non-interactive --agree-tos --email luckymifta.s@gmail.com --redirect
```

## Testing Your Deployment

### 1. Check Services Status
```bash
# Check PM2 processes
pm2 status

# Check Nginx
systemctl status nginx

# Check application logs
pm2 logs dash-atm-main-api --lines 20
pm2 logs dash-atm-user-api --lines 20
pm2 logs dash-atm-frontend --lines 20
```

### 2. Test Endpoints
```bash
# Test health endpoint
curl -I http://localhost/health

# Test main API
curl -I http://localhost:8000/api/v1/health

# Test user API
curl -I http://localhost:8001/health

# Test frontend
curl -I https://dash.luckymifta.dev
```

### 3. Test External Access
Visit these URLs in your browser:
- https://dash.luckymifta.dev (Main application)
- https://dash.luckymifta.dev/health (Health check)
- https://dash.luckymifta.dev/api/v1/health (API health)
- https://dash.luckymifta.dev/user-api/health (User API health)

## Management Commands

### Restart Services
```bash
# Restart all PM2 processes
pm2 restart all

# Restart specific service
pm2 restart dash-atm-main-api
pm2 restart dash-atm-user-api
pm2 restart dash-atm-frontend

# Restart Nginx
systemctl restart nginx
```

### Update Application
```bash
cd /var/www/dash-atm
git pull origin main

# For backend changes
cd backend
source venv/bin/activate
pip install -r requirements.txt
pm2 restart dash-atm-main-api
pm2 restart dash-atm-user-api

# For frontend changes
cd ../frontend
npm install
NODE_ENV=production npm run build
pm2 restart dash-atm-frontend
```

### View Logs
```bash
# PM2 logs
pm2 logs
pm2 logs dash-atm-main-api
pm2 logs dash-atm-user-api
pm2 logs dash-atm-frontend

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Application logs
tail -f /var/log/dash-atm/main-api-combined.log
tail -f /var/log/dash-atm/user-api-combined.log
tail -f /var/log/dash-atm/frontend-combined.log
```

## Troubleshooting

### Critical Fixes Applied

#### 1. Nginx API Routing Fix
**Issue**: API calls failing with 404 errors despite backend running.
**Solution**: Ensure Nginx preserves the `/api` path prefix:
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;  # Include /api/ in proxy_pass
    # ... other settings
}
```

#### 2. PM2 Permission Issues
**Issue**: PM2 processes failing to start or access log files.
**Solution**: 
- Run all PM2 processes under a single user (avoid mixing root/non-root)
- Ensure log directory permissions are correct:
```bash
sudo mkdir -p /var/log/dash-atm
sudo chown -R luckymifta:luckymifta /var/log/dash-atm
```

#### 3. Port 3000 Conflicts
**Issue**: Multiple Next.js processes competing for port 3000.
**Solution**:
- Stop all conflicting processes: `pm2 delete all` then restart properly
- Use `lsof -i :3000` to identify port conflicts
- Ensure only one frontend process runs on port 3000

#### 4. SSL Certificate Email
**Issue**: SSL certificate renewal failures with invalid email.
**Solution**: Use a real, monitored email address:
```bash
sudo certbot --nginx -d yourdomain.com --email luckymifta.s@gmail.com --agree-tos --non-interactive
```

### Common Issues

1. **Port conflicts**: Make sure ports 80, 443, 3000, 8000, 8001 are available
2. **Database connection**: Verify that PostgreSQL is running on the VPS (`systemctl status postgresql`)
3. **Domain DNS**: Ensure dash.luckymifta.dev points to your VPS IP (88.222.214.26)
4. **Firewall**: Check UFW status with `ufw status`
5. **SSL issues**: Use `certbot certificates` to check certificate status
6. **Node.js version**: Ensure Node.js v20+ is installed (required for Next.js 15)

### Debugging Commands

```bash
# Check service status
pm2 status
systemctl status nginx postgresql

# Check port usage
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :8001

# Check logs
pm2 logs --lines 50
tail -f /var/log/nginx/error.log

# Test connectivity
curl -v http://localhost:3000
curl -v http://localhost:8000/api/v1/health
curl -v http://localhost:8001/health

# Check SSL certificate
sudo certbot certificates
```

### Service Recovery

If services are down, follow this recovery sequence:

```bash
# 1. Stop all services
pm2 delete all
sudo systemctl stop nginx

# 2. Check for port conflicts
sudo lsof -i :3000 :8000 :8001
# Kill any conflicting processes if found

# 3. Restart services in order
cd /var/www/dash-atm
pm2 start ecosystem.config.js
sudo systemctl start nginx

# 4. Verify services
pm2 status
curl -I https://dash.luckymifta.dev/health
```

### Quick Health Check Script
```bash
# Create a health check script
cat > /var/www/dash-atm/health_check.sh << 'EOF'
#!/bin/bash
echo "=== ATM Dashboard Health Check ==="
echo "PM2 Status:"
pm2 status | grep -E "(online|stopped|errored)"
echo ""
echo "Service Tests:"
curl -s -o /dev/null -w "Health endpoint: %{http_code}\n" http://localhost/health
curl -s -o /dev/null -w "Main API: %{http_code}\n" http://localhost:8000/api/v1/health
curl -s -o /dev/null -w "User API: %{http_code}\n" http://localhost:8001/health
curl -s -o /dev/null -w "Frontend: %{http_code}\n" https://dash.luckymifta.dev
echo ""
echo "Disk usage:"
df -h /var/www/dash-atm
echo ""
echo "Memory usage:"
pm2 monit
EOF

chmod +x /var/www/dash-atm/health_check.sh
```

Run health check: `/var/www/dash-atm/health_check.sh`

## Success Verification

### Expected API Responses

Once deployment is successful, these endpoints should return the following:

#### 1. Health Check Endpoint
```bash
curl https://dash.luckymifta.dev/health
# Expected: "Nginx working"
```

#### 2. Main API Health
```bash
curl https://dash.luckymifta.dev/api/v1/health
# Expected JSON:
{
  "status": "healthy",
  "environment": "production",
  "database_connected": true,
  "timestamp": "2024-12-19T09:15:30.123456"
}
```

#### 3. User API Health
```bash
curl https://dash.luckymifta.dev/user-api/health
# Expected JSON:
{
  "status": "healthy",
  "service": "user-management",
  "database_connected": true
}
```

#### 4. ATM Status Data (Sample)
```bash
curl https://dash.luckymifta.dev/api/v1/atm-status
# Expected: Array of ATM data with 40+ entries, example:
[
  {
    "terminal_id": "BNU001",
    "terminal_name": "BNU COMORO",
    "bank": "BNU",
    "location": "COMORO",
    "status": "Online",
    "availability_percentage": 95.5,
    "last_transaction": "2024-12-19T08:45:00Z"
  }
  // ... more entries
]
```

### Performance Indicators

A successful deployment should show:

1. **PM2 Status**: All 3 processes online
```bash
pm2 status
# Expected:
# ┌─────┬────────────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
# │ id  │ name                   │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
# ├─────┼────────────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
# │ 0   │ dash-atm-main-api      │ default     │ N/A     │ fork    │ 12345    │ 5m     │ 0    │ online    │ 0%       │ 45.2mb   │ root     │ disabled │
# │ 1   │ dash-atm-user-api      │ default     │ N/A     │ fork    │ 12346    │ 5m     │ 0    │ online    │ 0%       │ 32.1mb   │ root     │ disabled │
# │ 2   │ dash-atm-frontend      │ default     │ N/A     │ fork    │ 12347    │ 5m     │ 0    │ online    │ 0%       │ 98.5mb   │ root     │ disabled │
# └─────┴────────────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
```

2. **SSL Certificate**: Valid and auto-renewing
```bash
sudo certbot certificates
# Expected: Certificate valid for 90 days, auto-renewal enabled
```

3. **Database Connectivity**: 
   - Main API shows `database_connected: true`
   - ATM status endpoint returns real data (40+ records)
   - Average availability percentage around 90%+

4. **Dashboard Features**:
   - Login/authentication working
   - Real-time ATM status display
   - "API Connected" status indicator
   - Bank filtering (BNU, BNCTL, Mandiri)
   - Location-based status tracking

### Final Deployment Checklist

- [ ] All PM2 processes online and stable
- [ ] HTTPS working with valid SSL certificate
- [ ] API endpoints returning expected JSON responses
- [ ] Frontend loading at https://dash.luckymifta.dev
- [ ] Database connectivity confirmed
- [ ] Real ATM data displaying (40+ records)
- [ ] Authentication system functional
- [ ] Nginx logs showing successful requests
- [ ] No critical errors in PM2 logs
- [ ] SSL certificate auto-renewal configured

### Expected Data Volume

A successful deployment will show:
- **ATM Count**: 40+ terminals across Timor-Leste
- **Banks**: BNU, BNCTL, Mandiri
- **Availability**: 85-95% average
- **Locations**: Dili, Baucau, Maliana, etc.
- **Update Frequency**: Real-time status updates

Your ATM monitoring dashboard is now successfully deployed and operational! 🎉
