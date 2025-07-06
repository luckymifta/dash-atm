'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import {
  MaintenanceApi,
  MaintenanceCreate,
  MaintenanceUpdate,
  MaintenanceRecord,
  MaintenanceTypeEnum,
  MaintenancePriorityEnum,
  MaintenanceStatusEnum,
} from '@/services/maintenanceApi';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { TerminalDropdown } from '@/components/TerminalDropdown';
import {
  Wrench,
  AlertTriangle,
  Save,
  X,
  ArrowLeft,
  AlertCircle,
  Clock,
  CheckCircle,
} from 'lucide-react';

interface MaintenanceFormProps {
  recordId?: string; // If provided, form is in edit mode
  className?: string;
}

interface FormData {
  terminal_id: string;
  start_datetime: string;
  end_datetime?: string;
  problem_description: string;
  solution_description?: string;
  maintenance_type: MaintenanceTypeEnum;
  priority: MaintenancePriorityEnum;
  status: MaintenanceStatusEnum;
}

export function MaintenanceForm({ recordId, className = '' }: MaintenanceFormProps) {
  const router = useRouter();
  const isEditMode = !!recordId;
  
  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingRecord, setExistingRecord] = useState<MaintenanceRecord | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    watch,
    reset,
    control,
  } = useForm<FormData>({
    mode: 'onChange',
    defaultValues: {
      maintenance_type: MaintenanceTypeEnum.CORRECTIVE,
      priority: MaintenancePriorityEnum.MEDIUM,
      status: MaintenanceStatusEnum.PLANNED,
    },
  });
  
  // Watch end_datetime to validate it's after start_datetime
  const startDateTime = watch('start_datetime');
  const endDateTime = watch('end_datetime');
  
  // Load existing record for edit mode
  const loadExistingRecord = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const record = await MaintenanceApi.getMaintenanceRecord(id);
      setExistingRecord(record);
      
      // Populate form with existing data
      reset({
        terminal_id: record.terminal_id,
        start_datetime: record.start_datetime.slice(0, 16), // Format for datetime-local input
        end_datetime: record.end_datetime?.slice(0, 16) || '',
        problem_description: record.problem_description,
        solution_description: record.solution_description || '',
        maintenance_type: record.maintenance_type,
        priority: record.priority,
        status: record.status,
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load maintenance record');
      console.error('Error loading record:', err);
    } finally {
      setLoading(false);
    }
  }, [reset]);

  useEffect(() => {
    if (isEditMode && recordId) {
      loadExistingRecord(recordId);
    }
  }, [isEditMode, recordId, loadExistingRecord]);
  
  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      setError(null);
      
      // Validate dates
      if (data.end_datetime && data.start_datetime && new Date(data.end_datetime) <= new Date(data.start_datetime)) {
        setError('End date must be after start date');
        return;
      }
      
      // Validate start date is not more than 1 hour in the future (as per PRD)
      const startDate = new Date(data.start_datetime);
      const oneHourFromNow = new Date(Date.now() + 60 * 60 * 1000);
      if (startDate > oneHourFromNow) {
        setError('Start date cannot be more than 1 hour in the future');
        return;
      }
      
      if (isEditMode && recordId) {
        // Update existing record
        const updateData: MaintenanceUpdate = {
          start_datetime: data.start_datetime,
          end_datetime: data.end_datetime || undefined,
          problem_description: data.problem_description,
          solution_description: data.solution_description || undefined,
          maintenance_type: data.maintenance_type,
          priority: data.priority,
          status: data.status,
        };
        
        await MaintenanceApi.updateMaintenanceRecord(recordId, updateData);
      } else {
        // Create new record
        const createData: MaintenanceCreate = {
          terminal_id: data.terminal_id,
          start_datetime: data.start_datetime,
          end_datetime: data.end_datetime || undefined,
          problem_description: data.problem_description,
          solution_description: data.solution_description || undefined,
          maintenance_type: data.maintenance_type,
          priority: data.priority,
          status: data.status,
        };
        
        await MaintenanceApi.createMaintenanceRecord(createData);
      }
      
      // Navigate back to list or record view
      router.push('/maintenance');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save maintenance record');
      console.error('Error saving record:', err);
    } finally {
      setSaving(false);
    }
  };
  
  const handleCancel = () => {
    router.back();
  };
  
  if (loading) {
    return <LoadingSkeleton />;
  }
  
  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-100 ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={handleCancel}
              className="mr-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isEditMode ? 'Edit Maintenance Record' : 'Create Maintenance Record'}
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                {isEditMode 
                  ? `Editing record for terminal ${existingRecord?.terminal_id}`
                  : 'Create a new maintenance record for ATM terminal'
                }
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              <X className="w-4 h-4 mr-2" />
              Cancel
            </button>
            <button
              type="submit"
              form="maintenance-form"
              disabled={!isValid || saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
            >
              {saving ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              {saving ? 'Saving...' : isEditMode ? 'Update Record' : 'Create Record'}
            </button>
          </div>
        </div>
      </div>
      
      {/* Error Message */}
      {error && (
        <div className="px-6 py-4 bg-red-50 border-b border-red-100">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}
      
      {/* Form */}
      <form id="maintenance-form" onSubmit={handleSubmit(onSubmit)} className="p-8 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Column - Terminal & Basic Info */}
            <div className="space-y-6">
              {/* Terminal Information */}
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                  <Wrench className="w-5 h-5 mr-2 text-blue-600" />
                  Terminal Information
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Terminal ID *
                    </label>
                <Controller
                  name="terminal_id"
                  control={control}
                  rules={{
                    required: 'Terminal ID is required'
                  }}
                  render={({ field: { value, onChange } }) => (
                    <TerminalDropdown
                      value={value}
                      onChange={onChange}
                      disabled={isEditMode}
                      placeholder="Select ATM Terminal"
                      error={errors.terminal_id?.message}
                      className="w-full"
                    />
                  )}
                />
              </div>
            </div>
          </div>
          
          {/* Maintenance Details */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2 text-orange-600" />
              Maintenance Details
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Maintenance Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maintenance Type *
                </label>
                <select
                  {...register('maintenance_type', { required: 'Maintenance type is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {Object.values(MaintenanceTypeEnum).map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                {errors.maintenance_type && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.maintenance_type.message}
                  </p>
                )}
              </div>
              
              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority *
                </label>
                <select
                  {...register('priority', { required: 'Priority is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900"
                >
                  {Object.values(MaintenancePriorityEnum).map(priority => (
                    <option key={priority} value={priority}>{priority}</option>
                  ))}
                </select>
                {errors.priority && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.priority.message}
                  </p>
                )}
              </div>
              
              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status *
                </label>
                <select
                  {...register('status', { required: 'Status is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900"
                >
                  {Object.values(MaintenanceStatusEnum).map(status => (
                    <option key={status} value={status}>{status.replace('_', ' ')}</option>
                  ))}
                </select>
                {errors.status && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.status.message}
                  </p>
                )}
              </div>
            </div>
          </div>
            </div>
          
            {/* Right Column - Timing & Descriptions */}
            <div className="space-y-6">
              {/* Timing */}
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                  <Clock className="w-5 h-5 mr-2 text-green-600" />
                  Timing
                </h3>
                
                <div className="space-y-4">
                  {/* Start Date/Time */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      {...register('start_datetime', { 
                        required: 'Start date and time is required',
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900"
                    />
                    {errors.start_datetime && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.start_datetime.message}
                      </p>
                    )}
                    <p className="mt-1 text-xs text-gray-500">
                      Cannot be more than 1 hour in the future
                    </p>
                  </div>
                  
                  {/* End Date/Time */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Date & Time
                    </label>
                    <input
                      type="datetime-local"
                      {...register('end_datetime')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Leave empty if maintenance is ongoing
                    </p>
                    {endDateTime && startDateTime && new Date(endDateTime) <= new Date(startDateTime) && (
                      <p className="mt-1 text-sm text-red-600">
                        End time must be after start time
                      </p>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Problem Description */}
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">
                  Problem Description
                </h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Describe the problem *
                  </label>
                  <textarea
                    rows={4}
                    {...register('problem_description', {
                      required: 'Problem description is required',
                      minLength: {
                        value: 10,
                        message: 'Problem description must be at least 10 characters'
                      },
                      maxLength: {
                        value: 2000,
                        message: 'Problem description cannot exceed 2000 characters'
                      }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900 placeholder-gray-500"
                    placeholder="Describe the issue that requires maintenance..."
                  />
                  {errors.problem_description && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.problem_description.message}
                    </p>
                  )}
                </div>
              </div>
              
              {/* Solution Description */}
              <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                  Solution Description
                </h3>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Describe the solution (optional)
                  </label>
                  <textarea
                    rows={4}
                    {...register('solution_description', {
                      maxLength: {
                        value: 2000,
                        message: 'Solution description cannot exceed 2000 characters'
                      }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900 placeholder-gray-500"
                    placeholder="Describe the solution or actions taken to resolve the issue..."
                  />
                  {errors.solution_description && (
                    <p className="mt-1 text-sm text-red-600">
                      {errors.solution_description.message}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
