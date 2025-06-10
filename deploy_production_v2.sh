#!/bin/bash

# ATM Dashboard Production Deployment Script with Audit Log System
# This script deploys the complete ATM Dashboard system to Ubuntu VPS
# Version: 2.0.0 - With User Management and Audit Logs

set -e

echo "🚀 Starting ATM Dashboard Production Deployment (v2.0.0)"
echo "=================================================="

# Configuration
PROJECT_DIR="/var/www/dash-atm"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
LOG_DIR="/var/log/atm-dashboard"
NGINX_CONF="/etc/nginx/sites-available/atm-dashboard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

print_status "Step 1: Creating directories and setting permissions"
sudo mkdir -p ${PROJECT_DIR}
sudo mkdir -p ${LOG_DIR}
sudo chown -R $USER:www-data ${PROJECT_DIR}
sudo chown -R $USER:www-data ${LOG_DIR}
sudo chmod -R 755 ${PROJECT_DIR}
sudo chmod -R 755 ${LOG_DIR}

print_status "Step 2: Installing system dependencies"
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    postgresql-client \
    nginx \
    nodejs \
    npm \
    supervisor \
    git \
    curl \
    htop

print_status "Step 3: Setting up Python virtual environment"
cd ${BACKEND_DIR}
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

print_status "Step 4: Installing Python dependencies"
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_fastapi.txt

# Install additional dependencies for user management API
pip install \
    bcrypt==4.0.1 \
    python-jose[cryptography]==3.3.0 \
    python-multipart==0.0.6 \
    passlib[bcrypt]==1.7.4 \
    pydantic[email]==2.5.0 \
    python-dotenv==1.0.0 \
    pytz==2023.3

print_status "Step 5: Setting up environment files"
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    cp ${BACKEND_DIR}/.env.production ${BACKEND_DIR}/.env
    print_warning "Please update ${BACKEND_DIR}/.env with your production settings"
fi

print_status "Step 6: Setting up frontend"
cd ${FRONTEND_DIR}

# Install Node.js 18 (required for Next.js 15)
if ! node --version | grep -q "v18"; then
    print_status "Installing Node.js 18"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

print_status "Installing frontend dependencies"
npm install

print_status "Building frontend for production"
if [ ! -f "${FRONTEND_DIR}/.env.production" ]; then
    cp ${FRONTEND_DIR}/.env.production.example ${FRONTEND_DIR}/.env.production || true
fi
npm run build

print_status "Step 7: Setting up systemd services"

# Copy service files
sudo cp ${PROJECT_DIR}/deployment/atm-api.service /etc/systemd/system/ || print_warning "ATM API service file not found"
sudo cp ${PROJECT_DIR}/deployment/atm-user-api.service /etc/systemd/system/

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable atm-api || print_warning "ATM API service not enabled"
sudo systemctl enable atm-user-api

print_status "Step 8: Setting up Nginx configuration"

# Create nginx configuration
sudo tee ${NGINX_CONF} > /dev/null <<EOF
server {
    listen 80;
    server_name staging.luckymifta.dev;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.luckymifta.dev;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/staging.luckymifta.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.luckymifta.dev/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # ATM Data API (port 8000)
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://staging.luckymifta.dev" always;
        add_header Access-Control-Allow-Credentials true always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "*" always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }

    # User Management API (port 8001)
    location /user-api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://staging.luckymifta.dev" always;
        add_header Access-Control-Allow-Credentials true always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "*" always;
        
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/atm-dashboard.access.log;
    error_log /var/log/nginx/atm-dashboard.error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF

# Enable the site
sudo ln -sf ${NGINX_CONF} /etc/nginx/sites-enabled/atm-dashboard
sudo nginx -t
sudo systemctl reload nginx

print_status "Step 9: Setting up PM2 for frontend"
sudo npm install -g pm2

# Create PM2 ecosystem file
tee ${FRONTEND_DIR}/ecosystem.config.js > /dev/null <<EOF
module.exports = {
  apps: [{
    name: 'atm-dashboard-frontend',
    script: 'npm',
    args: 'start',
    cwd: '${FRONTEND_DIR}',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: '${LOG_DIR}/frontend-error.log',
    out_file: '${LOG_DIR}/frontend-out.log',
    log_file: '${LOG_DIR}/frontend.log'
  }]
};
EOF

print_status "Step 10: Starting services"

# Start backend services
sudo systemctl start atm-user-api
sudo systemctl status atm-user-api --no-pager || print_warning "User API service failed to start"

# Start ATM API if service exists
sudo systemctl start atm-api || print_warning "ATM API service not started"

# Start frontend with PM2
cd ${FRONTEND_DIR}
pm2 start ecosystem.config.js
pm2 save
pm2 startup | tail -1 | sudo bash || print_warning "PM2 startup script failed"

print_status "Step 11: Setting up log rotation"
sudo tee /etc/logrotate.d/atm-dashboard > /dev/null <<EOF
${LOG_DIR}/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
    su $USER www-data
}
EOF

print_status "Step 12: Creating monitoring script"
sudo tee /usr/local/bin/atm-dashboard-status > /dev/null <<'EOF'
#!/bin/bash
echo "=== ATM Dashboard Status ==="
echo "User Management API (Port 8001):"
systemctl is-active atm-user-api
curl -s http://localhost:8001/health 2>/dev/null | head -c 50 || echo "API not responding"

echo -e "\nATM Data API (Port 8000):"
systemctl is-active atm-api 2>/dev/null || echo "Service not found"

echo -e "\nFrontend (Port 3000):"
pm2 list | grep atm-dashboard-frontend

echo -e "\nNginx Status:"
systemctl is-active nginx

echo -e "\nPort Status:"
netstat -tlnp | grep -E ":(3000|8000|8001|80|443)"
EOF

sudo chmod +x /usr/local/bin/atm-dashboard-status

print_status "Step 13: Final security setup"

# Set proper file permissions
sudo chown -R $USER:www-data ${PROJECT_DIR}
sudo chmod -R 750 ${PROJECT_DIR}
sudo chmod -R 755 ${PROJECT_DIR}/frontend/.next
sudo chmod +x ${BACKEND_DIR}/venv/bin/python

# Create a basic firewall setup
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable || print_warning "UFW setup failed"

echo "=================================================="
print_status "✅ ATM Dashboard v2.0.0 deployment completed!"
echo ""
echo "📋 Summary:"
echo "   - User Management API: http://localhost:8001"
echo "   - ATM Data API: http://localhost:8000 (if configured)"
echo "   - Frontend: http://localhost:3000"
echo "   - Nginx Proxy: https://staging.luckymifta.dev"
echo ""
echo "🔧 Management Commands:"
echo "   - Check status: atm-dashboard-status"
echo "   - Frontend logs: pm2 logs atm-dashboard-frontend"
echo "   - API logs: sudo journalctl -f -u atm-user-api"
echo "   - Restart user API: sudo systemctl restart atm-user-api"
echo "   - Restart frontend: pm2 restart atm-dashboard-frontend"
echo ""
print_warning "⚠️  IMPORTANT SECURITY STEPS:"
echo "   1. Update SECRET_KEY in ${BACKEND_DIR}/.env"
echo "   2. Review database connection settings"
echo "   3. Set up SSL certificates with Let's Encrypt"
echo "   4. Change default admin password (username: admin, password: admin123)"
echo ""
print_status "🎉 Your ATM Dashboard with audit logging is ready for production!"
