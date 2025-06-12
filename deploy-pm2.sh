#!/bin/bash

# 🚀 ATM Dashboard PM2 Quick Deployment Script
# This script provides a simplified deployment process using PM2

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored status messages
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

# Function to check if command executed successfully
check_status() {
    if [ $? -eq 0 ]; then
        print_success "$1"
    else
        print_error "$1 failed"
        exit 1
    fi
}

echo "======================================================"
echo "🚀 ATM Dashboard PM2 Deployment Script"
echo "======================================================"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Verify prerequisites
print_status "Checking prerequisites..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js v20.x first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version $NODE_VERSION is too old. Please install Node.js v20.x or higher."
    exit 1
fi
print_success "Node.js $(node -v) is installed"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    print_status "Installing PM2..."
    npm install -g pm2
    check_status "PM2 installation"
else
    print_success "PM2 $(pm2 -v) is already installed"
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed. Please install Python 3.11+."
    exit 1
fi
print_success "Python $(python3 --version) is installed"

# Check if application directory exists
if [ ! -d "/var/www/dash-atm" ]; then
    print_error "Application directory /var/www/dash-atm not found. Please clone the repository first."
    exit 1
fi
print_success "Application directory found"

print_status "Prerequisites check completed"
echo

# Navigate to application directory
cd /var/www/dash-atm

