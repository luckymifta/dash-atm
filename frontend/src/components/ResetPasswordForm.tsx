'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useRouter, useSearchParams } from 'next/navigation';
import { Eye, EyeOff, AlertCircle, CheckCircle, ArrowLeft, Shield } from 'lucide-react';
import Image from 'next/image';
import { authApi } from '@/services/authApi';

interface ResetPasswordFormData {
  new_password: string;
  confirm_password: string;
}

interface TokenVerification {
  valid: boolean;
  username?: string;
  email?: string;
}

export default function ResetPasswordForm() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenData, setTokenData] = useState<TokenVerification | null>(null);
  const [isVerifyingToken, setIsVerifyingToken] = useState(true);
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ResetPasswordFormData>();

  const password = watch('new_password');

  // Verify token on component mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setError('No reset token provided. Please check your email link.');
        setIsVerifyingToken(false);
        return;
      }

      try {
        const data = await authApi.verifyResetToken(token);
        setTokenData(data);
      } catch (error) {
        console.error('Token verification error:', error);
        setError(error instanceof Error ? error.message : 'Failed to verify reset token. Please try again.');
      } finally {
        setIsVerifyingToken(false);
      }
    };

    verifyToken();
  }, [token]);

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) {
      setError('No reset token available.');
      return;
    }

    if (data.new_password !== data.confirm_password) {
      setError('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      await authApi.resetPassword(token, data.new_password);
      setIsSuccess(true);
    } catch (error) {
      console.error('Reset password error:', error);
      setError(error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackToLogin = () => {
    router.push('/auth/login');
  };

  // Loading state while verifying token
  if (isVerifyingToken) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying reset token...</p>
        </div>
      </div>
    );
  }

  // Success state
  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 via-blue-700 to-blue-800 relative overflow-hidden">
        {/* Floating decorative elements */}
        <div className="absolute top-32 left-20 w-16 h-16 bg-orange-500 rounded-lg transform rotate-12 opacity-80 animate-pulse"></div>
        <div className="absolute top-20 right-32 w-24 h-24 bg-orange-400 rounded-lg transform -rotate-12 opacity-70 animate-pulse" style={{ animationDelay: '1s' }}></div>
        
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
                Password Reset Successful
              </h1>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-green-800 mb-2">
                  Your password has been successfully updated for:
                </p>
                <p className="font-medium text-green-900">
                  {tokenData?.username}
                </p>
              </div>

              <div className="text-left bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-blue-900 mb-2">Security Notice:</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• All other sessions have been logged out</li>
                  <li>• Use your new password to login</li>
                  <li>• Store your password securely</li>
                  <li>• Contact support if you have any issues</li>
                </ul>
              </div>

              <button
                onClick={handleBackToLogin}
                className="w-full flex items-center justify-center space-x-2 py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Continue to Login</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state or main form
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
            <h1 className="text-2xl font-semibold text-gray-800 mb-2">
              Reset Your Password
            </h1>
            {tokenData && (
              <p className="text-sm text-gray-600">
                Setting new password for: <span className="font-medium">{tokenData.username}</span>
              </p>
            )}
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

          {/* Show form only if token is valid */}
          {tokenData && (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* New Password Field */}
              <div>
                <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
                  New Password
                </label>
                <div className="relative">
                  <input
                    {...register('new_password', {
                      required: 'New password is required',
                      minLength: {
                        value: 8,
                        message: 'Password must be at least 8 characters',
                      },
                      pattern: {
                        value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                        message: 'Password must contain uppercase, lowercase, and number',
                      },
                    })}
                    type={showPassword ? 'text' : 'password'}
                    id="new_password"
                    autoComplete="new-password"
                    className={`w-full px-4 py-3 bg-gray-50 border ${
                      errors.new_password ? 'border-red-300' : 'border-gray-200'
                    } rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400 pr-12`}
                    placeholder="Enter your new password"
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
                {errors.new_password && (
                  <p className="mt-1 text-sm text-red-600">{errors.new_password.message}</p>
                )}
              </div>

              {/* Confirm Password Field */}
              <div>
                <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm New Password
                </label>
                <div className="relative">
                  <input
                    {...register('confirm_password', {
                      required: 'Please confirm your password',
                      validate: (value) =>
                        value === password || 'Passwords do not match',
                    })}
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="confirm_password"
                    autoComplete="new-password"
                    className={`w-full px-4 py-3 bg-gray-50 border ${
                      errors.confirm_password ? 'border-red-300' : 'border-gray-200'
                    } rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400 pr-12`}
                    placeholder="Confirm your new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {errors.confirm_password && (
                  <p className="mt-1 text-sm text-red-600">{errors.confirm_password.message}</p>
                )}
              </div>

              {/* Password Requirements */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Shield className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Password Requirements</p>
                    <ul className="text-xs space-y-1">
                      <li>• At least 8 characters long</li>
                      <li>• Contains uppercase and lowercase letters</li>
                      <li>• Contains at least one number</li>
                      <li>• Use a unique password you have not used before</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Reset Password Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
              >
                {isSubmitting ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Updating Password...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Shield className="h-4 w-4" />
                    <span>Update Password</span>
                  </div>
                )}
              </button>
            </form>
          )}

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
