# Deploy API URL Fix to VPS

## Problem
The frontend is making requests to `/api/v1/api/v1/...` (URL duplication) instead of `/api/v1/...`, causing "API Disconnected" status and fallback to mock data.

## Solution
We've fixed the API configuration to remove the URL duplication by:
1. Changing `NEXT_PUBLIC_API_BASE_URL` from `https://staging.luckymifta.dev/api/v1` to `https://staging.luckymifta.dev/api`
2. Updating API endpoints to include `/v1` since BASE_URL now excludes it

## Deployment Steps

### Option 1: Run from Your Mac (Recommended)
1. **Upload files to VPS:**
   ```bash
   cd "/Users/luckymifta/Documents/2. AREA/dash-atm"
   
   # Upload the fixed frontend code
   rsync -avz --delete \
     --exclude='node_modules' \
     --exclude='.next' \
     --exclude='.git' \
     frontend/ \
     root@staging.luckymifta.dev:/var/www/dash-atm/frontend/
   ```

2. **SSH into VPS and apply fixes:**
   ```bash
   ssh root@staging.luckymifta.dev
   ```

### Option 2: Run Directly on VPS
1. **SSH into VPS:**
   ```bash
   ssh root@staging.luckymifta.dev
   ```

2. **Navigate to project and pull latest changes:**
   ```bash
   cd /var/www/dash-atm
   git stash push -m "Local VPS changes"
   git pull origin main
   ```

## VPS Commands (Run these on the VPS)

```bash
# 1. Navigate to frontend directory
cd /var/www/dash-atm/frontend

# 2. Update environment file with correct API URL
cat > .env.production << 'EOF'
# Production Environment Configuration for Frontend
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api
NODE_ENV=production
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
EOF

# 3. Clear build cache and rebuild
rm -rf .next
rm -rf node_modules/.cache
npm install

# 4. Build with production environment
NODE_ENV=production npm run build

# 5. Restart the frontend service
systemctl restart dash-atm-frontend
systemctl status dash-atm-frontend

# 6. Test the fix
echo "Testing API connectivity..."
curl -s https://staging.luckymifta.dev/api/v1/health | jq '.'
echo ""
curl -s https://staging.luckymifta.dev/api/v1/atm/status/summary | jq '.'
```

## Verification
After deployment, visit `https://staging.luckymifta.dev` and check:
1. ✅ Dashboard shows "API Connected" status (not "API Disconnected")
2. ✅ Real ATM data is displayed (not mock data)
3. ✅ No URL duplication in browser network tab (`/api/v1/...` not `/api/v1/api/v1/...`)
4. ✅ All API endpoints return real data

## Expected Results
- **Before:** Frontend shows "API Disconnected" and mock data
- **After:** Frontend shows "API Connected" and real ATM data from your backend APIs

## Files Changed
- `frontend/.env.production` - Fixed API base URL
- `frontend/src/config/api.ts` - Updated BASE_URL and endpoint paths
- `frontend/src/services/atmApi.ts` - Updated to use API_CONFIG.ENDPOINTS
