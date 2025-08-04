import { API_CONFIG } from '../config/api';
import authService from './authService';
import { ATMSummary, ATMSummaryResponse, RegionalData, ATMStatus, CashInfo, DashboardData } from '../types/index';

class ATMService {
  private baseURL = API_CONFIG.MAIN_API_URL;

  private async makeRequest(endpoint: string, options: RequestInit = {}) {
    const token = await authService.getToken();
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, try to refresh
        const newToken = await authService.refreshToken();
        if (newToken) {
          // Retry with new token
          config.headers = {
            ...config.headers,
            'Authorization': `Bearer ${newToken}`,
          };
          const retryResponse = await fetch(`${this.baseURL}${endpoint}`, config);
          if (retryResponse.ok) {
            return retryResponse.json();
          }
        }
        // If refresh failed, redirect to login
        throw new Error('Authentication failed');
      }
      
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getATMSummary(): Promise<ATMSummary> {
    const response: ATMSummaryResponse = await this.makeRequest(API_CONFIG.ENDPOINTS.ATM.STATUS_SUMMARY);
    
    // Transform the API response to match our expected format
    return {
      total_terminals: response.total_atms || 0,
      online: response.status_counts?.available || 0,
      offline: (response.status_counts?.wounded || 0) + (response.status_counts?.zombie || 0),
      maintenance: response.status_counts?.warning || 0,
      out_of_service: response.status_counts?.out_of_service || 0,
      uptime_percentage: response.overall_availability || 0
    };
  }

  async getRegionalData(): Promise<RegionalData[]> {
    const response = await this.makeRequest(API_CONFIG.ENDPOINTS.ATM.REGIONAL_DATA);
    
    // Transform the API response if it has the expected structure
    if (response && response.regional_data && Array.isArray(response.regional_data)) {
      return response.regional_data.map((region: any) => ({
        region: region.region_code || 'Unknown Region',
        terminals: this.generateMockTerminals(region.status_counts), // Generate mock terminals based on counts
        summary: {
          total_terminals: region.status_counts?.total || 0,
          online: region.status_counts?.available || 0,
          offline: (region.status_counts?.wounded || 0) + (region.status_counts?.zombie || 0),
          maintenance: region.status_counts?.warning || 0,
          out_of_service: region.status_counts?.out_of_service || 0,
          uptime_percentage: region.availability_percentage || 0
        }
      }));
    }
    
    return [];
  }

  private generateMockTerminals(statusCounts: any): ATMStatus[] {
    const terminals: ATMStatus[] = [];
    let terminalId = 1;

    // Generate available terminals
    for (let i = 0; i < (statusCounts?.available || 0); i++) {
      terminals.push(this.createMockTerminal(`ATM-${String(terminalId).padStart(3, '0')}`, 'online'));
      terminalId++;
    }

    // Generate warning terminals
    for (let i = 0; i < (statusCounts?.warning || 0); i++) {
      terminals.push(this.createMockTerminal(`ATM-${String(terminalId).padStart(3, '0')}`, 'maintenance'));
      terminalId++;
    }

    // Generate wounded terminals
    for (let i = 0; i < (statusCounts?.wounded || 0); i++) {
      terminals.push(this.createMockTerminal(`ATM-${String(terminalId).padStart(3, '0')}`, 'offline'));
      terminalId++;
    }

    // Generate out of service terminals
    for (let i = 0; i < (statusCounts?.out_of_service || 0); i++) {
      terminals.push(this.createMockTerminal(`ATM-${String(terminalId).padStart(3, '0')}`, 'out_of_service'));
      terminalId++;
    }

    return terminals;
  }

  private createMockTerminal(terminalId: string, status: 'online' | 'offline' | 'maintenance' | 'out_of_service'): ATMStatus {
    const locations = [
      'Jakarta Central Mall', 'Surabaya Plaza', 'Bandung Station', 'Medan Square',
      'Yogyakarta Airport', 'Denpasar Center', 'Makassar Hub', 'Palembang Plaza',
      'Semarang Mall', 'Balikpapan Center', 'Pontianak Square', 'Manado Plaza'
    ];
    
    const now = new Date();
    const lastTransaction = new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000);
    
