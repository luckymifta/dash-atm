// API Configuration for mobile app
const isDevelopment = true; // Set to false for production

export const API_CONFIG = {
  // Update these URLs to match your deployment
  // Using local IP instead of localhost for iOS device compatibility
  MAIN_API_URL: isDevelopment ? 'http://192.168.1.189:8000' : 'https://your-main-api.com',
  USER_API_URL: isDevelopment ? 'http://192.168.1.189:8001' : 'https://your-user-api.com',
  MOBILE_API_URL: isDevelopment ? 'http://192.168.1.189:8002' : 'https://your-mobile-api.com',
  
  // API endpoints
  ENDPOINTS: {
    // User Management API (Port 8001)
    AUTH: {
      LOGIN: '/auth/login',
      LOGOUT: '/auth/logout',
      REFRESH: '/auth/refresh',
    },
    
    // Main API (Port 8000)
    ATM: {
      STATUS_SUMMARY: '/api/v1/atm/status/summary',
      REGIONAL_DATA: '/api/v1/atm/status/regional',
      TERMINAL_DETAILS: '/api/v1/atm/terminal',
      CASH_INFO: '/api/v1/atm/cash',
    },
    
    // Mobile-specific API (Port 8002) - Future implementation
    MOBILE: {
      DASHBOARD: '/mobile/dashboard',
      NOTIFICATIONS: '/mobile/notifications',
      USER_PREFERENCES: '/mobile/preferences',
    }
  }
};

export default API_CONFIG;
