# ATM Dashboard Deployment Guide for Ubuntu VPS

## Overview
This guide will walk you through deploying the ATM Dashboard application (FastAPI backend + Next.js frontend) to your Ubuntu VPS using the domain `staging.luckymifta.dev`.

## Prerequisites
- Ubuntu VPS with sudo access
- Domain `staging.luckymifta.dev` pointing to your VPS IP
- SSH access to your VPS

## Architecture
- **Frontend**: Next.js application served by PM2
- **Backend**: FastAPI application served by PM2 with Uvicorn
- **Database**: PostgreSQL
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt (Certbot)
- **Process Manager**: PM2

---

## Phase 1: Initial VPS Setup

### 1.1 Connect to VPS and Update System
```bash
ssh root@your-vps-ip
apt update && apt upgrade -y
```

### 1.2 Install Essential Dependencies
```bash
# Install curl, wget, and other utilities
apt install -y curl wget unzip git software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Nginx
apt install -y nginx

# Install Python 3.11+ and pip
apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt install -y nodejs

# Install PM2 globally
npm install -g pm2

# Install Certbot for SSL
apt install -y certbot python3-certbot-nginx
```

### 1.3 Verify PostgreSQL Configuration
Since you already have PostgreSQL configured, let's verify the setup:

```bash
# Check PostgreSQL status
systemctl status postgresql

# Test connection to your existing database
sudo -u postgres psql -d dash -c "SELECT current_database(), current_user;"

# If you need to create the database and user (skip if already exists)
# sudo -u postgres psql
# CREATE USER timlesdev WITH PASSWORD 'timlesdev';
# CREATE DATABASE dash OWNER timlesdev;
# GRANT ALL PRIVILEGES ON DATABASE dash TO timlesdev;
# \q
```

### 1.4 Configure Firewall
```bash
# Install and configure UFW
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

---

## Phase 2: Application Deployment

### 2.1 Create Application Directory
```bash
mkdir -p /var/www/dash-atm
cd /var/www/dash-atm
```

### 2.2 Clone Repository

#### Option A: HTTPS Clone (Recommended)
```bash
# Clone your repository using HTTPS
git clone https://github.com/luckymifta/dash-atm.git .

# If the repository is private, you'll need to enter your GitHub credentials
# Or use a Personal Access Token instead of password
```

#### Option B: SSH Clone (Advanced)
If you prefer SSH and have a private repository, set up SSH keys first:

```bash
# Generate SSH key on VPS
ssh-keygen -t ed25519 -C "your-email@example.com"

# Display the public key
cat ~/.ssh/id_ed25519.pub

# Copy the output and add it to your GitHub account:
# 1. Go to GitHub.com → Settings → SSH and GPG keys
# 2. Click "New SSH key"
# 3. Paste the public key content
# 4. Save the key

# Test SSH connection
ssh -T git@github.com

# Clone using SSH
git clone git@github.com:luckymifta/dash-atm.git .
```

### 2.3 Setup Backend

#### 2.3.1 Create Python Virtual Environment
```bash
cd /var/www/dash-atm/backend
python3.11 -m venv venv
source venv/bin/activate
```

#### 2.3.2 Install Python Dependencies
```bash
# First, install system dependencies (required for asyncpg and other packages)
apt update
apt install -y libpq-dev python3-dev build-essential gcc

# Ensure you're in the virtual environment
source venv/bin/activate

# Verify virtual environment is active
which python
which pip

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Install Python dependencies with verbose output
pip install -r requirements.txt -v

# If the above fails, try installing key packages individually:
# pip install fastapi uvicorn asyncpg python-dotenv psycopg2-binary

# Verify installation was successful
echo "Checking installed packages:"
pip list

# Verify critical dependencies
python -c "import asyncpg; print('✅ asyncpg installed successfully:', asyncpg.__version__)"
python -c "import fastapi; print('✅ fastapi installed successfully:', fastapi.__version__)"
python -c "import uvicorn; print('✅ uvicorn installed successfully:', uvicorn.__version__)"

# If any imports fail, the virtual environment needs to be recreated
```

#### 2.3.3 Setup Environment File
Since `.env.production` is not in the repository for security reasons, you need to create it manually:

**Option A: Create the file manually (Recommended)**
```bash
# Create the .env file with production configuration
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

