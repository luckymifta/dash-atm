# ATM Dashboard Mobile App

A React Native mobile application for managing ATM dashboard operations, built with Expo for cross-platform compatibility.

## Features

- **🔐 Authentication**: Secure login/logout using existing user management API
- **📊 Dashboard**: Real-time ATM status overview with interactive charts
- **🏧 Terminal Details**: Comprehensive terminal monitoring and filtering
- **💰 Cash Information**: Detailed cash level tracking and denomination breakdown
- **📱 Cross-Platform**: iOS and Android support with native performance
- **🔄 Real-time Updates**: Live data synchronization with backend APIs

## Tech Stack

- **Framework**: React Native with Expo
- **Navigation**: React Navigation v6
- **UI Components**: React Native Paper + Custom Components
- **State Management**: React Context API
- **Icons**: Expo Vector Icons
- **Storage**: AsyncStorage & SecureStore
- **API Integration**: Fetch with custom service layer

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo CLI
- iOS Simulator (for iOS development)
- Android Studio/Emulator (for Android development)

## Installation

1. **Clone and Navigate**:
   ```bash
   cd mobile
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Install Expo CLI** (if not already installed):
   ```bash
   npm install -g @expo/cli
   ```

4. **Update API Configuration**:
   Edit `src/config/api.ts` and update the API URLs to match your backend deployment:
   ```typescript
   export const API_CONFIG = {
     MAIN_API_URL: 'http://your-backend-url:8000',
     USER_API_URL: 'http://your-backend-url:8001',
     // ... other configs
   };
   ```

## Development

1. **Start Development Server**:
   ```bash
   expo start
   ```

2. **Run on Specific Platform**:
   ```bash
   # iOS
   expo start --ios
   
   # Android
   expo start --android
   
   # Web
   expo start --web
   ```

3. **QR Code Scanning**:
   - Install Expo Go app on your device
   - Scan the QR code from the terminal

## Project Structure

```
mobile/
├── src/
│   ├── components/         # Reusable UI components
│   ├── contexts/           # React contexts (Auth, etc.)
│   ├── screens/            # Screen components
│   │   ├── LoginScreen.tsx
│   │   ├── DashboardScreen.tsx
│   │   ├── TerminalDetailsScreen.tsx
│   │   └── CashInfoScreen.tsx
│   ├── services/           # API service layer
│   │   ├── authService.ts
│   │   └── atmService.ts
│   ├── types/              # TypeScript type definitions
│   └── config/             # App configuration
├── assets/                 # Images, fonts, etc.
├── App.tsx                 # Main app component
├── app.json               # Expo configuration
├── package.json           # Dependencies
└── tsconfig.json          # TypeScript config
```

## API Integration

The mobile app connects to your existing FastAPI backends:

### Main API (Port 8000)
- ATM status and monitoring data
- Dashboard analytics
- Regional information

### User Management API (Port 8001)
- User authentication
- Login/logout functionality
- User session management

### Mobile-Specific Features
- **Offline Support**: Caches essential data for offline viewing
- **Push Notifications**: ATM status alerts (configurable)
- **Biometric Auth**: Face ID/Touch ID for secure access
- **Location Services**: Find nearest ATMs

## Screen Descriptions

### 1. Login Screen
- **Purpose**: Secure authentication portal
- **Features**: 
  - Username/password input with validation
  - Professional branding with ATM dashboard theme
  - Error handling and loading states
  - Remember credentials option

### 2. Dashboard Screen
- **Purpose**: Real-time ATM network overview
- **Features**:
  - System uptime visualization
  - Status summary cards (Online/Offline/Maintenance)
  - Regional breakdown with interactive stats
  - Pull-to-refresh functionality

### 3. Terminal Details Screen
- **Purpose**: Individual ATM monitoring and management
- **Features**:
  - Searchable terminal list
  - Status filtering (All/Online/Offline/Maintenance)
  - Detailed terminal information
  - Cash level indicators with progress bars

### 4. Cash Information Screen
- **Purpose**: Financial monitoring and cash management
- **Features**:
  - Denomination breakdown (20K, 50K, 100K IDR)
  - Total cash calculations
  - Days remaining estimates
  - Last refill tracking
  - Sortable by multiple criteria

## Security Features

- **Token-Based Auth**: JWT tokens with automatic refresh
- **Secure Storage**: Sensitive data encrypted using Expo SecureStore
- **API Security**: All requests include proper authentication headers
- **Session Management**: Automatic logout on token expiration

## Customization

### Theming
The app uses a consistent color scheme:
- **Primary**: #1976D2 (Blue)
- **Success**: #4CAF50 (Green)
- **Warning**: #FF9800 (Orange)
- **Error**: #F44336 (Red)

### Adding New Features
1. Create new screen in `src/screens/`
2. Add route to navigation in `App.tsx`
3. Implement API calls in appropriate service
4. Update types in `src/types/index.ts`

## Building for Production

### Android
```bash
expo build:android
```

### iOS
```bash
expo build:ios
```

### Expo Application Services (EAS)
```bash
# Install EAS CLI
npm install -g @expo/eas-cli

# Configure build
eas build:configure

# Build for production
eas build --platform all
```

## Troubleshooting

### Common Issues

1. **Metro bundler issues**:
   ```bash
   expo start --clear
   ```

2. **Dependency conflicts**:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **API connection issues**:
   - Check API URLs in configuration
   - Ensure backend services are running
   - Verify network connectivity

### Development Tips

- Use React Native Debugger for debugging
- Enable hot reloading for faster development
- Test on both iOS and Android devices
- Use TypeScript for better development experience

## Future Enhancements

- **Offline Mode**: Complete offline functionality with sync
- **Push Notifications**: Real-time alerts for critical ATM issues
- **Biometric Authentication**: Face ID/Touch ID support
- **Dark Mode**: Theme switching capability
- **Localization**: Multi-language support
- **Analytics**: User interaction tracking
- **Maps Integration**: ATM location mapping

## Support

For technical support or feature requests, please contact the development team or create an issue in the project repository.

## License

This project is proprietary software for ATM dashboard management operations.
