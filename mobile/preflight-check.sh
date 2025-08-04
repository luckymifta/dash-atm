#!/bin/bash

# Mobile App Pre-Flight Check Script

echo "🔍 Running pre-flight checks for ATM Dashboard Mobile App..."
echo ""

# Check if we're in the correct directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in mobile app directory. Please run from the mobile folder."
    exit 1
fi

echo "✅ In correct directory (mobile)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Error: Dependencies not installed. Run 'npm install' first."
    exit 1
fi

echo "✅ Dependencies installed"

# Check if assets directory exists
if [ ! -d "assets" ]; then
    echo "⚠️  Creating assets directory..."
    mkdir -p assets
    touch assets/icon.png assets/splash.png assets/adaptive-icon.png assets/favicon.png
fi

echo "✅ Assets directory ready"

# Check if Expo CLI is available
if ! command -v expo &> /dev/null; then
    echo "❌ Error: Expo CLI not found. Install with: npm install -g @expo/cli"
    exit 1
fi

echo "✅ Expo CLI available"

# Check if backend APIs are running
echo ""
echo "🌐 Checking backend APIs..."

# Check main API (port 8000)
if curl -s "http://localhost:8000/api/v1/health" > /dev/null 2>&1; then
    echo "✅ Main API (port 8000) is running"
else
    echo "⚠️  Main API (port 8000) is not responding"
    echo "   Start it with: python backend/api_option_2_fastapi_fixed.py"
fi

# Check user management API (port 8001)
if curl -s "http://localhost:8001/health" > /dev/null 2>&1; then
    echo "✅ User Management API (port 8001) is running"
else
    echo "⚠️  User Management API (port 8001) is not responding"
    echo "   Start it with: python backend/user_management_api.py"
fi

echo ""
echo "🚀 Pre-flight check complete!"
echo ""
echo "To start the mobile app:"
echo "1. Make sure both backend APIs are running"
echo "2. Run: expo start"
echo "3. Scan QR code with Expo Go app or run on simulator"
echo ""
echo "📱 Test credentials for login:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
