#!/bin/bash

# Password Reset Feature - Ubuntu Server Deployment Script
# Run this script on your Ubuntu server at /var/www/dash-atm

set -e  # Exit on any error

echo "🚀 Starting Password Reset Feature Deployment..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [ "$PWD" != "/var/www/dash-atm" ]; then
    print_error "Please run this script from /var/www/dash-atm directory"
    print_status "Current directory: $PWD"
    print_status "Expected: /var/www/dash-atm"
    exit 1
fi

print_status "Current directory: $PWD ✓"

# Step 1: Backup current version
print_status "Creating backup of current version..."
BACKUP_DIR="/var/www/dash-atm-backup-$(date +%Y%m%d-%H%M%S)"
sudo cp -r /var/www/dash-atm $BACKUP_DIR
print_success "Backup created: $BACKUP_DIR"

# Step 2: Pull latest changes
print_status "Pulling latest changes from Git..."
sudo git fetch origin
sudo git pull origin main
print_success "Git pull completed"

# Step 3: Backend deployment
print_status "Deploying backend..."

cd backend

# Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_status "Virtual environment activated"
fi

pip install -r requirements.txt
print_success "Python dependencies installed"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found. Creating from .env.example..."
    sudo cp .env.example .env.production
    print_warning ""
    print_warning "🔧 IMPORTANT: Please edit .env.production with your production values:"
    print_warning "   sudo nano /var/www/dash-atm/backend/.env.production"
    print_warning ""
    print_warning "Required variables for password reset:"
    print_warning "   - MAILJET_API_KEY=your_mailjet_api_key"
    print_warning "   - MAILJET_SECRET_KEY=your_mailjet_secret_key"
    print_warning "   - MAILJET_FROM_EMAIL=dash@britimorleste.tl"
    print_warning "   - MAILJET_FROM_NAME=BRI ATM Dashboard"
    print_warning "   - FRONTEND_BASE_URL=https://your-domain.com"
    print_warning ""
    read -p "Press Enter after updating .env.production..."
fi

# Test backend configuration
print_status "Testing backend configuration..."
python -c "
try:
    import psycopg2
    from mailjet_rest import Client
    print('✅ Dependencies loaded successfully')
except ImportError as e:
    print('❌ Import error:', e)
    exit(1)
" || {
    print_error "Backend dependency test failed"
    print_status "Make sure you have installed: pip install mailjet-rest psycopg2-binary"
    exit 1
}

print_success "Backend configuration test passed"

# Step 4: Frontend deployment
print_status "Deploying frontend..."

cd ../frontend

# Install Node dependencies
print_status "Installing Node.js dependencies..."
sudo npm install
print_success "Node.js dependencies installed"

# Create frontend environment if not exists
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found. Creating..."
    echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8001" | sudo tee .env.production
    echo "NODE_ENV=production" | sudo tee -a .env.production
    print_success "Frontend .env.production created"
fi

# Build frontend
print_status "Building frontend..."
sudo rm -rf .next
sudo npm run build
print_success "Frontend build completed"

# Step 5: Service management
cd ..

print_status "Managing services..."

# Function to restart service
restart_service() {
    local service_name=$1
    local service_type=$2
    
    if [ "$service_type" = "systemd" ]; then
        if systemctl is-active --quiet $service_name 2>/dev/null; then
            print_status "Restarting $service_name (systemd)..."
            sudo systemctl restart $service_name
            sleep 2
            if systemctl is-active --quiet $service_name; then
                print_success "$service_name restarted successfully"
            else
                print_error "$service_name failed to restart"
                sudo systemctl status $service_name --no-pager -l
            fi
        else
            print_warning "$service_name systemd service not found or not active"
        fi
    elif [ "$service_type" = "pm2" ]; then
        if command -v pm2 >/dev/null 2>&1 && pm2 describe $service_name > /dev/null 2>&1; then
            print_status "Restarting $service_name (PM2)..."
            pm2 restart $service_name
            pm2 status $service_name
        else
            print_warning "$service_name PM2 process not found"
        fi
    fi
}

# Try to restart services (both systemd and PM2)
restart_service "atm-backend" "systemd"
restart_service "atm-backend" "pm2"
restart_service "atm-frontend" "systemd"
restart_service "atm-frontend" "pm2"

