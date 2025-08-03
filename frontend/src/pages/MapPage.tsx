import React, { useState, useEffect, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useTrial } from '../contexts/TrialContext';
import { FaSearch, FaMapMarkerAlt, FaFilter, FaSpinner, FaExternalLinkAlt, FaPhone, FaInfoCircle } from 'react-icons/fa';
import { MdClear, MdMyLocation } from 'react-icons/md';

// Fix for default markers
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.divIcon({
  html: `<div style="background-color: #3B82F6; width: 25px; height: 25px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
    <div style="color: white; font-size: 12px; font-weight: bold;">📍</div>
  </div>`,
  iconSize: [25, 25],
  iconAnchor: [12, 25],
  popupAnchor: [0, -25]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface LocationData {
  lat: number;
  lng: number;
  city: string;
  state: string;
  country: string;
  trials: any[];
}

// Component to handle map centering
const MapCenter: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  
  useEffect(() => {
    map.setView(center, zoom);
  }, [map, center, zoom]);
  
  return null;
};

// Component to handle user location
const LocationControl: React.FC<{ onLocationFound: (lat: number, lng: number) => void }> = ({ onLocationFound }) => {
  const [isLoading, setIsLoading] = useState(false);
  
  const getUserLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by this browser.');
      return;
    }
    
    setIsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        onLocationFound(position.coords.latitude, position.coords.longitude);
        setIsLoading(false);
      },
      (error) => {
        console.error('Error getting location:', error);
        alert('Unable to retrieve your location. Please check permissions.');
        setIsLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
  };
  
  return (
    <button
      onClick={getUserLocation}
      disabled={isLoading}
      className="glass-button p-3 rounded-lg flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
      title="Find my location"
    >
      {isLoading ? <FaSpinner className="animate-spin" /> : <MdMyLocation />}
      {isLoading ? 'Locating...' : 'My Location'}
    </button>
  );
};

