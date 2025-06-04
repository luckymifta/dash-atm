import clsx from 'clsx';

interface LoadingSkeletonProps {
  className?: string;
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full';
  animate?: boolean;
}

export function LoadingSkeleton({ 
  className = 'h-4 w-full', 
  rounded = 'md',
  animate = true 
}: LoadingSkeletonProps) {
  const roundedClasses = {
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    '3xl': 'rounded-3xl',
    full: 'rounded-full',
  };

  return (
    <div
      className={clsx(
        'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200',
        roundedClasses[rounded],
        animate && 'animate-pulse',
        className
      )}
    />
  );
}

export function ATMStatusCardSkeleton() {
  return (
    <div className="rounded-2xl border border-gray-200 p-6 shadow-sm bg-white">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-3">
          <LoadingSkeleton className="h-4 w-24" />
          <LoadingSkeleton className="h-8 w-16" />
          <div className="flex items-center space-x-2">
            <LoadingSkeleton className="h-6 w-12" rounded="full" />
            <LoadingSkeleton className="h-3 w-20" />
          </div>
        </div>
        <LoadingSkeleton className="h-16 w-16" rounded="2xl" />
      </div>
    </div>
  );
}

export function DashboardLoadingSkeleton() {
  return (
    <div className="space-y-8">
      {/* Header Skeleton */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="space-y-2">
          <LoadingSkeleton className="h-10 w-64" />
          <LoadingSkeleton className="h-6 w-96" />
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <LoadingSkeleton className="h-8 w-48" rounded="xl" />
          <LoadingSkeleton className="h-8 w-32" rounded="xl" />
          <LoadingSkeleton className="h-10 w-28" rounded="xl" />
        </div>
      </div>

      {/* Availability Summary Skeleton */}
      <div className="rounded-3xl bg-gradient-to-br from-gray-200 to-gray-300 p-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <LoadingSkeleton className="h-10 w-10" rounded="xl" />
              <LoadingSkeleton className="h-6 w-32" />
            </div>
            <LoadingSkeleton className="h-16 w-32" />
            <LoadingSkeleton className="h-5 w-48" />
            <LoadingSkeleton className="h-4 w-40" />
            <div className="flex flex-wrap gap-4 pt-2">
              {[1, 2, 3].map((i) => (
                <LoadingSkeleton key={i} className="h-16 w-24" rounded="xl" />
              ))}
            </div>
          </div>
          <LoadingSkeleton className="h-32 w-32" rounded="3xl" />
        </div>
      </div>

      {/* Status Cards Skeleton */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <LoadingSkeleton className="h-8 w-48" />
          <LoadingSkeleton className="h-6 w-24" rounded="full" />
        </div>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <ATMStatusCardSkeleton key={i} />
          ))}
        </div>
      </div>

      {/* Chart Skeleton */}
      <LoadingSkeleton className="h-96 w-full" rounded="2xl" />
    </div>
  );
}
