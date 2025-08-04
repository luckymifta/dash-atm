# ATM Dashboard Mobile App (Flutter)

A professional mobile application built with Flutter/Dart for monitoring and managing ATM terminals. Features modern UI design with Material Design 3 and seamless integration with FastAPI backends.

## 🎯 Features

### ✅ Implemented
- **🔐 Professional Login Screen** - Modern UI with animated components and error handling
- **📱 Responsive Design** - Adaptive UI that works on all screen sizes
- **🎨 Modern Theme** - Professional color scheme with Inter font family
- **🔒 Secure Authentication** - Token-based auth with secure storage
- **📊 Navigation Structure** - Bottom navigation with Dashboard, Terminals, Cash Info

### 🚧 Coming Next (Step by step implementation)
- **📊 Dashboard Screen** - ATM summary with real-time statistics
- **🖥️ Terminal Details** - Comprehensive terminal monitoring
- **💰 Cash Information** - Cash level tracking and management

## 🚀 Quick Start

### Prerequisites
- Flutter SDK (>=3.13.0)
- Dart SDK (>=3.0.0)
- iOS Simulator or Android Emulator
- Your FastAPI backends running

### Installation

1. **Run the setup script:**
   ```bash
   cd mobile-flutter
   ./setup.sh
   ```

2. **Manual setup (alternative):**
   ```bash
   flutter pub get
   flutter packages pub run build_runner build
   ```

3. **Update API configuration:**
   Edit `lib/core/config/api_config.dart` and update the IP addresses:
   ```dart
   static const String mainApiUrl = 'http://YOUR_IP:8000';
   static const String userApiUrl = 'http://YOUR_IP:8001';
   ```

4. **Run the app:**
   ```bash
   flutter run
   ```

## 🔐 Demo Credentials

- **Username:** `admin`
- **Password:** `admin123`

## 🏗️ Project Structure

```
lib/
├── main.dart                          # App entry point
├── core/
│   ├── theme/
│   │   └── app_theme.dart            # App-wide theme and colors
│   └── config/
│       └── api_config.dart           # API endpoints and configuration
├── data/
│   ├── models/                       # Data models with Freezed
│   │   ├── user_model.dart
│   │   └── atm_model.dart
│   └── services/                     # API services
│       └── auth_service.dart
├── presentation/
│   ├── providers/                    # State management
│   │   └── auth_provider.dart
│   ├── screens/                      # UI screens
│   │   ├── splash_screen.dart
│   │   ├── login_screen.dart
│   │   ├── dashboard_screen.dart
│   │   ├── terminal_details_screen.dart
│   │   └── cash_info_screen.dart
│   └── widgets/                      # Reusable components
│       ├── custom_button.dart
│       ├── custom_text_field.dart
│       └── loading_overlay.dart
```

## 🎨 Design System

### Color Palette
- **Primary Blue:** #2563EB
- **Secondary Blue:** #3B82F6
- **Success Green:** #10B981
- **Warning Orange:** #F59E0B
- **Error Red:** #EF4444
- **Neutral Grays:** #FAFAFA to #171717

### Typography
- **Font Family:** Inter (Google Fonts)
- **Weights:** Regular (400), Medium (500), SemiBold (600), Bold (700)

### Components
- **Custom Buttons** - Elevated and outlined variants with loading states
- **Custom Text Fields** - Floating labels with focus animations
- **Loading Overlay** - Professional loading indicators
- **Animated Components** - Smooth transitions with animate_do

## 🔧 Dependencies

### Core
- `flutter_riverpod` / `provider` - State management
- `dio` - HTTP client for API calls
- `flutter_secure_storage` - Secure token storage
- `shared_preferences` - Local data persistence

### UI & Design
- `google_fonts` - Inter font family
- `phosphor_flutter` - Modern icon set
- `animate_do` - Smooth animations
- `flutter_screenutil` - Responsive design

### Code Generation
- `freezed` - Immutable data classes
- `json_annotation` - JSON serialization
- `build_runner` - Code generation

## 🔌 API Integration

The app connects to your existing FastAPI backends:

### Authentication API (Port 8001)
- `POST /auth/login` - User authentication
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Token refresh

### Main API (Port 8000)
- `GET /api/v1/atm/status/summary` - ATM summary statistics
- `GET /api/v1/atm/status/latest` - Terminal details with real-time data
- `GET /api/v1/atm/status/regional` - Regional ATM data

## 🧪 Testing the Login

1. **Start your backend APIs:**
   ```bash
   # Terminal 1
   python backend/api_option_2_fastapi_fixed.py
   
   # Terminal 2  
   python backend/user_management_api.py
   ```

2. **Update IP address in config**
3. **Run the Flutter app:**
   ```bash
   flutter run
   ```

4. **Test login with demo credentials**

## 📱 Screenshots

### Login Screen
- Modern gradient design
- Animated logo and form elements
- Interactive demo credentials
- Professional error handling
- Smooth focus transitions

### Navigation
- Clean bottom navigation
- Contextual icons
- Smooth transitions between screens

## 🔜 Next Steps

1. **Dashboard Implementation** - Real-time ATM statistics with charts
2. **Terminal Details** - Comprehensive monitoring with search and filters
3. **Cash Information** - Detailed cash management features
4. **Push Notifications** - Real-time alerts for ATM issues
5. **Offline Support** - Cached data for poor connectivity

## 🤝 Contributing

1. Create a feature branch from `feature/mobile-flutter`
2. Implement your changes
3. Test thoroughly on both iOS and Android
4. Submit a pull request

---

**Ready to build the future of ATM monitoring!** 🚀
