'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import ATMStatusCard from '@/components/ATMStatusCard';
import ATMAvailabilityChart from '@/components/ATMAvailabilityChart';
import ATMIndividualChart from '@/components/ATMIndividualChart';
import BellNotification from '@/components/BellNotification';
import { 
  Building2, 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  Skull, 
  XCircle,
  RefreshCw
} from 'lucide-react';
import { atmApiService, ATMSummaryResponse } from '@/services/atmApi';

export default function DashboardPage() {
  const [data, setData] = useState<ATMSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextRefresh, setNextRefresh] = useState<Date | null>(null);
  const [timeUntilRefresh, setTimeUntilRefresh] = useState<string>('');
  const router = useRouter();

  const handleCardClick = (status?: string) => {
    if (status) {
      router.push(`/atm-information?status=${encodeURIComponent(status)}`);
    } else {
      router.push('/atm-information');
    }
  };

  const handleManualRefresh = async () => {
    await fetchATMData();
    // Reset the next refresh time when manually refreshed
    setNextRefresh(new Date(Date.now() + 15 * 60 * 1000));
  };

  const fetchATMData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await atmApiService.getSummary('legacy');
      setData(result);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      console.error('Failed to fetch ATM data:', err);
      
      // Set mock data as fallback for development
      if (!data) {
        setData({
          total_atms: 14,
          status_counts: {
            available: 7,
            warning: 2,
            wounded: 2,
            zombie: 1,
            out_of_service: 2,
            total: 14,
          },
          overall_availability: 64.29,
          total_regions: 5,
          last_updated: new Date().toISOString(),
          data_source: 'mock',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchATMData();
    
    // Set initial next refresh time
    setNextRefresh(new Date(Date.now() + 15 * 60 * 1000));
    
    // Refresh data every 15 minutes
    const interval = setInterval(() => {
      fetchATMData();
      setNextRefresh(new Date(Date.now() + 15 * 60 * 1000));
    }, 15 * 60 * 1000); // 15 minutes = 900,000 milliseconds
    
    return () => clearInterval(interval);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Countdown timer for next refresh
  useEffect(() => {
    const updateCountdown = () => {
      if (nextRefresh) {
        const now = new Date();
        const timeLeft = nextRefresh.getTime() - now.getTime();
        
        if (timeLeft > 0) {
          const minutes = Math.floor(timeLeft / (1000 * 60));
          const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
          setTimeUntilRefresh(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        } else {
          setTimeUntilRefresh('Refreshing...');
        }
      }
    };

    updateCountdown();
    const countdownInterval = setInterval(updateCountdown, 1000);
    
    return () => clearInterval(countdownInterval);
  }, [nextRefresh]);

  if (loading && !data) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-lg">Loading ATM status...</span>
        </div>
      </DashboardLayout>
    );
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-lg">Loading ATM status...</span>
        </div>
      </DashboardLayout>
    );
  }

  if (error && !data) {
    return (
      <DashboardLayout>
        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
          <div className="flex">
            <XCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={fetchATMData}
                className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">ATM Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">
              Real-time monitoring of ATM status across all regions (updates every 15 minutes)
            </p>
          </div>
          <div className="flex items-center space-x-3">
            {data?.last_updated && (
              <div className="text-right">
                <p className="text-sm text-gray-500">
                  Last updated: {new Date(data.last_updated).toLocaleString('en-US', { 
                    timeZone: 'Asia/Dili',
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                  })} (Dili Time)
                </p>
                {nextRefresh && (
                  <p className="text-xs text-gray-400">
                    Next refresh: {nextRefresh.toLocaleString('en-US', { 
                      timeZone: 'Asia/Dili',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false
                    })} ({timeUntilRefresh})
                  </p>
                )}
              </div>
            )}
            {/* Connection Status */}
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium ${
              error 
                ? 'bg-red-100 text-red-800' 
                : 'bg-green-100 text-green-800'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                error ? 'bg-red-500' : 'bg-green-500'
              }`} />
              <span>{error ? 'API Disconnected' : 'API Connected'}</span>
            </div>
            <button
              onClick={handleManualRefresh}
              disabled={loading}
              className="inline-flex items-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            {/* Bell Notification */}
            <BellNotification className="ml-2" />
          </div>
        </div>

        {/* API Status Banner */}
        {error && (
          <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">API Connection Warning</h3>
                <p className="mt-1 text-sm text-yellow-700">
                  {error}. Showing {data?.data_source === 'mock' ? 'mock' : 'cached'} data.
                </p>
                <button
                  onClick={handleManualRefresh}
                  className="mt-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-3 py-1 rounded text-sm transition-colors"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Availability Summary */}
        {data && (
          <div className="rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Overall Availability</h2>
                <p className="text-3xl font-bold">{data.overall_availability.toFixed(2)}%</p>
                <p className="text-blue-100">
                  {data.status_counts.available + data.status_counts.warning} of {data.total_atms} ATMs operational
                </p>
              </div>
              <CheckCircle className="h-16 w-16 text-blue-200" />
            </div>
          </div>
        )}

        {/* ATM Status Cards */}
        {data && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <ATMStatusCard
              title="Total ATMs"
              value={data.total_atms}
              icon={Building2}
              color="blue"
              onClick={() => handleCardClick()}
            />
            
            <ATMStatusCard
              title="Available"
              value={data.status_counts.available}
              icon={CheckCircle}
              color="green"
              onClick={() => handleCardClick('available')}
            />
            
            <ATMStatusCard
              title="Warning"
              value={data.status_counts.warning}
              icon={AlertTriangle}
              color="yellow"
              onClick={() => handleCardClick('warning')}
            />
            
            <ATMStatusCard
              title="Wounded"
              value={data.status_counts.wounded}
              icon={ShieldAlert}
              color="orange"
              onClick={() => handleCardClick('wounded')}
            />
            
            <ATMStatusCard
              title="Zombie"
              value={data.status_counts.zombie}
              icon={Skull}
              color="red"
              onClick={() => handleCardClick('zombie')}
            />
            
            <ATMStatusCard
              title="Out of Service"
              value={data.status_counts.out_of_service}
              icon={XCircle}
              color="gray"
              onClick={() => handleCardClick('out_of_service')}
            />
          </div>
        )}

        {/* ATM Availability History Chart */}
        <ATMAvailabilityChart />

        {/* Individual ATM Historical Chart */}
        <ATMIndividualChart />
      </div>
    </DashboardLayout>
  );
}
