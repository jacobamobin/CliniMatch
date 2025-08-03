import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface DisclaimerModalProps {
  onAccept: () => void;
}

const DisclaimerModal: React.FC<DisclaimerModalProps> = ({ onAccept }) => {
  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        {/* Backdrop */}
        <motion.div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        />

        {/* Modal */}
        <motion.div
          className="relative glass-card-dark max-w-2xl w-full p-8 rounded-2xl shadow-2xl"
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          {/* Header */}
          <div className="text-center mb-6">
            <motion.div
              className="w-16 h-16 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-4"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <svg className="w-8 h-8 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </motion.div>
            <h2 className="text-2xl font-bold text-white mb-2">Important Disclaimer</h2>
            <p className="text-blue-300">Please read this information carefully</p>
          </div>

          {/* Content */}
          <div className="space-y-4 text-sm text-blue-100 leading-relaxed">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h3 className="font-semibold text-white mb-2">Medical Information Disclaimer</h3>
              <p>
                CliniMatch is designed to help you find clinical trials that may be relevant to your medical condition. 
                However, this tool is for informational purposes only and should not be considered as medical advice.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h3 className="font-semibold text-white mb-2">AI Translation Limitations</h3>
              <p>
                Our AI-powered translations are designed to make medical jargon more understandable, but they may not 
                capture all nuances. Always consult with healthcare professionals for medical decisions.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <h3 className="font-semibold text-white mb-2">Privacy & Data</h3>
              <p>
                Your profile information is used solely for trial matching and is not shared with third parties. 
                We use secure, encrypted connections to protect your data.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-blue-600/10 border border-blue-400/20 rounded-lg p-4"
            >
              <p className="text-blue-200 font-medium">
                <strong>Important:</strong> Always consult with your healthcare provider before participating in any clinical trial.
              </p>
            </motion.div>
          </div>

          {/* Actions */}
          <motion.div
            className="flex justify-center mt-8"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <motion.button
              onClick={onAccept}
              className="glass-button px-8 py-3 text-lg font-medium"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              I Understand & Continue
            </motion.button>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default DisclaimerModal; 