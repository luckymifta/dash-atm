'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useRef } from 'react';
import Cookies from 'js-cookie';
import { authApi, User, LoginRequest, RefreshSessionResponse } from '@/services/authApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  sessionExpiry: Date | null;
  showSessionWarning: boolean;
  diliTime: string | null;
  timeUntilMidnight: number | null;
  activeSessions: number;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  clearError: () => void;
  refreshSession: () => Promise<void>;
  dismissSessionWarning: () => void;
  revokeSession: (sessionToken: string) => Promise<void>;
  getUserSessions: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionExpiry, setSessionExpiry] = useState<Date | null>(null);
  const [showSessionWarning, setShowSessionWarning] = useState(false);
  const [diliTime, setDiliTime] = useState<string | null>(null);
  const [timeUntilMidnight, setTimeUntilMidnight] = useState<number | null>(null);
  const [activeSessions, setActiveSessions] = useState<number>(0);
  
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const warningTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const isAuthenticated = !!user && !!token;

  // Initialize auth state from cookies
  useEffect(() => {
    const savedToken = Cookies.get('auth_token');
    const savedUser = Cookies.get('auth_user');
    const savedExpiry = Cookies.get('session_expiry');

    if (savedToken && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(userData);
        
        if (savedExpiry) {
          setSessionExpiry(new Date(savedExpiry));
        }
      } catch (error) {
        console.error('Failed to parse user data from cookie:', error);
        // Clear corrupted cookies
        Cookies.remove('auth_token');
        Cookies.remove('auth_user');
        Cookies.remove('session_expiry');
      }
    }
    setIsLoading(false);
  }, []);

  // Session management utilities
  const clearSession = useCallback(() => {
    setToken(null);
    setUser(null);
    setSessionExpiry(null);
    setShowSessionWarning(false);
    Cookies.remove('auth_token');
    Cookies.remove('auth_user');
    Cookies.remove('session_expiry');
    
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
      warningTimeoutRef.current = null;
    }
  }, []);

  const refreshSession = useCallback(async () => {
    if (!token) return;

    try {
      const refreshResponse: RefreshSessionResponse = await authApi.refreshSession();
      
      // Update session info from API response
      setDiliTime(refreshResponse.dili_time);
      setTimeUntilMidnight(refreshResponse.time_until_midnight_seconds);
      
      console.log('Session refreshed:', refreshResponse.message);
      console.log('Dili time:', refreshResponse.dili_time);
      console.log('Time until midnight:', Math.floor(refreshResponse.time_until_midnight_seconds / 3600), 'hours');
      
      // Check if we should show session warning based on midnight proximity
      const hoursUntilMidnight = refreshResponse.time_until_midnight_seconds / 3600;
      if (hoursUntilMidnight <= 1 && !showSessionWarning) {
        setShowSessionWarning(true);
      }

      // Auto-logout if it's past midnight in Dili time
      if (refreshResponse.time_until_midnight_seconds <= 0) {
        console.log('Midnight auto-logout triggered for Dili timezone');
        clearSession();
        return;
      }

      setShowSessionWarning(false);
    } catch (error) {
      console.error('Session refresh failed:', error);
      // If refresh fails, logout user
      clearSession();
    }
  }, [token, clearSession, showSessionWarning]);

  const setupSessionExpiry = useCallback((expiresIn: number, rememberMe = false) => {
    const expiryTime = new Date(Date.now() + expiresIn * 1000);
    setSessionExpiry(expiryTime);
    
    // Save expiry to cookie for persistence
    Cookies.set('session_expiry', expiryTime.toISOString(), {
      expires: rememberMe ? 30 : 1, // 30 days if remember me, otherwise 1 day
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });

    // Clear existing timers
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
    }

    // Set up warning 5 minutes before expiry
    const warningTime = expiresIn - 5 * 60; // 5 minutes before expiry
    if (warningTime > 0) {
      warningTimeoutRef.current = setTimeout(() => {
        setShowSessionWarning(true);
      }, warningTime * 1000);
    }

    // Set up auto-refresh every 10 minutes for long sessions
    if (expiresIn > 20 * 60) { // Only for sessions longer than 20 minutes
      refreshIntervalRef.current = setInterval(() => {
        refreshSession();
      }, 10 * 60 * 1000); // Every 10 minutes
    }
  }, [refreshSession]);

  const dismissSessionWarning = useCallback(() => {
    setShowSessionWarning(false);
  }, []);

  // Monitor session expiry when user is authenticated
  useEffect(() => {
    if (!isAuthenticated || !sessionExpiry) return;

    const checkSessionExpiry = () => {
      const now = new Date();
      const timeUntilExpiry = sessionExpiry.getTime() - now.getTime();
      
      // If session has expired, logout
      if (timeUntilExpiry <= 0) {
        console.log('Session expired, logging out...');
        clearSession();
        return;
      }

      // If less than 5 minutes remaining, show warning
      if (timeUntilExpiry <= 5 * 60 * 1000 && !showSessionWarning) {
        setShowSessionWarning(true);
      }
    };

    // Check immediately
    checkSessionExpiry();

    // Check every minute
    const intervalId = setInterval(checkSessionExpiry, 60 * 1000);

    return () => clearInterval(intervalId);
  }, [isAuthenticated, sessionExpiry, showSessionWarning, clearSession]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
      if (warningTimeoutRef.current) {
        clearTimeout(warningTimeoutRef.current);
      }
    };
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // First, authenticate and get tokens
      const authResponse = await authApi.login(credentials);
      
      // Then, get user information using the access token
      const userInfo = await authApi.getCurrentUser(authResponse.access_token);
      
      // Save to state
      setToken(authResponse.access_token);
      setUser(userInfo);
      
      // Determine cookie expiry based on remember_me
      const cookieExpiry = authResponse.remember_me ? 30 : 1; // 30 days or 1 day
      
      // Save to cookies
      Cookies.set('auth_token', authResponse.access_token, { 
        expires: cookieExpiry,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict'
      });
      Cookies.set('auth_user', JSON.stringify(userInfo), { 
        expires: cookieExpiry,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict'
      });

      // Setup session expiry management
      setupSessionExpiry(authResponse.expires_in, authResponse.remember_me);
      
      // Get initial session count after state is set
      setTimeout(async () => {
        try {
          await getUserSessions();
          await refreshSession();
        } catch (error) {
          console.error('Failed to initialize session data:', error);
        }
      }, 100);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setError(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      if (token) {
        try {
          await authApi.logout(token);
        } catch (error) {
          // Even if logout API call fails, we should still clear local state
          console.error('Logout API call failed:', error);
        }
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear state and cookies using utility
      clearSession();
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const revokeSession = async (sessionToken: string) => {
    try {
      await authApi.revokeSession(sessionToken);
      // Refresh session count after revoking
      await getUserSessions();
    } catch (error) {
      console.error('Failed to revoke session:', error);
      throw error;
    }
  };

  const getUserSessions = async () => {
    if (!user?.id) return;
    
    try {
      const sessions = await authApi.getUserSessions(user.id);
      setActiveSessions(sessions.length);
    } catch (error) {
      console.error('Failed to get user sessions:', error);
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    sessionExpiry,
    showSessionWarning,
    diliTime,
    timeUntilMidnight,
    activeSessions,
    login,
    logout,
    error,
    clearError,
    refreshSession,
    dismissSessionWarning,
    revokeSession,
    getUserSessions,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
