# 🚀 Ubuntu Server Manual Deployment Guide - Password Reset Feature

## 📋 Overview
This guide provides step-by-step manual deployment instructions for the password reset feature on your Ubuntu server at `/var/www/dash-atm`.

## ⚠️ Prerequisites
- Ubuntu server with sudo access
- Git installed
- Node.js 18+ and npm
- Python 3.8+ and pip
- PostgreSQL database
- nginx (for reverse proxy)
- PM2 (for process management)

## 🔧 Pre-Deployment Checklist

### 1. Verify Server Environment
```bash
# SSH into your Ubuntu server
ssh your-username@your-server-ip

# Navigate to project directory
cd /var/www/dash-atm

# Check current directory and permissions
pwd
ls -la

# Verify git status
git status
git branch
```

### 2. Create Backup
```bash
# Create timestamped backup
sudo cp -r /var/www/dash-atm /var/www/dash-atm-backup-$(date +%Y%m%d-%H%M%S)

# Verify backup created
ls -la /var/www/dash-atm-backup-*
```

## 📦 Step 1: Update Code from GitHub

### 1.1 Pull Latest Changes
```bash
cd /var/www/dash-atm

# Fetch and pull latest changes
sudo git fetch origin
sudo git pull origin main

# If you're using feature branch, merge it first:
# sudo git checkout main
# sudo git merge feature/reset-password
```

### 1.2 Verify New Files
```bash
# Check that password reset files are present
ls -la backend/email_service.py
ls -la frontend/src/components/ForgotPasswordForm.tsx
ls -la frontend/src/components/ResetPasswordForm.tsx
ls -la frontend/src/app/auth/forgot-password/page.tsx
ls -la frontend/src/app/auth/reset-password/page.tsx
```

## 🐍 Step 2: Backend Deployment

### 2.1 Navigate to Backend
```bash
cd /var/www/dash-atm/backend
```

### 2.2 Activate Virtual Environment
```bash
# If virtual environment exists
source venv/bin/activate

# If venv doesn't exist, create it:
# python3 -m venv venv
# source venv/bin/activate
```

### 2.3 Install Dependencies
```bash
# Install/update Python packages
pip install -r requirements.txt

# Verify mailjet is installed
pip list | grep mailjet
```

### 2.4 Configure Environment Variables
```bash
# Check if .env.production exists
ls -la .env.production

# If not exists, create from example
sudo cp .env.example .env.production

# Edit production environment file
sudo nano .env.production
```

**Required environment variables for password reset:**
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/dash_atm
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dash_atm
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Mailjet Configuration (REQUIRED for password reset)
MAILJET_API_KEY=your_mailjet_api_key_here
MAILJET_SECRET_KEY=your_mailjet_secret_key_here
MAILJET_FROM_EMAIL=dash@britimorleste.tl
MAILJET_FROM_NAME=BRI ATM Dashboard

# Frontend URL (REQUIRED for reset links)
FRONTEND_BASE_URL=https://your-domain.com

# Security
SECRET_KEY=your-secret-key-here
```

### 2.5 Test Backend Configuration
```bash
# Test Python imports
python3 -c "
try:
    import psycopg2
    from mailjet_rest import Client
    import secrets
    print('✅ All dependencies loaded successfully')
except ImportError as e:
    print('❌ Import error:', e)
"

# Test database connection
python3 -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.production')

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print('❌ Database connection error:', e)
"
```

### 2.6 Test Mailjet Configuration
```bash
# Test Mailjet configuration
python3 -c "
import os
from dotenv import load_dotenv
from mailjet_rest import Client

load_dotenv('.env.production')

api_key = os.getenv('MAILJET_API_KEY')
api_secret = os.getenv('MAILJET_SECRET_KEY')

if not api_key or not api_secret:
    print('❌ Mailjet credentials not configured')
    exit(1)

try:
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    result = mailjet.send.get()
    print('✅ Mailjet connection successful')
except Exception as e:
    print('❌ Mailjet connection error:', e)
"
```

## 🌐 Step 3: Frontend Deployment

### 3.1 Navigate to Frontend
```bash
cd /var/www/dash-atm/frontend
```

### 3.2 Configure Frontend Environment
```bash
# Check if .env.production exists
ls -la .env.production

