'use client';

import React, { useState, useCallback } from 'react';
import { MaintenanceApi, validateFile, formatFileSize } from '@/services/maintenanceApi';
import { 
  Upload, 
  X, 
  CheckCircle, 
  AlertCircle, 
  File,
  Image as ImageIcon,
  XCircle
} from 'lucide-react';

interface ImageUploadProps {
  maintenanceId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

interface FileWithPreview extends File {
  preview?: string;
  id: string;
  error?: string;
}

export function ImageUpload({ maintenanceId, onSuccess, onCancel }: ImageUploadProps) {
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const MAX_FILES = 5;

  const handleFiles = useCallback((fileList: FileList | File[]) => {
    const newFiles: FileWithPreview[] = [];
    const fileArray = Array.from(fileList);

    if (files.length + fileArray.length > MAX_FILES) {
      setError(`Maximum ${MAX_FILES} files allowed`);
      return;
    }

    fileArray.forEach((file, index) => {
      const validation = validateFile(file);
      const fileWithPreview: FileWithPreview = Object.assign(file, {
        id: `${Date.now()}_${index}`,
        error: validation.valid ? undefined : validation.error
      });

      // Create preview for images
      if (file.type.startsWith('image/')) {
        fileWithPreview.preview = URL.createObjectURL(file);
      }

      newFiles.push(fileWithPreview);
    });

    setFiles(prev => [...prev, ...newFiles]);
    setError(null);
  }, [files.length]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const removeFile = (fileId: string) => {
    setFiles(prev => {
      const file = prev.find(f => f.id === fileId);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter(f => f.id !== fileId);
    });
  };

  const uploadFiles = async () => {
    const validFiles = files.filter(f => !f.error);
    if (validFiles.length === 0) {
      setError('No valid files to upload');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Use the original files directly
      const filesToUpload = validFiles as File[];

      await MaintenanceApi.uploadMaintenanceImages(maintenanceId, filesToUpload);
      
      // Clean up object URLs
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (file: FileWithPreview) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="h-8 w-8 text-blue-500" />;
    }
    return <File className="h-8 w-8 text-gray-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <div className="space-y-2">
          <p className="text-lg font-medium text-gray-900">
            Drop files here or click to browse
          </p>
          <p className="text-sm text-gray-500">
            Maximum {MAX_FILES} files, 10MB each. JPG, PNG, GIF, WebP formats supported.
          </p>
        </div>
        <input
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.gif,.webp"
          onChange={handleInputChange}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer focus-within:outline-none focus-within:ring-2 focus-within:ring-indigo-500"
        >
          Choose Files
        </label>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-gray-900">
            Selected Files ({files.length}/{MAX_FILES})
          </h3>
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.id}
                className={`flex items-center space-x-3 p-3 rounded-lg border ${
                  file.error ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50'
                }`}
              >
                {/* File Icon or Preview */}
                <div className="flex-shrink-0">
                  {file.preview ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={file.preview}
                      alt={file.name}
                      className="h-12 w-12 object-cover rounded"
                    />
                  ) : (
                    getFileIcon(file)
                  )}
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(file.size)}
                  </p>
                  {file.error && (
                    <p className="text-sm text-red-600 flex items-center">
                      <AlertCircle className="h-4 w-4 mr-1" />
                      {file.error}
                    </p>
                  )}
                </div>

                {/* Status */}
                <div className="flex-shrink-0">
                  {file.error ? (
                    <XCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeFile(file.id)}
                  className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600"
                  disabled={uploading}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-end space-x-3">
        <button
          onClick={onCancel}
          disabled={uploading}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={uploadFiles}
          disabled={uploading || files.length === 0 || files.every(f => f.error)}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {uploading ? 'Uploading...' : `Upload ${files.filter(f => !f.error).length} File${files.filter(f => !f.error).length !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
}
