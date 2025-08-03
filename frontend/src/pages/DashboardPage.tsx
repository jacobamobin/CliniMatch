import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { getUserProfile, getSearchHistory } from '../lib/supabase';
import { FaHospitalAlt, FaMapMarkerAlt, FaClipboardList, FaMapMarkedAlt, FaSearch } from 'react-icons/fa';

interface UserProfile {
  id: string;
  email: string;
  name: string;
  age?: number;
  conditions?: string[];
  location?: string;
  created_at: string;
}

interface SearchHistory {
  id: string;
  search_type: string;
  search_query: string;
  results_count: number;
  created_at: string;
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [loading, setLoading] = useState(true);

  const renderIcon = (iconName: string, size: number = 28) => {
    const iconProps = { size };
    switch (iconName) {
      case 'hospital': return <FaHospitalAlt {...iconProps} />;
      case 'marker': return <FaMapMarkerAlt {...iconProps} />;
      case 'clipboard': return <FaClipboardList {...iconProps} />;
      case 'map': return <FaMapMarkedAlt {...iconProps} />;
      case 'search': return <FaSearch {...iconProps} />;
      default: return <FaSearch {...iconProps} />;
    }
  };

  const loadUserData = async () => {
    if (!user) return;
    
    try {
      const [profileResponse, historyResponse] = await Promise.all([
        getUserProfile(user.id),
        getSearchHistory(user.id)
      ]);
      
      setUserProfile(profileResponse?.data || null);
      setSearchHistory(historyResponse?.data || []);
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUserData();
  }, [user]);

  const quickActions = [
    {
      title: "Search by Condition",
      description: "Find trials for specific conditions",
      iconName: "hospital",
      link: "/search/condition",
      color: "from-blue-500 to-blue-600"
    },
    {
      title: "Search by Location",
      description: "Find trials near you",
      iconName: "marker",
      link: "/search/location",
      color: "from-green-500 to-green-600"
    },
    {
      title: "Browse All Trials",
      description: "Explore all available trials",
      iconName: "clipboard",
      link: "/search/browse",
      color: "from-purple-500 to-purple-600"
    },
    {
      title: "View Map",
      description: "Interactive trial locations",
      iconName: "map",
      link: "/map",
      color: "from-orange-500 to-orange-600"
    }
  ];

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="glass-card-dark p-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Please sign in</h2>
          <p className="text-blue-300">You need to be signed in to access your dashboard.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="glass-card-dark p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4"></div>
          <p className="text-blue-300">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-8"
        >
          {/* Welcome Header */}
          <div className="text-center">
            <h1 className="text-4xl font-bold text-white mb-4">
              Welcome back, {user.user_metadata?.name || user.email}!
            </h1>
            <p className="text-blue-300 text-lg">
              Your personalized clinical trial dashboard
            </p>
          </div>

          {/* Quick Actions */}
          <div className="glass-card-dark p-6">
            <h2 className="text-2xl font-bold text-white mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {quickActions.map((action, index) => (
                <Link key={index} to={action.link}>
                  <motion.div
                    className="glass-card-dark p-6 hover:border-blue-400/50 transition-colors cursor-pointer"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${action.color} flex items-center justify-center text-white text-2xl mb-4`}>
                      {renderIcon(action.iconName, 28)}
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {action.title}
                    </h3>
                    <p className="text-blue-300 text-sm">
                      {action.description}
                    </p>
                  </motion.div>
                </Link>
              ))}
            </div>
          </div>

          {/* User Profile Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="glass-card-dark p-6">
              <h2 className="text-2xl font-bold text-white mb-6">Your Profile</h2>
              {userProfile ? (
                <div className="space-y-4">
                  <div>
                    <span className="text-blue-300">Email: </span>
                    <span className="text-white">{userProfile.email}</span>
                  </div>
                  {userProfile.age && (
                    <div>
                      <span className="text-blue-300">Age: </span>
                      <span className="text-white">{userProfile.age}</span>
                    </div>
                  )}
                  {userProfile.location && (
                    <div>
                      <span className="text-blue-300">Location: </span>
                      <span className="text-white">{userProfile.location}</span>
                    </div>
                  )}
                  {userProfile.conditions && userProfile.conditions.length > 0 && (
                    <div>
                      <span className="text-blue-300">Conditions: </span>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {userProfile.conditions.map((condition, index) => (
                          <span key={index} className="bg-blue-600/20 text-blue-300 px-3 py-1 rounded-full text-sm">
                            {condition}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  <Link to="/profile">
                    <button className="glass-button mt-4">
                      Update Profile
                    </button>
                  </Link>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-blue-300 mb-4">Complete your profile to get personalized trial recommendations</p>
                  <Link to="/profile">
                    <button className="glass-button">
                      Create Profile
                    </button>
                  </Link>
                </div>
              )}
            </div>

            {/* Search History */}
            <div className="glass-card-dark p-6">
              <h2 className="text-2xl font-bold text-white mb-6">Recent Searches</h2>
              {searchHistory.length > 0 ? (
                <div className="space-y-4">
                  {searchHistory.slice(0, 5).map((search, index) => (
                    <div key={search.id} className="border-b border-blue-400/20 pb-4 last:border-b-0">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">{search.search_query}</p>
                          <p className="text-blue-300 text-sm capitalize">{search.search_type} search</p>
                        </div>
                        <div className="text-right">
                          <p className="text-blue-400 text-sm">{search.results_count} results</p>
                          <p className="text-blue-300 text-xs">
                            {new Date(search.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                  <Link to="/results">
                    <button className="glass-button w-full mt-4">
                      View All Searches
                    </button>
                  </Link>
                </div>
              ) : (
                <div className="glass-card-dark p-8 text-center">
                  <div className="text-4xl mb-4 flex justify-center text-blue-400">
                    {renderIcon('search', 32)}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">No searches yet</h3>
                  <p className="text-blue-300 mb-6">Start your first search to find clinical trials</p>
                  <Link to="/search/condition">
                    <button className="glass-button">
                      Start Searching
                    </button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default DashboardPage; 