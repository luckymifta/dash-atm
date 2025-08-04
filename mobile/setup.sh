#!/bin/bash

# ATM Dashboard Mobile App Setup Script

echo "🚀 Setting up ATM Dashboard Mobile App..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Navigate to mobile directory
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
npm install

# Install Expo CLI globally if not already installed
if ! command -v expo &> /dev/null; then
    echo "📱 Installing Expo CLI..."
    npm install -g @expo/cli
fi

# Check if Expo CLI is now available
if ! command -v expo &> /dev/null; then
    echo "⚠️  Please install Expo CLI manually: npm install -g @expo/cli"
    echo "   Then run: expo start"
else
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Update API URLs in src/config/api.ts"
    echo "2. Ensure your backend APIs are running:"
    echo "   - Main API on port 8000"
    echo "   - User Management API on port 8001"
    echo "3. Start the development server:"
    echo "   expo start"
    echo ""
    echo "📱 To run on devices:"
    echo "   - iOS: expo start --ios"
    echo "   - Android: expo start --android"
    echo "   - Web: expo start --web"
fi
