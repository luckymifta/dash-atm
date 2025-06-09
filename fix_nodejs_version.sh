#!/bin/bash

# Fix Node.js Version for ATM Dashboard Deployment
# This script upgrades Node.js from v12 to v20 which is required for Next.js 15

echo "=== Node.js Version Fix for ATM Dashboard ==="
echo "Current Node.js version:"
node --version || echo "Node.js not found"

echo ""
echo "🔧 Fixing Node.js version to v20..."

# Remove existing Node.js and npm
echo "Removing old Node.js..."
apt remove -y nodejs npm

# Clean up any remaining files
rm -rf /usr/local/bin/node
rm -rf /usr/local/bin/npm
rm -rf /usr/local/lib/node_modules

# Add NodeSource repository for Node.js 20
echo "Adding NodeSource repository..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Install Node.js 20
echo "Installing Node.js 20..."
apt install -y nodejs

# Verify installation
echo ""
echo "✅ Installation complete!"
echo "New Node.js version:"
node --version
echo "New npm version:"
npm --version

# Install PM2 globally
echo ""
echo "Installing PM2 process manager..."
npm install -g pm2

echo ""
echo "🎉 Node.js upgrade complete!"
echo ""
echo "Now you can continue with frontend installation:"
echo "cd /var/www/dash-atm/frontend"
echo "npm install"
echo "NODE_ENV=production npm run build"
