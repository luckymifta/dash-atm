#!/bin/bash

# SPECIFIC Node.js Conflict Resolution Script
# Fixes the libnode-dev vs nodejs package conflict

echo "=== Node.js Conflict Resolution Script ==="
echo "This script specifically fixes the libnode-dev package conflict"
echo ""

echo "Current Node.js version: $(node --version 2>/dev/null || echo 'Not installed')"
echo ""

echo "Step 1: Force removing ALL conflicting Node.js packages..."
# Remove ALL conflicting packages at once
sudo apt remove -y libnode-dev libnode72 nodejs-doc nodejs npm --purge
sudo apt autoremove -y --purge

echo "Step 2: Removing conflicting files manually..."
# Remove the specific files that are causing conflicts
sudo rm -rf /usr/include/node*
sudo rm -rf /usr/share/nodejs*
sudo rm -rf /usr/local/bin/npm /usr/local/share/man/man1/node* ~/.npm
sudo rm -rf /usr/local/lib/node* /usr/local/bin/node* /usr/local/include/node*

echo "Step 3: Clearing package cache..."
# Clear apt cache completely
sudo apt clean
sudo apt autoclean
sudo rm -rf /var/cache/apt/archives/nodejs*

echo "Step 4: Downloading fresh Node.js package..."
# Download the package fresh
sudo apt update
sudo apt download nodejs

echo "Step 5: Force installing Node.js with overwrite..."
# Force install the package, overwriting conflicting files
sudo dpkg --force-overwrite -i nodejs_*nodesource*.deb

echo "Step 6: Fixing any remaining dependencies..."
# Fix any remaining broken dependencies
sudo apt --fix-broken install -y

echo "Step 7: Installing npm and PM2..."
# Install PM2
sudo npm install -g pm2

echo "Step 8: Final verification..."
echo "Node.js version: $(node --version)"
echo "NPM version: $(npm --version)"
echo "PM2 version: $(pm2 --version)"

echo ""
if [[ $(node --version) == v20* ]]; then
    echo "✅ SUCCESS! Node.js v20 installed successfully"
    echo "✅ The package conflict has been resolved"
    echo ""
    echo "Next steps:"
    echo "1. cd /var/www/dash-atm/frontend"
    echo "2. npm install"
    echo "3. NODE_ENV=production npm run build"
else
    echo "❌ INSTALLATION FAILED"
    echo "Current version: $(node --version)"
    echo ""
    echo "Try running these manual commands:"
    echo "sudo apt remove --purge -y libnode-dev libnode72"
    echo "sudo dpkg --force-overwrite -i /var/cache/apt/archives/nodejs_*nodesource*.deb"
    echo "sudo apt --fix-broken install"
fi

echo ""
echo "=== Conflict Resolution Complete ==="
