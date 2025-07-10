'use client';

import React from 'react';
import { MaintenanceDetail } from '@/components/maintenance/MaintenanceDetail';
import DashboardLayout from '@/components/DashboardLayout';
import { ArrowLeft } from 'lucide-react';
import { useRouter, useParams } from 'next/navigation';

export default function MaintenanceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const maintenanceId = params.id as string;

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gray-50">
        <div className="py-6">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-6">
              <button
                onClick={() => router.back()}
                className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
              >
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Maintenance List
              </button>
            </div>
            
            <MaintenanceDetail maintenanceId={maintenanceId} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
