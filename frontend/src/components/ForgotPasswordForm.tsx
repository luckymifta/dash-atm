'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Mail, AlertCircle, CheckCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { authApi } from '@/services/authApi';

interface ForgotPasswordFormData {
  email: string;
}

export default function ForgotPasswordForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
  } = useForm<ForgotPasswordFormData>();

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);
      
      await authApi.forgotPassword(data.email);
      setIsSuccess(true);
    } catch (error) {
      console.error('Forgot password error:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackToLogin = () => {
    router.push('/auth/login');
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 relative overflow-hidden">
        {/* Floating decorative elements */}
        <div className="absolute top-32 left-20 w-16 h-16 bg-orange-500 rounded-lg transform rotate-12 opacity-80 animate-pulse"></div>
        <div className="absolute top-20 right-32 w-24 h-24 bg-orange-400 rounded-lg transform -rotate-12 opacity-70 animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-40 left-16 w-12 h-12 bg-orange-500 rounded-lg transform rotate-45 opacity-60 animate-pulse" style={{ animationDelay: '2s' }}></div>
        
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
            </div>

            {/* Success Message */}
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
              
              <h1 className="text-2xl font-semibold text-gray-800 mb-4">
                Check Your Email
              </h1>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-green-800 mb-2">
                  We&apos;ve sent password reset instructions to:
                </p>
                <p className="font-medium text-green-900">
                  {getValues('email')}
                </p>
              </div>

              <div className="text-left bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-blue-900 mb-2">Next Steps:</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Check your email inbox and spam folder</li>
                  <li>• Click the reset link in the email</li>
                  <li>• Link expires in 24 hours for security</li>
                  <li>• Contact support if you don&apos;t receive the email</li>
                </ul>
              </div>

              <div className="space-y-3">
                <button
                  onClick={handleBackToLogin}
                  className="w-full flex items-center justify-center space-x-2 py-3 px-4 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200"
                >
                  <ArrowLeft className="h-4 w-4" />
                  <span>Back to Login</span>
                </button>
                
                <button
                  onClick={() => {
                    setIsSuccess(false);
                    setError(null);
                  }}
                  className="w-full py-3 px-4 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Send Another Email
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 relative overflow-hidden">
      {/* Floating decorative elements */}
      <div className="absolute top-32 left-20 w-16 h-16 bg-orange-500 rounded-lg transform rotate-12 opacity-80 animate-pulse"></div>
      <div className="absolute top-20 right-32 w-24 h-24 bg-orange-400 rounded-lg transform -rotate-12 opacity-70 animate-pulse" style={{ animationDelay: '1s' }}></div>
      <div className="absolute bottom-40 left-16 w-12 h-12 bg-orange-500 rounded-lg transform rotate-45 opacity-60 animate-pulse" style={{ animationDelay: '2s' }}></div>
      <div className="absolute bottom-32 right-20 w-20 h-20 bg-orange-400 rounded-lg transform -rotate-45 opacity-50 animate-pulse" style={{ animationDelay: '3s' }}></div>
      
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
              Forgot Your Password?
            </h1>
            <p className="text-sm text-gray-600">
              Enter your account details to receive reset instructions
            </p>
          </div>

          {/* Back to Login */}
          <button
            onClick={handleBackToLogin}
            className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Login</span>
          </button>

          {/* Error Alert */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3 mb-6">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* Forgot Password Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <input
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Please enter a valid email address',
                    },
                  })}
                  type="email"
                  id="email"
                  autoComplete="email"
                  className={`w-full px-4 py-3 bg-gray-50 border ${
                    errors.email ? 'border-red-300' : 'border-gray-200'
                  } rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400 pl-12`}
                  placeholder="Enter your email address"
                />
                <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            {/* Security Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Security Information</p>
                  <ul className="text-xs space-y-1">
                    <li>• Reset link expires in 24 hours</li>
                    <li>• Only one reset per account at a time</li>
                    <li>• Email will be sent from dash@britimorleste.tl</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Send Reset Email Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {isSubmitting ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Sending Reset Email...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Mail className="h-4 w-4" />
                  <span>Send Reset Email</span>
                </div>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-xs text-gray-500">
              BRI ATM Dashboard Password Reset
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
