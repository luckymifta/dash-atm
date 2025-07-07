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
import { ImageUpload } from '@/components/maintenance/ImageUpload';
import {
  Wrench,
  AlertTriangle,
  Save,
  X,
  AlertCircle,
  Clock,
  CheckCircle,
  Upload,
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
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [recordIdForUpload, setRecordIdForUpload] = useState<string | null>(null);
  const [existingRecord, setExistingRecord] = useState<MaintenanceRecord | null>(null);
  const [pendingImages, setPendingImages] = useState<File[]>([]); // Store images for new records
  
  // Debug effect to track modal state changes
  useEffect(() => {
    console.log('Modal state changed:', { 
      showImageUpload, 
      recordIdForUpload, 
      recordId,
      isEditMode 
    });
  }, [showImageUpload, recordIdForUpload, recordId, isEditMode]);
  
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
      
      // Debug: Check if we have an auth token
      const authToken = document.cookie.split('; ').find(row => row.startsWith('auth_token='));
      console.log('Auth token found:', authToken ? 'Yes' : 'No');
      if (!authToken) {
        setError('You are not logged in. Please log in again.');
        return;
      }
      
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
        setRecordIdForUpload(recordId);
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
        
        const newRecord = await MaintenanceApi.createMaintenanceRecord(createData);
        setRecordIdForUpload(newRecord.id);
        
        // If there are pending images, upload them automatically
        if (pendingImages.length > 0) {
          try {
            // Upload images to the newly created record
            await MaintenanceApi.uploadMaintenanceImages(newRecord.id, pendingImages);
            
            // Clear pending images after successful upload
            setPendingImages([]);
            
            // Navigate to maintenance list after successful creation and upload
            router.push('/maintenance');
            return; // Exit early, no need to show upload modal
          } catch (uploadError) {
            console.error('Error uploading images:', uploadError);
            setError('Record created successfully, but failed to upload images. You can upload them later.');
            // Still redirect to maintenance list even if image upload fails
            router.push('/maintenance');
            return;
          }
        } else {
          // No pending images, just navigate to maintenance list
          router.push('/maintenance');
          return;
        }
      }
      
      // For edit mode, show image upload option if needed
      if (isEditMode) {
        setShowImageUpload(true);
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save maintenance record';
      
      // Handle authentication errors specifically
      if (errorMessage.includes('Not authenticated') || errorMessage.includes('401')) {
        setError('Your session has expired. Please log out and log back in.');
        // Optionally redirect to login after a delay
        setTimeout(() => {
          router.push('/auth/login');
        }, 3000);
      } else {
        setError(errorMessage);
      }
      
      console.error('Error saving record:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleImageUploadSuccess = () => {
    // Refresh the maintenance record to get updated images
    if (recordIdForUpload && isEditMode) {
      loadExistingRecord(recordIdForUpload);
    }
    setShowImageUpload(false);
  };

  const handleImageUploadCancel = () => {
    setShowImageUpload(false);
  };
  
  const handleCancel = () => {
    router.back();
  };
  
  if (loading) {
    return <LoadingSkeleton />;
  }
  
  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-100 ${className}`}>
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
        <div className="max-w-3xl mx-auto">
          <div className="space-y-8">
            {/* Terminal Information */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                <Wrench className="w-5 h-5 mr-2 text-blue-600" />
                Terminal Information
              </h3>
              
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
            
            {/* Timing */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                <Clock className="w-5 h-5 mr-2 text-green-600" />
                Timing
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
            
            {/* Image Upload Section */}
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                <Upload className="w-5 h-5 mr-2 text-purple-600" />
                Images & Attachments
              </h3>
              
              <div className="space-y-4">                  {/* Current Images Display */}
                  {existingRecord?.images && existingRecord.images.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Current Images ({existingRecord.images.length})
                      </label>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {existingRecord.images.map((image, index) => {
                          const getImageUrl = (img: { image_id?: string; file_path?: string; url?: string }) => {
                            if (img.image_id && existingRecord.id) {
                              // Find the file extension from the file_path if available
                              let extension = '.png'; // default
                              if (img.file_path) {
                                const match = img.file_path.match(/\.(jpg|jpeg|png|gif|pdf|txt|doc|docx)$/i);
                                if (match) {
                                  extension = match[0];
                                }
                              }
                              
                              const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'http://localhost:8000';
                              const url = `${baseUrl}/uploads/${existingRecord.id}/${img.image_id}${extension}`;
                              console.log('Generated static file URL:', url);
                              return url;
                            }
                            console.log('Fallback image URL:', img.file_path || img.url || '');
                            return img.file_path || img.url || '';
                          };
                          
                          return (
                            <div key={index} className="relative group">
                              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                  src={getImageUrl(image)}
                                  alt={image.filename}
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    // Fallback to upload icon if image fails to load
                                    const target = e.target as HTMLImageElement;
                                    target.style.display = 'none';
                                    target.parentElement?.classList.add('flex', 'items-center', 'justify-center');
                                    const fallback = document.createElement('div');
                                    fallback.className = 'w-full h-full flex items-center justify-center text-gray-500';
                                    fallback.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>';
                                    target.parentElement?.appendChild(fallback);
                                  }}
                                />
                              </div>
                              <p className="mt-1 text-xs text-gray-600 truncate">
                                {image.filename}
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {/* Pending Images Display (for new records) */}
                  {!isEditMode && pendingImages.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Selected Images ({pendingImages.length}) - Will be uploaded when record is saved
                      </label>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {pendingImages.map((file, index) => {
                          const isImage = file.type.startsWith('image/');
                          const previewUrl = isImage ? URL.createObjectURL(file) : null;
                          
                          return (
                            <div key={index} className="relative group">
                              <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                                {isImage && previewUrl ? (
                                  /* eslint-disable-next-line @next/next/no-img-element */
                                  <img
                                    src={previewUrl}
                                    alt={file.name}
                                    className="w-full h-full object-cover"
                                    onLoad={() => {
                                      // Clean up the object URL after the image loads
                                      URL.revokeObjectURL(previewUrl);
                                    }}
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center text-gray-500">
                                    <Upload className="w-8 h-8" />
                                  </div>
                                )}
                              </div>
                              <p className="mt-1 text-xs text-gray-600 truncate">
                                {file.name}
                              </p>
                              <button
                                type="button"
                                onClick={() => {
                                  setPendingImages(prev => prev.filter((_, i) => i !== index));
                                }}
                                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                              >
                                ×
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {/* Upload New Images Button */}
                  <div>
                    <button
                      type="button"
                      onClick={() => {
                        console.log('Upload button clicked - Debug info:', { 
                          recordIdForUpload, 
                          isEditMode, 
                          recordId, 
                          showImageUpload,
                          pendingImagesCount: pendingImages.length
                        });
                        
                        // Always allow image upload now
                        setShowImageUpload(true);
                      }}
                      className="w-full px-4 py-3 border-2 border-dashed rounded-lg transition-colors flex items-center justify-center border-gray-300 text-gray-600 hover:border-gray-400 hover:text-gray-700"
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      {existingRecord?.images && existingRecord.images.length > 0 
                        ? 'Add More Images' 
                        : pendingImages.length > 0
                        ? `Add More Images (${pendingImages.length} selected)`
                        : isEditMode ? 'Upload Images' : 'Select Images'
                      }
                    </button>
                    {!isEditMode && (
                      <p className="mt-2 text-xs text-gray-500 text-center">
                        Images will be uploaded automatically when the record is saved
                      </p>
                    )}
                  </div>
              </div>
            </div>
            
            {/* Form Actions - Moved to Bottom */}
            <div className="flex items-center justify-end space-x-4 pt-8 border-t border-gray-200">
              <button
                type="button"
                onClick={handleCancel}
                className="px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors flex items-center"
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </button>
              <button
                type="submit"
                disabled={!isValid || saving}
                className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
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
      </form>
      
      {/* Image Upload Modal */}
      {showImageUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  {isEditMode ? 'Upload Images' : 'Select Images'}
                </h2>
                <button
                  onClick={() => setShowImageUpload(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              {isEditMode ? (
                <ImageUpload
                  maintenanceId={recordIdForUpload || recordId || ''}
                  onSuccess={handleImageUploadSuccess}
                  onCancel={handleImageUploadCancel}
                />
              ) : (
                // Simple file selector for new records
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Images to Upload
                    </label>
                    <input
                      type="file"
                      multiple
                      accept="image/*,.pdf,.txt,.doc,.docx"
                      onChange={(e) => {
                        if (e.target.files) {
                          const selectedFiles = Array.from(e.target.files);
                          setPendingImages(prev => [...prev, ...selectedFiles]);
                          setShowImageUpload(false);
                        }
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-white text-gray-900"
                    />
                    <p className="mt-2 text-xs text-gray-500">
                      Select multiple files (images, PDFs, documents). Max 10MB per file.
                    </p>
                  </div>
                  
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setShowImageUpload(false)}
                      className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
