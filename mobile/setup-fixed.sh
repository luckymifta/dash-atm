#!/bin/bash

# ATM Dashboard Mobile App Setup Script (Fixed)

echo "🚀 Setting up ATM Dashboard Mobile App with fixed configuration..."

# Navigate to mobile directory
cd "$(dirname "$0")"

# Remove any existing node_modules and package-lock.json to start fresh
echo "🧹 Cleaning up existing installations..."
rm -rf node_modules package-lock.json

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Install Expo CLI if not already installed
if ! command -v expo &> /dev/null; then
    echo "📱 Installing Expo CLI..."
    npm install -g @expo/cli
fi

# Create assets directory with placeholder files
echo "📁 Creating assets directory..."
mkdir -p assets

# Create placeholder icon files if they don't exist
if [ ! -f "assets/icon.png" ]; then
    echo "🖼️  Creating placeholder icon..."
    # Create a simple colored square as placeholder
    convert -size 1024x1024 xc:'#1976D2' assets/icon.png 2>/dev/null || echo "   (Skipping icon creation - install ImageMagick if you need custom icons)"
fi

if [ ! -f "assets/splash.png" ]; then
    echo "🖼️  Creating placeholder splash..."
    convert -size 1242x2436 xc:'#FFFFFF' assets/splash.png 2>/dev/null || echo "   (Skipping splash creation - install ImageMagick if you need custom splash)"
fi

if [ ! -f "assets/adaptive-icon.png" ]; then
    echo "🖼️  Creating placeholder adaptive icon..."
    convert -size 1024x1024 xc:'#1976D2' assets/adaptive-icon.png 2>/dev/null || echo "   (Skipping adaptive icon creation - install ImageMagick if you need custom icons)"
fi

if [ ! -f "assets/favicon.png" ]; then
    echo "🖼️  Creating placeholder favicon..."
    convert -size 48x48 xc:'#1976D2' assets/favicon.png 2>/dev/null || echo "   (Skipping favicon creation - install ImageMagick if you need custom favicon)"
fi

echo "✅ Setup completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Make sure your backend APIs are running:"
echo "   - Main API on http://localhost:8000"
echo "   - User Management API on http://localhost:8001"
echo ""
echo "2. Start the development server:"
echo "   expo start"
echo ""
echo "3. Test the app:"
echo "   - Scan QR code with Expo Go app on your phone"
echo "   - Or run: expo start --ios (for iOS simulator)"
echo "   - Or run: expo start --android (for Android emulator)"
echo ""
echo "🔧 If you encounter TypeScript errors:"
echo "   - Try: expo start --clear"
echo "   - Or: rm -rf node_modules && npm install"
echo ""
echo "📱 The app includes:"
echo "   ✅ Login/Logout functionality"
echo "   ✅ Dashboard with ATM status overview"
echo "   ✅ Terminal details with search & filtering"
echo "   ✅ Cash information with denomination breakdown"