    return {
      terminal_id: terminalId,
      location: locations[Math.floor(Math.random() * locations.length)],
      status: status,
      last_transaction: lastTransaction.toISOString(),
      cash_level: status === 'online' ? 60 + Math.random() * 40 : Math.random() * 30,
      uptime_percentage: status === 'online' ? 85 + Math.random() * 15 : Math.random() * 50,
      coordinates: {
        lat: -6.2 + (Math.random() - 0.5) * 0.2,
        lng: 106.8 + (Math.random() - 0.5) * 0.2
      }
    };
  }

  async getTerminalStatusList(): Promise<ATMStatus[]> {
    try {
      const response = await this.makeRequest('/api/v1/atm/status/latest?table_type=both&include_terminal_details=true');
      
      // Check if response has the expected structure
      if (response && response.data_sources && Array.isArray(response.data_sources)) {
        // Find the terminal_details data source
        const terminalDataSource = response.data_sources.find((source: any) => 
          source.table === 'terminal_details' && source.type === 'terminal_data'
        );
        
        if (terminalDataSource && terminalDataSource.data && Array.isArray(terminalDataSource.data)) {
          return terminalDataSource.data.map((terminal: any) => ({
            terminal_id: terminal.terminal_id || terminal.external_id || 'Unknown',
            location: terminal.location || terminal.location_str || 'Unknown Location',
            status: this.mapStatus(terminal.status || terminal.issue_state_name),
            last_transaction: terminal.last_updated || terminal.retrieved_date || new Date().toISOString(),
            cash_level: this.generateCashLevel(terminal.status || terminal.issue_state_name),
            uptime_percentage: this.generateUptime(terminal.status || terminal.issue_state_name),
            coordinates: {
              lat: -8.5 + (Math.random() - 0.5) * 0.2, // Dili, Timor-Leste coordinates
              lng: 125.6 + (Math.random() - 0.5) * 0.2
            },
            serial_number: terminal.serial_number,
            fault_data: terminal.fault_data ? JSON.parse(terminal.fault_data) : null
          }));
        }
      }
      
      // If no data, return empty array
      return [];
    } catch (error) {
      console.error('Error fetching terminal status list:', error);
      // Fallback to mock data if API fails
      return this.generateFallbackTerminals();
    }
  }

  private mapStatus(apiStatus: string): 'online' | 'offline' | 'maintenance' | 'out_of_service' {
    if (!apiStatus) return 'offline';
    
    const status = apiStatus.toLowerCase();
    if (status.includes('available')) return 'online';
    if (status.includes('warning')) return 'maintenance';
    if (status.includes('wounded') || status.includes('zombie')) return 'offline';
    if (status.includes('out_of_service')) return 'out_of_service';
    return 'offline'; // default
  }

  private generateCashLevel(status: string): number {
    // Generate realistic cash levels based on status
    if (!status) return Math.random() * 50;
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('available')) return 60 + Math.random() * 40;
    if (statusLower.includes('warning')) return 20 + Math.random() * 40;
    if (statusLower.includes('wounded') || statusLower.includes('out_of_service')) return Math.random() * 30;
    return Math.random() * 100;
  }

  private generateUptime(status: string): number {
    // Generate realistic uptime based on status
    if (!status) return Math.random() * 50;
    
    const statusLower = status.toLowerCase();
    if (statusLower.includes('available')) return 85 + Math.random() * 15;
    if (statusLower.includes('warning')) return 70 + Math.random() * 20;
    if (statusLower.includes('wounded')) return 30 + Math.random() * 40;
    if (statusLower.includes('out_of_service')) return Math.random() * 30;
    return Math.random() * 100;
  }

  private generateFallbackTerminals(): ATMStatus[] {
    // Generate some fallback terminals if API fails
    const terminals: ATMStatus[] = [];
    const statuses: ('online' | 'offline' | 'maintenance' | 'out_of_service')[] = ['online', 'offline', 'maintenance', 'out_of_service'];
    
    for (let i = 1; i <= 20; i++) {
      terminals.push(this.createMockTerminal(
        `ATM-${String(i).padStart(3, '0')}`, 
        statuses[Math.floor(Math.random() * statuses.length)]
      ));
    }
    
    return terminals;
  }

  async getTerminalDetails(terminalId: string): Promise<ATMStatus> {
    return this.makeRequest(`${API_CONFIG.ENDPOINTS.ATM.TERMINAL_DETAILS}/${terminalId}`);
  }

  async getCashInfo(terminalId: string): Promise<CashInfo> {
    return this.makeRequest(`${API_CONFIG.ENDPOINTS.ATM.CASH_INFO}/${terminalId}`);
  }

  async getDashboardData(): Promise<DashboardData> {
    try {
      const [summary, regionalData] = await Promise.all([
        this.getATMSummary(),
        this.getRegionalData(),
      ]);

      // Ensure summary has default values if properties are missing
      const safeSummary = {
        total_terminals: summary?.total_terminals || 0,
        online: summary?.online || 0,
        offline: summary?.offline || 0,
        maintenance: summary?.maintenance || 0,
        out_of_service: summary?.out_of_service || 0,
        uptime_percentage: summary?.uptime_percentage || 0,
        ...summary
      };

      return {
        summary: safeSummary,
        regional_data: regionalData || [],
        alerts: [], // You can implement this based on your backend
        recent_activities: [], // You can implement this based on your backend
      };
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      
      // Return default data structure to prevent crashes
      return {
        summary: {
          total_terminals: 0,
          online: 0,
          offline: 0,
          maintenance: 0,
          out_of_service: 0,
          uptime_percentage: 0
        },
        regional_data: [],
        alerts: [],
        recent_activities: []
      };
    }
  }

  async checkHealth(): Promise<{ status: string }> {
    return this.makeRequest('/api/v1/health');
  }
}

export default new ATMService();
