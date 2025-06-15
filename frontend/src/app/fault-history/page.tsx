'use client';

import { useState, useEffect } from 'react';
import { Calendar, Download, Filter, Clock, AlertTriangle, Monitor, CheckCircle, XCircle } from 'lucide-react';
import { atmApiService, FaultHistoryReportResponse, ATMListItem } from '@/services/atmApi';

// Chart imports
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface DateRange {
  startDate: string;
  endDate: string;
}

interface SelectedTerminals {
  all: boolean;
  terminals: string[];
}

const FaultHistoryReport = () => {
  const [reportData, setReportData] = useState<FaultHistoryReportResponse | null>(null);
  const [availableTerminals, setAvailableTerminals] = useState<ATMListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    endDate: new Date().toISOString().split('T')[0] // today
  });
  
  const [selectedTerminals, setSelectedTerminals] = useState<SelectedTerminals>({
    all: true,
    terminals: []
  });
  
  const [includeOngoing, setIncludeOngoing] = useState(true);

  // Load available terminals on component mount
  useEffect(() => {
    const loadTerminals = async () => {
      try {
        const response = await atmApiService.getATMList();
        setAvailableTerminals(response.atms);
      } catch (err) {
        console.error('Failed to load terminals:', err);
      }
    };
    
    loadTerminals();
  }, []);

  // Generate report
  const generateReport = async () => {
    if (!dateRange.startDate || !dateRange.endDate) {
      setError('Please select both start and end dates');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const terminalIds = selectedTerminals.all 
        ? 'all' 
        : selectedTerminals.terminals.join(',');

      const response = await atmApiService.getFaultHistoryReport(
        dateRange.startDate,
        dateRange.endDate,
        terminalIds,
        includeOngoing
      );

      setReportData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  // Handle terminal selection
  const handleTerminalSelection = (terminalId: string, checked: boolean) => {
    if (checked) {
      setSelectedTerminals(prev => ({
        all: false,
        terminals: [...prev.terminals, terminalId]
      }));
    } else {
      setSelectedTerminals(prev => ({
        all: false,
        terminals: prev.terminals.filter(id => id !== terminalId)
      }));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedTerminals({
        all: true,
        terminals: []
      });
    } else {
      setSelectedTerminals({
        all: false,
        terminals: []
      });
    }
  };

  // Export to CSV
  const exportToCSV = () => {
    if (!reportData) return;

    const csvData = [
      ['Terminal ID', 'Terminal Name', 'Location', 'Fault State', 'Start Time', 'End Time', 'Duration (Hours)', 'Fault Description', 'Fault Type', 'Component Type', 'Resolved'],
      ...reportData.fault_duration_data.map(fault => [
        fault.terminal_id,
        fault.terminal_name || '',
        fault.location || '',
        fault.fault_state,
        fault.start_time,
        fault.end_time || 'Ongoing',
        fault.duration_minutes ? (fault.duration_minutes / 60).toFixed(2) : 'N/A',
        fault.fault_description || '',
        fault.fault_type || '',
        fault.component_type || '',
        fault.end_time ? 'Yes' : 'No'
      ])
    ];

    const csvContent = csvData.map(row => 
      row.map(cell => `"${cell}"`).join(',')
    ).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `fault_history_report_${dateRange.startDate}_${dateRange.endDate}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  // Format duration for display
  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Fault History Report</h1>
          <p className="text-gray-600">
            Analyze ATM fault durations and patterns to understand how long ATMs stay in fault states before returning to AVAILABLE
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            <Filter className="w-5 h-5 mr-2 text-blue-600" />
            Report Filters
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1 text-gray-500" />
                Start Date
              </label>
              <input
                type="date"
                value={dateRange.startDate}
                onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                placeholder="Select start date"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 text-gray-700"
              />
              <p className="text-xs text-gray-500 mt-1">Choose the report start date</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1 text-gray-500" />
                End Date
              </label>
              <input
                type="date"
                value={dateRange.endDate}
                onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                placeholder="Select end date"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400 text-gray-700"
              />
              <p className="text-xs text-gray-500 mt-1">Choose the report end date</p>
            </div>

            {/* Terminal Selection */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Monitor className="w-4 h-4 inline mr-1 text-gray-500" />
                Terminal Selection
              </label>
              <div className="space-y-2 max-h-32 overflow-y-auto bg-gray-50 border border-gray-200 p-3 rounded-md">
                <label className="flex items-center cursor-pointer hover:bg-gray-100 p-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedTerminals.all}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="mr-3 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="font-medium text-gray-800">Select All Terminals</span>
                </label>
                
                {!selectedTerminals.all && availableTerminals.length === 0 && (
                  <div className="text-sm text-gray-500 italic p-2">
                    Loading terminals...
                  </div>
                )}
                
                {!selectedTerminals.all && availableTerminals.map(terminal => (
                  <label key={terminal.terminal_id} className="flex items-center cursor-pointer hover:bg-gray-100 p-1 rounded">
                    <input
                      type="checkbox"
                      checked={selectedTerminals.terminals.includes(terminal.terminal_id)}
                      onChange={(e) => handleTerminalSelection(terminal.terminal_id, e.target.checked)}
                      className="mr-3 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">
                      <span className="font-medium">{terminal.terminal_id}</span>
                      <span className="text-gray-500"> - {terminal.location}</span>
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                        terminal.current_status === 'AVAILABLE' ? 'bg-green-100 text-green-800' :
                        terminal.current_status === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                        terminal.current_status === 'WOUNDED' ? 'bg-orange-100 text-orange-800' :
                        terminal.current_status === 'ZOMBIE' ? 'bg-purple-100 text-purple-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {terminal.current_status}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {selectedTerminals.all ? 'All terminals selected' : 
                 selectedTerminals.terminals.length > 0 ? `${selectedTerminals.terminals.length} terminal(s) selected` :
                 'No specific terminals selected'}
              </p>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between bg-gray-50 p-4 rounded-md">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={includeOngoing}
                onChange={(e) => setIncludeOngoing(e.target.checked)}
                className="mr-3 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                <span className="font-medium">Include ongoing faults</span>
                <span className="text-gray-500"> (faults not yet resolved)</span>
              </span>
            </label>

            <button
              onClick={generateReport}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-2 rounded-md font-medium transition-colors shadow-sm hover:shadow-md"
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </span>
              ) : (
                'Generate Report'
              )}
            </button>
          </div>
        </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
          <AlertTriangle className="w-5 h-5 inline mr-2" />
          {error}
        </div>
      )}

      {/* Report Results */}
      {reportData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">Total Faults</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {reportData.overall_summary.total_faults}
                  </p>
                </div>
                <AlertTriangle className="w-8 h-8 text-orange-500" />
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">Avg Duration</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatDuration(reportData.overall_summary.avg_duration_minutes)}
                  </p>
                </div>
                <Clock className="w-8 h-8 text-blue-500" />
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">Resolved Faults</p>
                  <p className="text-2xl font-bold text-green-600">
                    {reportData.overall_summary.faults_resolved}
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-1">Ongoing Faults</p>
                  <p className="text-2xl font-bold text-red-600">
                    {reportData.overall_summary.faults_ongoing}
                  </p>
                </div>
                <XCircle className="w-8 h-8 text-red-500" />
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Duration by State Bar Chart */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Average Duration by Fault State</h3>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={reportData.chart_data.duration_by_state}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="state" tick={{ fontSize: 12 }} />
                  <YAxis label={{ value: 'Hours', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value} hours`, 
                      name === 'avg_duration_hours' ? 'Average Duration' : name
                    ]}
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Bar 
                    dataKey="avg_duration_hours" 
                    fill="#3B82F6"
                    name="Average Duration"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Resolution Rate Pie Chart */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Fault Resolution Rates</h3>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={reportData.chart_data.duration_by_state}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ state, resolution_rate }) => `${state}: ${resolution_rate}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="resolution_rate"
                  >
                    {reportData.chart_data.duration_by_state.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={reportData.chart_data.colors[entry.state] || '#8884d8'} 
                      />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => [`${value}%`, 'Resolution Rate']}
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Summary by State */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-800">Summary by Fault State</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-4 py-3 text-left font-medium text-gray-700">State</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Total Faults</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Avg Duration</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Max Duration</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Resolved</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Ongoing</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(reportData.summary_by_state).map(([state, summary]) => (
                    <tr key={state} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          state === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                          state === 'WOUNDED' ? 'bg-orange-100 text-orange-800' :
                          state === 'ZOMBIE' ? 'bg-purple-100 text-purple-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {state}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">{summary.total_faults}</td>
                      <td className="px-4 py-3 text-center">{formatDuration(summary.avg_duration_minutes)}</td>
                      <td className="px-4 py-3 text-center">{formatDuration(summary.max_duration_minutes)}</td>
                      <td className="px-4 py-3 text-center text-green-600 font-medium">{summary.faults_resolved}</td>
                      <td className="px-4 py-3 text-center text-red-600 font-medium">{summary.faults_ongoing}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Detailed Fault Data */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-800">Detailed Fault History</h3>
              <button
                onClick={exportToCSV}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center shadow-sm hover:shadow-md"
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-4 py-3 text-left font-medium text-gray-700">Terminal</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-700">Location</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Fault State</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Start Time</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">End Time</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Duration</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-700">Description</th>
                    <th className="px-4 py-3 text-center font-medium text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.fault_duration_data.map((fault, index) => (
                    <tr key={index} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{fault.terminal_id}</td>
                      <td className="px-4 py-3 text-gray-600">{fault.location}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          fault.fault_state === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                          fault.fault_state === 'WOUNDED' ? 'bg-orange-100 text-orange-800' :
                          fault.fault_state === 'ZOMBIE' ? 'bg-purple-100 text-purple-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {fault.fault_state}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-gray-600">
                        {new Date(fault.start_time).toLocaleDateString('en-US', { 
                          month: 'short', 
                          day: '2-digit', 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </td>
                      <td className="px-4 py-3 text-center text-gray-600">
                        {fault.end_time ? new Date(fault.end_time).toLocaleDateString('en-US', { 
                          month: 'short', 
                          day: '2-digit', 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        }) : 'Ongoing'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {fault.duration_minutes ? formatDuration(fault.duration_minutes) : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {fault.fault_description || 'No description'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {fault.end_time ? (
                          <span className="text-green-600 font-medium">✓ Resolved</span>
                        ) : (
                          <span className="text-red-600 font-medium">⚠ Ongoing</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      </div>
    </div>
  );
};

export default FaultHistoryReport;
