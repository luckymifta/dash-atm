# 🚀 Quick Deployment Commands - Password Reset Feature

## Step 1: Commit & Push from Local Mac

```bash
# Navigate to project directory
cd "/Users/luckymifta/Documents/2. AREA/dash-atm"

# Run the git commit script
./deploy_password_reset_feature.sh

# This will:
# - Stage all password reset files
# - Create detailed commit message
# - Push to GitHub
```

## Step 2: Deploy on Ubuntu Server

### 2.1 Connect to Server
```bash
# SSH into your Ubuntu server
ssh your-username@your-server-ip

# Navigate to project directory
cd /var/www/dash-atm
```

### 2.2 Run Deployment Script
```bash
# Download the deployment script (if needed)
# Or ensure it's in your repository

# Make it executable
chmod +x ubuntu_deploy_password_reset.sh

# Run the deployment
./ubuntu_deploy_password_reset.sh
```

### 2.3 Manual Commands (if script fails)

#### Backend Deployment:
```bash
cd /var/www/dash-atm

# Pull latest code
sudo git pull origin main

# Backend setup
cd backend
pip install -r requirements.txt

# Configure environment
sudo cp .env.example .env.production
sudo nano .env.production
# Add Mailjet credentials and production settings

# Restart backend
sudo systemctl restart atm-backend
# OR
pm2 restart atm-backend
# OR manually:
pkill -f user_management_api.py
nohup python user_management_api.py > ../logs/backend.log 2>&1 &
```

#### Frontend Deployment:
```bash
cd /var/www/dash-atm/frontend

# Install dependencies and build
sudo npm install
sudo npm run build

# Restart frontend
sudo systemctl restart atm-frontend
# OR
pm2 restart atm-frontend
# OR manually:
pkill -f "next\|npm"
nohup npm start > ../logs/frontend.log 2>&1 &
```

## Step 3: Configuration

### 3.1 Backend Environment (.env.production)
```bash
# Edit backend environment
sudo nano /var/www/dash-atm/backend/.env.production

# Required for password reset:
MAILJET_API_KEY=your_mailjet_api_key_here
MAILJET_SECRET_KEY=your_mailjet_secret_key_here
MAILJET_FROM_EMAIL=dash@britimorleste.tl
MAILJET_FROM_NAME=BRI ATM Dashboard
FRONTEND_BASE_URL=https://your-domain.com

# Database settings
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### 3.2 Frontend Environment (.env.production)
```bash
# Edit frontend environment
sudo nano /var/www/dash-atm/frontend/.env.production

# API configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
NODE_ENV=production
```

## Step 4: Testing

### 4.1 Health Checks
```bash
# Test backend
curl http://localhost:8001/health

# Test frontend
curl http://localhost:3000

# Test password reset endpoint
curl -X POST http://localhost:8001/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### 4.2 Complete User Flow Test
1. Visit: `http://your-domain.com/auth/login`
2. Click "Forgot Password?" link
3. Enter email address
4. Check email for reset link
5. Click reset link
6. Enter new password
7. Login with new password

## Step 5: Monitoring

### 5.1 Check Logs
```bash
# Backend logs
tail -f /var/www/dash-atm/logs/backend.log

# Frontend logs
tail -f /var/www/dash-atm/logs/frontend.log

# System logs
journalctl -u atm-backend -f
journalctl -u atm-frontend -f
```

### 5.2 Check Services
```bash
# Check service status
sudo systemctl status atm-backend
sudo systemctl status atm-frontend

# OR with PM2
pm2 status

# Check processes
ps aux | grep user_management_api.py
ps aux | grep "next\|npm"
```

## Step 6: Troubleshooting

### 6.1 Common Issues

**Email not sending:**
- Check Mailjet credentials in .env.production
- Verify sender email domain is authorized
- Check Mailjet dashboard for delivery status

**Reset links not working:**
- Verify FRONTEND_BASE_URL in backend .env.production
- Check that frontend routes are accessible
- Confirm token format in emails

**Database errors:**
- Ensure password_reset_tokens table exists
- Check database connection settings
- Verify user permissions

### 6.2 Rollback Commands
```bash
# If deployment fails, rollback to previous version
cd /var/www/dash-atm
sudo git reset --hard HEAD~1

# Restore from backup
sudo rm -rf /var/www/dash-atm
sudo mv /var/www/dash-atm-backup-YYYYMMDD-HHMMSS /var/www/dash-atm

# Restart services
sudo systemctl restart atm-backend atm-frontend
```

## 📞 Quick Support Commands

```bash
# Get Mailjet credentials location
echo "Backend env: /var/www/dash-atm/backend/.env.production"

# Test email delivery
curl -X POST http://localhost:8001/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "your-real-email@domain.com"}'

# Check if mailjet is installed
pip list | grep mailjet

# Check backend dependencies
cd /var/www/dash-atm/backend
python -c "from mailjet_rest import Client; print('Mailjet OK')"
```

---
**Deployment Complete! 🎉**

The password reset feature is now ready for production use.
