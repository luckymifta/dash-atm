import { API_CONFIG } from '@/config/api';

// Cash Information Interfaces
export interface CashInformationData {
  terminal_id: string;
  business_code?: string;
  technical_code?: string;
  external_id?: string;
  location?: string;
  total_cash_amount?: number;
  total_currency?: string;
  cassette_count?: number;
  cassettes_data?: Record<string, unknown> | Array<Record<string, unknown>>;
  has_low_cash_warning?: boolean;
  has_cash_errors?: boolean;
  retrieval_timestamp?: string;
  event_date?: string;
  raw_cash_data?: Record<string, unknown>;
}

export interface CashInformationResponse {
  cash_data: CashInformationData[];
  total_count: number;
  summary: {
    total_terminals: number;
    total_records: number;
    average_cash_amount: number;
    total_cash_across_atms: number;
    cash_status_distribution: {
      LOW?: number;
      NORMAL?: number;
      ERROR?: number;
    };
    data_period_hours: number;
    latest_update?: string;
    oldest_update?: string;
  };
  filters_applied: {
    terminal_id?: string;
    location_filter?: string;
    cash_status?: string;
    hours_back: number;
    limit: number;
    include_raw_data?: boolean;
  };
  timestamp: string;
}

export interface CashSummaryResponse {
  summary: {
    total_terminals_with_cash_data: number;
    total_fleet_cash: number;
    average_cash_per_atm: number;
    cash_range: {
      minimum: number;
      maximum: number;
    };
    cash_status_distribution: {
      LOW: number;
      NORMAL: number;
      ERROR: number;
    };
    currency_distribution: {
      USD: number;
    };
  };
  alerts: {
    low_cash_terminals: number;
    error_terminals: number;
    terminals_needing_attention: Array<{
      terminal_id: string;
      business_code?: string;
      cash_amount: number;
      status: string;
      last_updated?: string;
    }>;
  };
  timestamp: string;
  data_source: string;
}

export interface TerminalData {
  terminal_id: string;
  location: string;
  business_code: string;
  display_text: string;
}

export interface TerminalsResponse {
  terminals: TerminalData[];
  total_count: number;
  timestamp: string;
}

class CashApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  private async makeRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Cash API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Get general cash information with optional filters
   */
  async getCashInformation(params?: {
    terminal_id?: string;
    location_filter?: string;
    cash_status?: string;
    hours_back?: number;
    limit?: number;
    include_raw_data?: boolean;
  }): Promise<CashInformationResponse> {
    const searchParams = new URLSearchParams();
    
    if (params?.terminal_id) searchParams.append('terminal_id', params.terminal_id);
    if (params?.location_filter) searchParams.append('location_filter', params.location_filter);
    if (params?.cash_status) searchParams.append('cash_status', params.cash_status);
    if (params?.hours_back) searchParams.append('hours_back', params.hours_back.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.include_raw_data !== undefined) searchParams.append('include_raw_data', params.include_raw_data.toString());

    const endpoint = `/v1/atm/cash-information${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return this.makeRequest<CashInformationResponse>(endpoint);
  }

  /**
   * Get cash information for a specific terminal
   */
  async getTerminalCashInformation(terminalId: string, params?: {
    hours_back?: number;
    include_raw_data?: boolean;
  }): Promise<CashInformationResponse> {
    const searchParams = new URLSearchParams();
    
    if (params?.hours_back) searchParams.append('hours_back', params.hours_back.toString());
    if (params?.include_raw_data !== undefined) searchParams.append('include_raw_data', params.include_raw_data.toString());

    const endpoint = `/v1/atm/${terminalId}/cash-information${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return this.makeRequest<CashInformationResponse>(endpoint);
  }

  /**
   * Get cash information summary for all terminals
   */
  async getCashSummary(): Promise<CashSummaryResponse> {
    return this.makeRequest<CashSummaryResponse>('/v1/atm/cash-information/summary');
  }

  /**
   * Get all distinct terminals with their locations
   */
  async getTerminals(): Promise<TerminalsResponse> {
    return this.makeRequest<TerminalsResponse>('/v1/atm/terminals');
  }
}

// Export singleton instance
export const cashApiService = new CashApiService();
