# 🚀 Quick Ubuntu Deployment Commands - Password Reset Feature

## Copy-Paste Command Sections

### Section 1: Initial Setup & Backup
```bash
# SSH to server and navigate to project
ssh your-username@your-server-ip
cd /var/www/dash-atm

# Create backup
sudo cp -r /var/www/dash-atm /var/www/dash-atm-backup-$(date +%Y%m%d-%H%M%S)

# Pull latest changes
sudo git fetch origin
sudo git pull origin main
```

### Section 2: Backend Setup
```bash
# Navigate to backend
cd /var/www/dash-atm/backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify mailjet installation
pip list | grep mailjet
```

### Section 3: Configure Environment Variables
```bash
# Check/create .env.production
ls -la .env.production || sudo cp .env.example .env.production

# Edit environment file (ADD YOUR ACTUAL VALUES)
sudo nano .env.production
```

**Required variables to add/update:**
```env
# Mailjet Configuration
MAILJET_API_KEY=your_actual_mailjet_api_key_here
MAILJET_SECRET_KEY=your_actual_mailjet_secret_key_here
MAILJET_FROM_EMAIL=dash@britimorleste.tl
MAILJET_FROM_NAME=BRI ATM Dashboard

# Frontend URL
FRONTEND_BASE_URL=https://your-actual-domain.com

# Database (update if needed)
DATABASE_URL=postgresql://username:password@localhost:5432/dash_atm
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dash_atm
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### Section 4: Test Backend Configuration
```bash
# Test Python dependencies
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

# Test Mailjet connection
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

### Section 5: Frontend Setup
```bash
# Navigate to frontend
cd /var/www/dash-atm/frontend

# Install dependencies
npm install

# Check/create frontend .env.production
ls -la .env.production || sudo nano .env.production
```

**Frontend environment variables:**
```env
NEXT_PUBLIC_API_BASE_URL=https://your-actual-domain.com/api
NEXT_PUBLIC_API_URL=https://your-actual-domain.com/api
```

```bash
# Build frontend
npm run build
```

### Section 6: Service Management
```bash
# Stop current services
pm2 stop all

# Start backend
cd /var/www/dash-atm/backend
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name "dash-atm-backend"

# Start frontend
cd /var/www/dash-atm/frontend
pm2 start "npm start" --name "dash-atm-frontend"

# Save PM2 configuration
pm2 save

# Check status
pm2 status
```

### Section 7: Test Deployment
```bash
# Test backend health
curl -X GET "http://localhost:8000/health"

# Test frontend
curl -I http://localhost:3000

# Test password reset endpoint
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Check logs
pm2 logs dash-atm-backend --lines 10
pm2 logs dash-atm-frontend --lines 10
```

### Section 8: Nginx Reload (if needed)
```bash
# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

## 🚨 Emergency Rollback
```bash
# If something goes wrong, rollback
pm2 stop all
sudo rm -rf /var/www/dash-atm
sudo mv /var/www/dash-atm-backup-YYYYMMDD-HHMMSS /var/www/dash-atm
cd /var/www/dash-atm
pm2 start ecosystem.config.js
```

## ✅ Final Verification Commands
```bash
# Check all services
pm2 status

# Test password reset flow
echo "Visit: https://your-domain.com/auth/forgot-password"

# Monitor logs
pm2 logs --lines 20

# Check system resources
htop
df -h
```

---

## 🎯 Critical Steps Summary

1. **Backup first** - Always create backup before deployment
2. **Update environment variables** - Add Mailjet credentials and frontend URL
3. **Test connections** - Verify database and Mailjet work before starting services
4. **Monitor logs** - Check PM2 logs after starting services
5. **Test end-to-end** - Verify password reset flow works completely

## 📧 Mailjet Setup Reminder

To get Mailjet credentials:
1. Sign up at https://www.mailjet.com/
2. Go to Account Settings > API Keys
3. Create new API key pair
4. Add to .env.production file

## 🌐 Frontend URL Important Note

Make sure `FRONTEND_BASE_URL` in backend .env.production matches your actual domain:
- ✅ `https://your-actual-domain.com`
- ❌ `http://localhost:3000`

The reset email links use this URL to generate proper reset links!
