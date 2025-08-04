# Quick Start Guide for ATM Dashboard Mobile App

## Step 1: Fix Import Errors & Install Dependencies

The TypeScript configuration has been updated to resolve import errors. Follow these steps:

```bash
cd mobile

# Clean install to avoid conflicts
rm -rf node_modules package-lock.json
npm install

# Install Expo CLI globally
npm install -g @expo/cli
```

## Step 2: Create Required Asset Files

Create placeholder assets to prevent import errors:

```bash
# Create assets directory
mkdir -p assets

# You can add your own custom icons later, or use placeholders for now
touch assets/icon.png
touch assets/splash.png  
touch assets/adaptive-icon.png
touch assets/favicon.png
```

## Step 3: Update Configuration

The API URLs in `src/config/api.ts` are already configured for development:

```typescript
export const API_CONFIG = {
  MAIN_API_URL: 'http://localhost:8000',     // Your main API
  USER_API_URL: 'http://localhost:8001',     // Your user management API
};
```

For production, update these URLs to your deployed backend URLs.

## Step 4: Ensure Backend APIs are Running

Make sure your FastAPI backends are running:

```bash
# Terminal 1 - Main API
cd backend
python api_option_2_fastapi_fixed.py    # Should run on port 8000

# Terminal 2 - User Management API  
cd backend
python user_management_api.py           # Should run on port 8001
```

## Step 5: Start the Mobile App

```bash
# In the mobile directory
expo start

# If you get TypeScript errors, try:
expo start --clear
```

This will open the Expo developer tools in your browser with a QR code.

## Step 6: Run on Device/Simulator

### Option A: Physical Device
1. Install "Expo Go" app from App Store (iOS) or Google Play (Android)
2. Scan the QR code with your camera (iOS) or Expo Go app (Android)

### Option B: Simulator
```bash
# For iOS Simulator (requires Xcode)
expo start --ios

# For Android Emulator (requires Android Studio)
expo start --android

# For web browser
expo start --web
```

## Fixed Issues:

✅ **TypeScript Import Errors**: Updated tsconfig.json to use standard React Native configuration
✅ **Expo Base Config**: Removed dependency on expo/tsconfig.base
✅ **Module Resolution**: Fixed React Native and Expo module imports
✅ **Asset References**: Added placeholder assets to prevent import errors

## Troubleshooting

### Common Issues:

1. **"Cannot find module" Errors**: 
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   expo start --clear
   ```

2. **TypeScript Errors**: 
   - The updated tsconfig.json should resolve most issues
   - If you see persistent errors, try disabling strict mode in tsconfig.json

3. **Network Connection Error**: 
   - Make sure your mobile device and computer are on the same WiFi network
   - Check that backend APIs are actually running and accessible

4. **Asset Import Errors**:
   - Make sure the assets directory exists with placeholder files
   - Run the setup-fixed.sh script to create all required assets

## Features Available:

✅ **Login Screen** - Authentication with your user management API
✅ **Dashboard** - ATM status overview with real-time data  
✅ **Terminal Details** - Searchable/filterable terminal list
✅ **Cash Information** - Denomination breakdown and cash levels

The mobile app reuses your existing API endpoints without requiring any changes to your backend code!
