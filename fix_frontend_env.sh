#!/bin/bash
# Frontend Environment Variables Fix - Deploy to VPS
# Run this script on your VPS to fix the frontend localhost URL issue

echo "🔧 Fixing Frontend Environment Variables for Production"
echo "======================================================"

# Step 1: Navigate to frontend directory
cd /var/www/dash-atm/frontend || { echo "❌ Frontend directory not found"; exit 1; }

# Step 2: Backup existing environment files
echo "📦 Backing up existing environment files..."
cp .env.production .env.production.backup 2>/dev/null || echo "No existing .env.production to backup"
cp .env.local .env.local.backup 2>/dev/null || echo "No existing .env.local to backup"

# Step 3: Create proper .env.production file
echo "📝 Creating production environment configuration..."
cat > .env.production << 'EOF'
# Production Environment Configuration for Frontend
# API Configuration - Production HTTPS URLs
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api/v1
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api

# Environment
NODE_ENV=production

# NextAuth Configuration
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=

# Application Configuration
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF

# Step 4: Set proper permissions
echo "🔐 Setting proper permissions..."
chmod 644 .env.production
chown www-data:www-data .env.production

# Step 5: Remove/rename conflicting environment files
echo "🧹 Removing conflicting environment files..."
if [ -f .env.local ]; then
    mv .env.local .env.local.disabled
    echo "✅ Renamed .env.local to .env.local.disabled"
fi

# Step 6: Verify environment configuration
echo "🔍 Verifying environment configuration..."
echo "Contents of .env.production:"
cat .env.production

# Step 7: Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf .next
rm -rf node_modules/.cache

# Step 8: Rebuild frontend with production environment
echo "🔨 Rebuilding frontend with production environment..."
NODE_ENV=production npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

# Step 9: Restart PM2 frontend service
echo "🔄 Restarting frontend service..."
pm2 restart dash-atm-frontend

# Step 10: Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Step 11: Check service status
echo "📊 Checking service status..."
pm2 status dash-atm-frontend

# Step 12: Test the fix
echo "🧪 Testing the frontend fix..."
echo "Checking if frontend is responding..."
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend is responding locally" || echo "❌ Frontend not responding locally"

echo ""
echo "🎉 Frontend environment fix completed!"
echo "======================================"
echo ""
echo "📋 What was fixed:"
echo "  ✅ Created proper .env.production with HTTPS URLs"
echo "  ✅ Disabled conflicting .env.local file"
echo "  ✅ Rebuilt frontend with production environment"
echo "  ✅ Restarted PM2 frontend service"
echo ""
echo "🔗 Next steps:"
echo "  1. Test the application in browser: https://staging.luckymifta.dev"
echo "  2. Check browser network tab to verify HTTPS API calls"
echo "  3. Test login functionality with proper HTTPS endpoints"
echo ""
echo "🐛 If issues persist:"
echo "  - Check PM2 logs: pm2 logs dash-atm-frontend"
echo "  - Verify Nginx is running: sudo systemctl status nginx"
echo "  - Test individual services: curl https://staging.luckymifta.dev/health"