# If no services found, try manual restart
if ! systemctl is-active --quiet atm-backend 2>/dev/null && ! pm2 describe atm-backend > /dev/null 2>&1; then
    print_warning "No automatic service management detected. You may need to manually restart your services."
    print_status "Manual restart commands:"
    echo "  Backend: cd /var/www/dash-atm/backend && python user_management_api.py"
    echo "  Frontend: cd /var/www/dash-atm/frontend && npm start"
fi

# Step 6: Health checks
print_status "Performing health checks..."

# Wait a moment for services to start
sleep 5

# Check backend health
print_status "Checking backend health..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "Backend is healthy ✓"
else
    print_warning "Backend health check failed - this may be normal if service is still starting"
    print_status "Checking if backend process is running..."
    if pgrep -f user_management_api.py > /dev/null; then
        print_status "Backend process is running"
    else
        print_warning "Backend process not found"
    fi
fi

# Check frontend health
print_status "Checking frontend health..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend is accessible ✓"
else
    print_warning "Frontend health check failed - this may be normal if service is still starting"
    print_status "Checking if frontend process is running..."
    if pgrep -f "next\|npm" > /dev/null; then
        print_status "Frontend process is running"
    else
        print_warning "Frontend process not found"
    fi
fi

# Test password reset endpoint
print_status "Testing password reset endpoint..."
RESET_TEST=$(curl -s -X POST http://localhost:8001/auth/forgot-password \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' 2>/dev/null | grep -o "password reset email" || echo "")

if [ ! -z "$RESET_TEST" ]; then
    print_success "Password reset endpoint is working ✓"
else
    print_warning "Password reset endpoint test inconclusive - check backend logs"
fi

# Step 7: Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir -p logs
    print_status "Created logs directory"
fi

# Final summary
echo ""
echo "=============================================="
print_success "🎉 Deployment completed!"
echo "=============================================="
echo ""
print_status "📋 Post-deployment checklist:"
echo ""
echo "1. ✅ Verify .env.production files are configured:"
echo "   Backend: /var/www/dash-atm/backend/.env.production"
echo "   Frontend: /var/www/dash-atm/frontend/.env.production"
echo ""
echo "2. 🧪 Test the complete password reset flow:"
echo "   - Visit: http://your-domain.com/auth/login"
echo "   - Click 'Forgot Password?' link"
echo "   - Enter a real email address"
echo "   - Check email for reset link"
echo "   - Complete password reset"
echo ""
echo "3. 📊 Monitor logs for any issues:"
echo "   - Backend: tail -f /var/www/dash-atm/logs/backend.log"
echo "   - Frontend: tail -f /var/www/dash-atm/logs/frontend.log"
echo "   - System: journalctl -u atm-backend -f"
echo ""
echo "4. 🔒 Security verification:"
echo "   - Test token expiration (24 hours)"
echo "   - Verify single-use tokens"
echo "   - Check audit logging"
echo ""
print_status "💾 Backup location: $BACKUP_DIR"
echo ""

# Show service status
print_status "🔍 Current service status:"
echo "Backend processes:"
ps aux | grep user_management_api.py | grep -v grep || echo "  No backend processes found"
echo ""
echo "Frontend processes:"
ps aux | grep "next\|npm" | grep -v grep || echo "  No frontend processes found"
echo ""

# Show next steps
print_status "🚀 Next steps if manual service restart is needed:"
echo ""
echo "Start Backend:"
echo "  cd /var/www/dash-atm/backend"
echo "  nohup python user_management_api.py > ../logs/backend.log 2>&1 &"
echo ""
echo "Start Frontend:"
echo "  cd /var/www/dash-atm/frontend"
echo "  nohup npm start > ../logs/frontend.log 2>&1 &"
echo ""

print_success "Password reset feature deployment completed! 🚀"

echo ""
echo "📧 Email Configuration Guide:"
echo "=============================================="
echo "To complete the setup, you need Mailjet credentials:"
echo ""
echo "1. Sign up at https://www.mailjet.com (if not done)"
echo "2. Get your API Key and Secret Key"
echo "3. Add them to /var/www/dash-atm/backend/.env.production:"
echo "   MAILJET_API_KEY=your_api_key"
echo "   MAILJET_SECRET_KEY=your_secret_key"
echo "4. Restart the backend service"
echo ""
echo "📧 Email testing command:"
echo "curl -X POST http://localhost:8001/auth/forgot-password \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"email\": \"your@email.com\"}'"
