'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  MaintenanceApi, 
  MaintenanceRecord, 
  MaintenanceListParams,
  MaintenanceStatusEnum,
  MaintenancePriorityEnum,
  MaintenanceTypeEnum
} from '@/services/maintenanceApi';
import { ATMListItem } from '@/services/atmApi';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { TerminalDropdown } from '@/components/TerminalDropdown';
import Pagination from '@/components/Pagination';
import { 
  Plus, 
  Eye, 
  Edit, 
  Trash2, 
  Filter,
  Calendar,
  Clock,
  User,
  MapPin,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

const statusIcons = {
  PLANNED: <Calendar className="h-4 w-4" />,
  IN_PROGRESS: <Clock className="h-4 w-4" />,
  COMPLETED: <CheckCircle className="h-4 w-4" />,
  CANCELLED: <XCircle className="h-4 w-4" />
};

const statusColors = {
  PLANNED: 'bg-blue-100 text-blue-800',
  IN_PROGRESS: 'bg-yellow-100 text-yellow-800',
  COMPLETED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800'
};

const priorityColors = {
  LOW: 'bg-gray-100 text-gray-800',
  MEDIUM: 'bg-blue-100 text-blue-800',
  HIGH: 'bg-orange-100 text-orange-800',
  CRITICAL: 'bg-red-100 text-red-800'
};

const typeColors = {
  PREVENTIVE: 'bg-green-100 text-green-800',
  CORRECTIVE: 'bg-yellow-100 text-yellow-800',
  EMERGENCY: 'bg-red-100 text-red-800'
};

// Enhanced maintenance record with terminal details
interface EnhancedMaintenanceRecord extends MaintenanceRecord {
  terminal_location?: string;
  terminal_details?: ATMListItem;
}

export function MaintenanceList() {
  const router = useRouter();
  const [records, setRecords] = useState<EnhancedMaintenanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states
  const [terminalIdFilter, setTerminalIdFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<MaintenanceStatusEnum | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<MaintenancePriorityEnum | ''>('');
  const [typeFilter, setTypeFilter] = useState<MaintenanceTypeEnum | ''>('');
  const [createdByFilter, setCreatedByFilter] = useState('');
  
  const perPage = 20;

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch maintenance records
        const params: MaintenanceListParams = {
          page,
          per_page: perPage,
          ...(terminalIdFilter && { terminal_id: terminalIdFilter }),
          ...(statusFilter && { status: statusFilter }),
          ...(priorityFilter && { priority: priorityFilter }),
          ...(typeFilter && { maintenance_type: typeFilter }),
          ...(createdByFilter && { created_by: createdByFilter }),
        };
        
        // Fetch maintenance records only for now (optimize terminal fetching later)
        const maintenanceResponse = await MaintenanceApi.listMaintenanceRecords(params);
        
        // For now, just use the maintenance records without terminal details
        // TODO: Optimize terminal data fetching to avoid timeout issues
        const enhancedRecords: EnhancedMaintenanceRecord[] = maintenanceResponse.maintenance_records.map(record => ({
          ...record,
          terminal_location: record.location || `Terminal ${record.terminal_id}`,
          terminal_details: undefined
        }));
        
        setRecords(enhancedRecords);
        setTotalCount(maintenanceResponse.total_count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load maintenance records');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [page, terminalIdFilter, statusFilter, priorityFilter, typeFilter, createdByFilter, perPage]);

  const loadRecords = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: MaintenanceListParams = {
        page,
        per_page: perPage,
        ...(terminalIdFilter && { terminal_id: terminalIdFilter }),
        ...(statusFilter && { status: statusFilter }),
        ...(priorityFilter && { priority: priorityFilter }),
        ...(typeFilter && { maintenance_type: typeFilter }),
        ...(createdByFilter && { created_by: createdByFilter }),
      };
      
      // Fetch maintenance records only for now (optimize terminal fetching later)
      const maintenanceResponse = await MaintenanceApi.listMaintenanceRecords(params);
      
      // For now, just use the maintenance records without terminal details
      // TODO: Optimize terminal data fetching to avoid timeout issues
      const enhancedRecords: EnhancedMaintenanceRecord[] = maintenanceResponse.maintenance_records.map(record => ({
        ...record,
        terminal_location: record.location || `Terminal ${record.terminal_id}`,
        terminal_details: undefined
      }));
      
      setRecords(enhancedRecords);
      setTotalCount(maintenanceResponse.total_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load maintenance records');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleItemsPerPageChange = () => {
    // Would implement if needed
  };

  const handleView = (recordId: string) => {
    router.push(`/maintenance/${recordId}`);
  };

  const handleEdit = (recordId: string) => {
    router.push(`/maintenance/${recordId}/edit`);
  };

  const handleDelete = async (recordId: string) => {
    if (!confirm('Are you sure you want to delete this maintenance record?')) {
      return;
    }
    
    try {
      await MaintenanceApi.deleteMaintenanceRecord(recordId);
      loadRecords(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete maintenance record');
    }
  };

  const handleCreateNew = () => {
    router.push('/maintenance/create');
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const formatDuration = (durationHours: number | null | undefined) => {
    if (!durationHours) return 'N/A';
    const hours = Math.floor(durationHours);
    const minutes = Math.round((durationHours - hours) * 60);
    return `${hours}h ${minutes}m`;
  };

  const clearFilters = () => {
    setTerminalIdFilter('');
    setStatusFilter('');
    setPriorityFilter('');
    setTypeFilter('');
    setCreatedByFilter('');
    setPage(1);
  };

  if (loading && records.length === 0) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow border border-red-200 p-6">
        <div className="flex items-center text-red-700 mb-4">
          <AlertTriangle className="h-5 w-5 mr-2" />
          <h2 className="text-lg font-semibold">Error Loading Maintenance Records</h2>
        </div>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadRecords}
          disabled={loading}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Retrying...
            </>
          ) : (
            'Try Again'
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </button>
          <button
            onClick={handleCreateNew}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Maintenance
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Terminal ID
              </label>
              <TerminalDropdown
                value={terminalIdFilter}
                onChange={setTerminalIdFilter}
                placeholder="Filter by terminal"
                className="w-full"
              />
            </div>
            <div>
              <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as MaintenanceStatusEnum | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Statuses</option>
                <option value="PLANNED">Planned</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
            <div>
              <label htmlFor="priority-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                id="priority-filter"
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value as MaintenancePriorityEnum | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Priorities</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
            <div>
              <label htmlFor="type-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Type
              </label>
              <select
                id="type-filter"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value as MaintenanceTypeEnum | '')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Types</option>
                <option value="PREVENTIVE">Preventive</option>
                <option value="CORRECTIVE">Corrective</option>
                <option value="EMERGENCY">Emergency</option>
              </select>
            </div>
            <div>
              <label htmlFor="created-by-filter" className="block text-sm font-medium text-gray-700 mb-1">
                Created By
              </label>
              <input
                id="created-by-filter"
                type="text"
                value={createdByFilter}
                onChange={(e) => setCreatedByFilter(e.target.value)}
                placeholder="Filter by creator"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button
              onClick={clearFilters}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}

      {/* Records Table */}
      <div className="bg-white rounded-lg shadow border overflow-hidden">
        {records.length === 0 ? (
          <div className="text-center py-12 px-6">
            <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No maintenance records found</h3>
            <p className="text-gray-500 mb-4">
              {terminalIdFilter || statusFilter || priorityFilter || typeFilter || createdByFilter 
                ? 'No records match your current filters.' 
                : 'Get started by creating your first maintenance record.'}
            </p>
            <button
              onClick={handleCreateNew}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Maintenance Record
            </button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Terminal Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type / Status / Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date / Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Problem
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created By
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {records.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      {/* Terminal Location */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="font-medium text-gray-900 flex items-center">
                            <MapPin className="h-4 w-4 mr-2 text-gray-400" />
                            {record.terminal_location || record.location || 'Unknown Location'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {record.terminal_name ? `${record.terminal_name} (${record.terminal_id})` : `Terminal ${record.terminal_id}`}
                          </div>
                          {record.terminal_details && (
                            <div className="text-xs text-gray-400 mt-1">
                              Status: {record.terminal_details.current_status}
                            </div>
                          )}
                        </div>
                      </td>
                      
                      {/* Type / Status / Priority */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="space-y-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${typeColors[record.maintenance_type as keyof typeof typeColors]}`}>
                            {record.maintenance_type}
                          </span>
                          <br />
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusColors[record.status as keyof typeof statusColors]}`}>
                            {statusIcons[record.status as keyof typeof statusIcons]}
                            <span className="ml-1">{record.status.replace('_', ' ')}</span>
                          </span>
                          <br />
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${priorityColors[record.priority as keyof typeof priorityColors]}`}>
                            {record.priority}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="space-y-1">
                          <div className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                            {formatDate(record.start_datetime)}
                          </div>
                          {record.duration_hours && (
                            <div className="flex items-center text-xs text-gray-500">
                              <Clock className="h-3 w-3 mr-1" />
                              {formatDuration(record.duration_hours)}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 max-w-xs">
                          {record.problem_description.length > 100 
                            ? `${record.problem_description.substring(0, 100)}...` 
                            : record.problem_description}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-1 text-gray-400" />
                          {record.created_by}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleView(record.id)}
                          className="text-indigo-600 hover:text-indigo-900 p-1"
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(record.id)}
                          className="text-green-600 hover:text-green-900 p-1"
                          title="Edit"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(record.id)}
                          className="text-red-600 hover:text-red-900 p-1"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalCount > perPage && (
              <div className="px-6 py-4 border-t border-gray-200">
                <Pagination
                  currentPage={page}
                  totalPages={Math.ceil(totalCount / perPage)}
                  totalItems={totalCount}
                  itemsPerPage={perPage}
                  onPageChange={handlePageChange}
                  onItemsPerPageChange={handleItemsPerPageChange}
                />
              </div>
            )}
          </>
        )}
      </div>

      {loading && records.length > 0 && (
        <div className="text-center py-4">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      )}
    </div>
  );
}