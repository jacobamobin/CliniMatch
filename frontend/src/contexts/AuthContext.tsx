import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '@supabase/supabase-js';
import { supabase, getCurrentUser } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check URL for auth tokens
    console.log('🔗 Current URL:', window.location.href);
    if (window.location.hash.includes('access_token')) {
      console.log('🎫 Found auth token in URL');
    }
    
    // Get initial user
    getCurrentUser().then(({ user }) => {
      console.log('👤 Initial user check:', user?.email || 'None');
      setUser(user);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('🔐 Auth event:', event, 'User:', session?.user?.email || 'None');
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async () => {
    try {
      console.log('🚀 Starting Google OAuth...');
      console.log('🏠 Origin:', window.location.origin);
      console.log('🔄 Redirect will be to:', `${window.location.origin}/dashboard`);
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          scopes: 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid',
          redirectTo: `${window.location.origin}/dashboard`
        }
      });
      
      console.log('📤 OAuth response:', { data, error });
      
      if (error) {
        console.error('❌ Sign in error:', error);
        throw error;
      }
      
      if (data?.url) {
        console.log('🌐 Redirecting to Google at:', data.url);
      }
    } catch (error) {
      console.error('💥 Caught error:', error);
    }
  };

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  const value = {
    user,
    loading,
    signIn,
    signOut,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 