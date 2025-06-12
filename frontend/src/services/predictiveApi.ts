import { API_CONFIG } from '@/config/api';

// Types for Predictive Analytics API
export interface ComponentHealthScore {
  component_type: string;
  health_score: number;
  failure_risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  last_fault_date: string | null;
  fault_frequency: number;
}

export interface FailurePrediction {
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  prediction_horizon: string;
  confidence_level: number;
  contributing_factors: string[];
}

export interface MaintenanceRecommendation {
  component_type: string;
  recommendation: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  estimated_downtime?: string;
}

export interface ATMPredictiveAnalytics {
  terminal_id: string;
  location: string;
  overall_health_score: number;
  failure_prediction: FailurePrediction;
  component_health: ComponentHealthScore[];
  maintenance_recommendations: MaintenanceRecommendation[];
  data_quality_score: number;
  last_analysis: string;
  analysis_period: string;
}

export interface PredictiveAnalyticsResponse {
  atm_analytics: ATMPredictiveAnalytics;
  analysis_metadata: {
    data_points_analyzed: number;
    analysis_period_days: number;
    components_analyzed: number;
    algorithm_version: string;
    analysis_timestamp: string;
    data_source: string;
  };
}

export interface ATMSummaryItem {
  terminal_id: string;
  location: string;
  overall_health_score: number;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  critical_components: number;
  last_analysis: string;
}

export interface FleetStatistics {
  total_atms_analyzed: number;
  average_health_score: number;
  average_risk_score: number;
  risk_distribution: Record<string, number>;
  analysis_timestamp: string;
}

export interface PredictiveAnalyticsSummaryResponse {
  summary: ATMSummaryItem[];
  fleet_statistics: FleetStatistics;
}

class PredictiveApiService {
  private baseUrl: string;

  constructor() {
    // Use the base URL without /api suffix for predictive analytics endpoints
    const apiBaseUrl = API_CONFIG.BASE_URL;
    this.baseUrl = apiBaseUrl.replace('/api', ''); // Remove /api suffix if present
  }

  /**
   * Get predictive analytics for a specific ATM
   */
  async getATMPredictiveAnalytics(terminalId: string): Promise<PredictiveAnalyticsResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/atm/${terminalId}/predictive-analytics`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching ATM predictive analytics:', error);
      throw error;
    }
  }

  /**
   * Get predictive analytics summary for multiple ATMs
   */
  async getPredictiveAnalyticsSummary(
    riskLevelFilter?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
    limit: number = 20
  ): Promise<PredictiveAnalyticsSummaryResponse> {
    try {
      const params = new URLSearchParams();
      if (riskLevelFilter) {
        params.append('risk_level_filter', riskLevelFilter);
      }
      params.append('limit', limit.toString());

      const response = await fetch(
        `${this.baseUrl}/api/v1/atm/predictive-analytics/summary?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching predictive analytics summary:', error);
      throw error;
    }
  }

  /**
   * Get available terminals for predictive analytics
   */
  async getAvailableTerminals(): Promise<string[]> {
    try {
      // This endpoint might need to be implemented in the backend
      // For now, we'll use the existing ATM list endpoint
      const response = await fetch(`${this.baseUrl}/api/v1/atm/list`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.terminals || [];
    } catch (error) {
      console.error('Error fetching available terminals:', error);
      // Return some default terminals that we know have data
      return ['147', '2603', '2605', '49', '83', '169'];
    }
  }
}

export const predictiveApiService = new PredictiveApiService();
