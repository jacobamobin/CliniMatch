// API Configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:5001/api';

// Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  error_type?: string;
}

export interface ApiError {
  message: string;
  status: number;
  error_type?: string;
}

// API Client Class
class ApiClient {
  private baseURL: string;
  private defaultHeaders: HeadersInit;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new ApiError(
          data.message || `HTTP ${response.status}`,
          response.status,
          data.error_type
        );
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error',
        0
      );
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    return this.request('/health');
  }

  // Trial matching
  async matchTrials(userProfile: any): Promise<ApiResponse> {
    return this.request('/match', {
      method: 'POST',
      body: JSON.stringify(userProfile),
    });
  }

  // Get trial by ID
  async getTrialById(nctId: string): Promise<ApiResponse> {
    return this.request(`/trial/${nctId}`);
  }
}

// Custom Error Class
export class ApiError extends Error {
  public status: number;
  public error_type?: string;

  constructor(message: string, status: number, error_type?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.error_type = error_type;
  }
}

// Retry utility
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxRetries) {
        throw lastError;
      }

      // Don't retry on client errors (4xx)
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        throw error;
      }

      // Exponential backoff
      const waitTime = delay * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }

  throw lastError!;
}

// API instance
export const apiClient = new ApiClient();

// Utility functions
export const formatUserProfile = (profile: any) => {
  return {
    age: profile.age,
    conditions: profile.conditions.filter((c: string) => c.trim()),
    medications: profile.medications.filter((m: string) => m.trim()),
    location: {
      city: profile.location.city,
      state: profile.location.state,
      country: profile.location.country || 'United States',
      zip_code: profile.location.zip_code,
    },
    lifestyle: {
      smoking: profile.lifestyle.smoking,
      drinking: profile.lifestyle.drinking,
    },
  };
};

export const validateApiResponse = <T>(response: ApiResponse<T>): T => {
  if (!response.success) {
    throw new ApiError(
      response.message || 'API request failed',
      0,
      response.error_type
    );
  }
  
  if (!response.data) {
    throw new ApiError('No data received from API', 0);
  }
  
  return response.data;
};