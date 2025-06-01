import DashboardLayout from '@/components/DashboardLayout';
import { Users, UserPlus, Settings } from 'lucide-react';

export default function UserManagementPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage users and permissions
            </p>
          </div>
        </div>

        {/* Coming Soon Card */}
        <div className="text-center py-12">
          <Users className="mx-auto h-16 w-16 text-gray-400" />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Coming Soon</h2>
          <p className="mt-2 text-gray-600">
            User Management features are being developed and will be available soon.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
