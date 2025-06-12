'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Shield,
  X
} from 'lucide-react';
import { 
  predictiveApiService,
  PredictiveAnalyticsResponse
} from '@/services/predictiveApi';

// Import Recharts components
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';

interface ATMAnalyticsModalProps {
  terminalId: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function ATMAnalyticsModal({ terminalId, isOpen, onClose }: ATMAnalyticsModalProps) {
  const [data, setData] = useState<PredictiveAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchATMAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await predictiveApiService.getATMPredictiveAnalytics(terminalId);
      setData(result);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ATM analytics');
      console.error('Error fetching ATM analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [terminalId]);

  useEffect(() => {
    if (isOpen && terminalId) {
      fetchATMAnalytics();
    }
  }, [isOpen, terminalId, fetchATMAnalytics]);

  if (!isOpen) return null;

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW':
        return 'text-green-600 bg-green-100';
      case 'MEDIUM':
        return 'text-yellow-600 bg-yellow-100';
      case 'HIGH':
        return 'text-orange-600 bg-orange-100';
      case 'CRITICAL':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'LOW':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'MEDIUM':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'HIGH':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'CRITICAL':
        return <Shield className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  // Prepare chart data
  const componentHealthData = data?.atm_analytics.component_health.map(comp => ({
    name: comp.component_type?.replace('_', ' ') ?? 'Unknown Component',
    health: comp.health_score,
    risk: comp.failure_risk,
    faults: comp.fault_frequency
  })) || [];

  const healthScoreData = data ? [{
    name: 'Health Score',
    value: data.atm_analytics.overall_health_score,
    fill: data.atm_analytics.overall_health_score >= 85 ? '#10B981' :
          data.atm_analytics.overall_health_score >= 70 ? '#F59E0B' :
          data.atm_analytics.overall_health_score >= 50 ? '#F97316' : '#EF4444'
  }] : [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">ATM Predictive Analytics</h2>
            <p className="text-gray-600 mt-1">Terminal ID: {terminalId}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-600">Loading analytics...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            </div>
          )}

          {data && (
            <div className="space-y-6">
              {/* ATM Overview */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">ATM Overview</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-600">Location</p>
                    <p className="text-lg font-semibold text-gray-900 truncate" title={data.atm_analytics.location}>
                      {data.atm_analytics.location}
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-600">Overall Health</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {data.atm_analytics.overall_health_score?.toFixed(1) ?? '0.0'}%
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-600">Data Quality</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {data.atm_analytics.data_quality_score?.toFixed(1) ?? '0.0'}%
                    </p>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <p className="text-sm font-medium text-gray-600">Analysis Period</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {data.atm_analytics.analysis_period}
                    </p>
                  </div>
                </div>
              </div>

              {/* Failure Prediction */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Risk Assessment */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Failure Risk Assessment</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Risk Level:</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(data.atm_analytics.failure_prediction.risk_level)}`}>
                        {data.atm_analytics.failure_prediction.risk_level}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Risk Score:</span>
                      <span className="text-lg font-semibold text-gray-900">
                        {data.atm_analytics.failure_prediction.risk_score?.toFixed(1) ?? '0.0'}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Prediction Horizon:</span>
                      <span className="text-gray-900 font-medium">
                        {data.atm_analytics.failure_prediction.prediction_horizon}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Confidence:</span>
                      <span className="text-gray-900 font-medium">
                        {data.atm_analytics.failure_prediction.confidence_level?.toFixed(1) ?? '0.0'}%
                      </span>
                    </div>

                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-600 mb-2">Contributing Factors:</p>
                      <ul className="space-y-1">
                        {(data.atm_analytics.failure_prediction.contributing_factors || []).map((factor, index) => (
                          <li key={index} className="text-sm text-gray-700 flex items-center">
                            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Health Score Visualization */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Health Score</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={healthScoreData}>
                        <RadialBar dataKey="value" cornerRadius={10} fill={healthScoreData[0]?.fill} />
                        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-2xl font-bold fill-gray-900">
                          {data.atm_analytics.overall_health_score?.toFixed(1) ?? '0.0'}%
                        </text>
                      </RadialBarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Component Health */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Component Health Analysis</h3>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Component Health Chart */}
                  <div>
                    <h4 className="text-md font-medium text-gray-700 mb-3">Health Scores by Component</h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={componentHealthData} layout="horizontal">
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" domain={[0, 100]} />
                          <YAxis dataKey="name" type="category" width={100} />
                          <Tooltip />
                          <Bar dataKey="health" fill="#3B82F6" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Component Details Table */}
                  <div>
                    <h4 className="text-md font-medium text-gray-700 mb-3">Component Details</h4>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {(data.atm_analytics.component_health || []).map((component, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">
                              {component.component_type?.replace('_', ' ') ?? 'Unknown Component'}
                            </span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(component.failure_risk)}`}>
                              {component.failure_risk}
                            </span>
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <div className="flex justify-between">
                              <span>Health Score:</span>
                              <span className="font-medium">{component.health_score?.toFixed(1) ?? '0.0'}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Fault Frequency:</span>
                              <span className="font-medium">{component.fault_frequency}</span>
                            </div>
                            {component.last_fault_date && (
                              <div className="flex justify-between">
                                <span>Last Fault:</span>
                                <span className="font-medium">
                                  {new Date(component.last_fault_date).toLocaleDateString()}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Maintenance Recommendations */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Maintenance Recommendations</h3>
                
                {(data.atm_analytics.maintenance_recommendations || []).length > 0 ? (
                  <div className="space-y-4">
                    {(data.atm_analytics.maintenance_recommendations || []).map((recommendation, index) => (
                      <div key={index} className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-lg">
                        <div className="flex items-start">
                          <div className="flex-shrink-0 mr-3 mt-1">
                            {getPriorityIcon(recommendation.priority)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-900">
                                {recommendation.component_type?.replace('_', ' ') ?? 'Unknown Component'} Maintenance
                              </h4>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(recommendation.priority)}`}>
                                {recommendation.priority} Priority
                              </span>
                            </div>
                            <p className="text-gray-700 mb-2">{recommendation.recommendation}</p>
                            {recommendation.estimated_downtime && (
                              <p className="text-sm text-gray-600">
                                <Clock className="h-4 w-4 inline mr-1" />
                                Estimated downtime: {recommendation.estimated_downtime}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-600 text-center py-4">No maintenance recommendations at this time.</p>
                )}
              </div>

              {/* Analysis Metadata */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Analysis Details</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-600">
                  <div>
                    <span className="font-medium">Data Points:</span>
                    <br />
                    {data.analysis_metadata.data_points_analyzed}
                  </div>
                  <div>
                    <span className="font-medium">Algorithm:</span>
                    <br />
                    {data.analysis_metadata.algorithm_version}
                  </div>
                  <div>
                    <span className="font-medium">Components:</span>
                    <br />
                    {data.analysis_metadata.components_analyzed}
                  </div>
                  <div>
                    <span className="font-medium">Last Updated:</span>
                    <br />
                    {new Date(data.atm_analytics.last_analysis).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
