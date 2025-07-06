'use client';

import React, { useState, useEffect } from 'react';
import { MaintenanceRecord, MaintenanceApi, MaintenanceStatusEnum, MaintenancePriorityEnum, MaintenanceTypeEnum } from '@/services/maintenanceApi';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import Pagination from '@/components/Pagination';
import { 
  Clock, 
  MapPin, 
  User, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Calendar,
  Filter,
  Eye,
  Edit,
  Plus
} from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ATMMaintenanceHistoryProps {
  terminalId: string;
  terminalName?: string;
  location?: string;
  showActions?: boolean;
  onViewRecord?: (recordId: string) => void;
  onEditRecord?: (recordId: string) => void;
  onCreateNew?: () => void;
}

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

export function ATMMaintenanceHistory({ 
  terminalId, 
  terminalName, 
  location, 
  showActions = true,
  onViewRecord,
  onEditRecord,
  onCreateNew
}: ATMMaintenanceHistoryProps) {
  const router = useRouter();
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states
  const [statusFilter, setStatusFilter] = useState<MaintenanceStatusEnum | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<MaintenancePriorityEnum | ''>('');
  const [typeFilter, setTypeFilter] = useState<MaintenanceTypeEnum | ''>('');
  
  const perPage = 10;

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await MaintenanceApi.getATMMaintenanceHistory(terminalId, page, perPage);
        setRecords(response.maintenance_records);
        setTotalCount(response.total_count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load maintenance history');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [terminalId, page, statusFilter, priorityFilter, typeFilter]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await MaintenanceApi.getATMMaintenanceHistory(terminalId, page, perPage);
      setRecords(response.maintenance_records);
      setTotalCount(response.total_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load maintenance history');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleViewRecord = (recordId: string) => {
    if (onViewRecord) {
      onViewRecord(recordId);
    } else {
      router.push(`/maintenance/${recordId}`);
    }
  };

  const handleEditRecord = (recordId: string) => {
    if (onEditRecord) {
      onEditRecord(recordId);
    } else {
      router.push(`/maintenance/${recordId}/edit`);
    }
  };

  const handleCreateNew = () => {
    if (onCreateNew) {
      onCreateNew();
    } else {
      router.push(`/maintenance/create?terminal_id=${terminalId}`);
    }
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
    setStatusFilter('');
    setPriorityFilter('');
    setTypeFilter('');
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
          <h2 className="text-lg font-semibold">Error Loading Maintenance History</h2>
        </div>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadHistory}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Maintenance History</h1>
            <div className="text-lg text-gray-600 space-y-1">
              <div>Terminal: {terminalId}</div>
              {terminalName && <div>Name: {terminalName}</div>}
              {location && (
                <div className="flex items-center">
                  <MapPin className="h-4 w-4 mr-1" />
                  {location}
                </div>
              )}
            </div>
          </div>
          {showActions && (
            <div className="flex space-x-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </button>
              <button
                onClick={handleCreateNew}
                className="inline-flex items-center px-3 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                New Maintenance
              </button>
            </div>
          )}
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="border-t pt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
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
              <div className="flex items-end">
                <button
                  onClick={clearFilters}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Clear Filters
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">
          Maintenance Timeline ({totalCount} records)
        </h2>

        {records.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium mb-2">No maintenance records found</h3>
            <p>There are no maintenance records for this terminal yet.</p>
            {showActions && (
              <button
                onClick={handleCreateNew}
                className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create First Maintenance Record
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {records.map((record, index) => (
              <div key={record.id} className="relative">
                {/* Timeline line */}
                {index < records.length - 1 && (
                  <div className="absolute left-6 top-16 h-full w-0.5 bg-gray-200"></div>
                )}
                
                {/* Timeline item */}
                <div className="flex items-start space-x-4">
                  {/* Timeline dot */}
                  <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${statusColors[record.status as keyof typeof statusColors]}`}>
                    {statusIcons[record.status as keyof typeof statusIcons]}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0 bg-gray-50 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[record.status as keyof typeof statusColors]}`}>
                            {record.status.replace('_', ' ')}
                          </span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priorityColors[record.priority as keyof typeof priorityColors]}`}>
                            {record.priority}
                          </span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${typeColors[record.maintenance_type as keyof typeof typeColors]}`}>
                            {record.maintenance_type}
                          </span>
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 mb-1">
                          {record.maintenance_type} Maintenance
                        </h3>
                        <div className="text-sm text-gray-500 space-y-1">
                          <div className="flex items-center space-x-4">
                            <span className="flex items-center">
                              <Calendar className="h-4 w-4 mr-1" />
                              {formatDate(record.start_datetime)}
                            </span>
                            {record.end_datetime && (
                              <span className="flex items-center">
                                <Clock className="h-4 w-4 mr-1" />
                                Duration: {formatDuration(record.duration_hours)}
                              </span>
                            )}
                            <span className="flex items-center">
                              <User className="h-4 w-4 mr-1" />
                              {record.created_by}
                            </span>
                          </div>
                        </div>
                      </div>
                      {showActions && (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleViewRecord(record.id)}
                            className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            View
                          </button>
                          <button
                            onClick={() => handleEditRecord(record.id)}
                            className="inline-flex items-center px-2 py-1 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            <Edit className="h-3 w-3 mr-1" />
                            Edit
                          </button>
                        </div>
                      )}
                    </div>
                    
                    <div className="space-y-2">
                      <div>
                        <span className="text-sm font-medium text-gray-700">Problem:</span>
                        <p className="text-sm text-gray-600 mt-1">
                          {record.problem_description.length > 150 
                            ? `${record.problem_description.substring(0, 150)}...` 
                            : record.problem_description}
                        </p>
                      </div>
                      
                      {record.solution_description && (
                        <div>
                          <span className="text-sm font-medium text-gray-700">Solution:</span>
                          <p className="text-sm text-gray-600 mt-1">
                            {record.solution_description.length > 150 
                              ? `${record.solution_description.substring(0, 150)}...` 
                              : record.solution_description}
                          </p>
                        </div>
                      )}
                      
                      {record.images.length > 0 && (
                        <div className="text-sm text-gray-500">
                          📸 {record.images.length} image{record.images.length !== 1 ? 's' : ''} attached
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalCount > perPage && (
          <div className="mt-6 border-t pt-6">
            <Pagination
              currentPage={page}
              totalPages={Math.ceil(totalCount / perPage)}
              totalItems={totalCount}
              itemsPerPage={perPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={() => {}} // Not used in this component
            />
          </div>
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
