import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';

const Header: React.FC = () => {
  const { user, signIn, signOut } = useAuth();
  const location = useLocation();

  // Different nav items based on auth status
  const getNavItems = () => {
    if (user) {
      return [
        { path: '/dashboard', label: 'Dashboard' },
        { path: '/profile', label: 'Profile' },
        { path: '/results', label: 'Results' },
        { path: '/map', label: 'Map' },
      ];
    } else {
      return [
        { path: '/', label: 'Home' },
      ];
    }
  };

  const navItems = getNavItems();

  return (
    <motion.header 
      className="sticky top-0 z-50 glass-dark border-b border-blue-400/20"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to={user ? "/dashboard" : "/"} className="flex items-center space-x-3">
            <motion.div
              className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span className="text-white font-bold text-lg">CM</span>
            </motion.div>
            <div>
              <h1 className="text-xl font-bold text-white">CliniMatch</h1>
              <p className="text-xs text-blue-300">Find Your Trials</p>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`relative px-3 py-2 text-sm font-medium transition-colors duration-200 ${
                  location.pathname === item.path
                    ? 'text-blue-400'
                    : 'text-white/70 hover:text-white'
                }`}
              >
                {item.label}
                {location.pathname === item.path && (
                  <motion.div
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400"
                    layoutId="activeTab"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
              </Link>
            ))}
          </nav>

          {/* Auth Button */}
          {user ? (
            <div className="flex items-center space-x-4">
              <span className="text-white/70 text-sm">
                Welcome, {user.email?.split('@')[0]}
              </span>
              <motion.button
                onClick={signOut}
                className="glass-button text-sm px-4 py-2"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Sign Out
              </motion.button>
            </div>
          ) : (
            <motion.button
              onClick={signIn}
              className="glass-button text-sm px-4 py-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Sign In
            </motion.button>
          )}
        </div>
      </div>
    </motion.header>
  );
};

export default Header; 