# Application URLs
FRONTEND_URL=https://staging.luckymifta.dev
API_BASE_URL=https://staging.luckymifta.dev/api
USER_API_BASE_URL=https://staging.luckymifta.dev/user-api

# SSL Configuration (for Let's Encrypt)
SSL_CERT_PATH=/etc/letsencrypt/live/staging.luckymifta.dev/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/staging.luckymifta.dev/privkey.pem
EOF
```

**Option B: Transfer from local machine**
```bash
# From your local machine, use SCP to transfer the file:
# scp .env.production root@your-vps-ip:/var/www/dash-atm/backend/.env
```

**Verify the file was created:**
```bash
# Check if the file exists and has content
ls -la .env
head -5 .env
```

#### 2.3.4 Test Backend Services
```bash
# Test main API (should run on port 8000)
python api_option_2_fastapi_fixed.py &
MAIN_API_PID=$!

# Wait a moment and test
sleep 3
curl http://localhost:8000/api/v1/health || echo "Main API not responding"

# Stop the test
kill $MAIN_API_PID

# Test user management API (should run on port 8001)
python user_management_api.py &
USER_API_PID=$!

# Wait a moment and test
sleep 3
curl http://localhost:8001/health || echo "User API not responding"

# Stop the test
kill $USER_API_PID

echo "Backend services test completed"
```

### 2.4 Setup Frontend

#### 2.4.1 Install Node Dependencies
```bash
cd /var/www/dash-atm/frontend
npm install
```

#### 2.4.2 Create Production Environment
```bash
# Generate a secure NEXTAUTH_SECRET
NEXTAUTH_SECRET=$(openssl rand -base64 32)

# Create Next.js environment file with correct API endpoints
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

# Display the generated secret for your records
echo "Generated NEXTAUTH_SECRET: $NEXTAUTH_SECRET"
```

#### 2.4.3 Build Frontend
```bash
npm run build
```

---

## Phase 3: Process Management with PM2

### 3.1 Create PM2 Configuration
```bash
cd /var/www/dash-atm
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
```

### 3.2 Create Log Directory
```bash
mkdir -p /var/log/dash-atm
chown -R www-data:www-data /var/log/dash-atm
```

### 3.3 Start Applications with PM2
```bash
# Start all applications
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Follow the instructions provided by the command above

