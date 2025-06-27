# 🔧 Ubuntu Deployment Troubleshooting Guide

## 🚨 Common Issues & Solutions

### 1. Mailjet Connection Issues

#### Problem: "❌ Mailjet connection error"
```bash
# Check environment variables are set correctly
grep MAILJET /var/www/dash-atm/backend/.env.production

# Common issues:
# - Missing API keys
# - Wrong API keys  
# - Keys with extra spaces/quotes
```

**Solution:**
```bash
# Edit environment file carefully
sudo nano /var/www/dash-atm/backend/.env.production

# Ensure format is exactly:
MAILJET_API_KEY=your_key_without_quotes_or_spaces
MAILJET_SECRET_KEY=your_secret_without_quotes_or_spaces
MAILJET_FROM_EMAIL=dash@britimorleste.tl
MAILJET_FROM_NAME=BRI ATM Dashboard
```

#### Test Mailjet in Isolation:
```bash
cd /var/www/dash-atm/backend
source venv/bin/activate
python3 -c "
from mailjet_rest import Client
# Replace with your actual keys
mailjet = Client(auth=('your_api_key', 'your_secret'), version='v3.1')
data = {
    'Messages': [{
        'From': {'Email': 'dash@britimorleste.tl', 'Name': 'Test'},
        'To': [{'Email': 'your-email@example.com', 'Name': 'Test'}],
        'Subject': 'Test Email',
        'TextPart': 'This is a test email'
    }]
}
result = mailjet.send.create(data=data)
print('Status:', result.status_code)
print('Response:', result.json())
"
```

### 2. Database Connection Issues

#### Problem: "❌ Database connection error"
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Check if database exists
sudo -u postgres psql -c "\l" | grep dash_atm

# Check user permissions
sudo -u postgres psql -c "\du" | grep your_db_user
```

**Solution:**
```bash
# Start PostgreSQL if stopped
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database if missing
sudo -u postgres createdb dash_atm

# Create user if missing (replace with your credentials)
sudo -u postgres psql -c "CREATE USER your_db_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dash_atm TO your_db_user;"

# Test connection manually
psql -h localhost -U your_db_user -d dash_atm
```

### 3. PM2 Service Issues

#### Problem: Services not starting or crashing
```bash
# Check PM2 status
pm2 status

# Check detailed logs
pm2 logs dash-atm-backend --lines 50
pm2 logs dash-atm-frontend --lines 50

# Check if ports are in use
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :3000
```

**Solution:**
```bash
# Kill processes using the ports
sudo fuser -k 8000/tcp
sudo fuser -k 3000/tcp

# Restart PM2 completely
pm2 kill
pm2 start ecosystem.config.js

# Or start manually
cd /var/www/dash-atm/backend
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name "dash-atm-backend"

cd /var/www/dash-atm/frontend  
pm2 start "npm start" --name "dash-atm-frontend"
```

### 4. Frontend Build Issues

#### Problem: "npm run build" fails
```bash
# Check Node.js version
node --version
npm --version

# Check for build errors
cd /var/www/dash-atm/frontend
npm run build 2>&1 | tee build.log
```

**Solution:**
```bash
# Clear cache and reinstall
cd /var/www/dash-atm/frontend
rm -rf .next node_modules package-lock.json
npm install
npm run build

# If still failing, check environment variables
ls -la .env.production
cat .env.production

# Ensure .env.production has correct API URL
echo "NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api" | sudo tee .env.production
echo "NEXT_PUBLIC_API_URL=https://your-domain.com/api" | sudo tee -a .env.production
```

### 5. Nginx Configuration Issues

#### Problem: 502 Bad Gateway or 404 errors
```bash
# Check nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Check if services are running
curl -I http://localhost:3000
curl -I http://localhost:8000
```

**Solution:**
```bash
# Edit nginx configuration
sudo nano /etc/nginx/sites-available/dash-atm

# Ensure correct proxy_pass URLs:
# For frontend: proxy_pass http://localhost:3000;
# For API: proxy_pass http://localhost:8000;

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Permission Issues

#### Problem: Permission denied errors
```bash
# Check file permissions
ls -la /var/www/dash-atm/
ls -la /var/www/dash-atm/backend/
ls -la /var/www/dash-atm/frontend/
```

