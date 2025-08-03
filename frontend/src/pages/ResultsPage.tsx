import React from 'react';
import { motion } from 'framer-motion';
import { useTrial } from '../contexts/TrialContext';
import MatchCard from '../components/trials/MatchCard';
import { FaHospitalAlt, FaSearch } from 'react-icons/fa';

const ResultsPage: React.FC = () => {
  const { matchingResults, userProfile } = useTrial();

  const trials = matchingResults?.matches || [];

  if (trials.length === 0) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <motion.div
          className="glass-card-dark p-8 text-center max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="text-blue-400 mb-4 flex justify-center">
            <FaHospitalAlt size={48} />
          </div>
          <h2 className="text-2xl font-bold text-white mb-4">No Trials Found</h2>
          <p className="text-blue-300 mb-6">
            We couldn't find any clinical trials matching your criteria. Try updating your profile or search for different conditions.
          </p>
          <motion.button
            onClick={() => window.location.href = '/profile'}
            className="glass-button px-6 py-3 flex items-center gap-2 mx-auto"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaSearch className="w-4 h-4" />
            Update Profile
          </motion.button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <motion.div
        className="max-w-6xl mx-auto px-4 py-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <motion.div
          className="text-center mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl font-bold text-white mb-4">Clinical Trial Matches</h1>
          <p className="text-blue-300 text-lg">
            Found {trials.length} trial{trials.length !== 1 ? 's' : ''} that match your profile
          </p>
        </motion.div>

        {/* Results */}
        <div className="space-y-6">
          {trials.map((trial, index) => (
            <MatchCard
              key={trial.nctId || index}
              trial={trial}
              userState={userProfile?.location?.state}
            />
          ))}
        </div>

        {/* Footer Info */}
        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <p className="text-blue-400 text-sm">
            Trials are sorted by relevance and location proximity. Click "Learn More" to visit the official study page on ClinicalTrials.gov.
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default ResultsPage; 