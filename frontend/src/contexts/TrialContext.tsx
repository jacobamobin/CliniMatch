import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types
export interface UserProfile {
  age: number;
  conditions: string[];
  medications: string[];
  location: {
    city: string;
    state: string;
    country: string;
    zip_code?: string;
  };
  lifestyle: {
    smoking: boolean;
    drinking: 'never' | 'occasional' | 'regular';
  };
}

export interface TrialMatch {
  nctId: string;
  title: string;
  originalDescription: string;
  simplifiedDescription: string;
  locations: Array<{
    facility: string;
    city: string;
    state: string;
    country: string;
    zip_code?: string;
    coordinates?: [number, number];
  }>;
  eligibilityCriteria: string;
  eligibilitySimplified: string;
  compensation?: string;
  compensationExplanation?: string;
  timeCommitment: string;
  keyBenefits: string;
  contactInfo?: {
    name?: string;
    phone?: string;
    email?: string;
  };
  studyType: string;
  phase?: string;
  status: string;
  sponsor: string;
  conditions: string[];
  interventions: string[];
}

export interface MatchingResult {
  matches: TrialMatch[];
  totalFound: number;
  processingTime: number;
  cached: boolean;
  aiTranslationSuccessRate: number;
}

interface TrialContextType {
  userProfile: UserProfile | null;
  setUserProfile: (profile: UserProfile) => void;
  matchingResults: MatchingResult | null;
  setMatchingResults: (results: MatchingResult) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  clearResults: () => void;
  clearProfile: () => void;
}

const TrialContext = createContext<TrialContextType | undefined>(undefined);

export const useTrial = () => {
  const context = useContext(TrialContext);
  if (context === undefined) {
    throw new Error('useTrial must be used within a TrialProvider');
  }
  return context;
};

interface TrialProviderProps {
  children: ReactNode;
}

export const TrialProvider: React.FC<TrialProviderProps> = ({ children }) => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [matchingResults, setMatchingResults] = useState<MatchingResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load profile from localStorage on mount
  useEffect(() => {
    try {
      const savedProfile = localStorage.getItem('clinimatch-profile');
      if (savedProfile) {
        const parsedProfile = JSON.parse(savedProfile);
        setUserProfile(parsedProfile);
      }
    } catch (error) {
      console.warn('Failed to load profile from localStorage:', error);
    }
  }, []);

  // Enhanced setUserProfile that also saves to localStorage
  const setUserProfileWithStorage = (profile: UserProfile) => {
    setUserProfile(profile);
    try {
      localStorage.setItem('clinimatch-profile', JSON.stringify(profile));
    } catch (error) {
      console.warn('Failed to save profile to localStorage:', error);
    }
  };

  const clearResults = () => {
    setMatchingResults(null);
    setError(null);
  };

  // Clear profile from localStorage
  const clearProfile = () => {
    setUserProfile(null);
    try {
      localStorage.removeItem('clinimatch-profile');
    } catch (error) {
      console.warn('Failed to clear profile from localStorage:', error);
    }
  };

  const value = {
    userProfile,
    setUserProfile: setUserProfileWithStorage,
    matchingResults,
    setMatchingResults,
    isLoading,
    setIsLoading,
    error,
    setError,
    clearResults,
    clearProfile,
  };

  return (
    <TrialContext.Provider value={value}>
      {children}
    </TrialContext.Provider>
  );
}; 