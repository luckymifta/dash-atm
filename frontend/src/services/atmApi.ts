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

// Individual ATM Historical Data Interfaces
interface ATMStatusPoint {
  timestamp: string;
  status: 'AVAILABLE' | 'WARNING' | 'WOUNDED' | 'ZOMBIE' | 'OUT_OF_SERVICE';
  location?: string;
  fault_description?: string;
  serial_number?: string;
}

interface ATMHistoricalData {
  terminal_id: string;
  terminal_name?: string;
  location?: string;
  serial_number?: string;
  historical_points: ATMStatusPoint[];
  time_period: string;
  summary_stats: {
    data_points: number;
    time_range_hours: number;
    requested_hours: number;
    status_distribution: Record<string, number>;
    status_percentages: Record<string, number>;
    uptime_percentage: number;
    first_reading: string;
    last_reading: string;
    status_changes: number;
    has_fault_data: boolean;
    fallback_message?: string;
  };
}

interface ATMHistoricalResponse {
  atm_data: ATMHistoricalData;
  chart_config: {
    chart_type: string;
    x_axis: {
      field: string;
      label: string;
      format: string;
    };
    y_axis: {
      field: string;
      label: string;
      categories: string[];
      colors: Record<string, string>;
    };
    tooltip: {
      include_fields: string[];
      timestamp_format: string;
    };
    legend: {
      show: boolean;
      position: string;
    };
  };
}

interface ATMListItem {
  terminal_id: string;
  location: string;
  current_status: string;
  serial_number: string;
  last_updated: string;
}

interface ATMListResponse {
  atms: ATMListItem[];
  total_count: number;
  filters_applied: {
    region_code?: string;
    status_filter?: string;
  };
}

// Refresh Job Interfaces
interface RefreshJobStatus {
  QUEUED: 'queued';
  RUNNING: 'running';
  COMPLETED: 'completed';
  FAILED: 'failed';
}

interface RefreshJobResponse {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  message: string;
  error?: string;
}

interface RefreshJobRequest {
  force?: boolean;
  use_new_tables?: boolean;
}

// Fault History Report Interfaces
interface FaultDurationData {
  fault_state: string;
  terminal_id: string;
  start_time: string;
  end_time?: string;
  duration_minutes?: number;
  fault_description?: string;
  fault_type?: string;
  component_type?: string;
  terminal_name?: string;
  location?: string;
}

interface FaultDurationSummary {
  total_faults: number;
  avg_duration_minutes: number;
  max_duration_minutes: number;
  min_duration_minutes: number;
  faults_resolved: number;
  faults_ongoing: number;
}

interface FaultHistoryReportResponse {
  fault_duration_data: FaultDurationData[];
  summary_by_state: Record<string, FaultDurationSummary>;
  overall_summary: FaultDurationSummary;
  date_range: {
    start_date: string;
    end_date: string;
  };
  terminal_count: number;
  chart_data: {
    duration_by_state: Array<{
      state: string;
      avg_duration_hours: number;
      total_faults: number;
      resolution_rate: number;
    }>;
    timeline_data: Array<{
      terminal_id: string;
      fault_state: string;
      start_time: string;
      duration_hours?: number;
      resolved: boolean;
    }>;
    colors: Record<string, string>;
  };
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
    return this.fetchApi<ATMSummaryResponse>(`${API_CONFIG.ENDPOINTS.SUMMARY}?table_type=${tableType}`);
  }

  async getRegionalData(regionCode?: string, tableType: 'legacy' | 'new' | 'both' = 'legacy'): Promise<RegionalResponse> {
    try {
      const params = new URLSearchParams({ table_type: tableType });
      if (regionCode) {
        params.append('region_code', regionCode);
      }
      return await this.fetchApi<RegionalResponse>(`${API_CONFIG.ENDPOINTS.REGIONAL}?${params}`);
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
        `${API_CONFIG.ENDPOINTS.TRENDS}/${regionCode}?hours=${hours}&table_type=${tableType}`
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
    return this.fetchApi<LatestDataResponse>(`${API_CONFIG.ENDPOINTS.LATEST}?${params}`);
  }

  async getHealth(): Promise<HealthResponse> {
    return this.fetchApi<HealthResponse>(API_CONFIG.ENDPOINTS.HEALTH);
  }

  async getTerminalDetails(
    tableType: 'legacy' | 'new' | 'both' = 'legacy',
    includeTerminalDetails: boolean = true
  ): Promise<TerminalDetailsResponse> {
    const params = new URLSearchParams({ 
      table_type: tableType,
      include_terminal_details: includeTerminalDetails.toString()
    });
    return this.fetchApi<TerminalDetailsResponse>(`${API_CONFIG.ENDPOINTS.LATEST}?${params}`);
  }

  // Individual ATM Historical Data Methods
  async getATMHistory(
    terminalId: string,
    hours: number = 168,
    includeFaultDetails: boolean = true
  ): Promise<ATMHistoricalResponse> {
    const params = new URLSearchParams({
      hours: hours.toString(),
      include_fault_details: includeFaultDetails.toString()
    });
    return this.fetchApi<ATMHistoricalResponse>(`/v1/atm/${terminalId}/history?${params}`);
  }

  async getATMList(
    regionCode?: string,
    statusFilter?: string,
    limit: number = 100
  ): Promise<ATMListResponse> {
    const params = new URLSearchParams({
      limit: limit.toString()
    });
    if (regionCode) params.append('region_code', regionCode);
    if (statusFilter) params.append('status_filter', statusFilter);
    
    return this.fetchApi<ATMListResponse>(`/v1/atm/list?${params}`);
  }

  // Refresh Methods
  async triggerRefresh(
    force: boolean = false,
    useNewTables: boolean = true
  ): Promise<RefreshJobResponse> {
    const response = await fetch(`${this.baseUrl}/v1/atm/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        force,
        use_new_tables: useNewTables
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getRefreshJobStatus(jobId: string): Promise<RefreshJobResponse> {
    return this.fetchApi<RefreshJobResponse>(`/v1/atm/refresh/${jobId}`);
  }

  async listRefreshJobs(
    limit: number = 10,
    status?: 'queued' | 'running' | 'completed' | 'failed'
  ): Promise<RefreshJobResponse[]> {
    const params = new URLSearchParams({
      limit: limit.toString()
    });
    if (status) params.append('status', status);
    
    return this.fetchApi<RefreshJobResponse[]>(`/v1/atm/refresh?${params}`);
  }

  // Fault History Report Methods
  async getFaultHistoryReport(
    startDate: string,
    endDate: string,
    terminalIds?: string,
    includeOngoing: boolean = true
  ): Promise<FaultHistoryReportResponse> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      include_ongoing: includeOngoing.toString()
    });
    
    if (terminalIds) {
      params.append('terminal_ids', terminalIds);
    }
    
    return this.fetchApi<FaultHistoryReportResponse>(`/v1/atm/fault-history-report?${params}`);
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
  ATMStatusPoint,
  ATMHistoricalData,
  ATMHistoricalResponse,
  ATMListItem,
  ATMListResponse,
  RefreshJobStatus,
  RefreshJobResponse,
  RefreshJobRequest,
  FaultDurationData,
  FaultDurationSummary,
  FaultHistoryReportResponse
};