# Check if ecosystem.config.js exists
if [ ! -f "ecosystem.config.js" ]; then
    print_status "Creating PM2 ecosystem configuration..."
    cp ecosystem.config.js.example ecosystem.config.js 2>/dev/null || {
        print_warning "ecosystem.config.js.example not found, creating from template..."
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
        PORT: 8000,
        PYTHONPATH: '/var/www/dash-atm/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      error_file: '/var/log/dash-atm/main-api-error.log',
      out_file: '/var/log/dash-atm/main-api-out.log',
      log_file: '/var/log/dash-atm/main-api-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },
    {
      name: 'dash-atm-user-api',
      script: '/var/www/dash-atm/backend/venv/bin/python',
      args: '-m uvicorn user_management_api:app --host 0.0.0.0 --port 8001 --workers 2',
      cwd: '/var/www/dash-atm/backend',
      env: {
        NODE_ENV: 'production',
        PORT: 8001,
        PYTHONPATH: '/var/www/dash-atm/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      error_file: '/var/log/dash-atm/user-api-error.log',
      out_file: '/var/log/dash-atm/user-api-out.log',
      log_file: '/var/log/dash-atm/user-api-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
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
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      error_file: '/var/log/dash-atm/frontend-error.log',
      out_file: '/var/log/dash-atm/frontend-out.log',
      log_file: '/var/log/dash-atm/frontend-combined.log',
      time: true,
      merge_logs: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
EOF
    }
    check_status "PM2 ecosystem configuration created"
fi

# Create log directory
print_status "Setting up log directory..."
mkdir -p /var/log/dash-atm
chown -R www-data:www-data /var/log/dash-atm
chmod -R 755 /var/log/dash-atm
check_status "Log directory setup"

# Set proper permissions
print_status "Setting application permissions..."
chown -R www-data:www-data /var/www/dash-atm
chmod -R 755 /var/www/dash-atm
check_status "Application permissions set"

# Check backend environment
print_status "Checking backend environment..."
if [ ! -f "backend/.env" ]; then
    print_warning "Backend .env file not found. Please create it manually with your database credentials."
    echo "Example .env content:"
    echo "DB_HOST=localhost"
    echo "DB_PORT=5432"
    echo "DB_NAME=dash"
    echo "DB_USER=timlesdev"
    echo "DB_PASSWORD=timlesdev"
    echo
fi

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    print_status "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    check_status "Python virtual environment created"
else
    print_success "Python virtual environment exists"
fi

# Check frontend environment
print_status "Checking frontend environment..."
if [ ! -f "frontend/.env.production" ]; then
    print_warning "Frontend .env.production file not found. Creating template..."
    cat > frontend/.env.production << 'EOF'
# Production Environment Configuration for Frontend
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api/v1
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api
NODE_ENV=production
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF
    print_success "Frontend environment template created"
fi

# Build frontend
print_status "Building frontend application..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
rm -rf .next
rm -rf node_modules/.cache
NODE_ENV=production npm run build
cd ..
check_status "Frontend build completed"

# Stop existing PM2 processes
print_status "Stopping existing PM2 processes..."
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

# Start applications with PM2
print_status "Starting applications with PM2..."
pm2 start ecosystem.config.js
check_status "PM2 applications started"

# Save PM2 configuration
print_status "Saving PM2 configuration..."
pm2 save
check_status "PM2 configuration saved"

# Setup PM2 startup
print_status "Setting up PM2 startup script..."
pm2 startup systemd -u root --hp /root | tail -1 | bash
check_status "PM2 startup script configured"

# Wait for services to stabilize
print_status "Waiting for services to stabilize..."
sleep 10

# Health checks
print_status "Performing health checks..."

# Check PM2 status
echo "PM2 Process Status:"
pm2 status

echo
echo "Service Health Checks:"

# Check main API
MAIN_API_STATUS=$(curl -s -w "%{http_code}" http://localhost:8000/api/v1/health -o /dev/null 2>/dev/null || echo "000")
if [ "$MAIN_API_STATUS" = "200" ]; then
    print_success "Main API: Healthy (HTTP $MAIN_API_STATUS)"
else
    print_warning "Main API: Not responding (HTTP $MAIN_API_STATUS)"
fi

# Check user API
USER_API_STATUS=$(curl -s -w "%{http_code}" http://localhost:8001/health -o /dev/null 2>/dev/null || echo "000")
if [ "$USER_API_STATUS" = "200" ]; then
    print_success "User API: Healthy (HTTP $USER_API_STATUS)"
else
    print_warning "User API: Not responding (HTTP $USER_API_STATUS)"
fi

# Check frontend
FRONTEND_STATUS=$(curl -s -w "%{http_code}" http://localhost:3000 -o /dev/null 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    print_success "Frontend: Healthy (HTTP $FRONTEND_STATUS)"
else
    print_warning "Frontend: Not responding (HTTP $FRONTEND_STATUS)"
fi

# Show listening ports
echo
echo "Listening Ports:"
netstat -tlnp | grep -E ':(3000|8000|8001)' || echo "No services found on expected ports"

# Create health check script
print_status "Creating health check script..."
cat > health-check.sh << 'EOF'
#!/bin/bash

echo "=== ATM Dashboard Health Check ==="
echo "Timestamp: $(date)"
echo

# Check PM2 status
echo "📊 PM2 Process Status:"
pm2 jlist | jq -r '.[] | "\(.name): \(.pm2_env.status) (PID: \(.pid), Memory: \(.monit.memory / 1024 / 1024 | floor)MB, CPU: \(.monit.cpu)%)"' 2>/dev/null || pm2 status

echo
echo "🔍 API Health Checks:"

# Main API health check
MAIN_API=$(curl -s -w "%{http_code}" http://localhost:8000/api/v1/health -o /dev/null 2>/dev/null || echo "000")
if [ "$MAIN_API" = "200" ]; then
    echo "✅ Main API: Healthy (HTTP $MAIN_API)"
else
    echo "❌ Main API: Failed (HTTP $MAIN_API)"
fi

# User API health check
USER_API=$(curl -s -w "%{http_code}" http://localhost:8001/health -o /dev/null 2>/dev/null || echo "000")
if [ "$USER_API" = "200" ]; then
    echo "✅ User API: Healthy (HTTP $USER_API)"
else
    echo "❌ User API: Failed (HTTP $USER_API)"
fi

# Frontend health check
FRONTEND=$(curl -s -w "%{http_code}" http://localhost:3000 -o /dev/null 2>/dev/null || echo "000")
if [ "$FRONTEND" = "200" ]; then
    echo "✅ Frontend: Healthy (HTTP $FRONTEND)"
else
    echo "❌ Frontend: Failed (HTTP $FRONTEND)"
fi

echo
echo "📈 System Resources:"
echo "Memory Usage: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk Usage: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"

echo
echo "=== Health Check Complete ==="
EOF

chmod +x health-check.sh
check_status "Health check script created"

echo
echo "======================================================"
print_success "🎉 PM2 Deployment Completed Successfully!"
echo "======================================================"
echo
echo "📋 Deployment Summary:"
echo "  • Main API: http://localhost:8000/api/v1/health"
echo "  • User API: http://localhost:8001/health"
echo "  • Frontend: http://localhost:3000"
echo
echo "🛠️ Management Commands:"
echo "  • Check status: pm2 status"
echo "  • View logs: pm2 logs"
echo "  • Restart all: pm2 restart all"
echo "  • Health check: ./health-check.sh"
echo
echo "📝 Next Steps:"
echo "  1. Configure Nginx reverse proxy (if needed)"
echo "  2. Set up SSL certificate (if needed)"
echo "  3. Configure monitoring and alerts"
echo "  4. Test application functionality"
echo
echo "📖 For detailed instructions, see: PM2_DEPLOYMENT_GUIDE.md"
echo

# Show final status
print_status "Final system status:"
pm2 status
