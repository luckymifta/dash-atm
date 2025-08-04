// Types for the mobile app - shared with web app
export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
  user?: User; // User data might not be included in some API responses
}

export interface ATMStatus {
  terminal_id: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance' | 'out_of_service';
  last_transaction: string;
  cash_level: number;
  uptime_percentage: number;
  coordinates?: {
    lat: number;
    lng: number;
  };
  serial_number?: string;
  fault_data?: {
    day: string;
    year: string;
    month: string;
    creationDate: string;
    externalFaultId: string;
    agentErrorDescription: string;
  } | null;
}

export interface ATMSummary {
  total_terminals: number;
  online: number;
  offline: number;
  maintenance: number;
  out_of_service: number;
  uptime_percentage: number;
}

// API Response from backend (different structure)
export interface ATMSummaryResponse {
  total_atms: number;
  status_counts: {
    available: number;
    warning: number;
    zombie: number;
    wounded: number;
    out_of_service: number;
    total: number;
  };
  overall_availability: number;
  total_regions: number;
  last_updated: string;
  data_source: string;
}

export interface RegionalData {
  region: string;
  terminals: ATMStatus[];
  summary: ATMSummary;
}

export interface CashInfo {
  terminal_id: string;
  denomination_20k: number;
  denomination_50k: number;
  denomination_100k: number;
  total_cash: number;
  last_refill: string;
  estimated_days_remaining: number;
}

export interface DashboardData {
  summary: ATMSummary;
  regional_data: RegionalData[];
  alerts: Alert[];
  recent_activities: Activity[];
}

export interface Alert {
  id: string;
  type: 'low_cash' | 'offline' | 'maintenance' | 'error';
  terminal_id: string;
  message: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface Activity {
  id: string;
  terminal_id: string;
  action: string;
  timestamp: string;
  user: string;
}
