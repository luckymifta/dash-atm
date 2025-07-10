'use client';

import React from 'react';
import { MaintenanceList } from '@/components/maintenance/MaintenanceList';
import DashboardLayout from '@/components/DashboardLayout';

export default function MaintenancePage() {
  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gray-50">
        <div className="py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <MaintenanceList />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
