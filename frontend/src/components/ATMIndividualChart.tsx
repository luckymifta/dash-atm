'use client';

import { useEffect, useState } from 'react';
import { RefreshCw, Monitor, Clock, Download, ChevronDown } from 'lucide-react';
import { atmApiService, ATMHistoricalResponse, ATMListItem } from '@/services/atmApi';

// Import Recharts components
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

interface ATMStatusDataPoint {
  timestamp: string;
  status: string;
  statusValue: number;
  formattedTime: string;
  fault_description?: string;
}

interface ATMIndividualChartProps {
  className?: string;
}

type TimePeriod = '24h' | '7d' | '30d';

interface TimePeriodOption {
  value: TimePeriod;
  label: string;
  hours: number;
}

const TIME_PERIODS: TimePeriodOption[] = [
  { value: '24h', label: '24 Hours', hours: 24 },
  { value: '7d', label: '7 Days', hours: 24 * 7 },
  { value: '30d', label: '30 Days', hours: 24 * 30 }
];

// Status to numeric value mapping for chart
const STATUS_VALUES = {
  'OUT_OF_SERVICE': 0,
  'ZOMBIE': 1,
  'WOUNDED': 2,
  'WARNING': 3,
  'AVAILABLE': 4
} as const;

// Status colors mapping
const STATUS_COLORS = {
  'AVAILABLE': '#28a745',      // Green
  'WARNING': '#ffc107',        // Yellow  
  'WOUNDED': '#fd7e14',        // Orange
  'ZOMBIE': '#6f42c1',         // Purple
  'OUT_OF_SERVICE': '#dc3545'  // Red
} as const;

// Format time based on the selected period (Dili timezone UTC+9)
const formatTimeForPeriod = (date: Date, hours: number): string => {
  if (hours <= 24) {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Dili'
    });
  } else if (hours <= 168) {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      timeZone: 'Asia/Dili'
    });
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      timeZone: 'Asia/Dili'
    });
  }
};

// Custom tooltip component
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: ATMStatusDataPoint;
  }>;
  label?: string;
}

const CustomTooltip = ({ active, payload }: TooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">{data.formattedTime}</p>
        <div className="flex items-center mt-1">
          <div 
            className="w-3 h-3 rounded-full mr-2" 
            style={{ backgroundColor: STATUS_COLORS[data.status as keyof typeof STATUS_COLORS] }}
          />
          <p className="text-sm text-gray-700">Status: {data.status}</p>
        </div>
        {data.fault_description && (
          <p className="text-xs text-red-600 mt-1">Fault: {data.fault_description}</p>
        )}
      </div>
    );
  }
  return null;
};

