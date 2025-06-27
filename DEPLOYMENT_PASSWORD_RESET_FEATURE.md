# Password Reset Feature Deployment Guide

## 🎯 **Feature Overview**
Complete password reset functionality with email integration using Mailjet.

## 📋 **Deployment Checklist**

### **Backend Changes**
- [x] Password reset API endpoints (`/auth/forgot-password`, `/auth/reset-password`, `/auth/verify-reset-token/{token}`)
- [x] Mailjet email service integration
- [x] Email templates (HTML + plain text)
- [x] Database token storage and validation
- [x] Security features (24h expiration, single-use tokens)
- [x] Audit logging for password reset events

### **Frontend Changes**
- [x] Forgot password page (`/auth/forgot-password`)
- [x] Reset password page (`/auth/reset-password`)
- [x] Updated login form with "Forgot Password?" link
- [x] API service integration
- [x] Form validation and error handling

### **Dependencies Added**
- [x] Backend: `mailjet-rest==1.3.4` (already in requirements.txt)
- [x] Frontend: No new dependencies (using existing libraries)

## 🌍 **Production Deployment Steps (Ubuntu Server)**

### **Step 1: Git Commit & Push Changes**

#### **1.1 Prepare Local Repository**
```bash
# Navigate to project directory
cd "/Users/luckymifta/Documents/2. AREA/dash-atm"

# Check current status
git status

# Add all password reset feature files
git add .

# Create comprehensive commit
git commit -m "feat: Implement complete password reset functionality

- Add password reset API endpoints (/auth/forgot-password, /auth/reset-password, /auth/verify-reset-token)
- Integrate Mailjet email service with professional templates
- Add frontend pages for forgot/reset password flows
- Update login form with forgot password link
- Fix database schema compatibility issues
- Add comprehensive error handling and security features
- Update API service with password reset functions

Closes #[ISSUE_NUMBER] - Password Reset Feature"

# Push to GitHub
git push origin main
```

### **Step 2: Ubuntu Server Deployment**

#### **2.1 Server Connection & Navigation**
```bash
# SSH into your Ubuntu server
ssh your-username@your-server-ip

# Navigate to project directory
cd /var/www/dash-atm

# Verify current location
pwd
# Should output: /var/www/dash-atm
```

#### **2.2 Backup Current Version (Safety)**
```bash
# Create backup of current version
sudo cp -r /var/www/dash-atm /var/www/dash-atm-backup-$(date +%Y%m%d-%H%M%S)

# List backups to verify
ls -la /var/www/dash-atm-backup-*
```

#### **2.3 Pull Latest Changes**
```bash
# Navigate to project root
cd /var/www/dash-atm

# Fetch latest changes
sudo git fetch origin

# Pull latest code
sudo git pull origin main

# Verify the pull was successful
git log --oneline -5
```

### **Step 3: Backend Deployment**

#### **3.1 Install Python Dependencies**
```bash
# Navigate to backend directory
cd /var/www/dash-atm/backend

# Activate virtual environment (if using one)
source venv/bin/activate  # Skip if not using venv

# Install new dependencies
sudo pip install -r requirements.txt

# Verify mailjet is installed
pip list | grep mailjet
# Should show: mailjet-rest==1.3.4
```

#### **3.2 Configure Environment Variables**
```bash
# Navigate to backend directory
cd /var/www/dash-atm/backend

# Create production environment file
sudo cp .env.example .env.production

# Edit production environment (replace with your actual values)
sudo nano .env.production
```

**Add these variables to .env.production:**
```bash
# Database Configuration
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Mailjet Configuration (REQUIRED FOR PASSWORD RESET)
MAILJET_API_KEY=your_mailjet_api_key_here
MAILJET_SECRET_KEY=your_mailjet_secret_key_here
MAILJET_FROM_EMAIL=dash@britimorleste.tl
MAILJET_FROM_NAME=BRI ATM Dashboard

# Frontend URL for reset links
FRONTEND_BASE_URL=https://your-production-domain.com

# Server Configuration
PORT=8001
HOST=0.0.0.0
```

#### **3.3 Test Backend Configuration**
```bash
# Test database connection and dependencies
cd /var/www/dash-atm/backend
python -c "
import psycopg2
from mailjet_rest import Client
print('✅ Database and email dependencies loaded successfully')
"

# Test API startup (quick test)
timeout 10s python user_management_api.py
# Should show startup logs, then timeout (expected)
```

#### **3.4 Restart Backend Service**
```bash
# If using systemd service
sudo systemctl restart atm-backend

# OR if using PM2
pm2 restart atm-backend

# OR if using manual process (find and kill, then restart)
sudo pkill -f user_management_api.py
cd /var/www/dash-atm/backend
nohup python user_management_api.py > ../logs/backend.log 2>&1 &

# Verify backend is running
curl http://localhost:8001/health
# Should return: {"status": "healthy", "timestamp": "..."}
```

### **Step 4: Frontend Deployment**

#### **4.1 Install Frontend Dependencies**
```bash
# Navigate to frontend directory
cd /var/www/dash-atm/frontend

# Install dependencies (in case there are any updates)
sudo npm install

# Verify installation
npm list --depth=0
```

