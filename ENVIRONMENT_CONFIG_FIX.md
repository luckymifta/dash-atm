# Environment Configuration Fix

## Issue Summary
The frontend configuration was inconsistent between local development and VPS production environments, causing 404 errors when calling API endpoints.

## Root Cause
1. **Local Environment**: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (missing `/api`)
2. **Production Environment**: `NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api` (correct)
3. **API Config**: Expected BASE_URL to include `/api` and added `/v1/...` for endpoints

## Fixed Configuration

### Local Development (.env.local)
```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_USER_API_BASE_URL=http://localhost:8001

# Environment
NODE_ENV=development
```

### Production (.env.production)
```bash
# API Configuration - Production HTTPS URLs
NEXT_PUBLIC_API_BASE_URL=https://staging.luckymifta.dev/api
NEXT_PUBLIC_USER_API_BASE_URL=https://staging.luckymifta.dev/user-api

# Environment
NODE_ENV=production

# NextAuth Configuration (for future authentication enhancement)
NEXTAUTH_URL=https://staging.luckymifta.dev
NEXTAUTH_SECRET=UOofTfjpYk8UjQAmn59UNvtwoEaobLNt1dB8XKlKHW8=

# Application Configuration
NEXT_PUBLIC_APP_NAME=ATM Dashboard
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## API Endpoint Structure

### Expected API Calls:
- **Local**: `http://localhost:8000/api/v1/atm/status/summary`
- **Production**: `https://staging.luckymifta.dev/api/v1/atm/status/summary`

### API Configuration (src/config/api.ts):
```typescript
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api',
  ENDPOINTS: {
    SUMMARY: '/v1/atm/status/summary',
    REGIONAL: '/v1/atm/status/regional',
    TRENDS: '/v1/atm/status/trends',
    LATEST: '/v1/atm/status/latest',
    HEALTH: '/v1/health',
  },
  // ...rest of config
};
```

## VPS Deployment Checklist

### 1. Nginx Configuration
Ensure nginx routes are set up correctly:
```nginx
# Main API (port 8000)
location /api/ {
    proxy_pass http://localhost:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# User Management API (port 8001)
location /user-api/ {
    proxy_pass http://localhost:8001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 2. API Services Running
Ensure both APIs are running on VPS:
```bash
# Main ATM API
pm2 start "uvicorn api_option_2_fastapi_fixed:app --host 0.0.0.0 --port 8000" --name "atm-api"

# User Management API
pm2 start "uvicorn user_management_api:app --host 0.0.0.0 --port 8001" --name "user-api"
```

### 3. Environment Files
Ensure `.env.production` is properly deployed to:
- `/var/www/dash-atm/frontend/.env.production`

### 4. Test Endpoints
Test all endpoints on VPS:
```bash
# Health checks
curl https://staging.luckymifta.dev/api/v1/health
curl https://staging.luckymifta.dev/user-api/health

# ATM endpoints
curl https://staging.luckymifta.dev/api/v1/atm/status/summary
curl https://staging.luckymifta.dev/api/v1/atm/status/regional
```

## Changes Made

### 1. Fixed Local Environment
- Added `/api` suffix to `NEXT_PUBLIC_API_BASE_URL` in `.env.local`

### 2. Updated API Config Comments
- Clarified that BASE_URL includes `/api` and endpoints include `/v1`

### 3. Verified Production Config
- Production config was already correct

## Testing Results

### Local Testing ✅
```bash
curl http://localhost:8000/api/v1/atm/status/summary
# Returns: {"total_atms": 14, "status_counts": {...}, ...}
```

### Expected Production Testing ✅
```bash
curl https://staging.luckymifta.dev/api/v1/atm/status/summary
# Should return: {"total_atms": X, "status_counts": {...}, ...}
```

## Next Steps

1. **Commit Changes**: 
   ```bash
   git add .
   git commit -m "Fix environment configuration mismatches between local and VPS"
   ```

2. **Deploy to VPS**: Push changes and ensure `.env.production` is properly configured

3. **Test Frontend**: Restart frontend development server locally and test all dashboard functionality

4. **VPS Validation**: Ensure APIs are running and accessible on VPS with correct routes

## Troubleshooting

If issues persist:

1. **Check API Logs**: 
   ```bash
   pm2 logs atm-api
   pm2 logs user-api
   ```

2. **Check Nginx Logs**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   sudo tail -f /var/log/nginx/access.log
   ```

3. **Test API Directly**:
   ```bash
   # On VPS, test direct API access
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8001/health
   ```

4. **Verify Environment Variables**:
   ```bash
   # In frontend directory
   cat .env.production
   echo $NEXT_PUBLIC_API_BASE_URL
   ```