**Solution:**
```bash
# Fix permissions (adjust user as needed)
sudo chown -R www-data:www-data /var/www/dash-atm/
sudo chmod -R 755 /var/www/dash-atm/

# Or for your user:
sudo chown -R $USER:$USER /var/www/dash-atm/
chmod -R 755 /var/www/dash-atm/
```

### 7. Virtual Environment Issues

#### Problem: Python packages not found
```bash
# Check if venv exists
ls -la /var/www/dash-atm/backend/venv/

# Check if venv is activated
which python
echo $VIRTUAL_ENV
```

**Solution:**
```bash
# Create new virtual environment
cd /var/www/dash-atm/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verify mailjet installation
pip list | grep mailjet
```

### 8. Git Issues

#### Problem: Git pull fails or conflicts
```bash
# Check git status
cd /var/www/dash-atm
git status
git log --oneline -5
```

**Solution:**
```bash
# Stash local changes
git stash

# Pull latest changes
git pull origin main

# If conflicts, reset to remote
git reset --hard origin/main

# Or create new clone
cd /var/www/
sudo mv dash-atm dash-atm-old
sudo git clone https://github.com/your-username/dash-atm.git
sudo chown -R $USER:$USER dash-atm
```

### 9. Environment Variable Issues

#### Problem: Environment variables not loading
```bash
# Check if .env files exist
ls -la /var/www/dash-atm/backend/.env*
ls -la /var/www/dash-atm/frontend/.env*

# Check file contents (be careful with sensitive data)
head -5 /var/www/dash-atm/backend/.env.production
```

**Solution:**
```bash
# Recreate .env.production files
cd /var/www/dash-atm/backend
sudo cp .env.example .env.production
sudo nano .env.production

cd /var/www/dash-atm/frontend
sudo nano .env.production

# Ensure no extra quotes or spaces:
# ✅ MAILJET_API_KEY=abc123
# ❌ MAILJET_API_KEY="abc123"
# ❌ MAILJET_API_KEY= abc123
```

## 🔍 Diagnostic Commands

### System Health Check
```bash
# Check system resources
free -h
df -h
htop

# Check services
sudo systemctl status postgresql
sudo systemctl status nginx
pm2 status

# Check network connectivity
ping google.com
curl -I https://api.mailjet.com
```

### Application Health Check
```bash
# Test API endpoints
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/docs"

# Test password reset endpoint
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test frontend
curl -I http://localhost:3000
curl -I http://localhost:3000/auth/forgot-password
```

### Log Analysis
```bash
# Check all logs
pm2 logs --lines 50
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/syslog | grep dash-atm

# Check Python errors
cd /var/www/dash-atm/backend
python3 -c "
import main
print('✅ Backend imports successfully')
"
```

## 🆘 Emergency Recovery

### Complete Reset (Last Resort)
```bash
# Stop all services
pm2 kill
sudo systemctl stop nginx

# Restore from backup
sudo rm -rf /var/www/dash-atm
sudo mv /var/www/dash-atm-backup-YYYYMMDD-HHMMSS /var/www/dash-atm

# Start services
cd /var/www/dash-atm
pm2 start ecosystem.config.js
sudo systemctl start nginx
```

### Contact Support Checklist

Before asking for help, gather this information:
```bash
# System info
uname -a
cat /etc/os-release
node --version
python3 --version
postgres --version

# Service status
pm2 status
sudo systemctl status nginx
sudo systemctl status postgresql

# Recent logs
pm2 logs --lines 20
sudo tail -20 /var/log/nginx/error.log
```

---

## 📞 Quick Reference Commands

```bash
# Start everything
pm2 start all

# Stop everything  
pm2 stop all

# Restart everything
pm2 restart all

# Check status
pm2 status

# View logs
pm2 logs

# Test API
curl http://localhost:8000/health

# Test frontend
curl -I http://localhost:3000

# Edit backend config
sudo nano /var/www/dash-atm/backend/.env.production

# Edit frontend config
sudo nano /var/www/dash-atm/frontend/.env.production
```

Remember: Always create a backup before making changes! 🛡️
