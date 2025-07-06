'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  ChevronLeft, 
  ChevronRight, 
  ChevronDown,
  LayoutDashboard, 
  Landmark, 
  Users,
  LogOut,
  User,
  Shield,
  FileText,
  TrendingUp,
  ClipboardList,
  BarChart3,
  FolderOpen,
  Wrench
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/contexts/AuthContext';

interface SidebarProps {
  className?: string;
}

interface MenuSubItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

interface MenuItem {
  name: string;
  href?: string;
  icon: React.ElementType;
  roles?: string[];
  isDropdown?: boolean;
  subItems?: MenuSubItem[];
}

const menuItems: MenuItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'ATM Information',
    href: '/atm-information',
    icon: Landmark,
  },
  {
    name: 'ATM Maintenance',
    href: '/maintenance',
    icon: Wrench,
  },
  {
    name: 'Reports',
    icon: FolderOpen,
    isDropdown: true,
    subItems: [
      {
        name: 'Fault History Report',
        href: '/fault-history',
        icon: ClipboardList,
      },
      {
        name: 'ATM Status Report',
        href: '/atm-status-report',
        icon: BarChart3,
      },
    ],
  },
  {
    name: 'Predictive Analytics',
    href: '/predictive-analytics',
    icon: TrendingUp,
  },
  {
    name: 'User Management',
    href: '/user-management',
    icon: Users,
  },
  {
    name: 'Logs',
    href: '/logs',
    icon: FileText,
    roles: ['admin', 'super_admin'], // Only visible to admins
  },
];

export default function Sidebar({ className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [openDropdowns, setOpenDropdowns] = useState<Set<string>>(new Set());
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const toggleDropdown = (itemName: string) => {
    if (isCollapsed) return; // Don't allow dropdown when collapsed
    
    setOpenDropdowns(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemName)) {
        newSet.delete(itemName);
      } else {
        newSet.add(itemName);
      }
      return newSet;
    });
  };

  const isDropdownOpen = (itemName: string) => {
    return openDropdowns.has(itemName) && !isCollapsed;
  };

  // Check if any sub-item is active for dropdown highlighting
  const isDropdownActive = (subItems: MenuSubItem[] = []) => {
    return subItems.some(subItem => pathname === subItem.href);
  };

  const handleLogout = async () => {
    try {
      setIsLoggingOut(true);
      await logout();
      router.push('/auth/login');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'super_admin':
        return 'bg-red-100 text-red-800';
      case 'admin':
        return 'bg-blue-100 text-blue-800';
      case 'operator':
        return 'bg-green-100 text-green-800';
      case 'viewer':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      className={clsx(
        'relative bg-white border-r border-gray-200 text-gray-800 transition-all duration-300 ease-in-out flex flex-col shadow-sm',
        isCollapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200">
        {!isCollapsed && (
          <h1 className="text-xl font-bold text-gray-900">ATM Dashboard</h1>
        )}
        <button
          onClick={toggleSidebar}
          className="rounded-lg p-2 hover:bg-gray-100 transition-colors text-gray-600 hover:text-gray-900"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* User Info */}
      {user && !isCollapsed && (
        <div className="px-4 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user.first_name} {user.last_name}
              </p>
              <div className="flex items-center space-x-2 mt-1">
                <span className={clsx(
                  'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                  getRoleColor(user.role)
                )}>
                  <Shield className="h-3 w-3 mr-1" />
                  {user.role.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="mt-8 px-2 flex-1">
        <ul className="space-y-2">
          {menuItems.filter(item => 
            !item.roles || (user && item.roles.includes(user.role))
          ).map((item) => {
            if (item.isDropdown && item.subItems) {
              // Dropdown menu item
              const isActive = isDropdownActive(item.subItems);
              const isOpen = isDropdownOpen(item.name);
              const Icon = item.icon;

              return (
                <li key={item.name}>
                  <button
                    onClick={() => toggleDropdown(item.name)}
                    className={clsx(
                      'flex items-center w-full rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                      isCollapsed ? 'justify-center' : 'justify-between'
                    )}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <div className="flex items-center">
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      {!isCollapsed && (
                        <span className="ml-3 truncate">{item.name}</span>
                      )}
                    </div>
                    {!isCollapsed && (
                      <ChevronDown 
                        className={clsx(
                          'h-4 w-4 transition-transform',
                          isOpen ? 'rotate-180' : ''
                        )}
                      />
                    )}
                  </button>
                  
                  {/* Dropdown submenu */}
                  {isOpen && !isCollapsed && (
                    <ul className="mt-2 ml-6 space-y-1">
                      {item.subItems.map((subItem) => {
                        const isSubActive = pathname === subItem.href;
                        const SubIcon = subItem.icon;
                        
                        return (
                          <li key={subItem.href}>
                            <Link
                              href={subItem.href}
                              className={clsx(
                                'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                                isSubActive
                                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                              )}
                            >
                              <SubIcon className="h-4 w-4 flex-shrink-0" />
                              <span className="ml-3 truncate">{subItem.name}</span>
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </li>
              );
            } else {
              // Regular menu item
              const isActive = pathname === item.href;
              const Icon = item.icon;

              return (
                <li key={item.href || item.name}>
                  <Link
                    href={item.href!}
                    className={clsx(
                      'flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                      isCollapsed ? 'justify-center' : 'justify-start'
                    )}
                    title={isCollapsed ? item.name : undefined}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {!isCollapsed && (
                      <span className="ml-3 truncate">{item.name}</span>
                    )}
                  </Link>
                </li>
              );
            }
          })}
        </ul>
      </nav>

      {/* Logout Button */}
      <div className="p-4 border-t border-gray-200">
        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          className={clsx(
            'flex items-center w-full rounded-lg px-3 py-2 text-sm font-medium transition-colors',
            'text-gray-600 hover:bg-red-50 hover:text-red-700',
            isCollapsed ? 'justify-center' : 'justify-start',
            isLoggingOut && 'opacity-50 cursor-not-allowed'
          )}
          title={isCollapsed ? 'Logout' : undefined}
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          {!isCollapsed && (
            <span className="ml-3">
              {isLoggingOut ? 'Signing out...' : 'Sign out'}
            </span>
          )}
        </button>
      </div>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4">
          <div className="rounded-lg bg-gray-50 border border-gray-200 p-3">
            <p className="text-xs text-gray-600">
              ATM Dash System v2.0
            </p>
            {user && (
              <p className="text-xs text-gray-500 mt-1">
                Logged in as {user.username}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
