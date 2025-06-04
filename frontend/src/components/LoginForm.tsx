'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginRequest } from '@/services/authApi';
import Image from 'next/image';

interface LoginFormData {
  username: string;
  password: string;
  rememberMe: boolean;
}

export default function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, error, clearError } = useAuth();
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<LoginFormData>();

  const onSubmit = async (data: LoginFormData) => {
    try {
      setIsSubmitting(true);
      clearError();
      
      const credentials: LoginRequest = {
        username: data.username,
        password: data.password,
      };

      await login(credentials);
      
      // Reset form and redirect to dashboard
      reset();
      router.push('/dashboard');
      
    } catch (error) {
      // Error is already handled by the auth context
      console.error('Login failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 relative overflow-hidden">
      {/* Floating decorative elements */}
      <div className="absolute top-32 left-20 w-16 h-16 bg-orange-500 rounded-lg transform rotate-12 opacity-80 animate-pulse"></div>
      <div className="absolute top-20 right-32 w-24 h-24 bg-orange-400 rounded-lg transform -rotate-12 opacity-70 animate-pulse" style={{ animationDelay: '1s' }}></div>
      <div className="absolute bottom-40 left-16 w-12 h-12 bg-orange-500 rounded-lg transform rotate-45 opacity-60 animate-pulse" style={{ animationDelay: '2s' }}></div>
      <div className="absolute bottom-32 right-20 w-20 h-20 bg-orange-400 rounded-lg transform -rotate-45 opacity-50 animate-pulse" style={{ animationDelay: '3s' }}></div>
      <div className="absolute top-1/2 left-10 w-8 h-8 bg-orange-300 rounded-lg transform rotate-12 opacity-40 animate-pulse" style={{ animationDelay: '4s' }}></div>
      <div className="absolute top-1/3 right-16 w-14 h-14 bg-orange-500 rounded-lg transform -rotate-30 opacity-60 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
      
      {/* Main container */}
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md relative z-10 backdrop-blur-sm">
          {/* Logo Section */}
          <div className="text-center mb-8">
            <div className="mb-6">
              <Image
                src="/bri-logo.jpg"
                alt="BRI Global Financial"
                width={160}
                height={64}
                className="mx-auto"
                priority
              />
            </div>
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">
              Let&apos;s get you signed in
            </h1>
            <p className="text-sm text-gray-600">
              Secure ATM Dashboard Portal
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3 mb-6">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Email/Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                {...register('username', {
                  required: 'Username is required',
                  minLength: {
                    value: 3,
                    message: 'Please enter a valid username',
                  },
                })}
                type="text"
                id="username"
                autoComplete="username"
                className={`w-full px-4 py-3 bg-gray-50 border ${
                  errors.username ? 'border-red-300' : 'border-gray-200'
                } rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500`}
                placeholder="Enter your username"
                defaultValue="admin"
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                >
                  Forgot Password?
                </button>
              </div>
              <div className="relative">
                <input
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters',
                    },
                  })}
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  autoComplete="current-password"
                  className={`w-full px-4 py-3 bg-gray-50 border ${
                    errors.password ? 'border-red-300' : 'border-gray-200'
                  } rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-500 pr-12`}
                  placeholder="Enter your password"
                  defaultValue="admin123"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center">
              <input
                {...register('rememberMe')}
                id="rememberMe"
                type="checkbox"
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded transition-colors"
              />
              <label htmlFor="rememberMe" className="ml-2 block text-sm text-gray-700">
                Keep me logged in
              </label>
            </div>

            {/* Login Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {isSubmitting ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Signing in...</span>
                </div>
              ) : (
                'Login'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-xs text-gray-500">
              BRI ATM Dashboard Login Portal v2.0
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
