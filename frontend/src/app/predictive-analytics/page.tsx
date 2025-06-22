'use client';

import { useEffect, useState, useCallback } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import ATMAnalyticsModal from '@/components/ATMAnalyticsModal';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  RefreshCw,
  TrendingUp,
  Wrench,
  Shield,
  Database,
  Eye
} from 'lucide-react';
import { 
  predictiveApiService,
  PredictiveAnalyticsSummaryResponse
} from '@/services/predictiveApi';

// Import Recharts components
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

export default function PredictiveAnalyticsPage() {
  const [summaryData, setSummaryData] = useState<PredictiveAnalyticsSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRiskFilter, setSelectedRiskFilter] = useState<string>('ALL');
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTerminalId, setSelectedTerminalId] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);

  const fetchPredictiveData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const riskFilter = selectedRiskFilter === 'ALL' ? undefined : selectedRiskFilter as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
      const result = await predictiveApiService.getPredictiveAnalyticsSummary(riskFilter, 20);
      setSummaryData(result);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch predictive analytics data');
      console.error('Error fetching predictive analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedRiskFilter]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchPredictiveData();
    setRefreshing(false);
  };

  const handleViewDetails = (terminalId: string) => {
    setSelectedTerminalId(terminalId);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedTerminalId(null);
  };

  // Helper function to filter out invalid location records
  const getValidATMRecords = () => {
    if (!summaryData?.summary) return [];
    
    const validRecords = summaryData.summary.filter((atm) => {
      // Filter out records with invalid or missing location information
      if (!atm.location || atm.location.trim() === "") return false;
      
      // Filter out connection failure records (be robust with variations)
      const location = atm.location.toLowerCase().trim();
      const invalidPatterns = [
        'connection lost',
        'tl-dl',
        'tl dl',
        'auth_failed',
        'auth failed',
        'network_failed',
        'network failed',
        'timeout',
        'connection_error',
        'connection error'
      ];
      
      return !invalidPatterns.some(pattern => location.includes(pattern));
    });

    // Remove duplicates based on terminal_id, but prioritize records with better data
    const uniqueRecords = validRecords.reduce((acc, atm) => {
      const existingIndex = acc.findIndex(existing => existing.terminal_id === atm.terminal_id);
      
      if (existingIndex === -1) {
        // No duplicate found, add the record
        acc.push(atm);
      } else {
        // Duplicate found, keep the one with better data quality
        const existing = acc[existingIndex];
        
        // Prioritize records with:
        // 1. Higher health score
        // 2. More complete location (longer, more descriptive)
        // 3. Better risk level data
        const currentScore = (atm.overall_health_score || 0) + (atm.location?.length || 0);
        const existingScore = (existing.overall_health_score || 0) + (existing.location?.length || 0);
        
        if (currentScore > existingScore) {
          acc[existingIndex] = atm; // Replace with better record
        }
        // Otherwise keep the existing one
      }
      
      return acc;
    }, [] as typeof validRecords);

    return uniqueRecords;
  };

  useEffect(() => {
    fetchPredictiveData();
  }, [fetchPredictiveData]);

  // Calculate statistics from valid records only
  const validRecords = getValidATMRecords();
  
  // Prepare chart data using valid records only
  const riskDistributionData = validRecords.length > 0 ? 
    validRecords.reduce((acc, atm) => {
      const risk = atm.risk_level || 'UNKNOWN';
      acc[risk] = (acc[risk] || 0) + 1;
      return acc;
    }, {} as Record<string, number>) : {};

  const riskChartData = Object.entries(riskDistributionData).map(([risk, count]) => ({
    name: risk,
    value: count,
    percentage: validRecords.length > 0 ? 
      ((count / validRecords.length) * 100).toFixed(1) : '0'
  }));

  const healthScoreDistribution = validRecords.length > 0 ?
    validRecords.reduce((acc, atm) => {
      if (atm.overall_health_score !== undefined) {
        const bucket = Math.floor(atm.overall_health_score / 10) * 10;
        const key = `${bucket}-${bucket + 9}%`;
        acc[key] = (acc[key] || 0) + 1;
      }
      return acc;
    }, {} as Record<string, number>) : {};

  // Calculate fleet statistics from valid records
  const validFleetStats = {
    total_atms_analyzed: validRecords.length,
    average_health_score: validRecords.length > 0 ? 
      validRecords.reduce((sum, atm) => sum + (atm.overall_health_score || 0), 0) / validRecords.length : 0,
    average_risk_score: validRecords.length > 0 ? 
      validRecords.reduce((sum, atm) => sum + (atm.risk_score || 0), 0) / validRecords.length : 0,
    high_risk_count: validRecords.filter(atm => 
      atm.risk_level === 'HIGH' || atm.risk_level === 'CRITICAL'
    ).length
  };

  const healthDistributionData = Object.entries(healthScoreDistribution).map(([range, count]) => ({
    range,
    count
  }));

  // Color mapping for risk levels
  const RISK_COLORS = {
    'LOW': '#10B981',     // green
    'MEDIUM': '#F59E0B',  // yellow
    'HIGH': '#F97316',    // orange
    'CRITICAL': '#EF4444' // red
  };

  const getRiskIcon = (risk: string) => {
    switch (risk) {
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

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-96 bg-gray-200 rounded-lg"></div>
              <div className="h-96 bg-gray-200 rounded-lg"></div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-red-700">Error loading predictive analytics: {error}</span>
            </div>
            <button
              onClick={handleRefresh}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const fleetStats = validFleetStats;

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Predictive Analytics</h1>
            <p className="text-gray-600 mt-1">ATM health monitoring and failure prediction</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Risk Filter */}
            <select
              value={selectedRiskFilter}
              onChange={(e) => setSelectedRiskFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">Critical Risk</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>

            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Fleet Overview Cards */}
        {fleetStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">ATMs Analyzed</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {fleetStats?.total_atms_analyzed ?? 0}
                  </p>
                </div>
                <Database className="h-8 w-8 text-blue-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Health Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {fleetStats?.average_health_score?.toFixed(1) ?? '0.0'}%
                  </p>
                </div>
                <Activity className="h-8 w-8 text-green-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Risk Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {fleetStats?.average_risk_score?.toFixed(1) ?? '0.0'}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">High Risk ATMs</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {fleetStats?.high_risk_count || 0}
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-500" />
              </div>
            </div>
          </div>
        )}

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Risk Distribution Pie Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) => `${name}: ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.name as keyof typeof RISK_COLORS]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Health Score Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Score Distribution</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={healthDistributionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* ATM List Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">ATM Risk Assessment</h3>
            <p className="text-sm text-gray-600 mt-1">
              Showing {getValidATMRecords().length} ATMs sorted by risk level (excluding invalid locations)
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Terminal ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Health Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Critical Components
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Analysis
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {getValidATMRecords().map((atm, index) => (
                  <tr key={`${atm.terminal_id}-${index}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {atm.terminal_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 max-w-xs truncate">
                      {atm.location}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        <div className="w-12 h-2 bg-gray-200 rounded-full mr-2">
                          <div 
                            className="h-2 rounded-full"
                            style={{ 
                              width: `${atm.overall_health_score || 0}%`,
                              backgroundColor: (atm.overall_health_score || 0) >= 85 ? '#10B981' :
                                              (atm.overall_health_score || 0) >= 70 ? '#F59E0B' :
                                              (atm.overall_health_score || 0) >= 50 ? '#F97316' : '#EF4444'
                            }}
                          />
                        </div>
                        {atm.overall_health_score?.toFixed(1) ?? '0.0'}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center">
                        {getRiskIcon(atm.risk_level)}
                        <span className="ml-2">{atm.risk_level}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {atm.risk_score?.toFixed(1) ?? '0.0'}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {atm.critical_components > 0 ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
                          <Wrench className="h-3 w-3 mr-1" />
                          {atm.critical_components}
                        </span>
                      ) : (
                        <span className="text-gray-400">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(atm.last_analysis).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        onClick={() => handleViewDetails(atm.terminal_id)}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-blue-100 hover:bg-blue-200 transition-colors"
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Info */}
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-start">
            <TrendingUp className="h-5 w-5 text-blue-500 mt-0.5 mr-2" />
            <div className="text-sm text-blue-800">
              <p className="font-medium">Predictive Analytics Overview</p>
              <p className="mt-1">
                This dashboard uses machine learning algorithms to analyze ATM fault patterns and predict potential failures. 
                Health scores are calculated based on component performance, fault frequency, and historical patterns. 
                Maintenance recommendations are prioritized to help prevent downtime and optimize service availability.
              </p>
              {summaryData?.fleet_statistics?.analysis_timestamp && (
                <p className="mt-2 text-xs text-blue-600">
                  Last updated: {new Date(summaryData.fleet_statistics.analysis_timestamp).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ATM Analytics Modal */}
        {selectedTerminalId && (
          <ATMAnalyticsModal
            terminalId={selectedTerminalId}
            isOpen={showModal}
            onClose={handleCloseModal}
          />
        )}
      </div>
    </DashboardLayout>
  );
}
