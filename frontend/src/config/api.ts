// API Configuration
export const API_CONFIG = {
  // Base URL for the FastAPI backend
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
  
  // API endpoints (relative paths since BASE_URL includes /api/v1)
  ENDPOINTS: {
    SUMMARY: '/atm/status/summary',
    REGIONAL: '/atm/status/regional',
    TRENDS: '/atm/status/trends',
    LATEST: '/atm/status/latest',
    HEALTH: '/health',
  },
  
  // Request timeouts (in milliseconds)
  TIMEOUT: 10000,
  
  // Refresh intervals (in milliseconds)
  REFRESH_INTERVAL: 30000, // 30 seconds
  
  // Default table type for API requests
  DEFAULT_TABLE_TYPE: 'legacy' as const,
} as const;

// Environment-specific configurations
export const ENV_CONFIG = {
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
  apiBaseUrl: API_CONFIG.BASE_URL,
};

export default API_CONFIG;
