import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_CONFIG } from '../config/api';
import { LoginRequest, LoginResponse, User } from '../types/index';

class AuthService {
  private baseURL = API_CONFIG.USER_API_URL;

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      console.log('Attempting login to:', `${this.baseURL}${API_CONFIG.ENDPOINTS.AUTH.LOGIN}`);
      
      const response = await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.AUTH.LOGIN}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      console.log('Login response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Login failed with error:', errorData);
        throw new Error(errorData.detail || 'Login failed');
      }

      const data: LoginResponse = await response.json();
      console.log('Login successful, received data:', data);
      
      // Store token first
      await AsyncStorage.setItem('access_token', data.access_token);
      
      // Create user data based on login credentials since API doesn't return user info
      const userData: User = {
        id: 'user_' + Date.now(), // Generate a simple ID
        username: credentials.username,
        email: credentials.username.includes('@') ? credentials.username : `${credentials.username}@company.com`,
        role: credentials.username === 'admin' ? 'admin' : 'viewer',
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      console.log('Storing user data:', userData);
      await AsyncStorage.setItem('user_data', JSON.stringify(userData));
      
      return {
        ...data,
        user: userData
      };
    } catch (error) {
      console.error('Login error:', error);
      // Provide more specific error messages
      if (error instanceof TypeError && error.message.includes('Network request failed')) {
        throw new Error('Cannot connect to server. Please check if the backend is running and your network connection.');
      }
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      const token = await this.getToken();
      if (token) {
        await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.AUTH.LOGOUT}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of API call result
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('user_data');
    }
  }

  async getToken(): Promise<string | null> {
    return await AsyncStorage.getItem('access_token');
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  async isAuthenticated(): Promise<boolean> {
    const token = await this.getToken();
    return token !== null;
  }

  async refreshToken(): Promise<string | null> {
    try {
      const token = await this.getToken();
      if (!token) return null;

      const response = await fetch(`${this.baseURL}${API_CONFIG.ENDPOINTS.AUTH.REFRESH}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        await AsyncStorage.setItem('access_token', data.access_token);
        return data.access_token;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
    }
    
    return null;
  }
}

export default new AuthService();
