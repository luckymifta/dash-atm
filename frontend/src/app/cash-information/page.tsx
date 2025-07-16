'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { 
  Building2, 
  DollarSign, 
  AlertTriangle, 
  RefreshCw,
  Filter
} from 'lucide-react';
import { cashApiService, CashInformationData, CashInformationResponse, TerminalData } from '@/services/cashApi';

export default function CashInformationPage() {
  const [data, setData] = useState<CashInformationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTerminal, setSelectedTerminal] = useState('');
  const [terminals, setTerminals] = useState<TerminalData[]>([]);
  const [loadingTerminals, setLoadingTerminals] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const hoursBack = 24; // Fixed to 24 hours

  // Helper function to get only the latest cash data for each distinct terminal_id
  const getLatestCashDataByTerminal = (cashData: CashInformationData[]): CashInformationData[] => {
    const terminalMap = new Map<string, CashInformationData>();
    
    cashData.forEach((item) => {
      const existingItem = terminalMap.get(item.terminal_id);
      
      if (!existingItem) {
        terminalMap.set(item.terminal_id, item);
      } else {
        // Compare timestamps and keep the latest one
        const currentTimestamp = new Date(item.retrieval_timestamp || 0).getTime();
        const existingTimestamp = new Date(existingItem.retrieval_timestamp || 0).getTime();
        
        if (currentTimestamp > existingTimestamp) {
          terminalMap.set(item.terminal_id, item);
        }
      }
    });
    
    return Array.from(terminalMap.values()).sort((a, b) => a.terminal_id.localeCompare(b.terminal_id));
  };

  const fetchTerminals = async () => {
    try {
      setLoadingTerminals(true);
      const result = await cashApiService.getTerminals();
      setTerminals(result.terminals);
    } catch (err) {
      console.error('Failed to fetch terminals:', err);
      // Set empty array on error
      setTerminals([]);
    } finally {
      setLoadingTerminals(false);
    }
  };

  const fetchCashData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const filters = {
        hours_back: hoursBack,
        limit: 100,
        include_raw_data: false,
        ...(selectedTerminal && { terminal_id: selectedTerminal }),
        ...(statusFilter && { cash_status: statusFilter }),
      };

      const result = await cashApiService.getCashInformation(filters);
      
      // Filter to get only the latest retrieval_timestamp for each distinct terminal_id
      const latestCashData = getLatestCashDataByTerminal(result.cash_data);
      
      setData({
        ...result,
        cash_data: latestCashData,
        total_count: latestCashData.length,
      });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      console.error('Failed to fetch cash data:', err);
      
      // Mock data as fallback for development
      const mockData = {
        cash_data: [
          {
            terminal_id: 'ATM001',
            business_code: 'BR001 - Downtown Branch',
            location: 'Downtown Financial District',
            total_cash_amount: 25000,
            total_currency: 'USD',
            cassette_count: 4,
            has_low_cash_warning: false,
            has_cash_errors: false,
            retrieval_timestamp: new Date().toISOString(),
          },
          {
            terminal_id: 'ATM002',
            business_code: 'BR002 - Mall Branch',
            location: 'Central Shopping Mall',
            total_cash_amount: 5000,
            total_currency: 'USD',
            cassette_count: 4,
            has_low_cash_warning: true,
            has_cash_errors: false,
            retrieval_timestamp: new Date(Date.now() - 3600000).toISOString(),
          },
          {
            terminal_id: 'ATM003',
            business_code: 'BR003 - Airport Branch',
            location: 'International Airport Terminal 1',
            total_cash_amount: 0,
            total_currency: 'USD',
            cassette_count: 4,
            has_low_cash_warning: false,
            has_cash_errors: true,
            retrieval_timestamp: new Date(Date.now() - 7200000).toISOString(),
          },
        ],
        total_count: 3,
        summary: {
          total_terminals: 3,
          total_records: 3,
          average_cash_amount: 10000,
          total_cash_across_atms: 30000,
          cash_status_distribution: {
            NORMAL: 1,
            LOW: 1,
            ERROR: 1,
          },
          data_period_hours: 24,
        },
        filters_applied: {
          hours_back: 24,
          limit: 100,
        },
        timestamp: new Date().toISOString(),
      };
      
      // Apply the same filtering to mock data
      const latestMockData = getLatestCashDataByTerminal(mockData.cash_data);
      
      setData({
        ...mockData,
        cash_data: latestMockData,
        total_count: latestMockData.length,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTerminals();
    fetchCashData();
  }, [statusFilter, selectedTerminal]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = () => {
    fetchCashData();
  };

  const handleRefresh = () => {
    fetchCashData();
  };

  const formatCurrency = (amount: number | undefined) => {
    if (amount === undefined || amount === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDateTime = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZoneName: 'short',
      });
    } catch {
      return 'Invalid Date';
    }
  };

  const getCashStatusBadge = (item: CashInformationData) => {
    if (item.has_cash_errors) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Error
        </span>
      );
    }
    if (item.has_low_cash_warning) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Low Cash
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Normal
      </span>
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <DollarSign className="h-8 w-8 text-green-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Cash Information</h1>
                <p className="text-sm text-gray-600">Monitor ATM cash levels and status</p>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Building2 className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Terminals</dt>
                      <dd className="text-lg font-medium text-gray-900">{data.summary.total_terminals}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <DollarSign className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Total Fleet Cash</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {formatCurrency(data.summary.total_cash_across_atms)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <DollarSign className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Average Cash</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {formatCurrency(data.summary.average_cash_amount)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <AlertTriangle className="h-6 w-6 text-yellow-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">Alerts</dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {(data.summary.cash_status_distribution.LOW || 0) + (data.summary.cash_status_distribution.ERROR || 0)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="terminal-select" className="block text-sm font-medium text-gray-700 mb-2">
                Select Terminal
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Building2 className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  id="terminal-select"
                  value={selectedTerminal}
                  onChange={(e) => setSelectedTerminal(e.target.value)}
                  disabled={loadingTerminals}
                  className="block w-full pl-10 pr-8 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                >
                  <option value="" className="text-gray-600">All Terminals</option>
                  {terminals.map((terminal) => (
                    <option key={terminal.terminal_id} value={terminal.terminal_id} className="text-gray-900">
                      {terminal.display_text}
                    </option>
                  ))}
                </select>
                {loadingTerminals && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <RefreshCw className="h-4 w-4 animate-spin text-gray-400" />
                  </div>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-2">
                Cash Status
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Filter className="h-5 w-5 text-gray-400" />
                </div>
                <select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                >
                  <option value="" className="text-gray-600">All Status</option>
                  <option value="NORMAL" className="text-gray-900">Normal</option>
                  <option value="LOW" className="text-gray-900">Low Cash</option>
                  <option value="ERROR" className="text-gray-900">Error</option>
                </select>
              </div>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleSearch}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading Data</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                  <p className="mt-1 text-xs">Showing mock data for development.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Cash Information Table */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Terminal Cash Information
            </h3>
            <p className="mt-1 text-sm text-gray-600">
              {data ? `${data.total_count} terminals found` : 'Loading...'}
            </p>
          </div>

          {loading ? (
            <div className="p-6 text-center">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
              <p className="mt-2 text-sm text-gray-500">Loading cash information...</p>
            </div>
          ) : data && data.cash_data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Terminal ID
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Terminal Cash
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date Retrieved
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cassettes
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.cash_data.map((item, index) => (
                    <tr key={`${item.terminal_id}-${index}-${item.retrieval_timestamp}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {item.terminal_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.location || item.business_code || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <div className="font-medium">
                            {formatCurrency(item.total_cash_amount)}
                          </div>
                          {item.total_currency && (
                            <div className="text-xs text-gray-500">
                              {item.total_currency}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDateTime(item.retrieval_timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getCashStatusBadge(item)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.cassette_count || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center">
              <DollarSign className="h-12 w-12 mx-auto text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No cash information found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search filters or check back later.
              </p>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
