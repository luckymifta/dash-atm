// API Configuration
export const API_CONFIG = {
  // Base URL for the FastAPI backend
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  
  // API endpoints
  ENDPOINTS: {
    SUMMARY: '/api/v1/atm/status/summary',
    REGIONAL: '/api/v1/atm/status/regional',
    TRENDS: '/api/v1/atm/status/trends',
    LATEST: '/api/v1/atm/status/latest',
    HEALTH: '/api/v1/health',
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
