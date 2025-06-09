#!/bin/bash

# ATM Dashboard Deployment Script for Ubuntu VPS
# Domain: dash.luckymifta.dev
# Repository: https://github.com/luckymifta/dash-atm

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="dash.luckymifta.dev"
APP_DIR="/var/www/dash-atm"
REPO_URL="https://github.com/luckymifta/dash-atm.git"
DB_NAME="development_db"  # Using your updated database name

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 ATM Dashboard Deployment Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${YELLOW}Domain: ${DOMAIN}${NC}"
echo -e "${YELLOW}App Directory: ${APP_DIR}${NC}"
echo -e "${YELLOW}Database: ${DB_NAME}${NC}"
echo ""

# Function to check if a command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# Function to check if a service is running
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}✅ $1 is running${NC}"
    else
        echo -e "${YELLOW}⚠️  $1 is not running, starting...${NC}"
        systemctl start $1
        check_status "$1 started"
    fi
}

echo -e "${BLUE}Step 1: System Update and Dependencies${NC}"
echo "Updating system packages..."
apt update && apt upgrade -y
check_status "System updated"

echo "Installing essential dependencies..."
apt install -y curl wget unzip git software-properties-common apt-transport-https ca-certificates gnupg lsb-release nginx python3.11 python3.11-venv python3-pip libpq-dev python3-dev build-essential gcc certbot python3-certbot-nginx ufw
check_status "Dependencies installed"

echo "Installing Node.js 20 LTS..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    apt install -y nodejs
    check_status "Node.js installed"
else
    echo -e "${GREEN}✅ Node.js already installed${NC}"
fi

echo "Installing PM2..."
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
    check_status "PM2 installed"
else
    echo -e "${GREEN}✅ PM2 already installed${NC}"
fi

echo -e "${BLUE}Step 2: Firewall Configuration${NC}"
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
check_status "Firewall configured"

echo -e "${BLUE}Step 2.5: PostgreSQL Verification${NC}"
echo "Checking PostgreSQL status..."
check_service postgresql

echo "Verifying database and user exist..."
if sudo -u postgres psql -d development_db -c "\q" 2>/dev/null; then
    echo -e "${GREEN}✅ Database 'development_db' exists${NC}"
else
    echo -e "${YELLOW}⚠️  Database 'development_db' not found, attempting to create...${NC}"
    sudo -u postgres createdb development_db 2>/dev/null || echo -e "${YELLOW}Database may already exist${NC}"
fi

if sudo -u postgres psql -d development_db -c "\du" | grep -q timlesdev; then
    echo -e "${GREEN}✅ User 'timlesdev' exists${NC}"
else
    echo -e "${YELLOW}⚠️  User 'timlesdev' not found, attempting to create...${NC}"
    sudo -u postgres psql -d development_db -c "CREATE USER timlesdev WITH PASSWORD 'timlesdev';" 2>/dev/null || echo -e "${YELLOW}User may already exist${NC}"
    sudo -u postgres psql -d development_db -c "GRANT ALL PRIVILEGES ON DATABASE development_db TO timlesdev;" 2>/dev/null
fi

echo -e "${BLUE}Step 3: Application Deployment${NC}"
echo "Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

echo "Cloning repository..."
if [ -d ".git" ]; then
    echo "Repository already exists, pulling latest changes..."
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    git clone $REPO_URL .
fi
check_status "Repository cloned/updated"

echo -e "${BLUE}Step 4: Backend Setup${NC}"
cd $APP_DIR/backend

echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate
check_status "Virtual environment created"

echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
check_status "Python dependencies installed"

echo "Creating backend environment file..."
cat > .env << EOF
# Production Environment Configuration for ATM Dashboard

