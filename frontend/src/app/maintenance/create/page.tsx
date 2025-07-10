'use client';

import React from 'react';
import { MaintenanceForm } from '@/components/maintenance/MaintenanceForm';
import DashboardLayout from '@/components/DashboardLayout';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function CreateMaintenancePage() {
  const router = useRouter();

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-white">
        <div className="py-6">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-6">
              <button
                onClick={() => router.back()}
                className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Maintenance List
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Create Maintenance Record</h1>
              <p className="mt-2 text-gray-600">
                Create a new maintenance record for an ATM terminal.
              </p>
            </div>
            
            <MaintenanceForm />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
