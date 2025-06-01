'use client';

import { useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, Clock } from 'lucide-react';
import { atmApiService } from '@/services/atmApi';

// Import Recharts components directly since we're using 'use client'
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

// Format time based on the selected period
const formatTimeForPeriod = (date: Date, hours: number): string => {
  if (hours <= 24) {
    // 24 hours: show time only
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  } else if (hours <= 168) {
    // 7 days: show day and time
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } else {
    // 30 days: show date only
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric'
    });
  }
};

// Generate mock historical data for demonstration
const generateMockData = (hours: number): AvailabilityDataPoint[] => {
  const now = new Date();
  const dataPoints: AvailabilityDataPoint[] = [];
  
  // Generate data for the specified time period
  const intervalHours = hours <= 24 ? 2 : hours <= 168 ? 12 : 24; // 2h, 12h, or 24h intervals
  for (let i = hours - intervalHours; i >= 0; i -= intervalHours) {
    const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));
    // Simulate availability fluctuations between 60-95%
    const baseAvailability = 85;
    const variation = Math.sin(i / 4) * 10 + Math.random() * 10 - 5;
    const availability = Math.max(60, Math.min(95, baseAvailability + variation));
    
    dataPoints.push({
      timestamp: timestamp.toISOString(),
      availability: Math.round(availability * 100) / 100,
      formattedTime: formatTimeForPeriod(timestamp, hours)
    });
  }
  
  return dataPoints;
};

export default function ATMAvailabilityChart({ className = '' }: ATMAvailabilityChartProps) {
  const [data, setData] = useState<AvailabilityDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUsingRealData, setIsUsingRealData] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<TimePeriod>('24h');
  const [actualDataPeriod, setActualDataPeriod] = useState<string>('');

  useEffect(() => {
    // Fetch real historical availability data from API
    const fetchAvailabilityData = async () => {
      try {
        setLoading(true);
        
        const currentPeriod = TIME_PERIODS.find(p => p.value === selectedPeriod)!;
        
        // First, get regional data to find available regions
        const regionalResponse = await atmApiService.getRegionalData();
        const regions = regionalResponse.regional_data;
        
        if (regions.length === 0) {
          // Fallback to mock data if no regions found
          setData(generateMockData(currentPeriod.hours));
          setIsUsingRealData(false);
          setActualDataPeriod(`${currentPeriod.label} (Mock Data)`);
          return;
        }

        // Get trends for all regions and aggregate availability data
        const allTrendsPromises = regions.map(region => 
          atmApiService.getRegionalTrends(region.region_code, currentPeriod.hours, 'new')
            .catch(error => {
              console.warn(`Failed to fetch trends for region ${region.region_code}:`, error);
              return null;
            })
        );

        const allTrendsResults = await Promise.all(allTrendsPromises);
        const validTrends = allTrendsResults.filter(result => result !== null);

        if (validTrends.length === 0) {
          // Fallback to mock data if no trend data available
          setData(generateMockData(currentPeriod.hours));
          setIsUsingRealData(false);
          setActualDataPeriod(`${currentPeriod.label} (Mock Data)`);
          return;
        }

        // Aggregate availability data across all regions by timestamp
        const aggregatedData = new Map<string, { totalAvailability: number; regionCount: number }>();

        validTrends.forEach(trendResponse => {
          if (trendResponse?.trends) {
            trendResponse.trends.forEach(point => {
              const timestampKey = new Date(point.timestamp).toISOString();
              const existing = aggregatedData.get(timestampKey) || { totalAvailability: 0, regionCount: 0 };
              
              aggregatedData.set(timestampKey, {
                totalAvailability: existing.totalAvailability + point.availability_percentage,
                regionCount: existing.regionCount + 1
              });
            });
          }
        });

        // Convert aggregated data to chart format with proper timezone handling
        const chartData: AvailabilityDataPoint[] = Array.from(aggregatedData.entries())
          .map(([timestamp, data]) => {
            const date = new Date(timestamp);
            return {
              timestamp,
              availability: Math.round((data.totalAvailability / data.regionCount) * 100) / 100,
              formattedTime: formatTimeForPeriod(date, currentPeriod.hours)
            };
          })
          .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

        if (chartData.length > 0) {
          setData(chartData);
          setIsUsingRealData(true);
          
          // Calculate actual data period based on available data
          const dataSpanHours = (new Date(chartData[chartData.length - 1].timestamp).getTime() - 
                                new Date(chartData[0].timestamp).getTime()) / (1000 * 60 * 60);
          const actualPeriodText = dataSpanHours < 24 ? 
            `${Math.round(dataSpanHours)} hours` : 
            dataSpanHours < 168 ? 
              `${Math.round(dataSpanHours / 24)} days` : 
              `${Math.round(dataSpanHours / (24 * 7))} weeks`;
          
          setActualDataPeriod(`${actualPeriodText} (${chartData.length} data points)`);
        } else {
          // Fallback to mock data if aggregation fails
          setData(generateMockData(currentPeriod.hours));
          setIsUsingRealData(false);
          setActualDataPeriod(`${currentPeriod.label} (Mock Data)`);
        }
        
      } catch (error) {
        console.error('Failed to fetch availability data from API:', error);
        // Fallback to mock data on API error
        const currentPeriod = TIME_PERIODS.find(p => p.value === selectedPeriod)!;
        setData(generateMockData(currentPeriod.hours));
        setIsUsingRealData(false);
        setActualDataPeriod(`${currentPeriod.label} (Mock Data)`);
      } finally {
        setLoading(false);
      }
    };

    fetchAvailabilityData();
    
    // Refresh data every 5 minutes
    const interval = setInterval(fetchAvailabilityData, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [selectedPeriod]); // Add selectedPeriod as dependency

  const currentAvailability = data.length > 0 ? data[data.length - 1].availability : 0;
  const previousAvailability = data.length > 1 ? data[data.length - 2].availability : currentAvailability;
  const trend = currentAvailability - previousAvailability;

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
              {isUsingRealData ? 'Live Data' : 'Demo Data'}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
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
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
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
      </div>

      {/* Footer */}
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
    </div>
  );
}
