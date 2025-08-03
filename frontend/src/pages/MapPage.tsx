import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useTrial } from '../contexts/TrialContext';
import { useTrialMatching } from '../hooks/useTrialMatching';
import type { TrialMatch, UserProfile } from '../contexts/TrialContext';
import { 
  FaHospitalAlt, FaMapMarkerAlt, FaPhone, FaEnvelope, FaExternalLinkAlt, 
  FaFilter, FaSearch, FaSpinner, FaEye, FaInfoCircle, FaUsers, FaClock,
  FaListAlt, FaGlobe, FaTimes, FaChevronDown
} from 'react-icons/fa';

// Fix for default markers in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Improved geocoding function
const geocodeLocation = async (city: string, state: string, country: string): Promise<[number, number] | null> => {
  try {
    const locationQuery = `${city}, ${state}, ${country}`;
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationQuery)}&limit=1&addressdetails=1`
    );
    const data = await response.json();
    if (data && data.length > 0) {
      return [parseFloat(data[0].lat), parseFloat(data[0].lon)];
    }
  } catch (error) {
    console.warn('Geocoding failed for:', { city, state, country }, error);
  }
  return null;
};

// Component to handle map center changes
const MapCenterHandler: React.FC<{ center: [number, number] }> = ({ center }) => {
  const map = useMap();
  
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  
  return null;
};

// Preset conditions for easy searching
const PRESET_CONDITIONS = [
  { label: 'Diabetes', value: 'Diabetes', icon: '🩺' },
  { label: 'Cancer', value: 'Cancer', icon: '🎗️' },
  { label: 'Heart Disease', value: 'Heart Disease', icon: '❤️' },
  { label: 'Alzheimer\'s', value: 'Alzheimer Disease', icon: '🧠' },
  { label: 'COVID-19', value: 'COVID-19', icon: '🦠' },
  { label: 'Depression', value: 'Depression', icon: '🧠' },
  { label: 'Hypertension', value: 'Hypertension', icon: '📈' },
  { label: 'Obesity', value: 'Obesity', icon: '⚖️' },
];

interface TrialWithCoordinates extends TrialMatch {
  coordinateLocations: Array<{
    facility: string;
    city: string;
    state: string;
    country: string;
    coordinates: [number, number];
    zip_code?: string;
  }>;
}

const MapPage: React.FC = () => {
  const { matchingResults } = useTrial();
  const { matchTrials, isLoading } = useTrialMatching();
  const [selectedCondition, setSelectedCondition] = useState<string>('');
  const [customCondition, setCustomCondition] = useState<string>('');
  const [selectedTrial, setSelectedTrial] = useState<TrialWithCoordinates | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([39.8283, -98.5795]); // Center of US
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [trialsWithCoords, setTrialsWithCoords] = useState<TrialWithCoordinates[]>([]);
  const [geocoding, setGeocoding] = useState(false);
  const [showTrialList, setShowTrialList] = useState(true);

  // Get trials from context
  const trials = useMemo(() => matchingResults?.matches || [], [matchingResults]);

  // Geocode all trial locations
  const geocodeTrials = useCallback(async (trialsToGeocode: TrialMatch[]) => {
    if (!trialsToGeocode.length) return;
    
    setGeocoding(true);
    const geocodedTrials: TrialWithCoordinates[] = [];
    
    for (const trial of trialsToGeocode) {
      const coordinateLocations = [];
      
      for (const location of trial.locations) {
        const coords = await geocodeLocation(location.city, location.state, location.country);
        if (coords) {
          coordinateLocations.push({
            ...location,
            coordinates: coords
          });
        }
        // Add small delay to avoid overwhelming the geocoding service
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      if (coordinateLocations.length > 0) {
        geocodedTrials.push({
          ...trial,
          coordinateLocations
        });
      }
    }
    
    setTrialsWithCoords(geocodedTrials);
    setGeocoding(false);
    
    // Set map center to first trial location
    if (geocodedTrials.length > 0 && geocodedTrials[0].coordinateLocations.length > 0) {
      setMapCenter(geocodedTrials[0].coordinateLocations[0].coordinates);
    }
  }, []);

  // Effect to geocode trials when they change
  useEffect(() => {
    geocodeTrials(trials);
  }, [trials, geocodeTrials]);

  // Filter trials by status
  const filteredTrials = useMemo(() => {
    if (statusFilter === 'all') return trialsWithCoords;
    return trialsWithCoords.filter(trial => 
      trial.status.toLowerCase().includes(statusFilter.toLowerCase())
    );
  }, [trialsWithCoords, statusFilter]);

  // Search for trials by condition
  const handleConditionSearch = async (condition: string) => {
    if (!condition.trim()) return;

    // Create a minimal profile for searching with varied locations
    const locations = [
      { city: 'Los Angeles', state: 'CA' },
      { city: 'Chicago', state: 'IL' },
      { city: 'Houston', state: 'TX' },
      { city: 'Phoenix', state: 'AZ' },
      { city: 'Philadelphia', state: 'PA' },
      { city: 'Boston', state: 'MA' }
    ];
    
    const randomLocation = locations[Math.floor(Math.random() * locations.length)];
    
    const searchProfile: UserProfile = {
      age: 30, // Default age
      conditions: [condition],
      medications: [],
      location: {
        city: randomLocation.city,
        state: randomLocation.state,
        country: 'United States',
        zip_code: ''
      },
      lifestyle: {
        smoking: false,
        drinking: 'never'
      }
    };

    try {
      await matchTrials(searchProfile);
    } catch (error) {
      console.error('Failed to search trials:', error);
    }
  };

  // Handle preset condition selection
  const handlePresetSelect = (condition: string) => {
    setSelectedCondition(condition);
    setCustomCondition('');
    handleConditionSearch(condition);
  };

  // Handle custom condition search
  const handleCustomSearch = () => {
    if (customCondition.trim()) {
      setSelectedCondition('');
      handleConditionSearch(customCondition);
    }
  };

  // Custom marker icon with status colors
  const createCustomIcon = useCallback((status: string, isSelected: boolean = false) => {
    const getStatusColor = (trialStatus: string) => {
      switch (trialStatus.toLowerCase()) {
        case 'recruiting':
          return '#10B981'; // green
        case 'active, not recruiting':
          return '#3B82F6'; // blue
        case 'not yet recruiting':
          return '#F59E0B'; // yellow
        case 'completed':
          return '#6B7280'; // gray
        default:
          return '#8B5CF6'; // purple
      }
    };

    const color = getStatusColor(status);
    const size = isSelected ? 35 : 25;
    const strokeWidth = isSelected ? 4 : 2;
    
    return L.divIcon({
      html: `
        <div style="
          width: ${size}px; 
          height: ${size}px; 
          background: ${color}; 
          border: ${strokeWidth}px solid white;
          border-radius: 50%; 
          box-shadow: 0 2px 10px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: ${size * 0.5}px;
          font-weight: bold;
        ">
          🏥
        </div>
      `,
      className: 'custom-marker',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
  }, []);

  // Handle trial selection
  const handleTrialClick = useCallback((trial: TrialWithCoordinates) => {
    setSelectedTrial(trial);
    if (trial.coordinateLocations.length > 0) {
      setMapCenter(trial.coordinateLocations[0].coordinates);
    }
  }, []);

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-slate-800/50 border-b border-blue-400/20 p-6"
      >
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-4">Clinical Trials Map</h1>
          
          {/* Search Controls */}
          <div className="space-y-4">
            {/* Preset Conditions */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <FaListAlt className="w-4 h-4 text-blue-400" />
                Quick Search - Popular Conditions
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
                {PRESET_CONDITIONS.map((condition) => (
                  <motion.button
                    key={condition.value}
                    onClick={() => handlePresetSelect(condition.value)}
                    className={`glass-card-dark p-3 text-center hover:bg-blue-500/20 transition-colors ${
                      selectedCondition === condition.value ? 'bg-blue-500/30 border-blue-400' : ''
                    }`}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className="text-2xl mb-1">{condition.icon}</div>
                    <div className="text-white text-xs font-medium">{condition.label}</div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Custom Search */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <FaSearch className="w-4 h-4 text-blue-400" />
                Custom Condition Search
              </h3>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={customCondition}
                  onChange={(e) => setCustomCondition(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleCustomSearch()}
                  placeholder="Enter any medical condition (e.g., Parkinson's Disease, Asthma)"
                  className="flex-1 bg-slate-800/50 border border-blue-400/30 rounded-lg px-4 py-3 text-white placeholder-blue-300/60 focus:border-blue-400 focus:outline-none"
                />
                <motion.button
                  onClick={handleCustomSearch}
                  disabled={!customCondition.trim() || isLoading}
                  className="glass-button px-6 py-3 disabled:opacity-50"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {isLoading ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaSearch className="w-4 h-4" />}
                </motion.button>
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <FaFilter className="w-4 h-4 text-blue-400" />
                <label className="text-white text-sm">Status Filter:</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-800/50 border border-blue-400/30 rounded px-3 py-1 text-white text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="recruiting">Recruiting</option>
                  <option value="active">Active</option>
                  <option value="not yet recruiting">Not Yet Recruiting</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
              
              <button
                onClick={() => setShowTrialList(!showTrialList)}
                className="glass-button text-sm px-4 py-2 flex items-center gap-2"
              >
                <FaListAlt className="w-3 h-3" />
                {showTrialList ? 'Hide' : 'Show'} Trial List
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex h-screen">
        {/* Sidebar */}
        <AnimatePresence>
          {showTrialList && (
            <motion.div
              initial={{ x: -400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -400, opacity: 0 }}
              className="w-96 bg-slate-800/30 border-r border-blue-400/20 p-4 overflow-y-auto"
            >
              <div className="sticky top-0 bg-slate-800/30 p-2 -mx-2 mb-4">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <FaGlobe className="w-5 h-5 text-blue-400" />
                  Available Trials ({filteredTrials.length})
                </h2>
                {geocoding && (
                  <div className="flex items-center gap-2 text-blue-300 text-sm mt-2">
                    <FaSpinner className="w-3 h-3 animate-spin" />
                    Mapping trial locations...
                  </div>
                )}
              </div>

              <div className="space-y-3">
                {filteredTrials.length === 0 && !isLoading && (
                  <div className="text-center py-8">
                    <FaHospitalAlt className="w-12 h-12 text-blue-400/50 mx-auto mb-4" />
                    <p className="text-blue-300 text-lg">No trials found</p>
                    <p className="text-blue-300/60 text-sm">Try searching for a medical condition above</p>
                  </div>
                )}

                {filteredTrials.map((trial, index) => (
                  <motion.div
                    key={trial.nctId}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    onClick={() => handleTrialClick(trial)}
                    className={`glass-card-dark p-4 cursor-pointer hover:bg-blue-500/10 transition-colors ${
                      selectedTrial?.nctId === trial.nctId ? 'border-blue-400 bg-blue-500/20' : ''
                    }`}
                  >
                    <h3 className="text-white font-semibold text-sm mb-2 line-clamp-2">
                      {trial.title}
                    </h3>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          trial.status.toLowerCase() === 'recruiting' 
                            ? 'bg-green-500/20 text-green-400'
                            : trial.status.toLowerCase().includes('active')
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {trial.status}
                        </span>
                        {trial.phase && (
                          <span className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400">
                            {trial.phase}
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 text-blue-300 text-xs">
                        <FaMapMarkerAlt className="w-3 h-3" />
                        <span>{trial.coordinateLocations.length} location{trial.coordinateLocations.length !== 1 ? 's' : ''}</span>
                      </div>
                      
                      <div className="text-blue-200/80 text-xs">
                        {trial.sponsor}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Map */}
        <div className="flex-1 relative">
          {geocoding && (
            <div className="absolute top-4 left-4 z-[1000] bg-slate-800/90 backdrop-blur-sm rounded-lg p-3 border border-blue-400/30">
              <div className="flex items-center gap-2 text-blue-300">
                <FaSpinner className="w-4 h-4 animate-spin" />
                <span className="text-sm">Mapping {trials.length} trials...</span>
              </div>
            </div>
          )}

          <MapContainer
            center={mapCenter}
            zoom={4}
            style={{ height: '100%', width: '100%' }}
            className="rounded-lg"
            scrollWheelZoom={true}
            zoomControl={true}
          >
            <MapCenterHandler center={mapCenter} />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Render markers for all trial locations */}
            {filteredTrials.map((trial) =>
              trial.coordinateLocations.map((location, locationIndex) => {
                const isSelected = selectedTrial?.nctId === trial.nctId;
                return (
                  <Marker
                    key={`${trial.nctId}-${locationIndex}`}
                    position={location.coordinates}
                    icon={createCustomIcon(trial.status, isSelected)}
                    eventHandlers={{
                      click: () => handleTrialClick(trial)
                    }}
                  >
                    <Popup className="custom-popup">
                      <div className="p-2 min-w-[300px]">
                        <h4 className="font-bold text-gray-800 mb-2 text-sm">
                          {trial.title}
                        </h4>
                        
                        <div className="space-y-2 text-xs">
                          <div className="flex items-center gap-1">
                            <FaHospitalAlt className="w-3 h-3 text-blue-600" />
                            <span className="font-medium">{location.facility}</span>
                          </div>
                          
                          <div className="flex items-center gap-1">
                            <FaMapMarkerAlt className="w-3 h-3 text-red-600" />
                            <span>{location.city}, {location.state} {location.zip_code}</span>
                          </div>
                          
                          <div className="flex gap-1">
                            <span className={`px-2 py-1 rounded text-xs ${
                              trial.status.toLowerCase() === 'recruiting' 
                                ? 'bg-green-100 text-green-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {trial.status}
                            </span>
                            {trial.phase && (
                              <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800">
                                {trial.phase}
                              </span>
                            )}
                          </div>
                          
                          <div className="pt-2 border-t border-gray-200 flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(`https://clinicaltrials.gov/study/${trial.nctId}`, '_blank');
                              }}
                              className="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                            >
                              <FaExternalLinkAlt className="w-2 h-2" />
                              View Details
                            </button>
                          </div>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                );
              })
            )}
          </MapContainer>
        </div>
      </div>

      {/* Selected Trial Details Modal */}
      <AnimatePresence>
        {selectedTrial && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[2000] flex items-center justify-center p-4"
            onClick={() => setSelectedTrial(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card-dark max-w-4xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">
                      {selectedTrial.title}
                    </h2>
                    <div className="flex gap-2 mb-2">
                      <span className={`px-3 py-1 rounded text-sm font-medium ${
                        selectedTrial.status.toLowerCase() === 'recruiting' 
                          ? 'bg-green-500/20 text-green-400 border border-green-400/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-400/30'
                      }`}>
                        {selectedTrial.status}
                      </span>
                      {selectedTrial.phase && (
                        <span className="px-3 py-1 rounded text-sm bg-purple-500/20 text-purple-400 border border-purple-400/30">
                          {selectedTrial.phase}
                        </span>
                      )}
                    </div>
                    <p className="text-blue-300">NCT ID: {selectedTrial.nctId}</p>
                  </div>
                  <button
                    onClick={() => setSelectedTrial(null)}
                    className="glass-button p-2"
                  >
                    <FaTimes className="w-4 h-4" />
                  </button>
                </div>

                {/* Content */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Trial Info */}
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Study Description</h3>
                      <p className="text-blue-200 text-sm leading-relaxed">
                        {selectedTrial.simplifiedDescription}
                      </p>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Sponsor</h3>
                      <p className="text-blue-300">{selectedTrial.sponsor}</p>
                    </div>

                    {selectedTrial.conditions.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-2">Conditions</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedTrial.conditions.map((condition, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs"
                            >
                              {condition}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Locations */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                      <FaMapMarkerAlt className="w-4 h-4 text-blue-400" />
                      All Study Locations ({selectedTrial.coordinateLocations.length})
                    </h3>
                    <div className="max-h-96 overflow-y-auto space-y-3">
                      {selectedTrial.coordinateLocations.map((location, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-800/50 p-4 rounded-lg border border-blue-400/10 hover:border-blue-400/30 transition-colors cursor-pointer"
                          onClick={() => setMapCenter(location.coordinates)}
                        >
                          <h4 className="font-medium text-white mb-1">{location.facility}</h4>
                          <div className="flex items-center gap-2 text-blue-200 text-sm mb-2">
                            <FaMapMarkerAlt className="w-3 h-3" />
                            <span>{location.city}, {location.state} {location.zip_code}</span>
                          </div>
                          <p className="text-blue-300/60 text-xs">Click to center map on this location</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3 mt-6 pt-6 border-t border-blue-400/20">
                  <motion.button
                    onClick={() => window.open(`https://clinicaltrials.gov/study/${selectedTrial.nctId}`, '_blank')}
                    className="glass-button px-4 py-2 flex items-center gap-2"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <FaExternalLinkAlt className="w-3 h-3" />
                    View Full Details
                  </motion.button>
                  
                  {selectedTrial.contactInfo?.phone && (
                    <motion.button
                      onClick={() => window.open(`tel:${selectedTrial.contactInfo?.phone}`, '_self')}
                      className="glass-button px-4 py-2 flex items-center gap-2"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <FaPhone className="w-3 h-3" />
                      Call Study
                    </motion.button>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MapPage; 