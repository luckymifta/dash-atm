'use client';

import { useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, Clock, Download } from 'lucide-react';
import { atmApiService } from '@/services/atmApi';

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

interface AvailabilityDataPoint {
  timestamp: string;
  availability: number;
  formattedTime: string;
}

interface ATMAvailabilityChartProps {
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

// Format time based on the selected period (converts to Dili timezone UTC+9)
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
      minute: '2-digit',
      hour12: false,
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

// CSV Export functionality
const generateCSVContent = (data: AvailabilityDataPoint[], selectedPeriod: TimePeriod, actualDataPeriod: string): string => {
  const headers = ['Timestamp', 'Formatted Time', 'Availability Percentage'];
  const csvRows = [headers.join(',')];
  
  data.forEach(point => {
    const row = [
      `"${point.timestamp}"`,
      `"${point.formattedTime}"`,
      point.availability.toString()
    ];
    csvRows.push(row.join(','));
  });
  
  // Add metadata as comments at the top
  const metadata = [
    `# ATM Availability History Export`,
    `# Generated: ${new Date().toISOString()}`,
    `# Time Period: ${selectedPeriod.toUpperCase()}`,
    `# Data Period: ${actualDataPeriod}`,
    `# Total Data Points: ${data.length}`,
    `# Region: TL-DL`,
    `# Timezone: Asia/Dili (UTC+9)`,
    `# Note: Formatted Time column shows times in Dili local time`,
    ''
  ];
  
  return metadata.join('\n') + csvRows.join('\n');
};

const downloadCSV = (csvContent: string, filename: string): void => {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
};

export default function ATMAvailabilityChart({ className = '' }: ATMAvailabilityChartProps) {
  const [data, setData] = useState<AvailabilityDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUsingRealData, setIsUsingRealData] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('24h');
  const [actualDataPeriod, setActualDataPeriod] = useState<string>('');
  const [fallbackMessage, setFallbackMessage] = useState<string>('');

  useEffect(() => {
    const fetchAvailabilityData = async () => {
      try {
        setLoading(true);
        const currentPeriod = TIME_PERIODS.find(p => p.value === selectedPeriod)!;
        
        // Get trends for TL-DL region (main region with most data)
        const response = await atmApiService.getRegionalTrends('TL-DL', currentPeriod.hours, 'new');
        
        if (response.fallback_message) {
          setFallbackMessage(response.fallback_message);
        } else {
          setFallbackMessage('');
        }
        
        if (response.trends && response.trends.length > 0) {
          const chartData: AvailabilityDataPoint[] = response.trends.map(point => {
            const date = new Date(point.timestamp);
            return {
              timestamp: point.timestamp,
              availability: point.availability_percentage,
              formattedTime: formatTimeForPeriod(date, currentPeriod.hours)
            };
          });
          
          setData(chartData);
          setIsUsingRealData(true);
          
          const stats = response.summary_stats;
          const actualHours = stats.time_range_hours;
          const actualPeriodText = actualHours < 24 ? 
            `${Math.round(actualHours)} hours` : 
            actualHours < 168 ? 
              `${Math.round(actualHours / 24)} days` : 
              `${Math.round(actualHours / (24 * 7))} weeks`;
          
          setActualDataPeriod(`${actualPeriodText} (${stats.data_points} data points)`);
        } else {
          // No data available
          setData([]);
          setIsUsingRealData(false);
          setActualDataPeriod('No data available');
        }
        
      } catch (error) {
        console.error('Failed to fetch availability data:', error);
        setData([]);
        setIsUsingRealData(false);
        setActualDataPeriod('Failed to load data');
        setFallbackMessage('');
      } finally {
        setLoading(false);
      }
    };

    fetchAvailabilityData();
    
    // Refresh data every 30 minutes
    const interval = setInterval(fetchAvailabilityData, 30 * 60 * 1000); // 30 minutes = 1,800,000 milliseconds
    
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  const currentAvailability = data.length > 0 ? data[data.length - 1].availability : 0;
  const previousAvailability = data.length > 1 ? data[data.length - 2].availability : currentAvailability;
  const trend = currentAvailability - previousAvailability;

  // Handle CSV export
  const handleExport = () => {
    if (data.length === 0) {
      alert('No data available to export');
      return;
    }
    
    const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    const filename = `atm_availability_${selectedPeriod}_${timestamp}.csv`;
    const csvContent = generateCSVContent(data, selectedPeriod, actualDataPeriod);
    downloadCSV(csvContent, filename);
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 shadow-sm p-6 ${className}`}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-lg">Loading availability history...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">ATM Availability History</h3>
          <div className="flex items-center space-x-2">
            <p className="text-sm text-gray-500">
              {actualDataPeriod || `${TIME_PERIODS.find(p => p.value === selectedPeriod)?.label} availability trend`}
            </p>
            <div className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
              isUsingRealData 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {isUsingRealData ? 'Live Data' : 'No Data'}
            </div>
            {fallbackMessage && (
              <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                {fallbackMessage}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {/* Export Button */}
          {data.length > 0 && (
            <button
              onClick={handleExport}
              className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              title="Export data as CSV"
            >
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </button>
          )}
          
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
          {data.length > 0 && (
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {currentAvailability.toFixed(1)}%
              </div>
              <div className={`text-sm flex items-center ${
                trend >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                <TrendingUp className={`h-4 w-4 mr-1 ${trend < 0 ? 'rotate-180' : ''}`} />
                {trend >= 0 ? '+' : ''}{trend.toFixed(1)}%
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="formattedTime"
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                domain={[50, 100]}
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'Availability']}
                labelFormatter={(label) => `Time: ${label} (Dili Time)`}
              />
              <Line
                type="monotone"
                dataKey="availability"
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
                {isUsingRealData ? 'No trend data found for this time period' : 'Unable to connect to API'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      {data.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-sm font-medium text-gray-900">
                {Math.max(...data.map(d => d.availability)).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Peak</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">
                {(data.reduce((sum, d) => sum + d.availability, 0) / data.length).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Average</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">
                {Math.min(...data.map(d => d.availability)).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500">Lowest</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}