# If not exists, create it
sudo nano .env.production
```

**Frontend environment variables:**
```env
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api
NEXT_PUBLIC_API_URL=https://your-domain.com/api
```

### 3.3 Install Dependencies
```bash
# Install Node.js dependencies
npm install

# Check for any vulnerabilities
npm audit
```

### 3.4 Build Frontend
```bash
# Build for production
npm run build

# Verify build completed successfully
ls -la .next/
```

## 🔄 Step 4: Service Management

### 4.1 Stop Services
```bash
# Stop PM2 processes
pm2 stop all
pm2 list
```

### 4.2 Start Backend Service
```bash
cd /var/www/dash-atm/backend

# Start backend with PM2
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name "dash-atm-backend"

# Check backend status
pm2 logs dash-atm-backend --lines 10
```

### 4.3 Start Frontend Service
```bash
cd /var/www/dash-atm/frontend

# Start frontend with PM2
pm2 start "npm start" --name "dash-atm-frontend"

# Check frontend status
pm2 logs dash-atm-frontend --lines 10
```

### 4.4 Save PM2 Configuration
```bash
# Save current PM2 processes
pm2 save

# Setup PM2 startup script
pm2 startup

# Verify all services are running
pm2 status
```

## 🧪 Step 5: Testing Deployment

### 5.1 Test Backend API
```bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Test password reset endpoints
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### 5.2 Test Frontend
```bash
# Check if frontend is running
curl -I http://localhost:3000

# Test password reset pages
curl -I http://localhost:3000/auth/forgot-password
curl -I http://localhost:3000/auth/reset-password
```

### 5.3 Check Logs
```bash
# Check backend logs
pm2 logs dash-atm-backend --lines 20

# Check frontend logs
pm2 logs dash-atm-frontend --lines 20

# Check nginx logs (if applicable)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🔧 Step 6: Nginx Configuration (if needed)

### 6.1 Update Nginx Configuration
```bash
# Edit nginx site configuration
sudo nano /etc/nginx/sites-available/dash-atm
```

**Sample nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
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
```

### 6.2 Restart Nginx
```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

## ✅ Step 7: Final Verification

### 7.1 Full End-to-End Test
```bash
# Test the complete flow (replace with your domain)
echo "Testing password reset flow..."

# 1. Request password reset
curl -X POST "https://your-domain.com/api/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test-email@example.com"}'

# 2. Check if email was sent (check your email)
# 3. Visit reset link in email
# 4. Test password reset form
```

### 7.2 Monitor Services
```bash
# Monitor all processes
pm2 monit

# Check system resources
htop

# Check disk space
df -h
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Mailjet Connection Issues
```bash
# Check environment variables
grep MAILJET /var/www/dash-atm/backend/.env.production

# Test Mailjet credentials in Mailjet dashboard
# Verify API keys are active and not expired
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test database connection
psql -h localhost -U your_db_user -d dash_atm
```

#### 3. Frontend Build Issues
```bash
# Clear Next.js cache
cd /var/www/dash-atm/frontend
rm -rf .next node_modules
npm install
npm run build
```

#### 4. PM2 Process Issues
```bash
# Restart all processes
pm2 restart all

# Reset PM2
pm2 kill
pm2 start ecosystem.config.js
```

## 🔄 Rollback Instructions

### If Deployment Fails
```bash
# Stop current services
pm2 stop all

# Restore from backup
sudo rm -rf /var/www/dash-atm
sudo mv /var/www/dash-atm-backup-YYYYMMDD-HHMMSS /var/www/dash-atm

# Restart services
cd /var/www/dash-atm
pm2 start ecosystem.config.js
```

## 📞 Support Information

### Log Locations
- PM2 logs: `~/.pm2/logs/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

### Useful Commands
```bash
# Check all running processes
pm2 status

# Restart specific service
pm2 restart dash-atm-backend

# View real-time logs
pm2 logs --lines 50

# Check system resources
htop
df -h
free -h
```

---

## ✅ Deployment Complete!

After successful deployment:

1. ✅ Password reset feature is live
2. ✅ Mailjet email integration working
3. ✅ Frontend forms accessible
4. ✅ All services monitored by PM2
5. ✅ Nginx routing configured

**Test the complete flow:**
1. Visit `https://your-domain.com/auth/forgot-password`
2. Enter email and submit
3. Check email for reset link
4. Click reset link and set new password
5. Login with new password

🎉 **Password Reset Feature Successfully Deployed!**
