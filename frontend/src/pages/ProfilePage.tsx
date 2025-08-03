import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTrial } from '../contexts/TrialContext';
import { useTrialMatching } from '../hooks/useTrialMatching';
import type { UserProfile } from '../contexts/TrialContext';
import { FaTimes, FaSave, FaInfoCircle } from 'react-icons/fa';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { userProfile, setUserProfile } = useTrial();
  const { matchTrials, isLoading: isMatching, error: matchingError } = useTrialMatching();
  
  const [formData, setFormData] = useState<Partial<UserProfile>>({
    age: 0,
    conditions: [''],
    medications: [''],
    location: {
      city: '',
      state: '',
      country: 'United States',
      zip_code: ''
    },
    lifestyle: {
      smoking: false,
      drinking: 'never'
    }
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load saved profile data on mount
  useEffect(() => {
    if (userProfile) {
      setFormData({
        age: userProfile.age,
        conditions: userProfile.conditions.length > 0 ? userProfile.conditions : [''],
        medications: userProfile.medications.length > 0 ? userProfile.medications : [''],
        location: userProfile.location,
        lifestyle: userProfile.lifestyle
      });
    }
  }, [userProfile]);

  // Validation functions
  const validateField = (name: string, value: any): string => {
    switch (name) {
      case 'age':
        if (!value || value < 1 || value > 120) {
          return 'Age must be between 1 and 120';
        }
        break;
      case 'city':
        if (!value || value.trim().length < 2) {
          return 'City is required and must be at least 2 characters';
        }
        break;
      case 'state':
        if (!value || value.trim().length < 2) {
          return 'State is required and must be at least 2 characters';
        }
        break;
      case 'conditions':
        if (!value || value.length === 0 || value.every((c: string) => !c.trim())) {
          return 'At least one medical condition is required';
        }
        break;
    }
    return '';
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleConditionChange = (index: number, value: string) => {
    const newConditions = [...(formData.conditions || [])];
    newConditions[index] = value;
    setFormData(prev => ({
      ...prev,
      conditions: newConditions
    }));
  };

  const addCondition = () => {
    setFormData(prev => ({
      ...prev,
      conditions: [...(prev.conditions || []), '']
    }));
  };

  const removeCondition = (index: number) => {
    const newConditions = (formData.conditions || []).filter((_, i) => i !== index);
    setFormData(prev => ({
      ...prev,
      conditions: newConditions
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Validate all fields
    const newErrors: Record<string, string> = {};
    
    newErrors.age = validateField('age', formData.age);
    newErrors.city = validateField('city', formData.location?.city);
    newErrors.state = validateField('state', formData.location?.state);
    newErrors.conditions = validateField('conditions', formData.conditions);

    setErrors(newErrors);

    // Check if there are any errors
    if (Object.values(newErrors).some(error => error)) {
      setIsSubmitting(false);
      return;
    }

    // Prepare the complete user profile
    const userProfile: UserProfile = {
      age: formData.age || 0,
      conditions: (formData.conditions || []).filter(c => c.trim()),
      medications: (formData.medications || []).filter(m => m.trim()),
      location: {
        city: formData.location?.city || '',
        state: formData.location?.state || '',
        country: formData.location?.country || 'United States',
        zip_code: formData.location?.zip_code
      },
      lifestyle: {
        smoking: formData.lifestyle?.smoking || false,
        drinking: formData.lifestyle?.drinking || 'never'
      }
    };

    try {
      // Save profile to context
      setUserProfile(userProfile);
      
      // Call the backend to find matching trials
      await matchTrials(userProfile);
      
      // Navigate to results page
      navigate('/results');
    } catch (error) {
      console.error('Failed to find trials:', error);
      // Error is handled by the useTrialMatching hook
    } finally {
      setIsSubmitting(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 }
  };

  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case 'times': return <FaTimes />;
      default: return <FaTimes />;
    }
  };

  return (
    <motion.div
      className="min-h-screen py-8 px-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div variants={itemVariants} className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            {userProfile ? 'Update Your Profile' : 'Create Your Profile'}
          </h1>
          <p className="text-blue-300 text-lg mb-4">
            Tell us about yourself to find the best clinical trials for you
          </p>
          
          {/* Profile Save Info */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center gap-2 text-sm text-blue-200/80 bg-blue-500/10 border border-blue-400/20 rounded-lg px-4 py-2 inline-flex"
          >
            <FaInfoCircle className="w-4 h-4" />
            <span>Your profile is automatically saved locally and securely stored</span>
          </motion.div>
        </motion.div>

        {/* Form */}
        <motion.form
          variants={itemVariants}
          onSubmit={handleSubmit}
          className="glass-card-dark p-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Basic Information */}
            <motion.div variants={itemVariants} className="space-y-6">
              <h2 className="text-2xl font-semibold text-white mb-4">Basic Information</h2>
              
              {/* Age */}
              <div>
                <label className="block text-white font-medium mb-2">
                  Age *
                </label>
                <input
                  type="number"
                  value={formData.age || ''}
                  onChange={(e) => handleInputChange('age', parseInt(e.target.value) || 0)}
                  className={`glass-input-dark w-full ${errors.age ? 'border-red-400' : ''}`}
                  placeholder="Enter your age"
                  min="1"
                  max="120"
                />
                {errors.age && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-sm mt-1"
                  >
                    {errors.age}
                  </motion.p>
                )}
              </div>

              {/* Location */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-white">Location</h3>
                
                <div>
                  <label className="block text-white font-medium mb-2">
                    City *
                  </label>
                  <input
                    type="text"
                    value={formData.location?.city || ''}
                    onChange={(e) => handleInputChange('location', { ...formData.location, city: e.target.value })}
                    className={`glass-input-dark w-full ${errors.city ? 'border-red-400' : ''}`}
                    placeholder="Enter your city"
                  />
                  {errors.city && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-400 text-sm mt-1"
                    >
                      {errors.city}
                    </motion.p>
                  )}
                </div>

                <div>
                  <label className="block text-white font-medium mb-2">
                    State *
                  </label>
                  <input
                    type="text"
                    value={formData.location?.state || ''}
                    onChange={(e) => handleInputChange('location', { ...formData.location, state: e.target.value })}
                    className={`glass-input-dark w-full ${errors.state ? 'border-red-400' : ''}`}
                    placeholder="Enter your state"
                  />
                  {errors.state && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-red-400 text-sm mt-1"
                    >
                      {errors.state}
                    </motion.p>
                  )}
                </div>

                <div>
                  <label className="block text-white font-medium mb-2">
                    ZIP Code
                  </label>
                  <input
                    type="text"
                    value={formData.location?.zip_code || ''}
                    onChange={(e) => handleInputChange('location', { ...formData.location, zip_code: e.target.value })}
                    className="glass-input-dark w-full"
                    placeholder="Enter your ZIP code (optional)"
                  />
                </div>
              </div>
            </motion.div>

            {/* Medical Information */}
            <motion.div variants={itemVariants} className="space-y-6">
              <h2 className="text-2xl font-semibold text-white mb-4">Medical Information</h2>
              
              {/* Medical Conditions */}
              <div>
                <label className="block text-white font-medium mb-2">
                  Medical Conditions *
                </label>
                <div className="space-y-2">
                  {(formData.conditions || ['']).map((condition, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex gap-2"
                    >
                      <input
                        type="text"
                        value={condition}
                        onChange={(e) => handleConditionChange(index, e.target.value)}
                        className="glass-input-dark flex-1"
                        placeholder="e.g., Diabetes, Hypertension"
                      />
                      {(formData.conditions || []).length > 1 && (
                        <motion.button
                          type="button"
                          onClick={() => removeCondition(index)}
                          className="glass-card-dark px-3 py-2 text-red-400 hover:text-red-300"
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          {renderIcon('times')}
                        </motion.button>
                      )}
                    </motion.div>
                  ))}
                  <motion.button
                    type="button"
                    onClick={addCondition}
                    className="glass-button text-sm px-4 py-2"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    + Add Condition
                  </motion.button>
                </div>
                {errors.conditions && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-sm mt-1"
                  >
                    {errors.conditions}
                  </motion.p>
                )}
              </div>

              {/* Medications */}
              <div>
                <label className="block text-white font-medium mb-2">
                  Current Medications
                </label>
                <input
                  type="text"
                  value={formData.medications?.join(', ') || ''}
                  onChange={(e) => handleInputChange('medications', e.target.value.split(',').map(m => m.trim()))}
                  className="glass-input-dark w-full"
                  placeholder="e.g., Metformin, Lisinopril (separate with commas)"
                />
              </div>

              {/* Lifestyle */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-white">Lifestyle</h3>
                
                <div className="flex items-center space-x-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.lifestyle?.smoking || false}
                      onChange={(e) => handleInputChange('lifestyle', { ...formData.lifestyle, smoking: e.target.checked })}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-white">Smoker</span>
                  </label>
                </div>

                <div>
                  <label className="block text-white font-medium mb-2">
                    Alcohol Consumption
                  </label>
                  <select
                    value={formData.lifestyle?.drinking || 'never'}
                    onChange={(e) => handleInputChange('lifestyle', { ...formData.lifestyle, drinking: e.target.value as any })}
                    className="glass-input-dark w-full"
                  >
                    <option value="never">Never</option>
                    <option value="occasional">Occasional</option>
                    <option value="regular">Regular</option>
                  </select>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Submit Button */}
          <motion.div
            variants={itemVariants}
            className="flex justify-center mt-8"
          >
            <motion.button
              type="submit"
              disabled={isSubmitting || isMatching}
              className="glass-button text-lg px-8 py-4 disabled:opacity-50 disabled:cursor-not-allowed"
              whileHover={{ scale: (isSubmitting || isMatching) ? 1 : 1.05 }}
              whileTap={{ scale: (isSubmitting || isMatching) ? 1 : 0.95 }}
            >
              {(isSubmitting || isMatching) ? 'Finding Trials...' : 'Find Matching Trials'}
            </motion.button>
          </motion.div>
        </motion.form>
      </div>
    </motion.div>
  );
};

export default ProfilePage; 