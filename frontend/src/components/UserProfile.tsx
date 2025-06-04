'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import SessionManagement from './SessionManagement';
import { User, Clock, Shield, Activity, Calendar } from 'lucide-react';

const UserProfile: React.FC = () => {
  const { user, sessionExpiry, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');

  if (!isAuthenticated || !user) {
    return (
      <div className="p-4 text-center text-gray-500">
        Please log in to view your profile.
      </div>
    );
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', { 
      timeZone: 'Asia/Dili',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }) + ' (Dili Time)';
  };

  const getTimeUntilExpiry = () => {
    if (!sessionExpiry) return 'Unknown';
    
    const now = new Date();
    const expiry = new Date(sessionExpiry);
    const timeDiff = expiry.getTime() - now.getTime();
    
    if (timeDiff <= 0) return 'Expired';
    
    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'super_admin':
        return 'bg-red-100 text-red-800';
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      case 'operator':
        return 'bg-blue-100 text-blue-800';
      case 'viewer':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'sessions', label: 'Active Sessions', icon: Activity },
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="p-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-xl font-semibold">
              {user.first_name.charAt(0)}{user.last_name.charAt(0)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {user.first_name} {user.last_name}
              </h1>
              <p className="text-gray-600">@{user.username}</p>
              <div className="flex items-center space-x-2 mt-2">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${getRoleBadgeColor(user.role)}`}
                >
                  {user.role.replace('_', ' ').toUpperCase()}
                </span>
                {user.is_active ? (
                  <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                    Active
                  </span>
                ) : (
                  <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                    Inactive
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'profile' && (
            <div className="space-y-6">
              {/* Session Status */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <Clock className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-medium text-blue-900">Current Session</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-blue-700">Time Remaining:</span>
                    <p className="text-blue-600">{getTimeUntilExpiry()}</p>
                  </div>
                  <div>
                    <span className="font-medium text-blue-700">Expires At:</span>
                    <p className="text-blue-600">
                      {sessionExpiry ? new Date(sessionExpiry).toLocaleString('en-US', { 
                        timeZone: 'Asia/Dili',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: false
                      }) + ' (Dili Time)' : 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <span className="font-medium text-blue-700">Auto-Logout:</span>
                    <p className="text-blue-600">Midnight Dili Time</p>
                  </div>
                </div>
              </div>

              {/* User Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
                    <User className="w-5 h-5" />
                    <span>Personal Information</span>
                  </h3>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Full Name</label>
                      <p className="text-gray-900">{user.first_name} {user.last_name}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Email</label>
                      <p className="text-gray-900">{user.email}</p>
                    </div>
                    
                    {user.phone && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Phone</label>
                        <p className="text-gray-900">{user.phone}</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
                    <Shield className="w-5 h-5" />
                    <span>Account Security</span>
                  </h3>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Username</label>
                      <p className="text-gray-900">{user.username}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Role</label>
                      <p className="text-gray-900">{user.role.replace('_', ' ')}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Failed Login Attempts</label>
                      <p className="text-gray-900">{user.failed_login_attempts}</p>
                    </div>
                    
                    {user.account_locked_until && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Account Locked Until</label>
                        <p className="text-red-600">{formatDateTime(user.account_locked_until)}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Account Activity */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center space-x-2">
                  <Calendar className="w-5 h-5" />
                  <span>Account Activity</span>
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700">Last Login</label>
                    <p className="text-gray-900">
                      {user.last_login_at ? formatDateTime(user.last_login_at) : 'Never'}
                    </p>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700">Password Changed</label>
                    <p className="text-gray-900">{formatDateTime(user.password_changed_at)}</p>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700">Account Created</label>
                    <p className="text-gray-900">{formatDateTime(user.created_at)}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sessions' && (
            <SessionManagement userId={user.id} />
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
