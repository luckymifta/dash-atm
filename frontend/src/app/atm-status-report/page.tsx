'use client';

import { useState, useEffect, useCallback } from 'react';
import { Calendar, Download, Filter, RefreshCw, BarChart3, Monitor, AlertCircle } from 'lucide-react';
import DashboardLayout from '@/components/DashboardLayout';
import { atmApiService, ATMListItem } from '@/services/atmApi';

// Import Recharts components
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface FilterState {
  startDate: string;
  endDate: string;
  selectedATMs: string[];
}

interface AvailabilityDataPoint {
  timestamp: string;
  availability: number;
  formattedTime: string;
  date: string;
}

interface ATMStatusDataPoint {
  timestamp: string;
  formattedTime?: string;
  [key: string]: string | number | undefined; // For dynamic ATM status columns
}

const STATUS_COLORS = {
  'AVAILABLE': '#22c55e',
  'WARNING': '#f59e0b', 
  'WOUNDED': '#ef4444',
  'ZOMBIE': '#8b5cf6',
  'OUT_OF_SERVICE': '#6b7280'
};

const STATUS_VALUES = {
  'OUT_OF_SERVICE': 0,
  'ZOMBIE': 1,
  'WOUNDED': 2,
  'WARNING': 3,
  'AVAILABLE': 4
};