export default function ATMIndividualChart({ className = '' }: ATMIndividualChartProps) {
  const [data, setData] = useState<ATMStatusDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('7d');
  const [selectedATM, setSelectedATM] = useState<string>('');
  const [atmList, setATMList] = useState<ATMListItem[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [historicalData, setHistoricalData] = useState<ATMHistoricalResponse | null>(null);
  const [actualDataPeriod, setActualDataPeriod] = useState<string>('');
  const [fallbackMessage, setFallbackMessage] = useState<string>('');

  // Fetch ATM list on component mount
  useEffect(() => {
    const fetchATMList = async () => {
      try {
        const response = await atmApiService.getATMList();
        setATMList(response.atms);
        // Default to first ATM if none selected
        if (response.atms.length > 0 && !selectedATM) {
          setSelectedATM(response.atms[0].terminal_id);
        }
      } catch (error) {
        console.error('Failed to fetch ATM list:', error);
      }
    };

    fetchATMList();
  }, [selectedATM]);

  // Fetch historical data when ATM or period changes
  useEffect(() => {
    const fetchHistoricalData = async () => {
      if (!selectedATM) return;

      try {
        setLoading(true);
        const currentPeriod = TIME_PERIODS.find(p => p.value === selectedPeriod)!;
        
        const response = await atmApiService.getATMHistory(selectedATM, currentPeriod.hours, true);
        setHistoricalData(response);

        if (response.atm_data.summary_stats.fallback_message) {
          setFallbackMessage(response.atm_data.summary_stats.fallback_message);
        } else {
          setFallbackMessage('');
        }

        // Convert historical points to chart data
        const chartData: ATMStatusDataPoint[] = response.atm_data.historical_points.map(point => {
          const date = new Date(point.timestamp);
          return {
            timestamp: point.timestamp,
            status: point.status,
            statusValue: STATUS_VALUES[point.status],
            formattedTime: formatTimeForPeriod(date, currentPeriod.hours),
            fault_description: point.fault_description
          };
        });

        setData(chartData);

        const stats = response.atm_data.summary_stats;
        const actualHours = stats.time_range_hours;
        const actualPeriodText = actualHours < 24 ? 
          `${Math.round(actualHours)} hours` : 
          actualHours < 168 ? 
            `${Math.round(actualHours / 24)} days` : 
            `${Math.round(actualHours / (24 * 7))} weeks`;
        
        setActualDataPeriod(`${actualPeriodText} (${stats.data_points} data points)`);

      } catch (error) {
        console.error('Failed to fetch ATM historical data:', error);
        setData([]);
        setHistoricalData(null);
        setActualDataPeriod('Failed to load data');
        setFallbackMessage('');
      } finally {
        setLoading(false);
      }
    };

    fetchHistoricalData();
    
    // Refresh data every 30 minutes
    const interval = setInterval(fetchHistoricalData, 30 * 60 * 1000); // 30 minutes = 1,800,000 milliseconds
    
    return () => clearInterval(interval);
  }, [selectedATM, selectedPeriod]);

  // Get current status info
  const selectedATMInfo = atmList.find(atm => atm.terminal_id === selectedATM);
  const currentStatus = selectedATMInfo?.current_status || 'UNKNOWN';
  const uptime = historicalData?.atm_data.summary_stats.uptime_percentage || 0;

  // Handle CSV export
  const handleExport = () => {
    if (data.length === 0) {
      alert('No data available to export');
      return;
    }
    
    const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    const filename = `atm_${selectedATM}_history_${selectedPeriod}_${timestamp}.csv`;
    
    const headers = ['Timestamp', 'Status', 'Fault Description', 'Location'];
    const csvData = data.map(point => [
      point.timestamp,
      point.status,
      point.fault_description || '',
      selectedATMInfo?.location || ''
    ]);
    
    const csvContent = [headers, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  if (loading && data.length === 0) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-lg">Loading ATM history...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Individual ATM History</h3>
          <div className="flex items-center space-x-2">
            <p className="text-sm text-gray-500">
              {selectedATMInfo ? `${selectedATMInfo.location} (${selectedATM})` : 'Select an ATM'}
            </p>
            {selectedATMInfo && (
              <div className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                currentStatus === 'AVAILABLE' ? 'bg-green-100 text-green-800' :
                currentStatus === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                currentStatus === 'WOUNDED' ? 'bg-orange-100 text-orange-800' :
                currentStatus === 'ZOMBIE' ? 'bg-purple-100 text-purple-800' :
                'bg-red-100 text-red-800'
              }`}>
                {currentStatus}
              </div>
            )}
            {fallbackMessage && (
              <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                Limited Data
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* ATM Selection Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
            >
              <Monitor className="h-4 w-4" />
              <span>{selectedATM || 'Select ATM'}</span>
              <ChevronDown className="h-4 w-4" />
            </button>
            
            {isDropdownOpen && (
              <div className="absolute right-0 mt-1 w-80 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
                {atmList.map((atm) => (
                  <button
                    key={atm.terminal_id}
                    onClick={() => {
                      setSelectedATM(atm.terminal_id);
                      setIsDropdownOpen(false);
                    }}
                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 ${
                      selectedATM === atm.terminal_id ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                    }`}
                  >
                    <div className="font-medium">{atm.terminal_id}</div>
                    <div className="text-xs text-gray-500 truncate">{atm.location}</div>
                    <div className={`text-xs ${
                      atm.current_status === 'AVAILABLE' ? 'text-green-600' :
                      atm.current_status === 'WARNING' ? 'text-yellow-600' :
                      atm.current_status === 'WOUNDED' ? 'text-orange-600' :
                      atm.current_status === 'ZOMBIE' ? 'text-purple-600' :
                      'text-red-600'
                    }`}>
                      {atm.current_status}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Time Period Filter */}
          <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            <Clock className="h-4 w-4 text-gray-500 ml-2" />
            {TIME_PERIODS.map((period) => (
              <button
                key={period.value}
                onClick={() => setSelectedPeriod(period.value)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  selectedPeriod === period.value
                    ? 'bg-white text-blue-600 font-medium shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {period.label}
              </button>
            ))}
          </div>

          {/* Export Button */}
          {data.length > 0 && (
            <button
              onClick={handleExport}
              className="flex items-center space-x-1 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="h-80">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="formattedTime"
                stroke="#6b7280"
                fontSize={12}
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                domain={[0, 4]}
                ticks={[0, 1, 2, 3, 4]}
                tickFormatter={(value) => {
                  const statusLabels = ['OUT_OF_SERVICE', 'ZOMBIE', 'WOUNDED', 'WARNING', 'AVAILABLE'];
                  return statusLabels[value] || '';
                }}
                stroke="#6b7280"
                fontSize={12}
                tick={{ fontSize: 12 }}
                width={100}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="stepAfter"
                dataKey="statusValue"
                stroke="#3b82f6"
                strokeWidth={3}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#1d4ed8' }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-gray-400 text-lg mb-2">No Data Available</div>
              <div className="text-gray-500 text-sm">
                {selectedATM ? 'No historical data found for this ATM' : 'Please select an ATM to view history'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Stats */}
      {data.length > 0 && historicalData && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-sm font-medium text-gray-900">
                {uptime.toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Uptime</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">
                {historicalData.atm_data.summary_stats.status_changes}
              </div>
              <div className="text-xs text-gray-500">Status Changes</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">
                {historicalData.atm_data.summary_stats.data_points}
              </div>
              <div className="text-xs text-gray-500">Data Points</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">
                {actualDataPeriod.split(' (')[0]}
              </div>
              <div className="text-xs text-gray-500">Time Range</div>
            </div>
          </div>
          
          {fallbackMessage && (
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
              <strong>Note:</strong> {fallbackMessage}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
