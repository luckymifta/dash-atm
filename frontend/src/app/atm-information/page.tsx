'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { Landmark, Search, RefreshCw, AlertCircle, MapPin, Wrench, Clock, Filter, X } from 'lucide-react';
import { atmApiService, TerminalDetails } from '@/services/atmApi';

export default function ATMInformationPage() {
  const [terminalData, setTerminalData] = useState<TerminalDetails[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const searchParams = useSearchParams();
  const statusFilter = searchParams.get('status');

  const clearStatusFilter = () => {
    // Remove the status parameter from URL
    const url = new URL(window.location.href);
    url.searchParams.delete('status');
    window.history.replaceState({}, '', url.toString());
  };

  const fetchTerminalDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await atmApiService.getTerminalDetails('both', true);
      
      // Extract terminal details from the response
      let terminals: TerminalDetails[] = [];
      
      if (response.data_sources && response.data_sources.length > 0) {
        // Handle data_sources format - only get terminal_data type
        response.data_sources.forEach(source => {
          if (source.type === 'terminal_data' && source.data && Array.isArray(source.data)) {
            // Transform the data to match our interface expectations
            const transformedData = source.data.map((terminal: TerminalDetails) => {
              // Handle location field - convert object to string if needed
              let locationStr = terminal.location_str;
              if (!locationStr && terminal.location) {
                if (typeof terminal.location === 'string') {
                  locationStr = terminal.location;
                } else if (typeof terminal.location === 'object' && terminal.location.city) {
                  locationStr = terminal.location.city;
                }
              }
              
              return {
                ...terminal,
                location_str: locationStr,
                external_id: terminal.external_id || terminal.terminal_id, // Fallback for external_id
              };
            });
            terminals = terminals.concat(transformedData);
          }
        });
      } else if (response.terminal_details) {
        // Handle direct terminal_details format
        terminals = response.terminal_details;
      }
      
      setTerminalData(terminals);
    } catch (err) {
      console.error('Error fetching terminal details:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch terminal details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTerminalDetails();
    
    // Refresh data every 2 minutes
    const interval = setInterval(fetchTerminalDetails, 120000);
    
    return () => clearInterval(interval);
  }, []);

  // Filter terminals based on search term and status filter
  const filteredTerminals = terminalData.filter(terminal => {
    // First apply search term filter
    const matchesSearch = terminal.terminal_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      terminal.external_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      terminal.location_str?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      terminal.city?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      terminal.bank?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      terminal.issue_state_name?.toLowerCase().includes(searchTerm.toLowerCase());

    // If there's no status filter, return search results
    if (!statusFilter) {
      return matchesSearch;
    }

    // Apply status filter
    const terminalStatus = (terminal.issue_state_name || terminal.status || '').toLowerCase();
    let matchesStatus = false;

    switch (statusFilter.toLowerCase()) {
      case 'available':
        matchesStatus = terminalStatus === 'available' || terminalStatus === 'normal';
        break;
      case 'warning':
        matchesStatus = terminalStatus === 'warning' || terminalStatus === 'warn';
        break;
      case 'wounded':
        matchesStatus = terminalStatus === 'wounded' || terminalStatus === 'error';
        break;
      case 'zombie':
        matchesStatus = terminalStatus === 'zombie' || terminalStatus === 'offline';
        break;
      case 'out_of_service':
        matchesStatus = terminalStatus === 'out_of_service' || terminalStatus === 'maintenance';
        break;
      default:
        matchesStatus = true; // If unknown status filter, show all
        break;
    }

    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status?: string, issueStateName?: string) => {
    const displayStatus = issueStateName || status || 'UNKNOWN';
    let colorClasses = '';
    
    switch (displayStatus.toLowerCase()) {
      case 'available':
      case 'normal':
        colorClasses = 'bg-green-100 text-green-800';
        break;
      case 'warning':
      case 'warn':
        colorClasses = 'bg-yellow-100 text-yellow-800';
        break;
      case 'wounded':
      case 'error':
        colorClasses = 'bg-orange-100 text-orange-800';
        break;
      case 'zombie':
      case 'offline':
        colorClasses = 'bg-red-100 text-red-800';
        break;
      case 'out_of_service':
      case 'maintenance':
        colorClasses = 'bg-gray-100 text-gray-800';
        break;
      default:
        colorClasses = 'bg-gray-100 text-gray-800';
    }
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses}`}>
        {displayStatus}
      </span>
    );
  };

  const formatFaultData = (terminal: TerminalDetails) => {
    // Extract fault data from fault_data JSON field or fault_list array
    let externalFaultId = '';
    let agentErrorDescription = '';
    
    // First try to get fault data from fault_data JSON field (from API response)
    if (terminal.fault_data) {
      try {
        const faultData = typeof terminal.fault_data === 'string' 
          ? JSON.parse(terminal.fault_data) 
          : terminal.fault_data;
        externalFaultId = faultData.externalFaultId || '';
        agentErrorDescription = faultData.agentErrorDescription || '';
      } catch (error) {
        console.warn('Failed to parse fault_data JSON:', error);
      }
    }
    
    // Fallback to fault_list array if fault_data didn't provide the information
    if ((!externalFaultId || !agentErrorDescription) && terminal.fault_list && terminal.fault_list.length > 0) {
      const firstFault = terminal.fault_list[0];
      externalFaultId = externalFaultId || firstFault.externalFaultId || '';
      agentErrorDescription = agentErrorDescription || firstFault.agentErrorDescription || '';
    }

    if (!externalFaultId && !agentErrorDescription) {
      return (
        <div className="text-sm text-gray-500">
          No fault data
        </div>
      );
    }

    return (
      <div className="space-y-1">
        <div className="text-sm">
          <div className="font-medium text-red-600">
            {externalFaultId || 'Unknown Error ID'}
          </div>
          <div className="text-gray-600 text-sm">
            {agentErrorDescription || 'No description available'}
          </div>
        </div>
      </div>
    );
  };

  const formatDate = (terminal: TerminalDetails) => {
    // Priority order for date sources (prioritizing actual Dili time):
    // 1. metadata.retrieval_timestamp (already in Dili timezone UTC+9)
    // 2. retrieved_date (when data was fetched, needs timezone conversion)
    // 3. Most recent fault creation date (if available)
    // 4. last_updated (terminal's last update)
    // 5. fault_data.creationDate (legacy format)
    
    let dateToFormat = null;
    let dateSource = '';

    // First priority: metadata.retrieval_timestamp (already in Dili time)
    if (terminal.metadata) {
      try {
        const metadata = typeof terminal.metadata === 'string' 
          ? JSON.parse(terminal.metadata) 
          : terminal.metadata;
        if (metadata && typeof metadata === 'object' && 'retrieval_timestamp' in metadata) {
          dateToFormat = metadata.retrieval_timestamp as string;
          dateSource = 'Retrieved (Dili Time)';
        }
      } catch (error) {
        console.warn('Failed to parse metadata for date:', error);
      }
    }

    // Second priority: retrieved_date
    if (!dateToFormat && terminal.retrieved_date) {
      dateToFormat = terminal.retrieved_date;
      dateSource = 'Retrieved';
    }
    
    // Third priority: Most recent fault creation date
    if (!dateToFormat && terminal.fault_list && terminal.fault_list.length > 0) {
      const latestFault = terminal.fault_list[0]; // Assuming fault_list is sorted by most recent
      if (latestFault.creation_date) {
        dateToFormat = latestFault.creation_date;
        dateSource = 'Latest Fault';
      }
    }
    
    // Fourth priority: last_updated
    if (!dateToFormat && terminal.last_updated) {
      dateToFormat = terminal.last_updated;
      dateSource = 'Last Updated';
    }
    
    // Fifth priority: fault_data.creationDate (legacy parsing)
    if (!dateToFormat && terminal.fault_data) {
      try {
        const faultData = typeof terminal.fault_data === 'string' 
          ? JSON.parse(terminal.fault_data) 
          : terminal.fault_data;
        if (faultData.creationDate) {
          if (typeof faultData.creationDate === 'number') {
            // Unix timestamp in milliseconds
            dateToFormat = new Date(faultData.creationDate).toISOString();
            dateSource = 'Fault Created';
          } else if (typeof faultData.creationDate === 'string') {
            // Parse the creationDate format: "01:06:2025 10:51:36"
            const parts = faultData.creationDate.split(' ');
            if (parts.length === 2) {
              const datePart = parts[0].split(':');
              const timePart = parts[1];
              if (datePart.length === 3) {
                // Reconstruct as YYYY-MM-DD HH:mm:ss
                dateToFormat = `${datePart[2]}-${datePart[1]}-${datePart[0]} ${timePart}`;
                dateSource = 'Fault Created';
              }
            }
          }
        }
      } catch (error) {
        console.warn('Failed to parse fault_data for date:', error);
      }
    }

    if (!dateToFormat) {
      return (
        <div className="text-sm text-gray-500">
          No date available
        </div>
      );
    }

    try {
      const date = new Date(dateToFormat);
      if (isNaN(date.getTime())) {
        return (
          <div className="text-sm text-gray-500">
            Invalid date
          </div>
        );
      }

      return (
        <div className="space-y-1">
          <div className="text-sm font-medium text-gray-900">
            {date.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              timeZone: 'Asia/Dili'
            })}
          </div>
          <div className="text-xs text-gray-500">
            {date.toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
              timeZone: 'Asia/Dili'
            })}
          </div>
          <div className="text-xs text-blue-600 font-medium">
            Dili Time (UTC+9)
          </div>
          <div className="text-xs text-gray-400">
            {dateSource}
          </div>
        </div>
      );
    } catch {
      return (
        <div className="text-sm text-gray-500">
          Invalid date format
        </div>
      );
    }
  };

  if (loading && terminalData.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-lg">Loading terminal information...</span>
        </div>
      </DashboardLayout>
    );
  }

  if (error && terminalData.length === 0) {
    return (
      <DashboardLayout>
        <div className="rounded-lg bg-red-50 border border-red-200 p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
              <button
                onClick={fetchTerminalDetails}
                className="mt-2 bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm transition-colors"
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
            <h1 className="text-3xl font-bold text-gray-900">ATM Information</h1>
            <p className="mt-1 text-sm text-gray-500">
              Detailed information about individual ATMs and their current status
              {statusFilter && (
                <span className="ml-2 inline-flex items-center bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs font-medium">
                  Filtered by: {statusFilter.replace('_', ' ').toUpperCase()}
                </span>
              )}
            </p>
          </div>
          <button
            onClick={fetchTerminalDetails}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Search and Filter Bar */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by Terminal ID, External ID, Location, City, Bank, or Issue State..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            {/* Status Filter Indicator */}
            {statusFilter && (
              <div className="flex items-center space-x-2">
                <div className="flex items-center bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                  <Filter className="h-4 w-4 mr-1" />
                  <span className="font-medium">Status: {statusFilter.replace('_', ' ').toUpperCase()}</span>
                  <button
                    onClick={clearStatusFilter}
                    className="ml-2 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
                    title="Clear status filter"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              </div>
            )}
            
            <div className="flex items-center text-sm text-gray-500">
              <span className="font-medium">{filteredTerminals.length}</span>
              <span className="ml-1">of {terminalData.length} terminals</span>
              {statusFilter && (
                <span className="ml-1 text-blue-600">(filtered by {statusFilter.replace('_', ' ')})</span>
              )}
            </div>
          </div>
        </div>

        {/* Terminal Information Table */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
          <div className="px-4 py-5 sm:p-6">
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
                      Issue State Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fault Data
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date Created (Dili Time)
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredTerminals.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                        <Landmark className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">No terminals found</h3>
                        <p className="mt-1 text-sm text-gray-500">
                          {statusFilter ? (
                            <>
                              No terminals found with status &ldquo;{statusFilter.replace('_', ' ')}&rdquo;
                              {searchTerm && ' matching your search criteria'}.
                              <br />
                              <button
                                onClick={clearStatusFilter}
                                className="mt-2 text-blue-600 hover:text-blue-800 underline"
                              >
                                Clear status filter
                              </button>
                              {searchTerm && ' or adjust your search criteria.'}
                            </>
                          ) : searchTerm ? (
                            'Try adjusting your search criteria.'
                          ) : (
                            'No terminal data available.'
                          )}
                        </p>
                      </td>
                    </tr>
                  ) : (
                    filteredTerminals.map((terminal, index) => (
                      <tr key={terminal.terminal_id || index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {terminal.terminal_id || 'N/A'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {terminal.external_id || 'No External ID'}
                            </div>
                            {terminal.bank && (
                              <div className="text-xs text-blue-600 font-medium">
                                {terminal.bank}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-start space-x-2">
                            <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div>
                              <div className="text-sm text-gray-900">
                                {terminal.location_str || terminal.city || 'Unknown Location'}
                              </div>
                              {terminal.region && (
                                <div className="text-xs text-gray-500">
                                  Region: {terminal.region}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(terminal.status, terminal.issue_state_name)}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-start space-x-2">
                            <Wrench className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div className="min-w-0 flex-1">
                              {formatFaultData(terminal)}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-start space-x-2">
                            <Clock className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                            <div className="min-w-0 flex-1">
                              {formatDate(terminal)}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Summary Statistics */}
        {terminalData.length > 0 && (
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{terminalData.length}</div>
                <div className="text-sm text-gray-500">Total Terminals</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {terminalData.filter(t => 
                    (t.status?.toLowerCase() === 'available') || 
                    (t.issue_state_name?.toLowerCase() === 'available')
                  ).length}
                </div>
                <div className="text-sm text-gray-500">Available</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {terminalData.filter(t => 
                    (t.status?.toLowerCase() === 'warning') || 
                    (t.issue_state_name?.toLowerCase() === 'warning')
                  ).length}
                </div>
                <div className="text-sm text-gray-500">Warning</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {terminalData.filter(t => 
                    (t.status?.toLowerCase() === 'wounded') || 
                    (t.issue_state_name?.toLowerCase() === 'wounded') ||
                    (t.status?.toLowerCase() === 'error') || 
                    (t.issue_state_name?.toLowerCase() === 'error')
                  ).length}
                </div>
                <div className="text-sm text-gray-500">Wounded</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
