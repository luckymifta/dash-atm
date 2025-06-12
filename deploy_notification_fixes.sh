#!/bin/bash

# ATM Dashboard Notification Service Fixes Deployment Script
# Deploys the latest notification service connection fixes and predictive analytics
# Version: 2.0.0 - Enhanced Notification System with Connection Recovery

set -e

echo "🔧 Starting Notification Service Fixes Deployment"
echo "=================================================="

# Configuration
PROJECT_DIR="/var/www/dash-atm"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
LOG_DIR="/var/log/atm-dashboard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running with proper permissions
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as a regular user with sudo privileges."
   exit 1
fi

# Function to check if a service is running
check_service() {
    if sudo systemctl is-active --quiet $1; then
        print_status "$1 is running"
        return 0
    else
        print_warning "$1 is not running"
        return 1
    fi
}

print_header "1. Updating repository to latest main branch"
cd ${PROJECT_DIR}

# Stop services before update
print_status "Stopping services for update..."
sudo systemctl stop atm-api.service || true
sudo systemctl stop nginx || true

# Pull latest changes from main branch
print_status "Pulling latest changes from main branch..."
sudo -u $USER git fetch origin
sudo -u $USER git checkout main
sudo -u $USER git pull origin main

if [ $? -eq 0 ]; then
    print_status "Repository updated successfully"
else
    print_error "Failed to update repository"
    exit 1
fi

print_header "2. Backend notification service updates"
cd ${BACKEND_DIR}

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Install/update Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Test notification service
print_status "Testing notification service connectivity..."
python3 -c "
import asyncio
import sys
sys.path.append('.')
from notification_service import NotificationService

async def test():
    try:
        service = NotificationService()
        await service.init_db_pool()
        print('✅ Notification service initialized successfully')
        
        current_statuses = await service.get_current_atm_statuses()
        print(f'✅ Got {len(current_statuses)} ATM statuses')
        
        await service.close_db_pool()
        print('✅ Notification service test completed')
        return True
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

success = asyncio.run(test())
sys.exit(0 if success else 1)
"

if [ $? -eq 0 ]; then
    print_status "Notification service test passed"
else
    print_error "Notification service test failed"
    exit 1
fi

print_header "3. Frontend updates"
cd ${FRONTEND_DIR}

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install

# Build frontend with predictive analytics
print_status "Building frontend with new features..."
NODE_ENV=production npm run build

if [ $? -eq 0 ]; then
    print_status "Frontend build completed successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

print_header "4. Database verification"
print_status "Verifying notification tables..."

python3 << 'EOF'
import asyncio
import asyncpg
import sys

async def verify_tables():
    try:
        conn = await asyncpg.connect(
            host='88.222.214.26',
            port=5432,
            database='development_db',
            user='timlesdev',
            password='timlesdev'
        )
        
        # Check notification tables
        tables = ['atm_notifications', 'atm_status_history']
        for table in tables:
            exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table}'
                )
            """)
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"✅ {table}: {count} records")
            else:
                print(f"❌ {table}: table missing")
                return False
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

success = asyncio.run(verify_tables())
sys.exit(0 if success else 1)
EOF

if [ $? -eq 0 ]; then
    print_status "Database verification passed"
else
    print_error "Database verification failed"
    exit 1
fi

print_header "5. Service restart and verification"

# Restart services
print_status "Starting ATM API service..."
sudo systemctl start atm-api.service
sleep 5

if check_service "atm-api.service"; then
    print_status "ATM API service started successfully"
else
    print_error "Failed to start ATM API service"
    sudo journalctl -u atm-api.service --no-pager -n 20
    exit 1
fi

print_status "Starting Nginx..."
sudo systemctl start nginx

if check_service "nginx"; then
    print_status "Nginx started successfully"
else
    print_error "Failed to start Nginx"
    exit 1
fi

print_header "6. API endpoint verification"

# Wait for services to be ready
sleep 10

# Test notification endpoints
print_status "Testing notification API endpoints..."

# Test unread count endpoint
response=$(curl -s -w "%{http_code}" -o /tmp/unread_response.json http://localhost:8000/api/v1/notifications/unread-count)
if [ "$response" -eq 200 ]; then
    unread_count=$(cat /tmp/unread_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['unread_count'])")
    print_status "Unread notifications endpoint working (count: $unread_count)"
else
    print_error "Unread notifications endpoint failed (HTTP $response)"
    cat /tmp/unread_response.json
    exit 1
fi

# Test notifications list endpoint
response=$(curl -s -w "%{http_code}" -o /tmp/notifications_response.json "http://localhost:8000/api/v1/notifications?limit=5")
if [ "$response" -eq 200 ]; then
    total_count=$(cat /tmp/notifications_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['total_count'])")
    print_status "Notifications list endpoint working (total: $total_count)"
else
    print_error "Notifications list endpoint failed (HTTP $response)"
    cat /tmp/notifications_response.json
    exit 1
fi

# Test status check endpoint
response=$(curl -s -w "%{http_code}" -o /tmp/status_check_response.json -X POST http://localhost:8000/api/v1/notifications/check-changes)
if [ "$response" -eq 200 ]; then
    success=$(cat /tmp/status_check_response.json | python3 -c "import sys, json; print(json.load(sys.stdin)['success'])")
    if [ "$success" = "True" ]; then
        print_status "Status check endpoint working"
    else
        print_error "Status check endpoint returned success=false"
        cat /tmp/status_check_response.json
        exit 1
    fi
else
    print_error "Status check endpoint failed (HTTP $response)"
    cat /tmp/status_check_response.json
    exit 1
fi

# Test predictive analytics endpoint
response=$(curl -s -w "%{http_code}" -o /tmp/predictive_response.json http://localhost:8000/api/v1/atm/predictive-analytics)
if [ "$response" -eq 200 ]; then
    print_status "Predictive analytics endpoint working"
else
    print_warning "Predictive analytics endpoint returned HTTP $response (may be expected if no data)"
fi

# Cleanup temp files
rm -f /tmp/unread_response.json /tmp/notifications_response.json /tmp/status_check_response.json /tmp/predictive_response.json

print_header "7. Deployment verification summary"

cat << EOF

🎉 Notification Service Fixes Deployment Complete!
==================================================

✅ Repository updated to latest main branch
✅ Backend notification service enhanced with connection recovery
✅ Frontend updated with predictive analytics features  
✅ Database tables verified and operational
✅ Services restarted successfully
✅ API endpoints tested and working

🔧 Key Features Deployed:
• Enhanced notification service with robust connection recovery
• Automatic reconnection and retry logic for database connections
• Improved error handling and graceful degradation
• Predictive analytics dashboard (frontend)
• ATM analytics modal components
• Comprehensive logging and monitoring

🌐 Your application is now available at:
   https://dash.luckymifta.dev

📊 Notification System Status:
• Bell notifications: Active and stable
• Background monitoring: Running every 5 minutes
• Connection recovery: Enabled with 3-retry logic
• Database pool: Optimized (1-5 connections)

📱 Frontend Features:
• Predictive Analytics page available
• Enhanced notification system
• Real-time status updates
• Improved error handling

🔍 Monitoring Commands:
# Check service status
sudo systemctl status atm-api.service
sudo systemctl status nginx

# View logs  
sudo journalctl -u atm-api.service -f
tail -f ${LOG_DIR}/api.log

# Test notification endpoints
curl https://dash.luckymifta.dev/api/v1/notifications/unread-count
curl https://dash.luckymifta.dev/api/v1/notifications?limit=5

Deployment completed successfully! 🎉

EOF

print_status "Deployment script completed successfully"
exit 0
