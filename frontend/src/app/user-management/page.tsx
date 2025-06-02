'use client';

import { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import ProtectedRoute from '@/components/ProtectedRoute';
import UserTable from '@/components/UserTable';
import UserForm from '@/components/UserForm';
import PasswordChangeModal from '@/components/PasswordChangeModal';
import DeleteConfirmationModal from '@/components/DeleteConfirmationModal';
import SearchAndFilters from '@/components/SearchAndFilters';
import Pagination from '@/components/Pagination';
import { Users, UserPlus, RefreshCw, AlertCircle } from 'lucide-react';
import { authApi, User, CreateUserRequest, UpdateUserRequest } from '@/services/authApi';
import { useAuth } from '@/contexts/AuthContext';

interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export default function UserManagementPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  
  // State management
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  
  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  
  // Modal state
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [passwordChangeUser, setPasswordChangeUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);

  // Fetch users function
  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params: Record<string, string | number> = {
        page: currentPage,
        limit: itemsPerPage
      };
      
      if (searchTerm) params.search = searchTerm;
      if (selectedRole) params.role = selectedRole;
      if (selectedStatus) params.status = selectedStatus;
      
      const response: UserListResponse = await authApi.getUsers(params);
      
      setUsers(response.users || []);
      setTotalItems(response.total || 0);
      setTotalPages(response.total_pages || 0);
    } catch (err: unknown) {
      console.error('Error fetching users:', err);
      console.log('Current cookies:', document.cookie);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch users';
      setError(`Authentication error: ${errorMessage}. Check console for details.`);
      setUsers([]); // Ensure users is always an array
      setTotalItems(0);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  }, [currentPage, itemsPerPage, searchTerm, selectedRole, selectedStatus]);

  // Effects
  useEffect(() => {
    // Only fetch users if authenticated, not loading auth state, and have a token
    if (isAuthenticated && !authLoading && token) {
      fetchUsers();
    } else if (!authLoading && !isAuthenticated) {
      // Clear any existing data when not authenticated
      setUsers([]);
      setError('Please login to view users');
      setLoading(false);
    }
  }, [fetchUsers, isAuthenticated, authLoading, token]);

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedRole, selectedStatus]);

  // Handlers
  const handleCreateUser = async (data: CreateUserRequest | UpdateUserRequest) => {
    if (editingUser) {
      // Update existing user
      await authApi.updateUser(editingUser.id, data as UpdateUserRequest);
      setEditingUser(null);
    } else {
      // Create new user
      await authApi.createUser(data as CreateUserRequest);
      setShowCreateForm(false);
    }
    await fetchUsers();
  };

  const handlePasswordChange = () => {
    setPasswordChangeUser(null);
    // Optionally refresh users to update last_password_change
    fetchUsers();
  };

  const handleDeleteUser = () => {
    setDeletingUser(null);
    fetchUsers();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleItemsPerPageChange = (newItemsPerPage: number) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedRole('');
    setSelectedStatus('');
  };

  const handleRefresh = () => {
    fetchUsers();
  };

  return (
    <ProtectedRoute requiredRole={['admin', 'super_admin']}>
      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage users, roles, and permissions
              </p>
            </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <UserPlus className="h-4 w-4" />
              <span>Add User</span>
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <SearchAndFilters
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          selectedRole={selectedRole}
          onRoleChange={setSelectedRole}
          selectedStatus={selectedStatus}
          onStatusChange={setSelectedStatus}
          onClearFilters={handleClearFilters}
        />

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
              <div className="text-red-700">
                <p className="font-medium">Error loading users</p>
                <p className="text-sm">{error}</p>
              </div>
              <button
                onClick={handleRefresh}
                className="ml-auto text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <UserTable
            users={users || []}
            loading={loading}
            onEdit={setEditingUser}
            onChangePassword={setPasswordChangeUser}
            onDelete={setDeletingUser}
          />
          
          {/* Pagination */}
          {!loading && users && users.length > 0 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={totalItems}
              itemsPerPage={itemsPerPage}
              onPageChange={handlePageChange}
              onItemsPerPageChange={handleItemsPerPageChange}
            />
          )}
        </div>

        {/* Empty State */}
        {!loading && users && users.length === 0 && !error && (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
            <Users className="mx-auto h-16 w-16 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No users found</h3>
            <p className="mt-2 text-gray-600">
              {searchTerm || selectedRole || selectedStatus
                ? 'Try adjusting your search or filter criteria.'
                : 'Get started by creating your first user.'}
            </p>
            {!searchTerm && !selectedRole && !selectedStatus && (
              <button
                onClick={() => setShowCreateForm(true)}
                className="mt-4 inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <UserPlus className="h-4 w-4" />
                <span>Add User</span>
              </button>
            )}
          </div>
        )}

        {/* Modals */}
        {showCreateForm && (
          <UserForm
            isOpen={showCreateForm}
            onClose={() => setShowCreateForm(false)}
            onSubmit={handleCreateUser}
          />
        )}

        {editingUser && (
          <UserForm
            user={editingUser}
            isOpen={!!editingUser}
            onClose={() => setEditingUser(null)}
            onSubmit={handleCreateUser}
          />
        )}

        {passwordChangeUser && (
          <PasswordChangeModal
            isOpen={!!passwordChangeUser}
            onClose={() => setPasswordChangeUser(null)}
            userId={passwordChangeUser.id}
            userName={passwordChangeUser.username}
            onSuccess={handlePasswordChange}
          />
        )}

        {deletingUser && (
          <DeleteConfirmationModal
            isOpen={!!deletingUser}
            onClose={() => setDeletingUser(null)}
            user={deletingUser}
            onSuccess={handleDeleteUser}
          />
        )}
      </div>
    </DashboardLayout>
    </ProtectedRoute>
  );
}
