'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';
import { authApi, UserSession } from '@/services/authApi';
import { useAuth } from '@/contexts/AuthContext';

interface SessionManagementProps {
  userId?: string;
}

const SessionManagement: React.FC<SessionManagementProps> = ({ userId }) => {
  const { 
    user, 
    diliTime, 
    timeUntilMidnight, 
    activeSessions, 
    revokeSession: authRevokeSession, 
    getUserSessions: authGetUserSessions,
    refreshSession 
  } = useAuth();
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetUserId = userId || user?.id;

  const fetchSessions = useCallback(async () => {
    if (!targetUserId) return;

    try {
      setLoading(true);
      setError(null);
      const userSessions = await authApi.getUserSessions(targetUserId);
      setSessions(userSessions);
      // Update the session count in auth context
      await authGetUserSessions();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch sessions';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [targetUserId, authGetUserSessions]);

  const handleRevokeSession = async (sessionToken: string) => {
    try {
      await authRevokeSession(sessionToken);
      // Refresh the sessions list
      await fetchSessions();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to revoke session';
      setError(errorMessage);
    }
  };

  const handleRefreshSession = async () => {
    try {
      setLoading(true);
      await refreshSession();
      await fetchSessions();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to refresh session';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [targetUserId, fetchSessions]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatTimeUntilMidnight = (seconds: number | null) => {
    if (seconds === null) return 'Unknown';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const getDeviceInfo = (userAgent?: string) => {
    if (!userAgent) return 'Unknown Device';
    
    // Simple device detection
    if (userAgent.includes('Mobile')) return 'Mobile Device';
    if (userAgent.includes('iPad')) return 'iPad';
    if (userAgent.includes('iPhone')) return 'iPhone';
    if (userAgent.includes('Android')) return 'Android Device';
    if (userAgent.includes('Windows')) return 'Windows PC';
    if (userAgent.includes('Mac')) return 'Mac';
    if (userAgent.includes('Linux')) return 'Linux PC';
    
    return 'Web Browser';
  };

  if (loading && sessions.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading sessions...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Session Status Bar */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium text-blue-800">Active Sessions:</span>{' '}
            <span className="text-blue-600">{activeSessions}</span>
          </div>
          <div>
            <span className="font-medium text-blue-800">Dili Time:</span>{' '}
            <span className="text-blue-600">{diliTime || 'Loading...'}</span>
          </div>
          <div>
            <span className="font-medium text-blue-800">Until Midnight:</span>{' '}
            <span className={`${timeUntilMidnight && timeUntilMidnight < 3600 ? 'text-red-600 font-semibold' : 'text-blue-600'}`}>
              {formatTimeUntilMidnight(timeUntilMidnight)}
            </span>
          </div>
        </div>
        {timeUntilMidnight && timeUntilMidnight < 3600 && (
          <div className="mt-2 text-sm text-red-600">
            ⚠️ Sessions will be automatically logged out at midnight Dili time for security.
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Session Management
        </h3>
        <div className="flex space-x-2">
          <button
            onClick={handleRefreshSession}
            disabled={loading}
            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh Session'}
          </button>
          <button
            onClick={fetchSessions}
            disabled={loading}
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Reload List'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No active sessions found.
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => {
            const isCurrentSession = session.session_token === Cookies.get('auth_token');
            const expiryDate = new Date(session.expires_at);
            const isExpiringSoon = expiryDate.getTime() - Date.now() < 24 * 60 * 60 * 1000; // 24 hours
            
            return (
              <div
                key={session.session_token}
                className={`bg-white border-2 rounded-lg p-4 shadow-sm transition-all ${
                  isCurrentSession 
                    ? 'border-blue-500 bg-blue-50' 
                    : isExpiringSoon 
                    ? 'border-orange-300 bg-orange-50' 
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      isCurrentSession ? 'bg-blue-500' : 'bg-green-400'
                    }`}></div>
                    <span className="font-medium text-gray-900">
                      {getDeviceInfo(session.user_agent)}
                    </span>
                    {isCurrentSession && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded font-semibold">
                        Current Session
                      </span>
                    )}
                    {session.remember_me && (
                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                        Remember Me
                      </span>
                    )}
                    {isExpiringSoon && !isCurrentSession && (
                      <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded">
                        Expiring Soon
                      </span>
                    )}
                  </div>
                  
                  {!isCurrentSession && (
                    <button
                      onClick={() => handleRevokeSession(session.session_token)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                    >
                      Revoke
                    </button>
                  )}
                  {isCurrentSession && (
                    <span className="px-3 py-1 text-sm bg-gray-100 text-gray-500 rounded cursor-not-allowed">
                      Current
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">IP Address:</span>{' '}
                    <span className="font-mono">{session.ip_address || 'Unknown'}</span>
                  </div>
                  <div>
                    <span className="font-medium">Created:</span>{' '}
                    {formatDate(session.created_at)}
                  </div>
                  <div>
                    <span className="font-medium">Last Accessed:</span>{' '}
                    {formatDate(session.last_accessed_at)}
                  </div>
                  <div>
                    <span className="font-medium">Expires:</span>{' '}
                    <span className={isExpiringSoon ? 'text-orange-600 font-semibold' : ''}>
                      {formatDate(session.expires_at)}
                    </span>
                  </div>
                </div>

                {session.user_agent && (
                  <div className="mt-3 text-xs text-gray-500">
                    <span className="font-medium">User Agent:</span>{' '}
                    <span className="break-all font-mono">{session.user_agent}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Session Security Information</h4>
        <div className="text-sm text-gray-600 space-y-2">
          <p>
            <strong>Automatic Logout:</strong> All sessions are automatically logged out at midnight Dili time (UTC+9) for enhanced security.
          </p>
          <p>
            <strong>Remember Me:</strong> Sessions with &quot;Remember Me&quot; enabled have extended validity (30 days) but are still subject to the midnight logout rule.
          </p>
          <p>
            <strong>Session Management:</strong> You can revoke any session except your current one. Revoking a session will immediately log out that device.
          </p>
          <p className="text-xs text-gray-500 mt-3">
            Current session is highlighted in blue. Sessions expiring within 24 hours are highlighted in orange.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SessionManagement;