# Verify all services are running
pm2 status
pm2 logs --lines 20
```

---

## Phase 4: Nginx Configuration

### 4.1 Create Nginx Configuration
```bash
cat > /etc/nginx/sites-available/staging.luckymifta.dev << 'EOF'
server {
    listen 80;
    server_name staging.luckymifta.dev;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.luckymifta.dev;

    # SSL Configuration (will be added by Certbot)
    ssl_certificate /etc/letsencrypt/live/staging.luckymifta.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.luckymifta.dev/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
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
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF
```

### 4.2 Enable Nginx Site
```bash
# Create symbolic link to enable site
ln -s /etc/nginx/sites-available/staging.luckymifta.dev /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# If test passes, reload Nginx
systemctl reload nginx
```

---

## Phase 5: SSL Certificate Setup

### 5.1 Obtain SSL Certificate
```bash
# Stop Nginx temporarily for initial certificate
systemctl stop nginx

# Obtain certificate
certbot certonly --standalone -d staging.luckymifta.dev

# Start Nginx again
systemctl start nginx
```

### 5.2 Setup Auto-renewal
```bash
# Test renewal
certbot renew --dry-run

# Create renewal hook to reload Nginx
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF

chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

---

## Phase 6: Final Configuration and Testing

### 6.1 Set Proper Permissions
```bash
# Set ownership for application directory
chown -R www-data:www-data /var/www/dash-atm

# Set proper permissions
chmod -R 755 /var/www/dash-atm

# Set permissions for environment files (if they exist)
sudo chmod 644 /var/www/dash-atm/backend/.env 2>/dev/null || echo "Backend .env not found"
sudo chmod 644 /var/www/dash-atm/frontend/.env.production 2>/dev/null || echo "Frontend .env.production not found"
```

### 6.2 Verify Services
```bash
# Check PM2 status
pm2 status

# Check Nginx status
systemctl status nginx

# Check PostgreSQL status (your existing setup)
systemctl status postgresql

# Check application logs
pm2 logs dash-atm-main-api --lines 50
pm2 logs dash-atm-user-api --lines 50
pm2 logs dash-atm-frontend --lines 50
```

### 6.3 Test Application

**First, test internal services directly (most important):**
```bash
# Test internal services directly (from VPS)
curl http://localhost:8000/api/v1/health  # Main API
curl http://localhost:8001/health         # User API
curl http://localhost:3000                # Frontend

# Check which services are actually listening
sudo netstat -tlnp | grep :8000  # Main API
sudo netstat -tlnp | grep :8001  # User API
sudo netstat -tlnp | grep :3000  # Frontend
sudo netstat -tlnp | grep :80    # Nginx HTTP
```

**If internal services work, diagnose the HTTP port 80 connection issue:**

**Step 1: Check if Nginx is running and listening on port 80**
```bash
# Check Nginx status
sudo systemctl status nginx

# Check if port 80 is open and listening
sudo netstat -tlnp | grep :80
# OR use ss command
sudo ss -tlnp | grep :80

# Check if Nginx process is running
ps aux | grep nginx
```

**Step 2: Check firewall settings**
```bash
# Check UFW status and rules
sudo ufw status verbose

# Check if port 80 is allowed
sudo ufw status | grep -E "(80|http)"

# If port 80 is not allowed, add it:
sudo ufw allow 80/tcp
sudo ufw allow http
```

**Step 3: Check if Nginx configuration is valid**
```bash
# Test Nginx configuration
sudo nginx -t

# Check which config files are active
sudo nginx -T | head -20

# Check if staging.luckymifta.dev site is enabled
ls -la /etc/nginx/sites-enabled/
```

**Step 4: Check if Nginx can bind to port 80**
```bash
# Check if anything else is using port 80
sudo lsof -i :80

# Try to restart Nginx to see if there are binding issues
sudo systemctl restart nginx
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Step 5: Manual diagnostic tests**
```bash
# Test if you can reach the server at all
ping staging.luckymifta.dev

# Test if port 80 is reachable from outside (from your local machine)
# Run this from your LOCAL machine, not the VPS:
# telnet staging.luckymifta.dev 80
# nc -zv staging.luckymifta.dev 80

# Check DNS resolution
nslookup staging.luckymifta.dev
dig staging.luckymifta.dev
```

**Step 6: Create HTTP configuration or add SSL to existing config**

**Option A: If SSL certificates exist, create HTTPS configuration:**
```bash
# First, verify SSL certificates exist
sudo ls -la /etc/letsencrypt/live/staging.luckymifta.dev/

# If certificates exist, create HTTPS-enabled config using nano
sudo nano /etc/nginx/sites-available/staging.luckymifta.dev

# In nano editor, replace the content with this HTTPS configuration:
```

**HTTPS configuration to paste in nano (if SSL certificates exist):**
```nginx
# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name staging.luckymifta.dev;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name staging.luckymifta.dev;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/staging.luckymifta.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.luckymifta.dev/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Test endpoint
    location /health {
        return 200 "Nginx HTTPS is working!\n";
        add_header Content-Type text/plain;
    }

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
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
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

**Option B: If no SSL certificates, create HTTP-only config:**
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name staging.luckymifta.dev _;

    # Test endpoint
    location /health {
        return 200 "Nginx HTTP is working!\n";
        add_header Content-Type text/plain;
    }

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
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
}
EOF

# Test and reload Nginx
sudo nginx -t && sudo systemctl reload nginx

# Now test HTTP endpoints
curl http://staging.luckymifta.dev/api/v1/health
curl http://staging.luckymifta.dev/user-api/health
curl http://staging.luckymifta.dev/
```

**If you get "Connection refused" error on port 80, follow these diagnostic steps:**

```bash
# 1. Check if Nginx is actually running and listening on port 80
sudo systemctl status nginx
sudo netstat -tlnp | grep :80
sudo ss -tlnp | grep :80

# 2. Check Nginx configuration and logs
sudo nginx -t
sudo tail -50 /var/log/nginx/error.log
sudo tail -50 /var/log/nginx/access.log

# 3. Check if port 80 is blocked by firewall
sudo ufw status verbose
sudo iptables -L -n | grep 80

