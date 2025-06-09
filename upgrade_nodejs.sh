#!/bin/bash

# Node.js Version Upgrade Script for VPS
# Upgrades from Node.js v12.x to v20.x for Next.js compatibility

set -e

echo "🔧 Node.js Version Upgrade Script"
echo "================================"

# Check current Node.js version
echo "Current Node.js version:"
node --version 2>/dev/null || echo "Node.js not found"

echo ""
echo "📦 Starting Node.js upgrade process..."

# Remove old Node.js and npm
echo "1/6 Removing old Node.js installation..."
sudo apt remove -y nodejs npm || true

# Clean up any remaining Node.js files
echo "2/6 Cleaning up residual files..."
sudo rm -rf /usr/local/bin/npm /usr/local/share/man/man1/node* ~/.npm || true
sudo rm -rf /usr/local/lib/node* || true
sudo rm -rf /usr/local/bin/node* || true
sudo rm -rf /usr/local/include/node* || true

# Update package list
echo "3/6 Updating package list..."
sudo apt update

# Add NodeSource repository for Node.js 20
echo "4/6 Adding NodeSource repository..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Install Node.js 20
echo "5/6 Installing Node.js 20..."
sudo apt install -y nodejs

# Install PM2 globally
echo "6/6 Installing PM2 process manager..."
sudo npm install -g pm2

echo ""
echo "✅ Node.js upgrade completed!"
echo "================================"

# Verify installation
echo "📋 Verification:"
echo "Node.js version: $(node --version)"
echo "NPM version: $(npm --version)"
echo "PM2 version: $(pm2 --version)"

echo ""
echo "🎉 Ready for Next.js deployment!"
echo ""
echo "Next steps:"
echo "1. Navigate to your frontend directory: cd /var/www/dash-atm/frontend"
echo "2. Install dependencies: npm install"
echo "3. Build the application: NODE_ENV=production npm run build"