const MapPage: React.FC = () => {
  const { userProfile, matchingResults, isLoading } = useTrial();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCondition, setSelectedCondition] = useState('');
  const [mapCenter, setMapCenter] = useState<[number, number]>([39.8283, -98.5795]); // Center of US
  const [mapZoom, setMapZoom] = useState(4);
  const [locations, setLocations] = useState<LocationData[]>([]);
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [selectedTrial, setSelectedTrial] = useState<any>(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const geocodingCache = useRef(new Map<string, [number, number]>());

  // Get matches from context
  const matches = useMemo(() => matchingResults?.matches || [], [matchingResults]);

  // Predefined medical conditions for quick search
  const commonConditions = [
    'Cancer', 'Diabetes', 'Heart Disease', 'Alzheimer\'s', 'Depression',
    'Arthritis', 'Asthma', 'Multiple Sclerosis', 'Parkinson\'s', 'Stroke',
    'Kidney Disease', 'Liver Disease', 'Obesity', 'Hypertension', 'COPD'
  ];

  // Geocoding function using Google Geocoding API
  const geocodeLocation = async (city: string, state: string, country: string): Promise<[number, number] | null> => {
    const cacheKey = `${city},${state},${country}`;
    
    // Check cache first
    if (geocodingCache.current.has(cacheKey)) {
      return geocodingCache.current.get(cacheKey)!;
    }

    try {
      await new Promise(resolve => setTimeout(resolve, 100)); // Rate limiting
      
      const locationQuery = `${city}, ${state}, ${country}`;
      const apiKey = process.env.REACT_APP_GOOGLE_GEOCODING_API_KEY;
      
      if (!apiKey) {
        console.error('Google Geocoding API key not found');
        return null;
      }
      
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(locationQuery)}&key=${apiKey}`
      );
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const data = await response.json();
      if (data.status === 'OK' && data.results?.[0]) {
        const { lat, lng } = data.results[0].geometry.location;
        const coords: [number, number] = [lat, lng];
        geocodingCache.current.set(cacheKey, coords);
        return coords;
      }
    } catch (error) {
      console.warn('Geocoding failed for:', city, state, error);
    }
    return null;
  };

  // Process trial locations and geocode them
  useEffect(() => {
    if (!matches?.length) {
      setLocations([]);
      return;
    }

    const processLocations = async () => {
      setIsGeocoding(true);
      const locationMap = new Map<string, LocationData>();
      
      // Filter trials based on status
      const filteredTrials = matches.filter((trial: any) => {
        if (filterStatus === 'all') return true;
        if (filterStatus === 'recruiting') return trial.status?.toLowerCase().includes('recruiting');
        if (filterStatus === 'active') return trial.status?.toLowerCase().includes('active');
        if (filterStatus === 'not_recruiting') return trial.status?.toLowerCase().includes('not recruiting');
        return true;
      });

      // Filter by condition if selected
      const finalTrials = selectedCondition 
        ? filteredTrials.filter((trial: any) => 
            trial.conditions?.some((condition: string) => 
              condition.toLowerCase().includes(selectedCondition.toLowerCase())
            ) || 
            trial.title?.toLowerCase().includes(selectedCondition.toLowerCase()) ||
            trial.description?.toLowerCase().includes(selectedCondition.toLowerCase())
          )
        : filteredTrials;

      for (const trial of finalTrials) {
        if (trial.locations?.length > 0) {
          for (const location of trial.locations) {
            if (location.city && location.state) {
              const key = `${location.city},${location.state}`;
              
              if (!locationMap.has(key)) {
                const coords = await geocodeLocation(
                  location.city, 
                  location.state, 
                  location.country || 'United States'
                );
                
                if (coords) {
                  locationMap.set(key, {
                    lat: coords[0],
                    lng: coords[1],
                    city: location.city,
                    state: location.state,
                    country: location.country || 'United States',
                    trials: [trial]
                  });
                }
              } else {
                // Add trial to existing location
                const existing = locationMap.get(key)!;
                existing.trials.push(trial);
              }
            }
          }
        }
      }
      
      setLocations(Array.from(locationMap.values()));
      setIsGeocoding(false);
    };

    processLocations();
  }, [matches, selectedCondition, filterStatus]);

  // Handle search by location
  const handleLocationSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsGeocoding(true);
    const coords = await geocodeLocation(searchQuery, '', 'United States');
    if (coords) {
      setMapCenter(coords);
      setMapZoom(10);
    } else {
      alert('Location not found. Please try a different search term.');
    }
    setIsGeocoding(false);
  };

  // Handle user location
  const handleUserLocation = (lat: number, lng: number) => {
    setMapCenter([lat, lng]);
    setMapZoom(12);
  };

  // Get stats
  const stats = useMemo(() => {
    const totalTrials = locations.reduce((sum, loc) => sum + loc.trials.length, 0);
    const uniqueLocations = locations.length;
    const recruitingTrials = locations.reduce((sum, loc) => 
      sum + loc.trials.filter((trial: any) => trial.status?.toLowerCase().includes('recruiting')).length, 0
    );
    
    return { totalTrials, uniqueLocations, recruitingTrials };
  }, [locations]);

  return (
    <div className="min-h-screen bg-slate-900 pt-20">
      {/* Header */}
      <div className="glass-card mx-4 mb-6 p-6 rounded-xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Clinical Trial Map</h1>
            <p className="text-slate-300">
              Explore {stats.totalTrials} trials across {stats.uniqueLocations} locations
            </p>
          </div>
          
          {/* Stats */}
          <div className="flex gap-4 text-sm">
            <div className="glass-card-dark p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-400">{stats.totalTrials}</div>
              <div className="text-slate-400">Total Trials</div>
            </div>
            <div className="glass-card-dark p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-400">{stats.recruitingTrials}</div>
              <div className="text-slate-400">Recruiting</div>
            </div>
            <div className="glass-card-dark p-3 rounded-lg text-center">
              <div className="text-2xl font-bold text-purple-400">{stats.uniqueLocations}</div>
              <div className="text-slate-400">Locations</div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 mx-4">
        {/* Search and Filters Sidebar */}
        <div className="w-full lg:w-80 space-y-4">
          {/* Location Search */}
          <div className="glass-card p-4 rounded-xl">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <FaSearch className="text-blue-400" />
              Search Location
            </h3>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter city, state, or address..."
                className="glass-input-dark flex-1 px-3 py-2 rounded-lg text-white placeholder-slate-400"
                onKeyPress={(e) => e.key === 'Enter' && handleLocationSearch()}
              />
              <button
                onClick={handleLocationSearch}
                disabled={isGeocoding || !searchQuery.trim()}
                className="glass-button px-4 py-2 rounded-lg text-blue-400 disabled:opacity-50"
              >
                {isGeocoding ? <FaSpinner className="animate-spin" /> : <FaSearch />}
              </button>
            </div>
            <div className="mt-3">
              <LocationControl onLocationFound={handleUserLocation} />
            </div>
          </div>

          {/* Condition Filter */}
          <div className="glass-card p-4 rounded-xl">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <FaFilter className="text-purple-400" />
              Filter by Condition
            </h3>
            <select
              value={selectedCondition}
              onChange={(e) => setSelectedCondition(e.target.value)}
              className="glass-input-dark w-full px-3 py-2 rounded-lg text-white"
            >
              <option value="">All Conditions</option>
              {commonConditions.map(condition => (
                <option key={condition} value={condition}>{condition}</option>
              ))}
            </select>
            {selectedCondition && (
              <button
                onClick={() => setSelectedCondition('')}
                className="mt-2 text-slate-400 hover:text-white text-sm flex items-center gap-1"
              >
                <MdClear /> Clear filter
              </button>
            )}
          </div>

          {/* Status Filter */}
          <div className="glass-card p-4 rounded-xl">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <FaInfoCircle className="text-green-400" />
              Trial Status
            </h3>
            <div className="space-y-2">
              {[
                { value: 'all', label: 'All Trials', count: stats.totalTrials },
                { value: 'recruiting', label: 'Recruiting', count: stats.recruitingTrials },
                { value: 'active', label: 'Active', count: stats.totalTrials - stats.recruitingTrials },
              ].map(option => (
                <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value={option.value}
                    checked={filterStatus === option.value}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="text-blue-500"
                  />
                  <span className="text-slate-300">{option.label}</span>
                  <span className="text-slate-500 text-sm">({option.count})</span>
                </label>
              ))}
            </div>
          </div>

          {/* Selected Trial Details */}
          {selectedTrial && (
            <div className="glass-card p-4 rounded-xl">
              <h3 className="text-white font-semibold mb-3">Trial Details</h3>
              <div className="space-y-2 text-sm">
                <h4 className="font-medium text-white line-clamp-2">{selectedTrial.title}</h4>
                <p className="text-slate-400">Status: {selectedTrial.status}</p>
                <p className="text-slate-400">Phase: {selectedTrial.phase || 'Not specified'}</p>
                {selectedTrial.sponsor && (
                  <p className="text-slate-400">Sponsor: {selectedTrial.sponsor}</p>
                )}
                <div className="flex gap-2 mt-3">
                  {selectedTrial.nctId && (
                    <a
                      href={`https://clinicaltrials.gov/ct2/show/${selectedTrial.nctId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="glass-button px-3 py-1 rounded text-blue-400 text-xs flex items-center gap-1"
                    >
                      <FaExternalLinkAlt /> View Details
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Map */}
        <div className="flex-1">
          <div className="glass-card p-4 rounded-xl">
            <div className="relative">
              {isGeocoding && (
                <div className="absolute top-4 left-4 z-[1000] glass-card-dark px-3 py-2 rounded-lg flex items-center gap-2 text-white">
                  <FaSpinner className="animate-spin" />
                  Loading locations...
                </div>
              )}
              
              <MapContainer
                center={mapCenter}
                zoom={mapZoom}
                style={{ height: '600px', width: '100%' }}
                className="rounded-lg"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                
                <MapCenter center={mapCenter} zoom={mapZoom} />
                
                {locations.map((location, index) => (
                  <Marker
                    key={index}
                    position={[location.lat, location.lng]}
                  >
                    <Popup>
                      <div className="p-2 max-w-sm">
                        <h3 className="font-bold text-lg mb-2">
                          {location.city}, {location.state}
                        </h3>
                        <p className="text-sm text-gray-600 mb-3">
                          {location.trials.length} trial{location.trials.length !== 1 ? 's' : ''} available
                        </p>
                        
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {location.trials.slice(0, 3).map((trial, trialIndex) => (
                            <div key={trialIndex} className="border-b border-gray-200 pb-2 last:border-b-0">
                              <h4 className="font-medium text-sm line-clamp-2 mb-1">
                                {trial.title}
                              </h4>
                              <p className="text-xs text-gray-600">
                                Status: {trial.status}
                              </p>
                              <p className="text-xs text-gray-600">
                                Phase: {trial.phase || 'Not specified'}
                              </p>
                              <button
                                onClick={() => setSelectedTrial(trial)}
                                className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                              >
                                View Details
                              </button>
                            </div>
                          ))}
                          {location.trials.length > 3 && (
                            <p className="text-xs text-gray-500 text-center pt-1">
                              +{location.trials.length - 3} more trials
                            </p>
                          )}
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Trials List Section */}
      {locations.length > 0 && (
        <div className="mx-4 mt-6 mb-6">
          <div className="glass-card p-6 rounded-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <FaMapMarkerAlt className="text-blue-400" />
                All Geocoded Trials ({locations.reduce((sum, loc) => sum + loc.trials.length, 0)})
              </h2>
              <div className="text-sm text-slate-400">
                Showing trials across {locations.length} locations
              </div>
            </div>

            <div className="grid gap-4">
              {locations.map((location, locationIndex) => (
                <div key={locationIndex} className="glass-card-dark p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      {location.city}, {location.state}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <span>{location.trials.length} trial{location.trials.length !== 1 ? 's' : ''}</span>
                      <button
                        onClick={() => {
                          setMapCenter([location.lat, location.lng]);
                          setMapZoom(12);
                        }}
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                        title="Center map on this location"
                      >
                        <FaMapMarkerAlt />
                      </button>
                    </div>
                  </div>

                  <div className="grid gap-3">
                    {location.trials.map((trial, trialIndex) => (
                      <div 
                        key={trialIndex} 
                        className="bg-slate-800/30 p-4 rounded-lg border border-slate-700/50 hover:border-blue-500/50 transition-colors cursor-pointer"
                        onClick={() => setSelectedTrial(trial)}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-white text-sm mb-2 line-clamp-2">
                              {trial.title}
                            </h4>
                            
                            <div className="flex flex-wrap gap-2 mb-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                trial.status?.toLowerCase().includes('recruiting') 
                                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                                  : trial.status?.toLowerCase().includes('active')
                                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                                  : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                              }`}>
                                {trial.status}
                              </span>
                              
                              {trial.phase && (
                                <span className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400 border border-purple-500/30">
                                  {trial.phase}
                                </span>
                              )}
                            </div>

                            <div className="space-y-1 text-xs text-slate-400">
                              {trial.sponsor && (
                                <p><span className="text-slate-500">Sponsor:</span> {trial.sponsor}</p>
                              )}
                              {trial.nctId && (
                                <p><span className="text-slate-500">NCT ID:</span> {trial.nctId}</p>
                              )}
                              {trial.conditions?.length > 0 && (
                                <p><span className="text-slate-500">Conditions:</span> {trial.conditions.slice(0, 2).join(', ')}{trial.conditions.length > 2 ? '...' : ''}</p>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-col gap-2 shrink-0">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedTrial(trial);
                              }}
                              className="glass-button px-3 py-1 rounded text-blue-400 text-xs flex items-center gap-1 hover:text-blue-300"
                            >
                              <FaInfoCircle /> Details
                            </button>
                            
                            {trial.nctId && (
                              <a
                                href={`https://clinicaltrials.gov/ct2/show/${trial.nctId}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="glass-button px-3 py-1 rounded text-green-400 text-xs flex items-center gap-1 hover:text-green-300"
                              >
                                <FaExternalLinkAlt /> ClinicalTrials.gov
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Summary Statistics */}
            <div className="mt-6 pt-6 border-t border-slate-700/50">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                <div className="glass-card-dark p-3 rounded-lg">
                  <div className="text-xl font-bold text-blue-400">
                    {locations.reduce((sum, loc) => sum + loc.trials.length, 0)}
                  </div>
                  <div className="text-xs text-slate-400">Total Trials</div>
                </div>
                
                <div className="glass-card-dark p-3 rounded-lg">
                  <div className="text-xl font-bold text-green-400">
                    {locations.reduce((sum, loc) => 
                      sum + loc.trials.filter((trial: any) => trial.status?.toLowerCase().includes('recruiting')).length, 0
                    )}
                  </div>
                  <div className="text-xs text-slate-400">Recruiting</div>
                </div>
                
                <div className="glass-card-dark p-3 rounded-lg">
                  <div className="text-xl font-bold text-purple-400">{locations.length}</div>
                  <div className="text-xs text-slate-400">Unique Locations</div>
                </div>
                
                <div className="glass-card-dark p-3 rounded-lg">
                  <div className="text-xl font-bold text-orange-400">
                    {locations.reduce((sum, loc) => 
                      sum + loc.trials.filter((trial: any) => trial.phase).length, 0
                    )}
                  </div>
                  <div className="text-xs text-slate-400">With Phase Info</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapPage; 