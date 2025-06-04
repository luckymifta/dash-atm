'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';

const SessionWarning: React.FC = () => {
  const { showSessionWarning, dismissSessionWarning, refreshSession, logout } = useAuth();

  if (!showSessionWarning) return null;

  const handleExtendSession = async () => {
    try {
      await refreshSession();
      dismissSessionWarning();
    } catch (error) {
      console.error('Failed to extend session:', error);
      // If refresh fails, the context will handle logout
    }
  };

  const handleLogoutNow = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <div className="flex items-center mb-4">
          <div className="flex-shrink-0">
            <svg
              className="w-6 h-6 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-gray-900">
              Session Expiring Soon
            </h3>
          </div>
        </div>
        
        <div className="mb-6">
          <p className="text-sm text-gray-600">
            Your session will expire in less than 5 minutes due to inactivity. 
            Would you like to extend your session or log out now?
          </p>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleExtendSession}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Extend Session
          </button>
          
          <button
            onClick={handleLogoutNow}
            className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Logout Now
          </button>
        </div>

        <div className="mt-3">
          <button
            onClick={dismissSessionWarning}
            className="w-full text-sm text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            Dismiss (session will still expire)
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionWarning;
