#!/bin/bash

# Node.js v20 Upgrade Script with Conflict Resolution
# Handles package conflicts when upgrading from v12.22.9 to v20

echo "=== Node.js v20 Upgrade Script ==="
echo "Current Node.js version:"
node --version

echo ""
echo "Step 1: Removing old Node.js packages completely..."

# Remove all Node.js related packages
sudo apt remove -y nodejs npm nodejs-doc libnode-dev libnode72
sudo apt autoremove -y

echo ""
echo "Step 2: Cleaning up Node.js files and directories..."

# Clean up any remaining Node.js files
sudo rm -rf /usr/local/bin/npm 
sudo rm -rf /usr/local/share/man/man1/node* 
sudo rm -rf ~/.npm
sudo rm -rf /usr/local/lib/node* 
sudo rm -rf /usr/local/bin/node* 
sudo rm -rf /usr/local/include/node*
sudo rm -rf /etc/apt/sources.list.d/nodesource.list*

# Clean up apt cache
sudo apt clean
sudo apt autoclean

echo ""
echo "Step 3: Adding NodeSource repository for Node.js 20..."

# Add NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

echo ""
echo "Step 4: Updating package lists..."
sudo apt update

echo ""
echo "Step 5: Installing Node.js 20..."

# Install Node.js (with conflict resolution)
sudo apt install -y nodejs || {
    echo "Installation failed, attempting conflict resolution..."
    
    # Configure any unconfigured packages
    sudo dpkg --configure -a
    
    # Fix broken dependencies
    sudo apt --fix-broken install -y
    
    # Try forcing the installation
    sudo apt install -y nodejs --fix-missing || {
        echo "Force installation with dpkg..."
        cd /var/cache/apt/archives/
        sudo dpkg -i --force-overwrite nodejs_*.deb
        sudo apt --fix-broken install -y
    }
}

echo ""
echo "Step 6: Installing PM2 globally..."

# Install PM2 globally
sudo npm install -g pm2

echo ""
echo "Step 7: Verifying installation..."

# Verify installation
echo "New Node.js version:"
node --version
echo "NPM version:"
npm --version
echo "PM2 version:"
pm2 --version

echo ""
echo "=== Node.js Upgrade Complete ==="

# Check if versions are correct
NODE_VERSION=$(node --version | sed 's/v//' | cut -d'.' -f1)
if [ "$NODE_VERSION" -ge 18 ]; then
    echo "✅ SUCCESS: Node.js v$(node --version) is compatible with Next.js 15"
    echo "✅ You can now proceed with npm install in your frontend directory"
else
    echo "❌ ERROR: Node.js version is still too old"
    echo "❌ Please check for any remaining conflicts"
    exit 1
fi

echo ""
echo "🎉 Ready to continue with deployment!"
