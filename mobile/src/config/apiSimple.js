// Simplified API configuration
export const API_CONFIG = {
  MAIN_API_URL: 'http://localhost:8000',
  USER_API_URL: 'http://localhost:8001',
  
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      LOGOUT: '/auth/logout',
      REFRESH: '/auth/refresh',
    },
    ATM: {
      STATUS_SUMMARY: '/api/v1/atm/status/summary',
      REGIONAL_DATA: '/api/v1/atm/status/regional',
      TERMINAL_DETAILS: '/api/v1/atm/terminal',
      CASH_INFO: '/api/v1/atm/cash',
    }
  }
};

export default API_CONFIG;
