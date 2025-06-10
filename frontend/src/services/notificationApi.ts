import { API_CONFIG } from '@/config/api';

export interface Notification {
  notification_id: string;
  terminal_id: string;
  previous_status?: string;
  current_status: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  title: string;
  message: string;
  created_at: string;
  is_read: boolean;
  metadata?: Record<string, unknown>;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total_count: number;
  unread_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface UnreadCountResponse {
  unread_count: number;
  timestamp: string;
}

export interface StatusCheckResponse {
  success: boolean;
  message: string;
  new_notifications_count: number;
  new_notifications: Array<{
    terminal_id: string;
    status_change: string;
    severity: string;
  }>;
  timestamp: string;
}

class NotificationApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  private async fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Get paginated list of notifications
   */
  async getNotifications(
    page: number = 1,
    perPage: number = 20,
    unreadOnly: boolean = false
  ): Promise<NotificationListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      unread_only: unreadOnly.toString(),
    });

    return this.fetchApi<NotificationListResponse>(`/v1/notifications?${params}`);
  }

  /**
   * Get count of unread notifications
   */
  async getUnreadCount(): Promise<UnreadCountResponse> {
    return this.fetchApi<UnreadCountResponse>('/v1/notifications/unread-count');
  }

  /**
   * Mark a specific notification as read
   */
  async markNotificationAsRead(notificationId: string): Promise<void> {
    await this.fetchApi(`/v1/notifications/${notificationId}/mark-read`, {
      method: 'POST',
    });
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsAsRead(): Promise<{ updated_count: number }> {
    return this.fetchApi<{ updated_count: number }>('/v1/notifications/mark-all-read', {
      method: 'POST',
    });
  }

  /**
   * Manually trigger status change check
   */
  async checkStatusChanges(): Promise<StatusCheckResponse> {
    return this.fetchApi<StatusCheckResponse>('/v1/notifications/check-changes', {
      method: 'POST',
    });
  }

  /**
   * Get severity color for UI styling
   */
  getSeverityColor(severity: string): string {
    switch (severity) {
      case 'CRITICAL':
        return 'text-red-600 bg-red-50';
      case 'ERROR':
        return 'text-red-500 bg-red-50';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50';
      case 'INFO':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  }

  /**
   * Get severity icon
   */
  getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'CRITICAL':
        return '🚨';
      case 'ERROR':
        return '❌';
      case 'WARNING':
        return '⚠️';
      case 'INFO':
        return 'ℹ️';
      default:
        return '📄';
    }
  }

  /**
   * Get ATM status redirect URL with filter
   */
  getAtmInformationUrl(status: string): string {
    return `/atm-information?status=${encodeURIComponent(status.toLowerCase())}`;
  }

  /**
   * Format relative time
   */
  formatRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
  }
}

export const notificationApiService = new NotificationApiService();
