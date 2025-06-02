'use client';

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { authApi } from '@/services/authApi';

interface DeleteConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: {
    id: string;
    username: string;
    email: string;
  } | null;
  onSuccess: () => void;
}

export default function DeleteConfirmationModal({
  isOpen,
  onClose,
  user,
  onSuccess
}: DeleteConfirmationModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      await authApi.deleteUser(user.id);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete user';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="bg-red-100 p-2 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Delete User</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          <div className="mb-6">
            <p className="text-gray-700 mb-3">
              Are you sure you want to delete this user? This action cannot be undone.
            </p>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="text-sm">
                <p><span className="font-medium">Username:</span> {user.username}</p>
                <p><span className="font-medium">Email:</span> {user.email}</p>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-6">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5 mr-2" />
              <div className="text-sm text-yellow-700">
                <p className="font-medium">Warning:</p>
                <ul className="mt-1 list-disc list-inside space-y-1">
                  <li>The user will be soft-deleted and marked as inactive</li>
                  <li>All active sessions will be terminated</li>
                  <li>User data will be retained for audit purposes</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDelete}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Deleting...' : 'Delete User'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
