import { API_CONFIG } from '@/config/api';
import Cookies from 'js-cookie';

// Types based on the PRD specifications and backend implementation
export enum MaintenanceTypeEnum {
  PREVENTIVE = 'PREVENTIVE',
  CORRECTIVE = 'CORRECTIVE',
  EMERGENCY = 'EMERGENCY',
  UPGRADE = 'UPGRADE'
}

export enum MaintenancePriorityEnum {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum MaintenanceStatusEnum {
  PLANNED = 'PLANNED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

export interface MaintenanceImage {
  image_id: string;
  filename: string;
  file_path: string;
  uploaded_at: string;
  file_size: number;
}

export interface MaintenanceCreate {
  terminal_id: string;
  start_datetime: string;
  end_datetime?: string;
  problem_description: string;
  solution_description?: string;
  maintenance_type: MaintenanceTypeEnum;
  priority: MaintenancePriorityEnum;
  status: MaintenanceStatusEnum;
}

export interface MaintenanceUpdate {
  start_datetime?: string;
  end_datetime?: string;
  problem_description?: string;
  solution_description?: string;
  maintenance_type?: MaintenanceTypeEnum;
  priority?: MaintenancePriorityEnum;
  status?: MaintenanceStatusEnum;
}

export interface MaintenanceRecord {
  id: string;
  terminal_id: string;
  terminal_name?: string;
  location?: string;
  start_datetime: string;
  end_datetime?: string;
  problem_description: string;
  solution_description?: string;
  maintenance_type: MaintenanceTypeEnum;
  priority: MaintenancePriorityEnum;
  status: MaintenanceStatusEnum;
  images: MaintenanceImage[];
  duration_hours?: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceListParams {
  page?: number;
  per_page?: number;
  terminal_id?: string;
  status?: MaintenanceStatusEnum;
  maintenance_type?: MaintenanceTypeEnum;
  priority?: MaintenancePriorityEnum;
  created_by?: string;
  start_date?: string;
  end_date?: string;
}

export interface MaintenanceListResponse {
  maintenance_records: MaintenanceRecord[];
  total_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
  filters_applied: Record<string, string | number | boolean>;
}

export interface ATMMaintenanceHistoryResponse {
  terminal_id: string;
  terminal_name?: string;
  location?: string;
  maintenance_records: MaintenanceRecord[];
  total_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface UploadImageResponse {
  message: string;
  uploaded_count: number;
  images: MaintenanceImage[];
}

// File upload configuration matching the backend
export const UPLOAD_CONFIG = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedExtensions: ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx'] as string[],
  maxFilesPerRecord: 10,
} as const;

// API endpoints for maintenance
const MAINTENANCE_ENDPOINTS = {
  LIST: '/v1/maintenance',
  CREATE: '/v1/maintenance',
  GET: (id: string) => `/v1/maintenance/${id}`,
  UPDATE: (id: string) => `/v1/maintenance/${id}`,
  DELETE: (id: string) => `/v1/maintenance/${id}`,
  ATM_HISTORY: (terminalId: string) => `/v1/atm/${terminalId}/maintenance`,
  UPLOAD_IMAGES: (id: string) => `/v1/maintenance/${id}/images`,
  DELETE_IMAGE: (id: string, imageId: string) => `/v1/maintenance/${id}/images/${imageId}`,
} as const;

// Helper function to build API URLs
function buildUrl(endpoint: string): string {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
}

// Helper function to get authorization headers
function getAuthHeaders(): HeadersInit {
  // Get the auth token from cookies (same as in AuthApiService)
  const token = Cookies.get('auth_token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

// Helper function to handle API errors
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// Maintenance API service class
export class MaintenanceApi {
  
  /**
   * List maintenance records with filtering and pagination
   */
  static async listMaintenanceRecords(params: MaintenanceListParams = {}): Promise<MaintenanceListResponse> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });
    
    const url = buildUrl(`${MAINTENANCE_ENDPOINTS.LIST}?${queryParams.toString()}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<MaintenanceListResponse>(response);
  }
  
  /**
   * Create a new maintenance record
   */
  static async createMaintenanceRecord(data: MaintenanceCreate): Promise<MaintenanceRecord> {
    const url = buildUrl(MAINTENANCE_ENDPOINTS.CREATE);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<MaintenanceRecord>(response);
  }
  
  /**
   * Get a specific maintenance record by ID
   */
  static async getMaintenanceRecord(id: string): Promise<MaintenanceRecord> {
    const url = buildUrl(MAINTENANCE_ENDPOINTS.GET(id));
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<MaintenanceRecord>(response);
  }
  
  /**
   * Update a maintenance record
   */
  static async updateMaintenanceRecord(id: string, data: MaintenanceUpdate): Promise<MaintenanceRecord> {
    const url = buildUrl(MAINTENANCE_ENDPOINTS.UPDATE(id));
    
    const response = await fetch(url, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<MaintenanceRecord>(response);
  }
  
  /**
   * Delete a maintenance record
   */
  static async deleteMaintenanceRecord(id: string): Promise<{ message: string }> {
    const url = buildUrl(MAINTENANCE_ENDPOINTS.DELETE(id));
    
    const response = await fetch(url, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<{ message: string }>(response);
  }
  
  /**
   * Get maintenance history for a specific ATM terminal
   */
  static async getATMMaintenanceHistory(
    terminalId: string, 
    page: number = 1, 
    perPage: number = 20
  ): Promise<ATMMaintenanceHistoryResponse> {
    const queryParams = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    
    const url = buildUrl(`${MAINTENANCE_ENDPOINTS.ATM_HISTORY(terminalId)}?${queryParams.toString()}`);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<ATMMaintenanceHistoryResponse>(response);
  }
  
  /**
   * Upload images to a maintenance record
   */
  static async uploadMaintenanceImages(id: string, files: File[]): Promise<UploadImageResponse> {
    const url = buildUrl(MAINTENANCE_ENDPOINTS.UPLOAD_IMAGES(id));
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    // Get the auth token for the Authorization header
    const token = Cookies.get('auth_token');
    const headers: HeadersInit = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Don't set Content-Type for FormData, let browser set it with boundary
    
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
      signal: AbortSignal.timeout(30000), // Longer timeout for file uploads
    });
    
    return handleApiResponse<UploadImageResponse>(response);
  }
  
  /**
   * Delete a specific image from a maintenance record
   */
  static async deleteMaintenanceImage(id: string, imageId: string): Promise<{ message: string }> {
    const url = buildUrl(MAINTENANCE_ENDPOINTS.DELETE_IMAGE(id, imageId));
    
    const response = await fetch(url, {
      method: 'DELETE',
      headers: getAuthHeaders(),
      signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
    });
    
    return handleApiResponse<{ message: string }>(response);
  }
}

// Utility functions for validation and formatting

/**
 * Validate file before upload
 */
export function validateFile(file: File): { valid: boolean; error?: string } {
  if (file.size > UPLOAD_CONFIG.maxFileSize) {
    return {
      valid: false,
      error: `File size exceeds ${UPLOAD_CONFIG.maxFileSize / (1024 * 1024)}MB limit`
    };
  }
  
  const extension = '.' + file.name.split('.').pop()?.toLowerCase();
  if (!UPLOAD_CONFIG.allowedExtensions.includes(extension)) {
    return {
      valid: false,
      error: `File type ${extension} not allowed. Allowed types: ${UPLOAD_CONFIG.allowedExtensions.join(', ')}`
    };
  }
  
  return { valid: true };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  // Handle invalid inputs
  if (typeof bytes !== 'number' || isNaN(bytes) || bytes < 0) {
    return 'Unknown size';
  }
  
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format duration hours for display
 */
export function formatDuration(hours?: number): string {
  if (!hours) return 'N/A';
  
  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes} min`;
  } else if (hours < 24) {
    return `${hours.toFixed(1)} hrs`;
  } else {
    const days = Math.floor(hours / 24);
    const remainingHours = Math.round(hours % 24);
    return `${days}d ${remainingHours}h`;
  }
}

/**
 * Get status color class for Tailwind CSS
 */
export function getStatusColor(status: MaintenanceStatusEnum): string {
  switch (status) {
    case MaintenanceStatusEnum.PLANNED:
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
    case MaintenanceStatusEnum.IN_PROGRESS:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
    case MaintenanceStatusEnum.COMPLETED:
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case MaintenanceStatusEnum.CANCELLED:
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  }
}

/**
 * Get priority color class for Tailwind CSS
 */
export function getPriorityColor(priority: MaintenancePriorityEnum): string {
  switch (priority) {
    case MaintenancePriorityEnum.LOW:
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case MaintenancePriorityEnum.MEDIUM:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
    case MaintenancePriorityEnum.HIGH:
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300';
    case MaintenancePriorityEnum.CRITICAL:
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  }
}
