import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { TrialMatch } from '../../contexts/TrialContext';
import { 
  FaMapMarkerAlt, FaPhone, FaEnvelope, FaExternalLinkAlt, 
  FaClock, FaUsers, FaFlask, FaHospitalAlt, FaChevronDown, 
  FaChevronUp, FaMap, FaTimes, FaSpinner
} from 'react-icons/fa';

// Fix for default markers in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface TrialCardProps {
  trial: TrialMatch;
  userState?: string;
}

interface LocationWithCoords {
  facility: string;
  city: string;
  state: string;
  country: string;
  zip_code?: string;
  coordinates?: [number, number];
}

// Geocoding function using Google Geocoding API (reliable, fast)
const geocodeLocation = async (city: string, state: string, country: string, retryCount = 0): Promise<[number, number] | null> => {
  const maxRetries = 2;
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
  
  try {
    // Rate limiting - 50 requests per second allowed by Google
    await delay(100);
    
    const locationQuery = `${city}, ${state}, ${country}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    // Use Google Geocoding API
    const apiKey = process.env.REACT_APP_GOOGLE_GEOCODING_API_KEY;
    if (!apiKey) {
      console.error('Google Geocoding API key not found in environment variables');
      return null;
    }
    
    const response = await fetch(
      `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(locationQuery)}&key=${apiKey}`,
      { 
        signal: controller.signal,
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      }
    );
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    if (data.status === 'OK' && data.results && data.results.length > 0) {
      const result = data.results[0];
      if (result.geometry && result.geometry.location) {
        const { lat, lng } = result.geometry.location;
        console.log(`Geocoded: ${city}, ${state} -> ${lat}, ${lng}`);
        return [lat, lng];
      }
    } else if (data.status === 'OVER_QUERY_LIMIT') {
      console.warn(`Google API quota exceeded for: ${city}, ${state}`);
      throw new Error('API quota exceeded');
    } else if (data.status === 'ZERO_RESULTS') {
      console.warn(`No results found for: ${city}, ${state}`);
      return null;
    } else {
      console.warn(`Geocoding failed with status: ${data.status} for: ${city}, ${state}`);
      return null;
    }
    
    return null;
  } catch (error) {
    console.warn(`Geocoding attempt ${retryCount + 1} failed for: ${city}, ${state}`, error);
    
    if (retryCount < maxRetries) {
      const waitTime = 1000 * (retryCount + 1); // Linear backoff
      console.warn(`Geocoding retry ${retryCount + 1}/${maxRetries} for: ${city}, ${state} in ${waitTime}ms`);
      await delay(waitTime);
      return geocodeLocation(city, state, country, retryCount + 1);
    }
    
    console.error('Geocoding failed after all retries:', { city, state, country }, error);
    return null;
  }
};

// Mini Map Component
const TrialMiniMap: React.FC<{ locations: LocationWithCoords[]; trialTitle: string }> = ({ locations, trialTitle }) => {
  const [locationsWithCoords, setLocationsWithCoords] = useState<LocationWithCoords[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [mapCenter, setMapCenter] = useState<[number, number]>([39.8283, -98.5795]); // Center of US
  const [currentlyGeocoding, setCurrentlyGeocoding] = useState<string>('');
  const [geocodingProgress, setGeocodingProgress] = useState({ current: 0, total: 0 });

  const geocodeLocations = useCallback(async () => {
    if (!locations.length) return;
    
    setIsLoading(true);
    setGeocodingProgress({ current: 0, total: locations.length });
    const geocodedLocations: LocationWithCoords[] = [];
    
    for (let i = 0; i < locations.length; i++) {
      const location = locations[i];
      setCurrentlyGeocoding(`${location.city}, ${location.state}`);
      setGeocodingProgress({ current: i + 1, total: locations.length });
      
      const coords = await geocodeLocation(location.city, location.state, location.country);
      if (coords) {
        geocodedLocations.push({
          ...location,
          coordinates: coords
        });
      }
    }
    
    setLocationsWithCoords(geocodedLocations);
    setIsLoading(false);
    setCurrentlyGeocoding('');
    
    // Set map center to first location or average of all locations
    if (geocodedLocations.length > 0) {
      if (geocodedLocations.length === 1) {
        setMapCenter(geocodedLocations[0].coordinates!);
      } else {
        // Calculate center of all locations
        const avgLat = geocodedLocations.reduce((sum, loc) => sum + loc.coordinates![0], 0) / geocodedLocations.length;
        const avgLng = geocodedLocations.reduce((sum, loc) => sum + loc.coordinates![1], 0) / geocodedLocations.length;
        setMapCenter([avgLat, avgLng]);
      }
    }
  }, [locations]);

  useEffect(() => {
    geocodeLocations();
  }, [geocodeLocations]);

  // Custom marker icon
  const createCustomIcon = (isMultiple: boolean = false) => {
    const color = '#3B82F6';
    const size = isMultiple ? 30 : 25;
    
    return L.divIcon({
      html: `
        <div style="
          width: ${size}px; 
          height: ${size}px; 
          background: ${color}; 
          border: 3px solid white;
          border-radius: 50%; 
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: ${size * 0.4}px;
          font-weight: bold;
        ">
          🏥
        </div>
      `,
      className: 'custom-marker',
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
  };

  if (isLoading) {
    return (
      <div className="h-48 bg-slate-800/30 rounded-lg flex flex-col items-center justify-center border border-blue-400/20 p-4">
        <div className="flex items-center gap-2 text-blue-300 mb-3">
          <FaSpinner className="w-4 h-4 animate-spin" />
          <span className="text-sm">Mapping locations...</span>
        </div>
        
        <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
            style={{ width: `${(geocodingProgress.current / geocodingProgress.total) * 100}%` }}
          ></div>
        </div>
        
        <div className="text-xs text-blue-400 text-center">
          <div>Processing {geocodingProgress.current} of {geocodingProgress.total}</div>
          {currentlyGeocoding && (
            <div className="mt-1 text-blue-300">📍 {currentlyGeocoding}</div>
          )}
        </div>
      </div>
    );
  }

  if (locationsWithCoords.length === 0) {
    return (
      <div className="h-48 bg-slate-800/30 rounded-lg border border-blue-400/20 p-4">
        <div className="text-center text-blue-300 mb-4">
          <FaMapMarkerAlt className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Map unavailable - showing location list</p>
        </div>
        
        {/* Fallback: Show locations as a list */}
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {locations.map((location, idx) => (
            <div key={idx} className="bg-slate-700/50 p-2 rounded text-xs">
              <div className="font-medium text-white">{location.facility}</div>
              <div className="text-blue-300">{location.city}, {location.state}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="h-48 rounded-lg overflow-hidden border border-blue-400/30">
      <MapContainer
        center={mapCenter}
        zoom={locationsWithCoords.length === 1 ? 10 : 4}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
        attributionControl={false}
        scrollWheelZoom={false}
        dragging={true}
        doubleClickZoom={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {locationsWithCoords.map((location, index) => (
          <Marker
            key={index}
            position={location.coordinates!}
            icon={createCustomIcon(locationsWithCoords.length > 1)}
          >
            <Popup className="custom-popup">
              <div className="p-2">
                <h4 className="font-bold text-gray-800 text-sm mb-1">
                  {location.facility}
                </h4>
                <p className="text-gray-600 text-xs">
                  {location.city}, {location.state} {location.zip_code}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      
      {/* Show count of mapped vs total locations */}
      {locationsWithCoords.length < locations.length && (
        <div className="absolute bottom-2 right-2 bg-slate-800/90 text-xs text-blue-300 px-2 py-1 rounded">
          {locationsWithCoords.length}/{locations.length} mapped
        </div>
      )}
    </div>
  );
};

const MatchCard: React.FC<TrialCardProps> = ({ trial, userState }) => {
  const [expanded, setExpanded] = useState(false);
  const [sortedLocations, setSortedLocations] = useState<LocationWithCoords[]>([]);

  // Sort locations by user's state
  useEffect(() => {
    if (!trial.locations || trial.locations.length === 0) return;
    
    const sorted = [...trial.locations].sort((a, b) => {
      const aIsUserState = a.state?.toUpperCase() === userState?.toUpperCase();
      const bIsUserState = b.state?.toUpperCase() === userState?.toUpperCase();
      
      if (aIsUserState && !bIsUserState) return -1;
      if (!aIsUserState && bIsUserState) return 1;
      return 0;
    });
    
    setSortedLocations(sorted);
  }, [trial.locations, userState]);

  // Get the status color
  const getStatusColor = () => {
    switch (trial.status.toLowerCase()) {
      case 'recruiting':
        return 'bg-green-500/20 text-green-400 border-green-400/30';
      case 'active, not recruiting':
        return 'bg-blue-500/20 text-blue-400 border-blue-400/30';
      case 'not yet recruiting':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-400/30';
      case 'completed':
        return 'bg-gray-500/20 text-gray-400 border-gray-400/30';
      default:
        return 'bg-purple-500/20 text-purple-400 border-purple-400/30';
    }
  };

  // Get the phase color
  const getPhaseColor = () => {
    if (!trial.phase) return 'bg-slate-600/20 text-slate-400 border-slate-400/30';
    
    switch (trial.phase.toLowerCase()) {
      case 'phase 1':
      case 'phase1':
        return 'bg-red-500/20 text-red-400 border-red-400/30';
      case 'phase 2':
      case 'phase2':
        return 'bg-orange-500/20 text-orange-400 border-orange-400/30';
      case 'phase 3':
      case 'phase3':
        return 'bg-green-500/20 text-green-400 border-green-400/30';
      case 'phase 4':
      case 'phase4':
        return 'bg-blue-500/20 text-blue-400 border-blue-400/30';
      default:
        return 'bg-purple-500/20 text-purple-400 border-purple-400/30';
    }
  };

  // Get primary location (preferably in user's state)
  const primaryLocation = sortedLocations[0];

  const handleLearnMore = () => {
    if (trial.nctId) {
      window.open(`https://clinicaltrials.gov/study/${trial.nctId}`, '_blank');
    }
  };

  const handleContactStudy = () => {
    if (trial.contactInfo?.phone) {
      window.open(`tel:${trial.contactInfo.phone}`, '_self');
    } else if (trial.contactInfo?.email) {
      window.open(`mailto:${trial.contactInfo.email}`, '_self');
    } else {
      handleLearnMore();
    }
  };

  return (
    <motion.div
      className="glass-card-dark p-6 hover:bg-blue-500/5 transition-all duration-300"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      layout
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 pr-4">
          <h3 className="text-lg font-semibold text-white mb-2 leading-tight">
            {trial.title}
          </h3>
          
          <div className="flex flex-wrap gap-2 mb-2">
            <span className={`px-3 py-1 rounded text-sm font-medium border ${getStatusColor()}`}>
              {trial.status}
            </span>
            {trial.phase && (
              <span className={`px-3 py-1 rounded text-sm font-medium border ${getPhaseColor()}`}>
                {trial.phase}
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="glass-button p-2 ml-2"
        >
          {expanded ? <FaChevronUp className="w-4 h-4" /> : <FaChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Description */}
      <p className="text-blue-200 text-sm leading-relaxed mb-4">
        {trial.simplifiedDescription}
      </p>

      {/* Primary Location */}
      {primaryLocation && (
        <div className="flex items-center gap-2 text-blue-300 text-sm mb-3">
          <FaMapMarkerAlt className="w-4 h-4 text-blue-400" />
          <span>{primaryLocation.facility}</span>
          <span className="text-blue-400">•</span>
          <span>{primaryLocation.city}, {primaryLocation.state}</span>
          {trial.locations.length > 1 && (
            <span className="text-blue-400">+{trial.locations.length - 1} more</span>
          )}
        </div>
      )}

      {/* Sponsor */}
      <div className="text-blue-300/80 text-sm mb-4">
        <span className="font-medium">Sponsor:</span> {trial.sponsor}
      </div>

      {/* Time Commitment */}
      {trial.timeCommitment && trial.timeCommitment !== "Not specified" && 
       !trial.timeCommitment.includes("Time commitment information not available") && (
        <div className="flex items-start gap-2 p-3 bg-blue-500/10 border border-blue-400/20 rounded-lg mb-4">
          <FaClock className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <div>
            <span className="text-blue-300 text-sm font-medium">Time Commitment:</span>
            <p className="text-blue-200 text-sm mt-1">{trial.timeCommitment}</p>
          </div>
        </div>
      )}

      {/* Compensation */}
      {trial.compensation && (
        <div className="p-3 bg-green-500/10 border border-green-400/20 rounded-lg mb-4">
          <span className="text-green-400 text-sm font-medium flex items-center gap-2">
            💰 {trial.compensation}
          </span>
        </div>
      )}

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            {/* Study Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Eligibility */}
              <div>
                <h4 className="text-white font-medium mb-2 flex items-center gap-2">
                  <FaUsers className="w-4 h-4 text-blue-400" />
                  Eligibility
                </h4>
                <p className="text-blue-200 text-sm bg-slate-800/30 p-3 rounded-lg">
                  {trial.eligibilitySimplified}
                </p>
              </div>

              {/* Study Type & Interventions */}
              <div>
                <h4 className="text-white font-medium mb-2 flex items-center gap-2">
                  <FaFlask className="w-4 h-4 text-blue-400" />
                  Study Details
                </h4>
                <div className="bg-slate-800/30 p-3 rounded-lg space-y-2">
                  {trial.studyType && (
                    <div>
                      <span className="text-blue-300 text-xs font-medium">Type:</span>
                      <p className="text-blue-200 text-sm">{trial.studyType}</p>
                    </div>
                  )}
                  {trial.interventions && trial.interventions.length > 0 && (
                    <div>
                      <span className="text-blue-300 text-xs font-medium">Interventions:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {trial.interventions.slice(0, 3).map((intervention, idx) => (
                          <span key={idx} className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                            {intervention}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* All Locations */}
            {trial.locations.length > 1 && (
              <div>
                <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                  <FaHospitalAlt className="w-4 h-4 text-blue-400" />
                  All Study Locations ({trial.locations.length})
                </h4>

                {/* Map View */}
                <AnimatePresence>
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mb-4"
                  >
                    <TrialMiniMap locations={trial.locations} trialTitle={trial.title} />
                  </motion.div>
                </AnimatePresence>

                {/* Location List */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto">
                  {sortedLocations.map((location, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border transition-colors ${
                        userState && location.state.toLowerCase() === userState.toLowerCase()
                          ? 'bg-blue-500/10 border-blue-400/30'
                          : 'bg-slate-800/30 border-slate-600/30'
                      }`}
                    >
                      <h5 className="text-white text-sm font-medium mb-1">{location.facility}</h5>
                      <p className="text-blue-300 text-xs">
                        {location.city}, {location.state} {location.zip_code}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Contact Information */}
            {trial.contactInfo && (trial.contactInfo.name || trial.contactInfo.phone || trial.contactInfo.email) && (
              <div>
                <h4 className="text-white font-medium mb-2">Contact Information</h4>
                <div className="bg-slate-800/30 p-3 rounded-lg">
                  {trial.contactInfo.name && (
                    <p className="text-blue-200 text-sm mb-1">{trial.contactInfo.name}</p>
                  )}
                  <div className="flex flex-wrap gap-3 text-sm">
                    {trial.contactInfo.phone && (
                      <span className="text-blue-300">📞 {trial.contactInfo.phone}</span>
                    )}
                    {trial.contactInfo.email && (
                      <span className="text-blue-300">✉️ {trial.contactInfo.email}</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action Buttons */}
      <div className="flex gap-3 mt-4 pt-4 border-t border-blue-400/20">
        <motion.button
          onClick={handleLearnMore}
          className="flex-1 glass-button py-2 px-4 flex items-center justify-center gap-2"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <FaExternalLinkAlt className="w-3 h-3" />
          Learn More
        </motion.button>
        
        <motion.button
          onClick={handleContactStudy}
          className="flex-1 bg-blue-600/20 border border-blue-400/30 text-blue-300 hover:bg-blue-600/30 hover:border-blue-400/50 transition-colors py-2 px-4 rounded-lg flex items-center justify-center gap-2"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {trial.contactInfo?.phone ? <FaPhone className="w-3 h-3" /> : <FaEnvelope className="w-3 h-3" />}
          Contact Study
        </motion.button>
      </div>
    </motion.div>
  );
};

export default MatchCard; 