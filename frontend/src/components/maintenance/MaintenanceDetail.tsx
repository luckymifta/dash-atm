'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { MaintenanceRecord, MaintenanceApi } from '@/services/maintenanceApi';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ImageUpload } from '@/components/maintenance/ImageUpload';
import { 
  Edit, 
  Trash2, 
  Camera, 
  Clock, 
  MapPin, 
  User, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Calendar,
  Image as ImageIcon,
  ZoomIn,
  Download,
  X
} from 'lucide-react';

interface MaintenanceDetailProps {
  maintenanceId: string;
  onEdit?: () => void;
  onDelete?: () => void;
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

export function MaintenanceDetail({ maintenanceId, onEdit, onDelete }: MaintenanceDetailProps) {
  const router = useRouter();
  const [record, setRecord] = useState<MaintenanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await MaintenanceApi.getMaintenanceRecord(maintenanceId);
        console.log('Loaded maintenance record:', data);
        console.log('Images data:', data.images);
        setRecord(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load maintenance record');
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [maintenanceId]);

  const loadRecord = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await MaintenanceApi.getMaintenanceRecord(maintenanceId);
      setRecord(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load maintenance record');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit();
    } else {
      router.push(`/maintenance/${maintenanceId}/edit`);
    }
  };

  const handleDelete = async () => {
    try {
      setDeleteLoading(true);
      await MaintenanceApi.deleteMaintenanceRecord(maintenanceId);
      setShowDeleteModal(false);
      if (onDelete) {
        onDelete();
      } else {
        router.push('/maintenance');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete maintenance record');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleImageUploadSuccess = () => {
    setShowImageUpload(false);
    loadRecord(); // Refresh to show new images
  };

  const handleImageDelete = async (imageId: string) => {
    try {
      await MaintenanceApi.deleteMaintenanceImage(maintenanceId, imageId);
      loadRecord(); // Refresh to remove deleted image
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete image');
    }
  };

  const formatDuration = (durationHours: number | null | undefined) => {
    if (!durationHours) return 'N/A';
    const hours = Math.floor(durationHours);
    const minutes = Math.round((durationHours - hours) * 60);
    return `${hours}h ${minutes}m`;
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const downloadImage = (imageUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getImageUrl = (image: { image_id?: string; file_path?: string; url?: string }) => {
    console.log('getImageUrl called with image:', image);
    console.log('record?.id:', record?.id);
    
    // Use static file mounting - much simpler and more reliable
    if (image.image_id && record?.id) {
      // Find the file extension from the file_path if available
      let extension = '.png'; // default
      if (image.file_path) {
        const match = image.file_path.match(/\.(jpg|jpeg|png|gif|pdf|txt|doc|docx)$/i);
        if (match) {
          extension = match[0];
        }
      }
      
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'http://localhost:8000';
      const url = `${baseUrl}/uploads/${record.id}/${image.image_id}${extension}`;
      console.log('Generated static file URL:', url);
      return url;
    }
    
    // Fallback: try the API endpoint
    if (image.image_id && record?.id) {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api', '') || 'http://localhost:8000';
      const url = `${baseUrl}/api/v1/maintenance/images/${record.id}/${image.image_id}`;
      console.log('Generated API URL:', url);
      return url;
    }
    
    // Final fallback to direct file path or url
    console.log('Fallback image URL:', image.file_path || image.url || '');
    return image.file_path || image.url || '';
  };

  const getImageId = (image: { image_id?: string; id?: string }) => {
    return image.image_id || image.id || '';
  };

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow border border-red-200 p-6">
        <div className="flex items-center text-red-700 mb-4">
          <AlertTriangle className="h-5 w-5 mr-2" />
          <h2 className="text-lg font-semibold">Error Loading Maintenance Record</h2>
        </div>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={loadRecord}
          className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!record) {
    return (
      <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Maintenance Record Not Found</h2>
        <p className="text-gray-600 mb-4">The requested maintenance record could not be found.</p>
        <button
          onClick={() => router.push('/maintenance')}
          className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Back to Maintenance List
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">Maintenance Record</h1>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[record.status as keyof typeof statusColors]}`}>
                {statusIcons[record.status as keyof typeof statusIcons]}
                <span className="ml-1">{record.status.replace('_', ' ')}</span>
              </span>
            </div>
            <p className="text-lg text-gray-600">
              Terminal: {record.terminal_id} {record.terminal_name && `(${record.terminal_name})`}
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleEdit}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </button>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-500">Priority</div>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priorityColors[record.priority as keyof typeof priorityColors]}`}>
              {record.priority}
            </span>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-500">Type</div>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${typeColors[record.maintenance_type as keyof typeof typeColors]}`}>
              {record.maintenance_type}
            </span>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-500">Duration</div>
            <div className="flex items-center text-gray-900">
              <Clock className="h-4 w-4 mr-1 text-gray-400" />
              {formatDuration(record.duration_hours)}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-500">Created By</div>
            <div className="flex items-center text-gray-900">
              <User className="h-4 w-4 mr-1 text-gray-400" />
              {record.created_by}
            </div>
          </div>
        </div>

        {record.location && (
          <div className="mb-6">
            <div className="text-sm font-medium text-gray-500 mb-1">Location</div>
            <div className="flex items-center text-gray-900">
              <MapPin className="h-4 w-4 mr-1 text-gray-400" />
              {record.location}
            </div>
          </div>
        )}
      </div>

      {/* Timeline Section */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
          <Calendar className="h-5 w-5 mr-2" />
          Timeline
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-sm font-medium text-gray-500 mb-1">Start Date & Time</div>
            <div className="text-lg text-gray-900">
              {formatDate(record.start_datetime)}
            </div>
          </div>
          {record.end_datetime && (
            <div>
              <div className="text-sm font-medium text-gray-500 mb-1">End Date & Time</div>
              <div className="text-lg text-gray-900">
                {formatDate(record.end_datetime)}
              </div>
            </div>
          )}
        </div>
        <div className="text-xs text-gray-500">
          Created: {formatDate(record.created_at)} • 
          Updated: {formatDate(record.updated_at)}
        </div>
      </div>

      {/* Problem & Solution Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Problem Description
          </h2>
          <div className="whitespace-pre-wrap text-gray-700">
            {record.problem_description}
          </div>
        </div>

        {record.solution_description && (
          <div className="bg-white rounded-lg shadow border p-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center mb-4">
              <CheckCircle className="h-5 w-5 mr-2" />
              Solution Description
            </h2>
            <div className="whitespace-pre-wrap text-gray-700">
              {record.solution_description}
            </div>
          </div>
        )}
      </div>

      {/* Images Section */}
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <ImageIcon className="h-5 w-5 mr-2" />
            Images ({record.images.length})
          </h2>
          <button
            onClick={() => setShowImageUpload(true)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <Camera className="h-4 w-4 mr-2" />
            Add Images
          </button>
        </div>

        {record.images.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <ImageIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No images uploaded yet</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {record.images.map((image) => (
              <div key={getImageId(image)} className="relative group">
                <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getImageUrl(image)}
                    alt={image.filename}
                    className="w-full h-full cursor-pointer transition-transform group-hover:scale-105"
                    style={{ objectFit: 'cover' }}
                    onClick={() => setSelectedImage(getImageUrl(image))}
                    onError={(e) => {
                      console.error('Image failed to load:', getImageUrl(image));
                      console.error('Error event:', e);
                      const target = e.target as HTMLImageElement;
                      target.style.backgroundColor = '#fee2e2';
                      target.style.color = '#dc2626';
                      target.style.fontSize = '12px';
                      target.style.padding = '8px';
                      target.style.textAlign = 'center';
                      target.style.display = 'flex';
                      target.style.alignItems = 'center';
                      target.style.justifyContent = 'center';
                      target.alt = 'Failed to load image';
                      target.innerHTML = 'Image load failed';
                    }}
                    onLoad={() => {
                      console.log('Image loaded successfully:', getImageUrl(image));
                    }}
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity flex items-center justify-center">
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-2">
                      <button
                        onClick={() => setSelectedImage(getImageUrl(image))}
                        className="p-1 bg-white bg-opacity-80 rounded-full hover:bg-opacity-100"
                      >
                        <ZoomIn className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => downloadImage(getImageUrl(image), image.filename)}
                        className="p-1 bg-white bg-opacity-80 rounded-full hover:bg-opacity-100"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleImageDelete(getImageId(image))}
                        className="p-1 bg-red-500 bg-opacity-80 text-white rounded-full hover:bg-opacity-100"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1 truncate" title={image.filename}>
                  {image.filename}
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(image.uploaded_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Image Upload Modal */}
      {showImageUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Upload Images</h3>
              <button
                onClick={() => setShowImageUpload(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <p className="text-gray-600 mb-4">
              Add images to this maintenance record. Maximum 5 images, 10MB each.
            </p>
            <ImageUpload
              maintenanceId={maintenanceId}
              onSuccess={handleImageUploadSuccess}
              onCancel={() => setShowImageUpload(false)}
            />
          </div>
        </div>
      )}

      {/* Image Preview Modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
          <div className="relative max-w-4xl max-h-[90vh] w-full mx-4">
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 text-white hover:text-gray-300 z-10"
            >
              <X className="h-8 w-8" />
            </button>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={selectedImage}
              alt="Preview"
              className="max-w-full max-h-full object-contain mx-auto"
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center text-red-700 mb-4">
              <AlertTriangle className="h-6 w-6 mr-2" />
              <h3 className="text-lg font-semibold">Delete Maintenance Record</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this maintenance record? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deleteLoading}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
              >
                {deleteLoading ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