export default function ATMStatusReportPage() {
  const [availableATMs, setAvailableATMs] = useState<ATMListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days ago
    endDate: new Date().toISOString().split('T')[0], // Today
    selectedATMs: [] // Empty means all ATMs
  });

  // Chart data
  const [availabilityData, setAvailabilityData] = useState<AvailabilityDataPoint[]>([]);
  const [individualData, setIndividualData] = useState<ATMStatusDataPoint[]>([]);
  
  // UI state
  const [showFilters, setShowFilters] = useState(false);
  const [activeChart, setActiveChart] = useState<'availability' | 'individual'>('availability');

  const fetchAvailableATMs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await atmApiService.getATMList();
      setAvailableATMs(response.atms || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch ATM list:', err);
      setError('Failed to load ATM list');
    } finally {
      setLoading(false);
    }
  }, []);

  const formatTimestamp = useCallback((timestamp: string, hours: number): string => {
    const date = new Date(timestamp);
    
    if (hours <= 24) {
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false,
        timeZone: 'Asia/Dili'
      });
    } else if (hours <= 168) { // 7 days
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZone: 'Asia/Dili'
      });
    } else { // 30 days+
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        timeZone: 'Asia/Dili'
      });
    }
  }, []);

  const generateMockAvailabilityData = useCallback((hours: number): AvailabilityDataPoint[] => {
    const data: AvailabilityDataPoint[] = [];
    const now = new Date();
    const interval = Math.max(1, Math.floor(hours / 50)); // Show about 50 points
    
    for (let i = hours; i >= 0; i -= interval) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
      const availability = 85 + Math.random() * 15; // 85-100% availability
      
      data.push({
        timestamp: timestamp.toISOString(),
        availability: Math.round(availability * 100) / 100,
        formattedTime: formatTimestamp(timestamp.toISOString(), hours),
        date: timestamp.toISOString().split('T')[0]
      });
    }
    
    return data;
  }, [formatTimestamp]);

  const fetchAvailabilityData = useCallback(async (hours: number) => {
    try {
      // Fetch regional trends for TL-DL region
      const response = await atmApiService.getRegionalTrends('TL-DL', hours);
      
      if (response.trends && response.trends.length > 0) {
        const formattedData: AvailabilityDataPoint[] = response.trends.map(point => ({
          timestamp: point.timestamp,
          availability: point.availability_percentage,
          formattedTime: formatTimestamp(point.timestamp, hours),
          date: new Date(point.timestamp).toISOString().split('T')[0]
        }));
        
        // Filter data by date range
        const filteredData = formattedData.filter(point => {
          return point.date >= filters.startDate && point.date <= filters.endDate;
        });
        
        setAvailabilityData(filteredData);
      } else {
        // Generate mock data if no real data available
        setAvailabilityData(generateMockAvailabilityData(hours));
      }
    } catch (err) {
      console.error('Failed to fetch availability data:', err);
      // Generate mock data as fallback
      setAvailabilityData(generateMockAvailabilityData(hours));
    }
  }, [filters.startDate, filters.endDate, formatTimestamp, generateMockAvailabilityData]);

  const generateMockATMData = useCallback((atmId: string, hours: number) => {
    const data = [];
    const now = new Date();
    const statuses = ['AVAILABLE', 'WARNING', 'WOUNDED', 'ZOMBIE', 'OUT_OF_SERVICE'];
    let currentStatus = 'AVAILABLE';
    
    for (let i = hours; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000);
      
      // Randomly change status occasionally
      if (Math.random() < 0.05) {
        currentStatus = statuses[Math.floor(Math.random() * statuses.length)];
      }
      
      data.push({
        timestamp: timestamp.toISOString(),
        status: currentStatus,
        fault_description: currentStatus !== 'AVAILABLE' ? `${currentStatus} status detected` : undefined
      });
    }
    
    return data;
  }, []);

  const combineATMData = useCallback((atmDataResults: Array<{atmId: string; data: Array<{timestamp: string; status: string; fault_description?: string | null}>}>): ATMStatusDataPoint[] => {
    const timeMap = new Map<string, ATMStatusDataPoint>();

    atmDataResults.forEach(({ atmId, data }) => {
      data.forEach((point) => {
        const timestamp = point.timestamp;
        if (!timeMap.has(timestamp)) {
          timeMap.set(timestamp, {
            timestamp,
            formattedTime: formatTimestamp(timestamp, 168) // Default to 7 days format
          });
        }
        
        const dataPoint = timeMap.get(timestamp)!;
        dataPoint[`ATM_${atmId}`] = STATUS_VALUES[point.status as keyof typeof STATUS_VALUES] || 0;
        dataPoint[`ATM_${atmId}_status`] = point.status;
      });
    });

    return Array.from(timeMap.values()).sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [formatTimestamp]);

  const fetchIndividualATMData = useCallback(async (atmIds: string[], hours: number) => {
    try {
      const atmDataPromises = atmIds.map(async (atmId) => {
        try {
          const response = await atmApiService.getATMHistory(atmId, hours);
          return {
            atmId,
            data: response.atm_data?.historical_points || []
          };
        } catch (err) {
          console.error(`Failed to fetch data for ATM ${atmId}:`, err);
          return {
            atmId,
            data: generateMockATMData(atmId, hours)
          };
        }
      });

      const atmDataResults = await Promise.all(atmDataPromises);
      
      // Combine data from all ATMs into a time-series format
      const combinedData = combineATMData(atmDataResults);
      setIndividualData(combinedData);
    } catch (err) {
      console.error('Failed to fetch individual ATM data:', err);
      setError('Failed to load individual ATM data');
    }
  }, [generateMockATMData, combineATMData]);

  const fetchChartData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const startDate = new Date(filters.startDate);
      const endDate = new Date(filters.endDate);
      const hoursDifference = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60));

      // Determine which ATMs to fetch data for
      const targetATMs = filters.selectedATMs.length > 0 
        ? filters.selectedATMs 
        : availableATMs.slice(0, 5).map(atm => atm.terminal_id); // Limit to first 5 if all selected

      if (activeChart === 'availability') {
        await fetchAvailabilityData(hoursDifference);
      } else {
        await fetchIndividualATMData(targetATMs, hoursDifference);
      }
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
      setError('Failed to load chart data');
    } finally {
      setLoading(false);
    }
  }, [filters, availableATMs, activeChart, fetchAvailabilityData, fetchIndividualATMData]);

  // Fetch available ATMs on component mount
  useEffect(() => {
    fetchAvailableATMs();
  }, [fetchAvailableATMs]);

  // Fetch chart data when filters change
  useEffect(() => {
    if (availableATMs.length > 0) {
      fetchChartData();
    }
  }, [availableATMs, fetchChartData]);

  // Remove the duplicate function definitions
  const handleATMSelection = (atmId: string, checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      selectedATMs: checked 
        ? [...prev.selectedATMs, atmId]
        : prev.selectedATMs.filter(id => id !== atmId)
    }));
  };

  const handleSelectAllATMs = (checked: boolean) => {
    setFilters(prev => ({
      ...prev,
      selectedATMs: checked ? availableATMs.map(atm => atm.terminal_id) : []
    }));
  };

  const exportToCSV = () => {
    const data = activeChart === 'availability' ? availabilityData : individualData;
    const headers = activeChart === 'availability' 
      ? ['Timestamp', 'Availability %'] 
      : ['Timestamp', ...filters.selectedATMs.map(id => `ATM ${id}`)];
    
    const csvContent = [
      headers.join(','),
      ...data.map(row => {
        if (activeChart === 'availability') {
          const point = row as AvailabilityDataPoint;
          return `${point.timestamp},${point.availability}`;
        } else {
          const point = row as ATMStatusDataPoint;
          return `${point.timestamp},${filters.selectedATMs.map(id => point[`ATM_${id}_status`] || 'N/A').join(',')}`;
        }
      })
    ].join('\\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `atm-status-report-${activeChart}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  interface TooltipProps {
    active?: boolean;
    payload?: Array<{
      color: string;
      name: string;
      value: string | number;
    }>;
    label?: string;
  }

  const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900">{label}</p>
          {payload.map((entry, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {activeChart === 'availability' && '%'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">ATM Status Report</h1>
          <p className="text-gray-600">
            Comprehensive analysis of ATM availability trends and individual terminal status over time
          </p>
        </div>

        {/* Controls */}
        <div className="mb-6 bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Chart Type Selection */}
            <div className="flex space-x-2">
              <button
                onClick={() => setActiveChart('availability')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeChart === 'availability'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <BarChart3 className="h-4 w-4 inline mr-2" />
                Availability History
              </button>
              <button
                onClick={() => setActiveChart('individual')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeChart === 'individual'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Monitor className="h-4 w-4 inline mr-2" />
                Individual ATMs
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Filter className="h-4 w-4 inline mr-2" />
                Filters
              </button>
              <button
                onClick={fetchChartData}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`h-4 w-4 inline mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              <button
                onClick={exportToCSV}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Download className="h-4 w-4 inline mr-2" />
                Export CSV
              </button>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    <Calendar className="h-4 w-4 inline mr-1" />
                    Date Range
                  </label>
                  <div className="space-y-2">
                    <input
                      type="date"
                      value={filters.startDate}
                      onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-medium"
                    />
                    <input
                      type="date"
                      value={filters.endDate}
                      onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 font-medium"
                    />
                  </div>
                </div>

                {/* ATM Selection */}
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    <Monitor className="h-4 w-4 inline mr-1" />
                    Select ATMs ({filters.selectedATMs.length} selected)
                  </label>
                  <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-2">
                    <div className="mb-2">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={filters.selectedATMs.length === availableATMs.length}
                          onChange={(e) => handleSelectAllATMs(e.target.checked)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-900">Select All ({availableATMs.length} ATMs)</span>
                      </label>
                    </div>
                    <div className="grid grid-cols-2 gap-1">
                      {availableATMs.map((atm) => (
                        <label key={atm.terminal_id} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={filters.selectedATMs.includes(atm.terminal_id)}
                            onChange={(e) => handleATMSelection(atm.terminal_id, e.target.checked)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-gray-800">ATM {atm.terminal_id}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {activeChart === 'availability' ? 'ATM Availability History' : 'Individual ATM Status'}
            </h2>
            <p className="text-sm text-gray-600">
              {activeChart === 'availability' 
                ? `Overall availability percentage over time (${filters.startDate} to ${filters.endDate})`
                : `Status timeline for ${filters.selectedATMs.length || 'selected'} ATMs`
              }
            </p>
          </div>

          {loading ? (
            <div className="h-96 flex items-center justify-center">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-blue-600" />
                <p className="text-gray-600">Loading chart data...</p>
              </div>
            </div>
          ) : (
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                {activeChart === 'availability' ? (
                  <LineChart data={availabilityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="formattedTime"
                      tick={{ fontSize: 12 }}
                      interval="preserveStartEnd"
                    />
                    <YAxis 
                      domain={[0, 100]}
                      tick={{ fontSize: 12 }}
                      label={{ value: 'Availability %', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Line 
                      type="monotone" 
                      dataKey="availability" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6', strokeWidth: 2, r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                ) : (
                  <LineChart data={individualData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="formattedTime"
                      tick={{ fontSize: 12 }}
                      interval="preserveStartEnd"
                    />
                    <YAxis 
                      domain={[0, 4]}
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => {
                        const statusMap = ['OUT_OF_SERVICE', 'ZOMBIE', 'WOUNDED', 'WARNING', 'AVAILABLE'];
                        return statusMap[value] || '';
                      }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {filters.selectedATMs.slice(0, 10).map((atmId, index) => (
                      <Line
                        key={atmId}
                        type="stepAfter"
                        dataKey={`ATM_${atmId}`}
                        stroke={Object.values(STATUS_COLORS)[index % Object.values(STATUS_COLORS).length]}
                        strokeWidth={2}
                        dot={false}
                        name={`ATM ${atmId}`}
                      />
                    ))}
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Status Legend for Individual Chart */}
        {activeChart === 'individual' && (
          <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Status Legend</h3>
            <div className="flex flex-wrap gap-4">
              {Object.entries(STATUS_COLORS).map(([status, color]) => (
                <div key={status} className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-sm text-gray-800">{status.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Date Range</h3>
            <p className="text-lg font-semibold text-gray-900">
              {filters.startDate} to {filters.endDate}
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-1">ATMs in Report</h3>
            <p className="text-lg font-semibold text-gray-900">
              {filters.selectedATMs.length || availableATMs.length} ATMs
            </p>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Data Points</h3>
            <p className="text-lg font-semibold text-gray-900">
              {activeChart === 'availability' ? availabilityData.length : individualData.length} points
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
