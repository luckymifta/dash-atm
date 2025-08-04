#!/bin/bash

echo "🚀 Setting up Flutter ATM Dashboard Mobile App..."

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter is not installed. Please install Flutter first:"
    echo "   https://docs.flutter.dev/get-started/install"
    exit 1
fi

echo "📦 Installing dependencies..."
flutter pub get

echo "🔨 Generating model files..."
flutter packages pub run build_runner build --delete-conflicting-outputs

echo "🔍 Checking Flutter setup..."
flutter doctor

echo "✅ Setup complete!"
echo ""
echo "📱 To run the app:"
echo "   flutter run"
echo ""
echo "🔧 Make sure your FastAPI backends are running:"
echo "   Terminal 1: python backend/api_option_2_fastapi_fixed.py     # Port 8000"
echo "   Terminal 2: python backend/user_management_api.py             # Port 8001"
echo ""
echo "⚙️  Update API configuration:"
echo "   Edit lib/core/config/api_config.dart and update IP addresses"
