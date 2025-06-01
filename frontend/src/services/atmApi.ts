import { API_CONFIG } from '@/config/api';
import { mockRegionalData, generateMockTrends } from './mockApiData';

interface ATMStatusCounts {
  available: number;
  warning: number;
  wounded: number;
  zombie: number;
  out_of_service: number;
  total: number;
}

interface ATMSummaryResponse {
  total_atms: number;
  status_counts: ATMStatusCounts;
  overall_availability: number;
  total_regions: number;
  last_updated: string;
  data_source: string;
}

interface RegionalData {
  region_code: string;
  status_counts: ATMStatusCounts;
  availability_percentage: number;
  last_updated: string;
  health_status: 'HEALTHY' | 'ATTENTION' | 'WARNING' | 'CRITICAL';
}

interface RegionalResponse {
  regional_data: RegionalData[];
  total_regions: number;
  summary: ATMStatusCounts;
  last_updated: string;
}

interface TrendPoint {
  timestamp: string;
  status_counts: ATMStatusCounts;
  availability_percentage: number;
}

interface TrendResponse {
  region_code: string;
  time_period: string;
  trends: TrendPoint[];
  summary_stats: {
    data_points: number;
    time_range_hours: number;
    avg_availability: number;
    min_availability: number;
    max_availability: number;
    first_reading: string | null;
    last_reading: string | null;
  };
  // Enhanced fallback metadata
  requested_hours?: number;
  fallback_message?: string;
}

interface HealthResponse {
  status: string;
  timestamp: string;
  database_connected: boolean;
  api_version: string;
  uptime_seconds: number;
}

interface LatestDataResponse {
  data_sources: Array<{
    table: string;
    type: string;
    records: number;
    data: unknown[];
  }>;
  summary: {
    total_tables_queried: number;
    timestamp: string;
    table_type_requested: string;
  };
}

// Terminal Details Interfaces
interface TerminalFaultData {
  externalFaultId: string;
  agentErrorDescription: string;
  creation_date?: string;
  creation_date_timestamp?: string;
  fault_type_code?: string;
  component_type_code?: string;
  issue_state_name?: string;
  year?: string;
  month?: string;
  date?: string;
  terminalId?: number;
  serviceRequestId?: number;
  location?: string;
  bank?: string;
  brand?: string;
  model?: string;
  day?: string;
}

interface TerminalDetails {
  terminal_id: string;
  terminal_name?: string;
  external_id?: string;
  bank?: string;
  region?: string;
  city?: string;
  location?: {
    city: string;
    latitude?: number;
    longitude?: number;
  };
  location_str?: string;
  status?: string;
  status_code?: string;
  issue_state_name?: string;
  issue_state_code?: string;
  last_updated?: string;
  retrieval_timestamp?: string;
  response_status?: string;
  fault_list?: TerminalFaultData[];
  fault_count?: number;
  fault_data?: string | object; // Can be JSON string or parsed object
  serial_number?: string;
  fetched_status?: string;
  retrieved_date?: string;
  metadata?: string | object;
  body?: Array<{
    terminalId: string;
    networkId?: string;
    externalId?: string;
    brand?: string;
    model?: string;
    supplier?: string;
    location?: string;
    geoLocation?: string;
    terminalType?: string;
    osVersion?: string;
    issueStateName?: string;
    creationDate?: number;
    faultData?: TerminalFaultData[];
  }>;
}

interface TerminalDetailsResponse {
  data_sources?: Array<{
    table: string;
    type: string;
    records: number;
    data: TerminalDetails[];
  }>;
  terminal_details?: TerminalDetails[];
  summary?: {
    total_tables_queried: number;
    timestamp: string;
    table_type_requested: string;
  };
  timestamp?: string;
  count?: number;
}

class ATMApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_CONFIG.BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchApi<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  async getSummary(tableType: 'legacy' | 'new' | 'both' = 'legacy'): Promise<ATMSummaryResponse> {
    return this.fetchApi<ATMSummaryResponse>(`/api/v1/atm/status/summary?table_type=${tableType}`);
  }

  async getRegionalData(regionCode?: string, tableType: 'legacy' | 'new' | 'both' = 'legacy'): Promise<RegionalResponse> {
    try {
      const params = new URLSearchParams({ table_type: tableType });
      if (regionCode) {
        params.append('region_code', regionCode);
      }
      return await this.fetchApi<RegionalResponse>(`/api/v1/atm/status/regional?${params}`);
    } catch (error) {
      console.warn('Failed to fetch regional data from API, using mock data:', error);
      // Return mock data when API is unavailable
      return mockRegionalData as RegionalResponse;
    }
  }

  async getRegionalTrends(
    regionCode: string, 
    hours: number = 24, 
    tableType: 'legacy' | 'new' | 'both' = 'legacy'
  ): Promise<TrendResponse> {
    try {
      return await this.fetchApi<TrendResponse>(
        `/api/v1/atm/status/trends/${regionCode}?hours=${hours}&table_type=${tableType}`
      );
    } catch (error) {
      console.warn(`Failed to fetch trends for region ${regionCode} from API, using mock data:`, error);
      // Return mock trend data when API is unavailable
      return generateMockTrends(regionCode, hours) as TrendResponse;
    }
  }

  async getLatestData(
    tableType: 'legacy' | 'new' | 'both' = 'both',
    includeTerminalDetails: boolean = false
  ): Promise<LatestDataResponse> {
    const params = new URLSearchParams({ 
      table_type: tableType,
      include_terminal_details: includeTerminalDetails.toString()
    });
    return this.fetchApi<LatestDataResponse>(`/api/v1/atm/status/latest?${params}`);
  }

  async getHealth(): Promise<HealthResponse> {
    return this.fetchApi<HealthResponse>('/api/v1/health');
  }

  async getTerminalDetails(
    tableType: 'legacy' | 'new' | 'both' = 'legacy',
    includeTerminalDetails: boolean = true
  ): Promise<TerminalDetailsResponse> {
    const params = new URLSearchParams({ 
      table_type: tableType,
      include_terminal_details: includeTerminalDetails.toString()
    });
    return this.fetchApi<TerminalDetailsResponse>(`/api/v1/atm/status/latest?${params}`);
  }
}

// Create a singleton instance
export const atmApiService = new ATMApiService();

// Export types for use in components
export type {
  ATMStatusCounts,
  ATMSummaryResponse,
  RegionalData,
  RegionalResponse,
  TrendPoint,
  TrendResponse,
  HealthResponse,
  LatestDataResponse,
  TerminalFaultData,
  TerminalDetails,
  TerminalDetailsResponse,
};