# 4. Test if Nginx responds locally vs externally
curl -v http://localhost/           # Test from VPS
curl -v http://127.0.0.1/          # Test from VPS
curl -v http://$(hostname -I | awk '{print $1}')/  # Test using VPS IP

# 5. Check DNS resolution
nslookup staging.luckymifta.dev
dig staging.luckymifta.dev

# 6. Test direct IP connection (replace YOUR_VPS_IP with actual IP)
# From your local machine:
# curl -v http://YOUR_VPS_IP/

# 7. Check if any process is blocking port 80
sudo lsof -i :80
sudo fuser 80/tcp

# 8. Restart Nginx completely
sudo systemctl stop nginx
sleep 2
sudo systemctl start nginx
sudo systemctl status nginx

# 9. Check Nginx is enabled and running
sudo systemctl is-enabled nginx
sudo systemctl is-active nginx

# 10. Verify the site is enabled
ls -la /etc/nginx/sites-enabled/
cat /etc/nginx/sites-enabled/staging.luckymifta.dev
```

**Common fixes for "Connection refused" on port 80:**

```bash
# Fix 1: Restart Nginx service
sudo systemctl restart nginx

# Fix 2: Check if Apache or another web server is running
sudo systemctl status apache2 2>/dev/null || echo "Apache not installed"
sudo pkill -f apache2 2>/dev/null || echo "No Apache processes"

# Fix 3: Ensure Nginx owns the sites-enabled symlink
sudo rm -f /etc/nginx/sites-enabled/staging.luckymifta.dev
sudo ln -s /etc/nginx/sites-available/staging.luckymifta.dev /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Fix 4: If firewall is blocking (check UFW status first)
sudo ufw allow 80/tcp
sudo ufw reload

# Fix 5: Check if SELinux is blocking (on some systems)
sudo setenforce 0 2>/dev/null || echo "SELinux not active"

# Fix 6: Use alternative Nginx configuration with explicit IPv4
sudo cat > /etc/nginx/sites-available/staging.luckymifta.dev << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name staging.luckymifta.dev _;

    # Test endpoint
    location /health {
        return 200 "Nginx working\n";
        add_header Content-Type text/plain;
    }

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # User Management API routes (port 8001)
    location /user-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx

# Test the health endpoint
curl http://staging.luckymifta.dev/nginx-health
```

**If the debug sequence shows issues, run these targeted fixes:**

**Fix 1: If Nginx is not running**
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

**Fix 2: If port 80 is not listening**
```bash
# Check if another service is using port 80
sudo lsof -i :80
sudo fuser -k 80/tcp  # Kill processes using port 80 (use with caution)
sudo systemctl restart nginx
```

**Fix 3: If firewall is blocking**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 'Nginx HTTP'
sudo ufw reload
sudo ufw status verbose
```

**Fix 4: If Nginx configuration has errors**
```bash
# Check configuration syntax
sudo nginx -t

# If errors found, create a minimal working config
sudo cp /etc/nginx/sites-available/staging.luckymifta.dev /etc/nginx/sites-available/staging.luckymifta.dev.backup

sudo cat > /etc/nginx/sites-available/staging.luckymifta.dev << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name staging.luckymifta.dev _;

    # Test endpoint
    location /health {
        return 200 "Nginx working\n";
        add_header Content-Type text/plain;
    }

    # Main API routes (port 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # User Management API routes (port 8001)
    location /user-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx
```

**Fix 5: If DNS is not resolving correctly**
```bash
# Check DNS from VPS
nslookup staging.luckymifta.dev
dig staging.luckymifta.dev

# Get your VPS IP address
curl -4 ifconfig.me
ip addr show | grep inet

# Test using direct IP instead of domain (replace YOUR_VPS_IP)
curl -H "Host: staging.luckymifta.dev" http://YOUR_VPS_IP/health
```

**Fix 6: Nuclear option - complete Nginx reinstall**
```bash
# Only if nothing else works
sudo systemctl stop nginx
sudo apt remove --purge nginx nginx-common
sudo apt autoremove
sudo apt install nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Recreate the basic configuration from scratch
```

**Once HTTP is working, test with these commands:**
```bash
# Test basic connectivity
curl -v http://staging.luckymifta.dev/health

# Test API endpoints
curl -v http://staging.luckymifta.dev/api/v1/health
curl -v http://staging.luckymifta.dev/user-api/health

# Test frontend
curl -v http://staging.luckymifta.dev/

# If all HTTP tests pass, you can proceed to SSL setup
```

