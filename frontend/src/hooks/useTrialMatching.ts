import { useState, useCallback } from 'react';
import { useTrial } from '../contexts/TrialContext';
import { apiClient, withRetry, formatUserProfile, validateApiResponse, ApiError } from '../utils/api';
import type { UserProfile, MatchingResult } from '../contexts/TrialContext';

interface UseTrialMatchingReturn {
  matchTrials: (profile: UserProfile, page?: number) => Promise<void>;
  loadMore: () => Promise<void>;
  isLoading: boolean;
  isLoadingMore: boolean;
  error: string | null;
  progress: number;
  retry: () => void;
  clearError: () => void;
  hasMore: boolean;
  currentPage: number;
}

export const useTrialMatching = (): UseTrialMatchingReturn => {
  const { setMatchingResults, setIsLoading, setError, userProfile, matchingResults } = useTrial();
  const [localLoading, setLocalLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [lastProfile, setLastProfile] = useState<UserProfile | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const clearError = useCallback(() => {
    setLocalError(null);
    setError(null);
  }, [setError]);

  const matchTrials = useCallback(async (profile: UserProfile, page: number = 1) => {
    const isFirstPage = page === 1;
    
    if (isFirstPage) {
      setLocalLoading(true);
      setCurrentPage(1);
    } else {
      setIsLoadingMore(true);
    }
    
    setLocalError(null);
    setProgress(0);
    setLastProfile(profile);

    try {
      // Update global loading state
      if (isFirstPage) {
        setIsLoading(true);
        setError(null);
      }

      // Format the profile for API
      const formattedProfile = { ...formatUserProfile(profile), page, limit: 20 };
      setProgress(10);

      // Make API call with retry logic
      const response = await withRetry(
        async () => {
          setProgress(30);
          const result = await apiClient.matchTrials(formattedProfile);
          setProgress(70);
          return result;
        },
        3, // max retries
        1000 // initial delay
      );

      // Validate response
      const data = validateApiResponse(response);
      setProgress(90);

      // Transform the data to match our frontend types
      const newMatches = data.matches || [];
      const totalFound = data.totalFound || 0;
      const pagination = data.pagination || {};
      
      const matchingResult: MatchingResult = {
        matches: isFirstPage 
          ? newMatches 
          : [...(matchingResults?.matches || []), ...newMatches],
        totalFound,
        processingTime: data.processingTime || 0,
        cached: data.cached || false,
        aiTranslationSuccessRate: data.aiTranslationSuccessRate || 0,
      };

      // Update pagination state
      setCurrentPage(page);
      setHasMore(pagination.has_next || false);

      // Update global state
      setMatchingResults(matchingResult);
      setProgress(100);

      // Small delay to show completion
      await new Promise(resolve => setTimeout(resolve, 500));

    } catch (error) {
      console.error('Trial matching error:', error);
      
      let errorMessage = 'Failed to find matching trials. Please try again.';
      
      if (error instanceof ApiError) {
        switch (error.status) {
          case 400:
            errorMessage = 'Invalid profile data. Please check your information and try again.';
            break;
          case 429:
            errorMessage = 'Too many requests. Please wait a moment and try again.';
            break;
          case 500:
            errorMessage = 'Server error. Please try again later.';
            break;
          default:
            errorMessage = error.message || errorMessage;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setLocalError(errorMessage);
      setError(errorMessage);
    } finally {
      if (isFirstPage) {
        setLocalLoading(false);
        setIsLoading(false);
      } else {
        setIsLoadingMore(false);
      }
      setProgress(0);
    }
  }, [setMatchingResults, setIsLoading, setError, matchingResults]);

  const loadMore = useCallback(async () => {
    if (lastProfile && hasMore && !isLoadingMore) {
      await matchTrials(lastProfile, currentPage + 1);
    }
  }, [lastProfile, hasMore, isLoadingMore, currentPage, matchTrials]);

  const retry = useCallback(() => {
    if (lastProfile) {
      matchTrials(lastProfile);
    }
  }, [lastProfile, matchTrials]);

  return {
    matchTrials,
    loadMore,
    isLoading: localLoading,
    isLoadingMore,
    error: localError,
    progress,
    retry,
    clearError,
    hasMore,
    currentPage,
  };
};

// Hook for getting individual trial details
export const useTrialDetails = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getTrialDetails = useCallback(async (nctId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await withRetry(
        () => apiClient.getTrialById(nctId),
        2,
        500
      );

      const data = validateApiResponse(response);
      return data;

    } catch (error) {
      console.error('Error fetching trial details:', error);
      
      let errorMessage = 'Failed to fetch trial details.';
      
      if (error instanceof ApiError) {
        if (error.status === 404) {
          errorMessage = 'Trial not found.';
        } else {
          errorMessage = error.message || errorMessage;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      setError(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    getTrialDetails,
    isLoading,
    error,
  };
};

// Hook for health check
export const useHealthCheck = () => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    setIsChecking(true);
    setError(null);

    try {
      const response = await apiClient.healthCheck();
      const isHealthyStatus = response.data?.status === 'healthy';
      setIsHealthy(isHealthyStatus);
      
      if (!isHealthyStatus) {
        setError('Service is not healthy');
      }
      
      return isHealthyStatus;
    } catch (error) {
      console.error('Health check error:', error);
      setIsHealthy(false);
      
      let errorMessage = 'Health check failed.';
      if (error instanceof ApiError) {
        errorMessage = error.message;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      return false;
    } finally {
      setIsChecking(false);
    }
  }, []);

  return {
    checkHealth,
    isHealthy,
    isChecking,
    error,
  };
}; 