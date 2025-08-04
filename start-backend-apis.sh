#!/bin/bash

echo "🚀 Starting ATM Dashboard Backend APIs..."

# Check if we're in the correct directory
if [ ! -f "backend/api_option_2_fastapi_fixed.py" ]; then
    echo "❌ Error: Please run this script from the dash-atm root directory"
    exit 1
fi

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

echo "📡 Checking ports..."
check_port 8000
check_port 8001

echo ""
echo "🔧 Starting User Management API (Port 8001)..."
osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'\" && python backend/user_management_api.py"'

sleep 2

echo "🔧 Starting Main ATM API (Port 8000)..."
osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'\" && python backend/api_option_2_fastapi_fixed.py"'

echo ""
echo "✅ Backend APIs are starting in separate Terminal windows"
echo "📱 Your mobile app should connect to:"
echo "   - User API: http://192.168.1.189:8001"
echo "   - Main API: http://192.168.1.189:8000"
echo ""
echo "🧪 Use the Network Test tab in your mobile app to verify connectivity"
