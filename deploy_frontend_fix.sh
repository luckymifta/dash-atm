#!/bin/bash

echo "🚀 Deploying Frontend API URL Fix to VPS..."

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Updating .env.production file...${NC}"
cat > /tmp/env.production << 'EOF'
# API Configuration - Production HTTPS URLs
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api

# NextAuth Configuration
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=your-production-secret-here-change-this

# Application Configuration  
NODE_ENV=production
EOF

echo -e "${BLUE}Step 2: Copying updated frontend files...${NC}"
# Copy local files to VPS (you'll need to run this locally)
rsync -avz --delete \
  --exclude='node_modules' \
  --exclude='.next' \
  --exclude='.git' \
  /Users/luckymifta/Documents/2.\ AREA/dash-atm/frontend/ \
  root@staging.luckymifta.dev:/var/www/dash-atm/frontend/

echo -e "${BLUE}Step 3: Updating environment file on VPS...${NC}"
cp /tmp/env.production /var/www/dash-atm/frontend/.env.production

echo -e "${BLUE}Step 4: Installing dependencies and rebuilding...${NC}"
cd /var/www/dash-atm/frontend
npm install
rm -rf .next
npm run build

echo -e "${BLUE}Step 5: Restarting frontend service...${NC}"
systemctl restart dash-atm-frontend
systemctl status dash-atm-frontend

echo -e "${GREEN}✅ Deployment complete! Testing API connectivity...${NC}"

echo -e "${YELLOW}Testing API endpoints:${NC}"
curl -s https://staging.luckymifta.dev/api/v1/health | jq '.'
echo ""
curl -s https://staging.luckymifta.dev/api/v1/atm/status/summary | jq '.'

echo -e "${GREEN}✅ Frontend should now be using correct API URLs!${NC}"
echo -e "${YELLOW}🌐 Visit: https://staging.luckymifta.dev${NC}"
