'use client';

import React, { useState } from 'react';
import { 
  User, 
  Edit, 
  Trash2, 
  Key, 
  MoreVertical, 
  Shield, 
  ShieldCheck, 
  ShieldX,
  Clock,
  Calendar
} from 'lucide-react';
import { User as UserType } from '@/services/authApi';

interface UserTableProps {
  users: UserType[];
  onEdit: (user: UserType) => void;
  onDelete: (user: UserType) => void;
  onChangePassword: (user: UserType) => void;
  loading?: boolean;
}

export default function UserTable({ 
  users, 
  onEdit, 
  onDelete, 
  onChangePassword, 
  loading = false 
}: UserTableProps) {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const getRoleIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case 'super_admin':
        return <ShieldCheck className="h-4 w-4 text-red-500" />;
      case 'admin':
        return <Shield className="h-4 w-4 text-orange-500" />;
      case 'operator':
        return <ShieldX className="h-4 w-4 text-blue-500" />;
      default:
        return <User className="h-4 w-4 text-gray-500" />;
    }
  };

  const getRoleBadge = (role: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (role.toLowerCase()) {
      case 'super_admin':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'admin':
        return `${baseClasses} bg-orange-100 text-orange-800`;
      case 'operator':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4">
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Login
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users && users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 flex-shrink-0">
                      <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                        <User className="h-5 w-5 text-indigo-600" />
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {user.first_name} {user.last_name}
                      </div>
                      <div className="text-sm text-gray-500">
                        @{user.username} • {user.email}
                      </div>
                      {user.phone && (
                        <div className="text-xs text-gray-400">
                          {user.phone}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getRoleIcon(user.role)}
                    <span className={getRoleBadge(user.role)}>
                      {user.role.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-col space-y-1">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    {user.account_locked_until && new Date(user.account_locked_until) > new Date() && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        <Clock className="h-3 w-3 mr-1" />
                        Locked
                      </span>
                    )}
                    {user.failed_login_attempts > 0 && (
                      <span className="text-xs text-gray-500">
                        {user.failed_login_attempts} failed attempts
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {user.last_login_at ? (
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{formatDate(user.last_login_at)}</span>
                    </div>
                  ) : (
                    <span className="text-gray-400">Never</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(user.created_at)}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="relative">
                    <button
                      onClick={() => setOpenDropdown(openDropdown === user.id ? null : user.id)}
                      className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded"
                    >
                      <MoreVertical className="h-5 w-5" />
                    </button>
                    
                    {openDropdown === user.id && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                        <div className="py-1">
                          <button
                            onClick={() => {
                              onEdit(user);
                              setOpenDropdown(null);
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            Edit User
                          </button>
                          <button
                            onClick={() => {
                              onChangePassword(user);
                              setOpenDropdown(null);
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            <Key className="h-4 w-4 mr-2" />
                            Change Password
                          </button>
                          <button
                            onClick={() => {
                              onDelete(user);
                              setOpenDropdown(null);
                            }}
                            className="flex items-center w-full px-4 py-2 text-sm text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete User
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {(!users || users.length === 0) && (
        <div className="text-center py-12">
          <User className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new user.
          </p>
        </div>
      )}
    </div>
  );
}
