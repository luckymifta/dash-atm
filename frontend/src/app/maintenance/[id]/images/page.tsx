'use client';

import React, { useState, useEffect } from 'react';
import { MaintenanceApi, MaintenanceRecord } from '@/services/maintenanceApi';
import DashboardLayout from '@/components/DashboardLayout';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ImageUpload } from '@/components/maintenance/ImageUpload';
import { ArrowLeft, Image as ImageIcon, Download, Trash2, Eye, AlertTriangle } from 'lucide-react';
import { useRouter, useParams } from 'next/navigation';

export default function MaintenanceImagesPage() {
  const router = useRouter();
  const params = useParams();
  const maintenanceId = params.id as string;
  
  const [record, setRecord] = useState<MaintenanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    const loadData = async () => {
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

  const handleImageDelete = async (imageId: string) => {
    if (!confirm('Are you sure you want to delete this image?')) {
      return;
    }
    
    try {
      await MaintenanceApi.deleteMaintenanceImage(maintenanceId, imageId);
      loadRecord(); // Refresh to remove deleted image
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete image');
    }
  };

  const handleUploadSuccess = () => {
    setShowUpload(false);
    loadRecord(); // Refresh to show new images
  };

  const downloadImage = (imageUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getImageUrl = (image: { file_path?: string; url?: string }) => {
    return image.file_path || image.url || '';
  };

  const getImageId = (image: { image_id?: string; id?: string }) => {
    return image.image_id || image.id || '';
  };

  if (loading) {
    return (
      <DashboardLayout>
        <LoadingSkeleton />
      </DashboardLayout>
    );
  }

  if (error || !record) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-gray-50">
          <div className="py-6">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="bg-white rounded-lg shadow border border-red-200 p-6">
                <div className="flex items-center text-red-700 mb-4">
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  <h2 className="text-lg font-semibold">Error Loading Maintenance Record</h2>
                </div>
                <p className="text-red-600 mb-4">{error || 'Maintenance record not found'}</p>
                <button
                  onClick={() => router.push('/maintenance')}
                  className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Back to Maintenance List
                </button>
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gray-50">
        <div className="py-6">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-6">
              <button
                onClick={() => router.push(`/maintenance/${maintenanceId}`)}
                className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Maintenance Details
              </button>
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Maintenance Images</h1>
                  <p className="mt-2 text-gray-600">
                    Terminal: {record.terminal_id} {record.terminal_name && `(${record.terminal_name})`}
                  </p>
                </div>
                <button
                  onClick={() => setShowUpload(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Upload Images
                </button>
              </div>
            </div>

            {/* Upload Section */}
            {showUpload && (
              <div className="bg-white rounded-lg shadow border p-6 mb-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload New Images</h2>
                <ImageUpload
                  maintenanceId={maintenanceId}
                  onSuccess={handleUploadSuccess}
                  onCancel={() => setShowUpload(false)}
                />
              </div>
            )}

            {/* Images Grid */}
            <div className="bg-white rounded-lg shadow border p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">
                  Images ({record.images.length})
                </h2>
              </div>

              {record.images.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <ImageIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium mb-2">No images uploaded</h3>
                  <p>Upload images to document this maintenance activity.</p>
                  <button
                    onClick={() => setShowUpload(true)}
                    className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <ImageIcon className="h-4 w-4 mr-2" />
                    Upload First Image
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {record.images.map((image) => (
                    <div key={getImageId(image)} className="group relative">
                      <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={getImageUrl(image)}
                          alt={image.filename}
                          className="w-full h-full object-cover cursor-pointer transition-transform group-hover:scale-105"
                          onClick={() => setSelectedImage(getImageUrl(image))}
                        />
                        
                        {/* Overlay with actions */}
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-opacity flex items-center justify-center">
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-2">
                            <button
                              onClick={() => setSelectedImage(getImageUrl(image))}
                              className="p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-colors"
                              title="View"
                            >
                              <Eye className="h-4 w-4 text-gray-700" />
                            </button>
                            <button
                              onClick={() => downloadImage(getImageUrl(image), image.filename)}
                              className="p-2 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-colors"
                              title="Download"
                            >
                              <Download className="h-4 w-4 text-gray-700" />
                            </button>
                            <button
                              onClick={() => handleImageDelete(getImageId(image))}
                              className="p-2 bg-red-500 bg-opacity-90 rounded-full hover:bg-opacity-100 transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4 text-white" />
                            </button>
                          </div>
                        </div>
                      </div>
                      
                      {/* Image info */}
                      <div className="mt-2">
                        <p className="text-sm font-medium text-gray-900 truncate" title={image.filename}>
                          {image.filename}
                        </p>
                        <div className="text-xs text-gray-500 space-y-1">
                          <p>{(image.file_size / 1024 / 1024).toFixed(2)} MB</p>
                          <p>{new Date(image.uploaded_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Image Preview Modal */}
            {selectedImage && (
              <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
                <div className="relative max-w-6xl max-h-[90vh] w-full mx-4">
                  <button
                    onClick={() => setSelectedImage(null)}
                    className="absolute top-4 right-4 text-white hover:text-gray-300 z-10"
                  >
                    <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
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
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