**Complete diagnostic checklist:**
```bash
# Run this complete sequence to identify the exact issue:

echo "1. Testing Nginx service status..."
sudo systemctl is-active nginx && echo "✅ Nginx is running" || echo "❌ Nginx is not running"

echo "2. Testing port 80 binding..."
sudo netstat -tlnp | grep :80 && echo "✅ Port 80 is listening" || echo "❌ Port 80 is not listening"

echo "3. Testing Nginx configuration..."
sudo nginx -t && echo "✅ Nginx config is valid" || echo "❌ Nginx config has errors"

echo "4. Testing local connectivity..."
curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|301\|302" && echo "✅ Local connection works" || echo "❌ Local connection failed"

echo "5. Testing firewall..."
sudo ufw status | grep -q "80/tcp.*ALLOW" && echo "✅ Port 80 is allowed in firewall" || echo "❌ Port 80 may be blocked by firewall"

echo "6. Testing DNS resolution..."
nslookup staging.luckymifta.dev > /dev/null && echo "✅ DNS resolves" || echo "❌ DNS resolution failed"

echo "7. Testing PM2 services..."
pm2 status | grep -q "online" && echo "✅ PM2 services are running" || echo "❌ PM2 services not running"

echo "8. Summary of listening ports:"
sudo netstat -tlnp | grep -E ':(80|8000|8001|3000)' || echo "No services listening on expected ports"

echo "9. Testing external connectivity..."
timeout 10 curl -s http://staging.luckymifta.dev/ > /dev/null && echo "✅ External HTTP works" || echo "❌ External HTTP connection failed"
````

## Troubleshooting Quick Reference

### Most Common Issues and Solutions

**1. Connection Refused on Port 80**
- **Check:** `sudo systemctl status nginx`
- **Fix:** `sudo systemctl start nginx`

**2. Nginx Not Listening on Port 80**
- **Check:** `sudo netstat -tlnp | grep :80`
- **Fix:** `sudo systemctl restart nginx`

**3. Firewall Blocking Connections**
- **Check:** `sudo ufw status`
- **Fix:** `sudo ufw allow 80/tcp && sudo ufw reload`

**4. DNS Not Resolving**
- **Check:** `nslookup staging.luckymifta.dev`
- **Fix:** Contact your DNS provider or wait for propagation

**5. Backend Services Not Running**
- **Check:** `pm2 status`
- **Fix:** `pm2 restart all`

**6. Configuration Errors**
- **Check:** `sudo nginx -t`
- **Fix:** Review and correct Nginx configuration

**7. Frontend Still Using Localhost URLs**
- **Check:** Browser network tab shows requests to `http://localhost:8001/auth/login`
- **Fix:** Frontend environment variables not properly configured
```bash
# On VPS: Check if .env.production exists
cd /var/www/dash-atm/frontend
ls -la .env*

# Create/update .env.production with HTTPS URLs
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api/v1
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api
NODE_ENV=production
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=
EOF

# Rebuild and restart frontend
npm run build
pm2 restart dash-atm-frontend

# Verify environment variables are loaded
pm2 logs dash-atm-frontend --lines 20
```

### Quick Recovery Commands
```bash
# Emergency restart all services
sudo systemctl restart nginx
pm2 restart all

# Check all service status
sudo systemctl status nginx --no-pager
pm2 status
sudo netstat -tlnp | grep -E ':(80|8000|8001|3000)'

# Test connectivity
curl http://localhost:8000/api/v1/health  # Main API
curl http://localhost:8001/health         # User API
curl http://localhost:3000                # Frontend
curl http://staging.luckymifta.dev/health # External
```

**Next Steps After HTTP is Working:**
1. Proceed to Phase 5 (SSL Certificate Setup) in this guide
2. Test HTTPS connectivity
3. Update frontend environment to use HTTPS URLs
4. Complete end-to-end testing

**Contact Information:**
- If you continue experiencing issues, run the complete diagnostic checklist above
- Note which specific step fails and the exact error message
- Check Nginx error logs: `sudo tail -50 /var/log/nginx/error.log`
- Check PM2 logs: `pm2 logs --lines 50`