# Database Configuration (local PostgreSQL on VPS)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
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
CORS_ORIGINS=["https://$DOMAIN", "http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# Security Settings
SECRET_KEY=2QNQK08xRdLElX4hT6zy61AqKdUFcGMT+r+XCzSEJIUV/WQYNcls8SBD3P8TKlqmG7pcl+VdwDhHU122/pbG7A==
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=
ENVIRONMENT=production

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/dash-atm/app.log

# Application URLs
FRONTEND_URL=https://$DOMAIN
EOF
check_status "Backend environment file created"

echo -e "${BLUE}Step 5: Frontend Setup${NC}"
echo "Deactivating Python virtual environment..."
deactivate 2>/dev/null || true  # Exit venv gracefully
cd $APP_DIR/frontend

echo "Installing Node.js dependencies..."
npm install
check_status "Node.js dependencies installed"

echo "Creating frontend environment file..."
NEXTAUTH_SECRET=$(openssl rand -base64 32)
cat > .env.production << EOF
# Production Environment Configuration for Frontend
# API Configuration - Production HTTPS URLs
NEXT_PUBLIC_API_BASE_URL=https://$DOMAIN/api
NEXT_PUBLIC_USER_API_BASE_URL=https://$DOMAIN/user-api

# Environment
NODE_ENV=production

# NextAuth Configuration
NEXTAUTH_URL=https://$DOMAIN
NEXTAUTH_SECRET=$NEXTAUTH_SECRET

# Application Configuration
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF
check_status "Frontend environment file created"

echo "Building frontend..."
NODE_ENV=production npm run build
check_status "Frontend built"

echo -e "${BLUE}Step 6: PM2 Configuration${NC}"
cd $APP_DIR

echo "Creating PM2 ecosystem configuration..."
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
check_status "PM2 configuration created"

echo "Creating log directory..."
mkdir -p /var/log/dash-atm
chown -R www-data:www-data /var/log/dash-atm
check_status "Log directory created"

echo "Starting applications with PM2..."
pm2 start ecosystem.config.js
pm2 save
check_status "PM2 applications started"

echo "Setting up PM2 startup..."
pm2 startup systemd -u root --hp /root
check_status "PM2 startup configured"

echo -e "${BLUE}Step 7: Nginx Configuration${NC}"
echo "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Test endpoint
    location /health {
        return 200 "Nginx working\n";
        add_header Content-Type text/plain;
    }

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # User Management API routes (port 8001)
    location /user-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
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
check_status "Nginx configuration created"

echo "Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
check_status "Nginx configuration validated"

systemctl restart nginx
check_status "Nginx restarted"

echo -e "${BLUE}Step 8: SSL Certificate Setup${NC}"
echo "Setting up SSL certificate with Let's Encrypt..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@luckymifta.dev --redirect
check_status "SSL certificate configured"

echo -e "${BLUE}Step 9: Final Verification${NC}"
echo "Checking service status..."
check_service nginx
check_service postgresql

echo "PM2 status:"
pm2 status

echo "Testing application endpoints..."
echo "Testing health endpoint..."
curl -f http://localhost/health && echo -e "${GREEN}✅ Health endpoint works${NC}" || echo -e "${RED}❌ Health endpoint failed${NC}"

echo "Testing API endpoint..."
curl -f http://localhost:8000/api/v1/health && echo -e "${GREEN}✅ Main API works${NC}" || echo -e "${RED}❌ Main API failed${NC}"

echo "Testing user API endpoint..."
curl -f http://localhost:8001/health && echo -e "${GREEN}✅ User API works${NC}" || echo -e "${RED}❌ User API failed${NC}"

echo "Testing frontend..."
curl -f http://localhost:3000 && echo -e "${GREEN}✅ Frontend works${NC}" || echo -e "${RED}❌ Frontend failed${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}📊 Application Status:${NC}"
echo -e "${YELLOW}• Website: https://$DOMAIN${NC}"
echo -e "${YELLOW}• Main API: https://$DOMAIN/api/v1/health${NC}"
echo -e "${YELLOW}• User API: https://$DOMAIN/user-api/health${NC}"
echo -e "${YELLOW}• Database: $DB_NAME on 88.222.214.26${NC}"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "${YELLOW}• PM2 status: pm2 status${NC}"
echo -e "${YELLOW}• PM2 logs: pm2 logs dash-atm-main-api${NC}"
echo -e "${YELLOW}• Nginx status: systemctl status nginx${NC}"
echo -e "${YELLOW}• Nginx reload: systemctl reload nginx${NC}"
echo ""
echo -e "${BLUE}📁 Important Paths:${NC}"
echo -e "${YELLOW}• App directory: $APP_DIR${NC}"
echo -e "${YELLOW}• Logs: /var/log/dash-atm/${NC}"
echo -e "${YELLOW}• Nginx config: /etc/nginx/sites-available/$DOMAIN${NC}"
echo ""
echo -e "${GREEN}Your ATM Dashboard is now live at: https://$DOMAIN${NC}"
