import { LucideIcon } from 'lucide-react';
import clsx from 'clsx';

interface ATMStatusCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  color: 'blue' | 'green' | 'yellow' | 'orange' | 'red' | 'gray';
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  onClick?: () => void;
}

const colorVariants = {
  blue: {
    bg: 'bg-blue-50',
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-600',
    textColor: 'text-blue-600',
  },
  green: {
    bg: 'bg-green-50',
    iconBg: 'bg-green-100',
    iconColor: 'text-green-600',
    textColor: 'text-green-600',
  },
  yellow: {
    bg: 'bg-yellow-50',
    iconBg: 'bg-yellow-100',
    iconColor: 'text-yellow-600',
    textColor: 'text-yellow-600',
  },
  orange: {
    bg: 'bg-orange-50',
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-600',
    textColor: 'text-orange-600',
  },
  red: {
    bg: 'bg-red-50',
    iconBg: 'bg-red-100',
    iconColor: 'text-red-600',
    textColor: 'text-red-600',
  },
  gray: {
    bg: 'bg-gray-50',
    iconBg: 'bg-gray-100',
    iconColor: 'text-gray-600',
    textColor: 'text-gray-600',
  },
};

export default function ATMStatusCard({ 
  title, 
  value, 
  icon: Icon, 
  color, 
  trend,
  onClick 
}: ATMStatusCardProps) {
  const colorClasses = colorVariants[color];

  return (
    <div 
      className={clsx(
        'rounded-lg border border-gray-200 p-6 shadow-sm transition-all duration-200',
        colorClasses.bg,
        onClick && 'cursor-pointer hover:shadow-lg hover:scale-[1.02]'
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
          {trend && (
            <div className="mt-2 flex items-center text-sm">
              <span className={clsx(
                'font-medium',
                trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
              )}>
                {trend.direction === 'up' ? '+' : '-'}{trend.value}%
              </span>
              <span className="ml-1 text-gray-500">from last hour</span>
            </div>
          )}
        </div>
        <div className={clsx(
          'rounded-full p-3',
          colorClasses.iconBg
        )}>
          <Icon className={clsx('h-8 w-8', colorClasses.iconColor)} />
        </div>
      </div>
    </div>
  );
}
