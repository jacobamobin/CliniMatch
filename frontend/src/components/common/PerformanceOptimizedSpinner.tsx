import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface PerformanceOptimizedSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  showProgress?: boolean;
  progress?: number;
}

const PerformanceOptimizedSpinner: React.FC<PerformanceOptimizedSpinnerProps> = ({
  size = 'md',
  text = 'Loading...',
  showProgress = false,
  progress = 0,
}) => {
  const prefersReducedMotion = useReducedMotion();

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const spinnerVariants = {
    animate: {
      rotate: 360,
      transition: {
        duration: prefersReducedMotion ? 0 : 1,
        repeat: Infinity,
        ease: "linear" as const,
      },
    },
  };

  const progressVariants = {
    animate: {
      scaleX: progress / 100,
      transition: {
        duration: 0.3,
        ease: "easeOut" as const,
      },
    },
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      {/* Spinner */}
      <motion.div
        className={`relative ${sizeClasses[size]}`}
        variants={spinnerVariants}
        animate="animate"
        aria-label="Loading spinner"
      >
        <div className="absolute inset-0 rounded-full border-4 border-blue-400/20"></div>
        <motion.div
          className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-400"
          variants={spinnerVariants}
          animate="animate"
        />
      </motion.div>

      {/* Text */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-center"
      >
        <p className="text-white font-medium">{text}</p>
      </motion.div>

      {/* Progress Bar */}
      {showProgress && (
        <motion.div
          initial={{ opacity: 0, width: 0 }}
          animate={{ opacity: 1, width: 200 }}
          transition={{ delay: 0.3 }}
          className="w-48 bg-blue-400/20 rounded-full h-2 overflow-hidden"
        >
          <motion.div
            className="h-full bg-blue-400 rounded-full origin-left"
            variants={progressVariants}
            animate="animate"
          />
        </motion.div>
      )}

      {/* Progress Text */}
      {showProgress && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="text-blue-300 text-sm"
        >
          {progress}% complete
        </motion.p>
      )}
    </div>
  );
};

export default PerformanceOptimizedSpinner; 