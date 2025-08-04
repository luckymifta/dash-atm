class ApiConfig {
  // Base URLs - Update these to match your local environment
  static const String mainApiUrl = 'http://192.168.1.124:8000';
  static const String userApiUrl = 'http://192.168.1.124:8001';
  
  // API Endpoints
  static const Map<String, String> endpoints = {
    // Authentication
    'login': '/auth/login',
    'logout': '/auth/logout',
    'refresh': '/auth/refresh',
    
    // ATM Data
    'atmSummary': '/api/v1/atm/status/summary',
    'regionalData': '/api/v1/atm/status/regional',
    'terminalDetails': '/api/v1/atm/status/latest',
    'cashInfo': '/api/v1/atm/cash-info',
  };
  
  // Request timeout configurations
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);
  
  // Headers
  static Map<String, String> get defaultHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };
  
  static Map<String, String> authHeaders(String token) => {
    ...defaultHeaders,
    'Authorization': 'Bearer $token',
  };
}
