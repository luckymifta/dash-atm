#!/bin/bash

# Deploy ML Dependencies for Predictive Analytics - VPS Script
# This script pulls the latest changes and installs ML dependencies

echo "🚀 ATM Dashboard - ML Dependencies Deployment"
echo "=============================================="

# Check if running on VPS
if [[ $(hostname) != *"timles"* ]] && [[ $(whoami) != "root" ]]; then
    echo "❌ This script is designed to run on the VPS"
    echo "   Please run this on the VPS server"
    exit 1
fi

# Navigate to project directory
echo "📁 Navigating to project directory..."
cd /var/www/dash-atm || {
    echo "❌ Cannot find project directory /var/www/dash-atm"
    exit 1
}

# Pull latest changes
echo "🔄 Pulling latest changes from repository..."
git pull origin main || {
    echo "❌ Failed to pull latest changes"
    exit 1
}

# Check if requirements.txt has ML dependencies
echo "🔍 Checking requirements.txt for ML dependencies..."
if grep -q "numpy" backend/requirements.txt; then
    echo "✅ Found ML dependencies in requirements.txt"
else
    echo "❌ ML dependencies not found in requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
cd backend
source venv/bin/activate || {
    echo "❌ Failed to activate virtual environment"
    echo "   Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
}

# Upgrade pip first
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing ML dependencies..."
echo "   This may take several minutes for numpy, pandas, scikit-learn..."

# Install each package individually to handle potential issues
packages=(
    "numpy>=1.24.0"
    "pandas>=2.0.0"
    "scikit-learn>=1.3.0"
    "matplotlib>=3.7.0"
    "seaborn>=0.12.0"
)

for package in "${packages[@]}"; do
    echo "   Installing $package..."
    pip install "$package" || {
        echo "⚠️ Warning: Failed to install $package"
        echo "   Continuing with other packages..."
    }
done

# Install all requirements
echo "📦 Installing all requirements from requirements.txt..."
pip install -r requirements.txt || {
    echo "⚠️ Warning: Some packages may have failed to install"
    echo "   Checking critical dependencies..."
}

# Verify critical imports
echo "🔍 Verifying ML dependencies installation..."
python3 -c "
import sys
packages = ['numpy', 'pandas', 'sklearn', 'matplotlib', 'seaborn']
failed = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} - OK')
    except ImportError as e:
        print(f'❌ {pkg} - FAILED: {e}')
        failed.append(pkg)

if failed:
    print(f'\\n❌ Failed imports: {failed}')
    sys.exit(1)
else:
    print('\\n✅ All ML dependencies installed successfully!')
"

if [ $? -ne 0 ]; then
    echo "❌ ML dependencies verification failed"
    echo "   Attempting alternative installation method..."
    
    # Try installing with conda if available
    if command -v conda &> /dev/null; then
        echo "🔄 Trying conda installation..."
        conda install -y numpy pandas scikit-learn matplotlib seaborn
    else
        echo "❌ Conda not available, please check your Python environment"
        exit 1
    fi
fi

# Stop PM2 services
echo "🛑 Stopping PM2 services..."
pm2 stop dash-atm-main-api 2>/dev/null || echo "   Main API was not running"

# Wait a moment
sleep 2

# Start PM2 services
echo "🚀 Starting PM2 services..."
pm2 start dash-atm-main-api || {
    echo "❌ Failed to start main API with PM2"
    echo "   Trying manual start to check for errors..."
    
    echo "🔍 Testing API startup..."
    timeout 10 python3 api_option_2_fastapi_fixed.py || {
        echo "❌ API startup failed - checking for specific errors..."
        python3 -c "
import sys
try:
    import numpy as np
    print('✅ numpy import successful')
    import pandas as pd  
    print('✅ pandas import successful')
    from api_option_2_fastapi_fixed import app
    print('✅ FastAPI app import successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
        exit 1
    }
}

# Check PM2 status
echo "📊 Checking PM2 status..."
pm2 status

echo ""
echo "✅ ML Dependencies Deployment Complete!"
echo "========================================"
echo ""
echo "🧪 Next Steps:"
echo "1. Test the predictive analytics endpoints:"
echo "   curl http://localhost:8000/api/v1/health"
echo "   curl http://localhost:8000/api/v1/atm/147/predictive-analytics"
echo ""
echo "2. Check API logs:"
echo "   pm2 logs dash-atm-main-api"
echo ""
echo "3. Monitor system resources:"
echo "   htop"
echo ""
echo "📦 Installed ML Packages:"
echo "   ✅ numpy (numerical computing)"
echo "   ✅ pandas (data manipulation)"
echo "   ✅ scikit-learn (machine learning)"
echo "   ✅ matplotlib (plotting)"
echo "   ✅ seaborn (statistical visualization)"
