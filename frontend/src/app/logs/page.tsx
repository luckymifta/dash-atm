'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';
import { authApi, AuditLogEntry } from '@/services/authApi';

export default function LogsPage() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [total, setTotal] = useState<number>(0);
  const [filters, setFilters] = useState({
    action: '',
    start_date: '',
    end_date: '',
  });
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [showModal, setShowModal] = useState<boolean>(false);

  // Check permissions
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
      return;
    }

    if (user && !['admin', 'super_admin'].includes(user.role)) {
      router.push('/dashboard');
      return;
    }
  }, [isAuthenticated, user, router]);

  // Fetch audit logs
  useEffect(() => {
    const fetchLogs = async () => {
      if (!user || !['admin', 'super_admin'].includes(user.role)) return;

      try {
        setLoading(true);
        setError(null);

        const params = {
          page: currentPage,
          limit: 20,
          ...(filters.action && { action: filters.action }),
          ...(filters.start_date && { start_date: filters.start_date }),
          ...(filters.end_date && { end_date: filters.end_date }),
        };

        const response = await authApi.getAuditLog(params);
        setLogs(response.audit_logs || []);
        setTotal(response.total);
        setTotalPages(response.total_pages);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, [user, currentPage, filters]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  const getActionBadgeColor = (action: string) => {
    switch (action?.toLowerCase()) {
      case 'login': return 'bg-green-100 text-green-800';
      case 'logout': return 'bg-gray-100 text-gray-800';
      case 'create_user': return 'bg-blue-100 text-blue-800';
      case 'update_user': return 'bg-yellow-100 text-yellow-800';
      case 'delete_user': return 'bg-red-100 text-red-800';
      case 'password_change': return 'bg-purple-100 text-purple-800';
      case 'account_lock': return 'bg-orange-100 text-orange-800';
      case 'account_unlock': return 'bg-cyan-100 text-cyan-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isAuthenticated || !user || !['admin', 'super_admin'].includes(user.role)) {
    return null;
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Audit Logs</h1>
          <p className="text-lg text-gray-600">Monitor system activities and user actions</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label htmlFor="action" className="block text-sm font-medium text-gray-700 mb-2">
                Action
              </label>
              <select
                id="action"
                value={filters.action}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, action: e.target.value }));
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Actions</option>
                <option value="LOGIN">Login</option>
                <option value="LOGOUT">Logout</option>
                <option value="CREATE_USER">Create User</option>
                <option value="UPDATE_USER">Update User</option>
                <option value="DELETE_USER">Delete User</option>
                <option value="PASSWORD_CHANGE">Password Change</option>
                <option value="ACCOUNT_LOCK">Account Lock</option>
                <option value="ACCOUNT_UNLOCK">Account Unlock</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                id="start_date"
                value={filters.start_date}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, start_date: e.target.value }));
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                id="end_date"
                value={filters.end_date}
                onChange={(e) => {
                  setFilters(prev => ({ ...prev, end_date: e.target.value }));
                  setCurrentPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex items-end">
              <button
                onClick={() => {
                  setFilters({ action: '', start_date: '', end_date: '' });
                  setCurrentPage(1);
                }}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Logs Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Audit Log Entries ({total})
            </h3>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
              <p className="text-gray-500 mt-4">Loading audit logs...</p>
            </div>
          ) : logs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500">No audit logs found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      IP Address
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User Agent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(log.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionBadgeColor(log.action)}`}>
                          {log.action?.replace('_', ' ') || 'Unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.target_username || log.performed_by_username || 'System'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.ip_address || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate">
                        {log.user_agent ? (
                          <span title={log.user_agent}>
                            {log.user_agent.length > 50 ? `${log.user_agent.substring(0, 50)}...` : log.user_agent}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => {
                            setSelectedLog(log);
                            setShowModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Pagination */}
          {!loading && logs.length > 0 && totalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing page {currentPage} of {totalPages} ({total} total entries)
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
                {/* Page numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = Math.max(1, currentPage - 2) + i;
                  if (pageNum > totalPages) return null;
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-1 text-sm rounded ${
                        currentPage === pageNum
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
        
        {/* Details Modal */}
        {showModal && selectedLog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Audit Log Details</h3>
                <button
                  onClick={() => {
                    setShowModal(false);
                    setSelectedLog(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="px-6 py-4 space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Basic Information</h4>
                    <div className="space-y-3">
                      <div>
                        <span className="text-xs text-gray-500 block">Timestamp</span>
                        <span className="text-sm text-gray-900">{formatDate(selectedLog.created_at)}</span>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 block">Action</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getActionBadgeColor(selectedLog.action)}`}>
                          {selectedLog.action?.replace('_', ' ') || 'Unknown'}
                        </span>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 block">Entity Type</span>
                        <span className="text-sm text-gray-900">{selectedLog.entity_type || '-'}</span>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 block">Entity ID</span>
                        <span className="text-sm text-gray-900">{selectedLog.entity_id || '-'}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">User Information</h4>
                    <div className="space-y-3">
                      <div>
                        <span className="text-xs text-gray-500 block">Performed By</span>
                        <span className="text-sm text-gray-900">{selectedLog.performed_by_username || 'System'}</span>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 block">Target User</span>
                        <span className="text-sm text-gray-900">{selectedLog.target_username || '-'}</span>
                      </div>
                      <div>
                        <span className="text-xs text-gray-500 block">IP Address</span>
                        <span className="text-sm text-gray-900">{selectedLog.ip_address || '-'}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">User Agent</h4>
                  <div className="bg-gray-50 rounded-md p-3">
                    <span className="text-sm text-gray-900 break-all">
                      {selectedLog.user_agent || 'Not available'}
                    </span>
                  </div>
                </div>
                
                {(selectedLog.old_values || selectedLog.new_values) && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {selectedLog.old_values && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-3">Old Values</h4>
                        <div className="bg-red-50 rounded-md p-3">
                          <pre className="text-xs text-gray-900 whitespace-pre-wrap">
                            {JSON.stringify(selectedLog.old_values, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                    
                    {selectedLog.new_values && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-3">New Values</h4>
                        <div className="bg-green-50 rounded-md p-3">
                          <pre className="text-xs text-gray-900 whitespace-pre-wrap">
                            {JSON.stringify(selectedLog.new_values, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
                <button
                  onClick={() => {
                    setShowModal(false);
                    setSelectedLog(null);
                  }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