#### **4.2 Configure Frontend Environment**
```bash
# Navigate to frontend directory
cd /var/www/dash-atm/frontend

# Create/update production environment
sudo nano .env.production
```

**Add to .env.production:**
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Production settings
NODE_ENV=production
```

#### **4.3 Build Frontend**
```bash
# Navigate to frontend directory
cd /var/www/dash-atm/frontend

# Clear previous build
sudo rm -rf .next

# Build production version
sudo npm run build

# Verify build success
ls -la .next
# Should show built files
```

#### **4.4 Restart Frontend Service**
```bash
# If using systemd service
sudo systemctl restart atm-frontend

# OR if using PM2
pm2 restart atm-frontend

# OR if using manual process
sudo pkill -f "next start"
cd /var/www/dash-atm/frontend
nohup npm start > ../logs/frontend.log 2>&1 &

# Verify frontend is running
curl http://localhost:3000
# Should return HTML content
```

### **Step 5: Nginx Configuration (if applicable)**

#### **5.1 Update Nginx Configuration**
```bash
# Edit Nginx configuration
sudo nano /etc/nginx/sites-available/atm-dashboard

# Ensure these routes are properly configured:
# /auth/forgot-password -> frontend
# /auth/reset-password -> frontend
# /api/* -> backend

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### **Step 6: Verification & Testing**

#### **6.1 Backend API Testing**
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test forgot password endpoint
curl -X POST http://localhost:8001/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Should return: {"message": "If a user with that email exists, a password reset email has been sent."}
```

#### **6.2 Frontend Testing**
```bash
# Test frontend accessibility
curl -I http://localhost:3000

# Test specific routes
curl -I http://localhost:3000/auth/login
curl -I http://localhost:3000/auth/forgot-password
curl -I http://localhost:3000/auth/reset-password
```

#### **6.3 Full Integration Test**
```bash
# Test complete flow
echo "1. Visit: http://your-domain.com/auth/login"
echo "2. Click 'Forgot Password?' link"
echo "3. Enter email address"
echo "4. Check email for reset link"
echo "5. Click reset link"
echo "6. Enter new password"
echo "7. Verify login with new password"
```

### **Step 7: Monitor Deployment**

#### **7.1 Check Service Status**
```bash
# Check backend status
sudo systemctl status atm-backend
# OR
pm2 status atm-backend

# Check frontend status
sudo systemctl status atm-frontend
# OR
pm2 status atm-frontend
```

#### **7.2 Monitor Logs**
```bash
# Backend logs
tail -f /var/www/dash-atm/logs/backend.log

# Frontend logs
tail -f /var/www/dash-atm/logs/frontend.log

# Nginx logs (if applicable)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Step 8: Post-Deployment Checklist**

#### **8.1 Functional Testing**
- [ ] Login page loads correctly
- [ ] "Forgot Password?" link works
- [ ] Forgot password form submits successfully
- [ ] Email is sent and received
- [ ] Reset link redirects to correct page
- [ ] Password reset form works
- [ ] New password login is successful

#### **8.2 Security Verification**
- [ ] Reset tokens expire after 24 hours
- [ ] Used tokens cannot be reused
- [ ] Email contains correct reset link
- [ ] HTTPS is working (if configured)

#### **8.3 Performance Check**
- [ ] API response times are acceptable
- [ ] Frontend pages load quickly
- [ ] Email delivery is timely
- [ ] Database queries are efficient

### **3. Testing in Production**

#### **Email Functionality**
- [ ] Test forgot password with real email address
- [ ] Verify email delivery and formatting
- [ ] Test reset link functionality
- [ ] Confirm token expiration works

#### **Security Validation**
- [ ] Test token expiration (24 hours)
- [ ] Test single-use token validation
- [ ] Verify audit logging
- [ ] Test rate limiting (if applicable)

#### **User Experience**
- [ ] Test complete user flow
- [ ] Verify error messages
- [ ] Test on mobile devices
- [ ] Check email deliverability

## 🔧 **Troubleshooting**

### **Common Issues**

1. **Email not sending**
   - Check Mailjet API credentials
   - Verify sender email domain
   - Check Mailjet dashboard for delivery status

2. **Reset links not working**
   - Verify FRONTEND_BASE_URL is correct
   - Check that frontend routes are accessible
   - Confirm token format in emails

3. **Database errors**
   - Ensure password_reset_tokens table exists
   - Check database permissions
   - Verify connection settings

### **Rollback Plan**
If issues occur, rollback steps:
1. Revert git commits: `git reset --hard HEAD~1`
2. Restart services with previous version
3. Check logs for specific errors

## 📊 **Monitoring**

### **Logs to Monitor**
- Backend API logs for password reset requests
- Email delivery logs from Mailjet
- Frontend error logs for user experience issues
- Database query performance

### **Success Metrics**
- Password reset request success rate
- Email delivery rate
- Token validation success rate
- User completion rate of reset flow

## 📞 **Support Information**

### **Contact Points**
- Email: support@britimorleste.tl
- Documentation: Internal wiki/docs
- Emergency contact: System administrator

---

**Deployment Date:** [TO BE FILLED]
**Deployed By:** [TO BE FILLED]
**Version:** v2.1 - Password Reset Feature
