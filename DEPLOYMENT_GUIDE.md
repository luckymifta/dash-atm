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
curl http://localhost:8000/health || echo "Main API not responding"

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

# Create Next.js environment file
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://staging.luckymifta.dev/api
NEXT_PUBLIC_USER_API_URL=https://staging.luckymifta.dev/user-api
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=$NEXTAUTH_SECRET
NODE_ENV=production
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
chmod -R 644 /var/www/dash-atm/.env*
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
```bash
# Test main API (port 8000)
curl -k https://staging.luckymifta.dev/api/health

# Test user management API (port 8001)
curl -k https://staging.luckymifta.dev/user-api/health

# Test frontend
curl -k https://staging.luckymifta.dev

# Test internal services directly (from VPS)
curl http://localhost:8000/health  # Main API
curl http://localhost:8001/health  # User API
curl http://localhost:3000         # Frontend
```

---

## Phase 7: Monitoring and Maintenance

### 7.1 Setup Log Rotation
```bash
cat > /etc/logrotate.d/dash-atm << 'EOF'
/var/log/dash-atm/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        pm2 reloadLogs
    endscript
}
EOF
```

### 7.2 Create Backup Script
```bash
cat > /root/backup-dash-atm.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump dash > $BACKUP_DIR/dash_db_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/dash_app_$DATE.tar.gz /var/www/dash-atm

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /root/backup-dash-atm.sh

# Add to crontab for daily backup at 2 AM
echo "0 2 * * * /root/backup-dash-atm.sh" | crontab -
```

---

## Useful Commands

### Application Management
```bash
# Restart all services
pm2 restart all

# Stop all services
pm2 stop all

# View logs
pm2 logs
pm2 logs dash-atm-main-api
pm2 logs dash-atm-user-api
pm2 logs dash-atm-frontend

# Monitor resources
pm2 monit
```

### Nginx Management
```bash
# Test configuration
nginx -t

# Reload configuration
systemctl reload nginx

# Check status
systemctl status nginx
```

### Database Management
```bash
# Connect to database
sudo -u postgres psql -d dash

# View database logs
tail -f /var/log/postgresql/postgresql-*.log
```

### Update Application
```bash
cd /var/www/dash-atm

# Pull latest changes
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Update frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
pm2 restart all
```

---

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using ports 8000, 8001, or 3000
   sudo lsof -i :8000  # Main API
   sudo lsof -i :8001  # User API  
   sudo lsof -i :3000  # Frontend
   
   # Kill process if needed
   sudo kill -9 <PID>
   ```

2. **Permission Errors**
   ```bash
   # Fix ownership
   chown -R www-data:www-data /var/www/dash-atm
   ```

3. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status (your existing setup)
   systemctl status postgresql
   
   # Test connection to your existing database
   sudo -u postgres psql -d dash -c "SELECT 1;"
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate expiry
   certbot certificates
   
   # Force renewal
   certbot renew --force-renewal
   ```

5. **Application Not Starting**
   ```bash
   # Check PM2 logs
   pm2 logs
   
   # Check environment variables
   cd /var/www/dash-atm/backend
   source venv/bin/activate
   python -c "import os; print(os.environ.get('DB_HOST'))"
   ```

---

## Security Considerations

1. **Change Default Passwords**: Update all default passwords in the `.env` file
2. **Firewall**: Ensure UFW is properly configured
3. **SSH Security**: Consider disabling password authentication and using SSH keys only
4. **Regular Updates**: Keep the system and dependencies updated
5. **Backup Strategy**: Implement regular backups as described above

---

## Next Steps

After deployment:
1. Test all application features
2. Setup monitoring (consider tools like Uptime Robot)
3. Configure automated data retrieval schedules
4. Setup error alerting
5. Optimize performance based on usage patterns

Your ATM Dashboard should now be accessible at: **https://staging.luckymifta.dev**
