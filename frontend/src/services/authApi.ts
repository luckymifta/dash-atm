// Authentication API Service
// Integrates with User Management API on port 8001

import Cookies from 'js-cookie';

export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  remember_me?: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  is_active: boolean;
  password_changed_at: string;
  failed_login_attempts: number;
  account_locked_until?: string;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface UserSession {
  session_token: string;
  user_id: string;
  is_active: boolean;
  expires_at: string;
  created_at: string;
  last_accessed_at: string;
  remember_me: boolean;
  user_agent?: string;
  ip_address?: string;
}

export interface RefreshSessionResponse {
  message: string;
  time_until_midnight_seconds: number;
  time_until_token_expiry_seconds: number;
  dili_time: string;
  next_midnight_dili: string;
  should_warn_expiry: boolean;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: string;
  password: string;
  is_active: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  role?: string;
  is_active?: boolean;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface AuditLogEntry {
  id: string;
  user_id?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  old_values?: Record<string, unknown>;
  new_values?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  performed_by?: string;
  created_at: string;
}

export interface AuditLogResponse {
  audit_entries: AuditLogEntry[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

class AuthApiService {
  private baseUrl = 'http://localhost:8001';

  private getToken(): string {
    // Use js-cookie library to get the token (same as AuthContext)
    const token = Cookies.get('auth_token');
    console.log('Token from js-cookie:', token);
    
    if (token) {
      return token;
    }
    
    console.log('No authentication token found - user may not be logged in');
    throw new Error('Please login to access this feature');
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data: LoginResponse = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred during login');
    }
  }

  async logout(token: string): Promise<void> {
    try {
      // Call the backend logout endpoint to invalidate the session
      const response = await fetch(`${this.baseUrl}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Backend logout failed:', errorData.detail);
        // Even if backend logout fails, continue with client-side cleanup
      }
      
      console.log('Successfully logged out from backend');
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Even if logout API call fails, we should still clear local state
    }
  }

  async getCurrentUser(token?: string): Promise<User> {
    try {
      const authToken = token || this.getToken();
      // Decode JWT to get user ID (basic JWT decode without verification)
      const payload = JSON.parse(atob(authToken.split('.')[1]));
      const userId = payload.sub;
      
      const response = await fetch(`${this.baseUrl}/users/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch current user');
      }

      const userData = await response.json();
      return userData;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while fetching current user');
    }
  }

  async getUsers(params: {
    page?: number;
    limit?: number;
    search?: string;
    role?: string;
    status?: string;
  } = {}): Promise<{
    users: User[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
  }> {
    try {
      const token = this.getToken();
      const urlParams = new URLSearchParams({
        page: (params.page || 1).toString(),
        limit: (params.limit || 50).toString(),
      });
      
      if (params.search) urlParams.append('search', params.search);
      if (params.role) urlParams.append('role', params.role);
      if (params.status) urlParams.append('is_active', params.status === 'active' ? 'true' : 'false');

      const response = await fetch(`${this.baseUrl}/users?${urlParams}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch users');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while fetching users');
    }
  }

  async createUser(userData: CreateUserRequest): Promise<User> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create user');
      }

      const user: User = await response.json();
      return user;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while creating user');
    }
  }

  async updateUser(userId: string, userData: UpdateUserRequest): Promise<User> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update user');
      }

      const user: User = await response.json();
      return user;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while updating user');
    }
  }

  async deleteUser(userId: string): Promise<void> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete user');
      }
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while deleting user');
    }
  }

  async changePassword(userId: string, newPassword: string): Promise<void> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/users/${userId}/password`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_password: newPassword
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change password');
      }
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while changing password');
    }
  }

  // Session Management Methods
  async getUserSessions(userId: string): Promise<UserSession[]> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/users/${userId}/sessions`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get user sessions');
      }

      const data = await response.json();
      return data.sessions;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while fetching user sessions');
    }
  }

  async revokeSession(sessionToken: string): Promise<void> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/sessions/${sessionToken}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to revoke session');
      }
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while revoking session');
    }
  }

  async refreshSession(): Promise<RefreshSessionResponse> {
    try {
      const token = this.getToken();
      const response = await fetch(`${this.baseUrl}/auth/refresh-session`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to refresh session');
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred while refreshing session');
    }
  }
}

export const authApi = new AuthApiService();
export default authApi;
