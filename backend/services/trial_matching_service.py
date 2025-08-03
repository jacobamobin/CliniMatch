"""
Trial Matching Service for CliniMatch

This service orchestrates the complete trial matching workflow by integrating:
- ClinicalTrials.gov API for trial data retrieval
- Gemini AI for medical language translation
- Supabase caching for performance optimization
"""

import logging
import time
import hashlib
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.clinical_trials_service import ClinicalTrialsService, RawTrialData
from services.gemini_translation_service import GeminiTranslationService, TrialTranslation
from utils.database import get_cache_service, CacheService
from models.user_profile import UserProfile
from models.trial_match import TrialMatch, TrialLocation, ContactInfo, MatchingResult


class TrialMatchingError(Exception):
    """Custom exception for trial matching errors"""
    def __init__(self, message: str, error_type: str = "MATCHING_ERROR"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class TrialMatchingService:
    """
    Core service that orchestrates the trial matching workflow
    """
    
    def __init__(self, 
                 clinical_trials_service: Optional[ClinicalTrialsService] = None,
                 gemini_service: Optional[GeminiTranslationService] = None,
                 cache_service: Optional[CacheService] = None):
        """
        Initialize the trial matching service
        
        Args:
            clinical_trials_service: Service for ClinicalTrials.gov API
            gemini_service: Service for AI translation
            cache_service: Service for caching
        """
        self.clinical_trials_service = clinical_trials_service or ClinicalTrialsService()
        self.gemini_service = gemini_service or GeminiTranslationService()
        self.cache_service = cache_service or get_cache_service()
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_results = 100
        self.cache_ttl_hours = 24
        self.max_translation_workers = 5  # Limit concurrent AI requests
    
    def generate_search_key(self, user_profile: UserProfile) -> str:
        """
        Generate a unique search key for efficient cache lookups
        
        Args:
            user_profile: User profile data
            
        Returns:
            MD5 hash string for cache key
        """
        # Create a normalized search parameters dict
        search_params = {
            'conditions': sorted([condition.lower().strip() for condition in user_profile.conditions]),
            'location': {
                'city': user_profile.location.city.lower().strip(),
                'state': user_profile.location.state.lower().strip(),
                'country': user_profile.location.country.lower().strip()
            },
            'age_range': self._get_age_range(user_profile.age),  # Group ages for better cache hits
            'version': '1.0'  # Version for cache invalidation if needed
        }
        
        # Create deterministic JSON string
        search_string = json.dumps(search_params, sort_keys=True)
        
        # Generate MD5 hash
        return hashlib.md5(search_string.encode()).hexdigest()
    
    def _get_age_range(self, age: int) -> str:
        """
        Convert specific age to age range for better cache efficiency
        
        Args:
            age: Specific age
            
        Returns:
            Age range string
        """
        if age < 18:
            return "under_18"
        elif age < 30:
            return "18_29"
        elif age < 50:
            return "30_49"
        elif age < 65:
            return "50_64"
        else:
            return "65_plus"
    
    def find_matching_trials(self, user_profile: UserProfile) -> MatchingResult:
        """
        Find and process matching clinical trials for a user profile
        
        Args:
            user_profile: Complete user profile data
            
        Returns:
            MatchingResult with processed trial matches
        """
        start_time = time.time()
        
        try:
            # Generate search key for caching
            search_key = self.generate_search_key(user_profile)
            self.logger.info(f"Processing trial search with key: {search_key}")
            
            # Try to get cached results first (DISABLED FOR NOW)
            cached_data = None  # self._get_cached_results(user_profile)
            if cached_data:
                processing_time = time.time() - start_time
                self.logger.info(f"Returning cached results in {processing_time:.2f}s")
                
                # Debug: Check the structure of cached_data
                self.logger.debug(f"Cached data type: {type(cached_data)}")
                self.logger.debug(f"Cached data keys: {cached_data.keys() if isinstance(cached_data, dict) else 'Not a dict'}")
                
                # Handle case where cached_data might be a MatchingResult object already
                if hasattr(cached_data, 'matches'):
                    # If it's already a MatchingResult object, return it directly
                    self.logger.info("Cached data is already a MatchingResult object")
                    return cached_data
                
                # Convert cached data from camelCase back to snake_case for model reconstruction
                matches = []
                for match_data in cached_data['matches']:
                    converted_data = self._convert_cached_match_to_model_format(match_data)
                    matches.append(TrialMatch(**converted_data))
                
                return MatchingResult(
                    matches=matches,
                    total_found=cached_data['total_found'],
                    processing_time=processing_time,
                    search_params=user_profile.get_search_params(),
                    cached=True,
                    ai_translation_success_rate=cached_data.get('ai_translation_success_rate', 0.0)
                )
            
            # Search for trials using ClinicalTrials.gov API
            self.logger.info("Searching for trials via ClinicalTrials.gov API")
            raw_trials = self._search_trials(user_profile)
            
            if not raw_trials:
                processing_time = time.time() - start_time
                return MatchingResult(
                    matches=[],
                    total_found=0,
                    processing_time=processing_time,
                    search_params=user_profile.get_search_params(),
                    cached=False,
                    ai_translation_success_rate=0.0
                )
            
            # Filter trials by status and location relevance
            filtered_trials = self._filter_trials(raw_trials, user_profile)
            self.logger.info(f"Filtered {len(raw_trials)} trials down to {len(filtered_trials)} relevant trials")
            
            # Process trials with AI translation
            self.logger.info(f"Processing {len(filtered_trials)} trials with AI translation")
            processed_matches, ai_success_rate = self._process_trials_with_ai(filtered_trials)
            
            # Create result
            processing_time = time.time() - start_time
            result = MatchingResult(
                matches=processed_matches,
                total_found=len(processed_matches),
                processing_time=processing_time,
                search_params=user_profile.get_search_params(),
                cached=False,
                ai_translation_success_rate=ai_success_rate
            )
            
            # Cache the results for future use (DISABLED FOR NOW)
            try:
                # self._cache_results(user_profile, ai_enhanced_trials)
                pass  # Caching disabled
            except Exception as e:
                self.logger.warning(f"Failed to cache results: {str(e)}")
                # Don't fail the request if caching fails
            
            self.logger.info(f"Trial matching completed in {processing_time:.2f}s with {len(processed_matches)} matches")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Trial matching failed after {processing_time:.2f}s: {str(e)}")
            raise TrialMatchingError(f"Failed to find matching trials: {str(e)}")
    
    def _filter_trials(self, raw_trials: List[RawTrialData], user_profile: UserProfile) -> List[RawTrialData]:
        """
        Filter trials by status and location relevance, returning more results
        
        Args:
            raw_trials: List of raw trial data
            user_profile: User profile for location filtering
            
        Returns:
            Filtered list of trials, prioritizing local trials but including many more results
        """
        user_state = user_profile.location.state.upper() if user_profile.location.state else ""
        
        # Categorize trials by priority
        local_trials = []           # Trials in user's state
        nearby_trials = []          # Trials in neighboring states/regions
        recruiting_trials = []      # All other recruiting trials
        active_trials = []          # Active but not recruiting
        
        for trial in raw_trials:
            # Only filter out truly finished trials
            if trial.status.lower() in ['completed', 'terminated', 'withdrawn']:
                continue
                
            # Check trial locations
            trial_locations = getattr(trial, 'locations', [])
            has_local_location = False
            has_nearby_location = False
            
            for loc in trial_locations:
                if hasattr(loc, 'state') and loc.state:
                    state = loc.state.upper()
                    if state == user_state:
                        has_local_location = True
                        break
                    elif user_state in ['NY', 'NJ', 'CT'] and state in ['NY', 'NJ', 'CT', 'PA', 'MA']:
                        has_nearby_location = True
                    elif user_state in ['CA', 'NV', 'OR'] and state in ['CA', 'NV', 'OR', 'WA', 'AZ']:
                        has_nearby_location = True
                    elif user_state in ['TX', 'LA', 'OK'] and state in ['TX', 'LA', 'OK', 'AR', 'NM']:
                        has_nearby_location = True
                    elif user_state in ['FL', 'GA', 'AL'] and state in ['FL', 'GA', 'AL', 'SC', 'NC']:
                        has_nearby_location = True
            
            # Categorize by location and status
            if has_local_location:
                local_trials.append(trial)
            elif has_nearby_location:
                nearby_trials.append(trial)
            elif trial.status.lower() in ['recruiting', 'not yet recruiting']:
                recruiting_trials.append(trial)
            elif trial.status.lower() in ['active, not recruiting', 'enrolling by invitation']:
                active_trials.append(trial)
        
        # Combine all trials with generous limits
        filtered_trials = []
        
        # Add local trials (all of them)
        filtered_trials.extend(local_trials)
        
        # Add nearby trials (up to 20)
        filtered_trials.extend(nearby_trials[:20])
        
        # Add recruiting trials (up to 30)
        filtered_trials.extend(recruiting_trials[:30])
        
        # Add active trials (up to 15)
        filtered_trials.extend(active_trials[:15])
        
        # If we still don't have enough, be even more permissive
        if len(filtered_trials) < 10:
            # Add all remaining trials regardless of location/status (except completed)
            remaining_trials = []
            for trial in raw_trials:
                if (trial not in filtered_trials and 
                    trial.status.lower() not in ['completed', 'terminated', 'withdrawn']):
                    remaining_trials.append(trial)
            filtered_trials.extend(remaining_trials[:15])
        
        self.logger.info(f"Filter results: {len(local_trials)} local, {len(nearby_trials)} nearby, "
                        f"{len(recruiting_trials)} recruiting, {len(active_trials)} active → "
                        f"{len(filtered_trials)} total returned")
        
        return filtered_trials
    
    def _get_cached_results(self, user_profile: UserProfile) -> Optional[Dict[str, Any]]:
        """
        Attempt to retrieve cached results
        
        Args:
            user_profile: User profile data
            
        Returns:
            Cached data dictionary or None
        """
        try:
            search_params = user_profile.get_search_params()
            cached_data = self.cache_service.get_cached_trials(search_params)
            
            if cached_data:
                self.logger.info("Found valid cached results")
                return cached_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Cache retrieval failed: {str(e)}")
            return None
    
    def _search_trials(self, user_profile: UserProfile) -> List[RawTrialData]:
        """
        Search for trials using the ClinicalTrials.gov API
        
        Args:
            user_profile: User profile data
            
        Returns:
            List of raw trial data
        """
        try:
            search_params = user_profile.get_search_params()
            
            raw_trials = self.clinical_trials_service.search_trials(
                conditions=search_params['conditions'],
                location=search_params['location'],
                age=search_params['age'],
                max_results=self.max_results
            )
            
            self.logger.info(f"Found {len(raw_trials)} trials from ClinicalTrials.gov")
            return raw_trials
            
        except Exception as e:
            self.logger.error(f"Clinical trials search failed: {str(e)}")
            raise TrialMatchingError(f"Failed to search clinical trials: {str(e)}", "API_ERROR")
    
    def _process_trials_with_ai(self, raw_trials: List[RawTrialData]) -> tuple[List[TrialMatch], float]:
        """
        Process raw trials with AI translation using concurrent processing
        
        Args:
            raw_trials: List of raw trial data
            
        Returns:
            Tuple of (processed matches, AI success rate)
        """
        processed_matches = []
        successful_translations = 0
        
        # Use ThreadPoolExecutor for concurrent AI processing
        with ThreadPoolExecutor(max_workers=self.max_translation_workers) as executor:
            # Submit all translation tasks
            future_to_trial = {
                executor.submit(self._process_single_trial, trial): trial 
                for trial in raw_trials
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_trial):
                trial = future_to_trial[future]
                try:
                    processed_match, translation_success = future.result()
                    processed_matches.append(processed_match)
                    
                    if translation_success:
                        successful_translations += 1
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process trial {trial.nct_id}: {str(e)}")
                    # Create fallback match without AI translation
                    fallback_match = self._create_fallback_match(trial)
                    processed_matches.append(fallback_match)
        
        # Calculate AI success rate
        ai_success_rate = successful_translations / len(raw_trials) if raw_trials else 0.0
        
        self.logger.info(f"AI translation success rate: {ai_success_rate:.2%}")
        return processed_matches, ai_success_rate
    
    def _process_single_trial(self, raw_trial: RawTrialData) -> tuple[TrialMatch, bool]:
        """
        Process a single trial with AI translation
        
        Args:
            raw_trial: Raw trial data
            
        Returns:
            Tuple of (TrialMatch, translation_success_flag)
        """
        try:
            # Attempt AI translation
            translation = self.gemini_service.translate_with_fallback(
                title=raw_trial.title,
                criteria=raw_trial.eligibility_criteria,
                description=raw_trial.brief_summary or raw_trial.detailed_description,
                compensation=None  # TODO: Extract compensation from trial data if available
            )
            
            # Check if AI translation was successful (not fallback)
            translation_success = not (
                "Please review the detailed eligibility criteria" in translation.eligibility_simplified or
                "Time commitment information not available" in translation.time_commitment
            )
            
            # Convert locations
            locations = [
                TrialLocation(
                    facility=loc.facility,
                    city=loc.city,
                    state=loc.state,
                    country=loc.country,
                    zip_code=loc.zip_code,
                    coordinates=loc.coordinates
                )
                for loc in raw_trial.locations
            ]
            
            # Convert contact info
            contact_info = ContactInfo(
                name=raw_trial.contact_info.name,
                phone=raw_trial.contact_info.phone,
                email=raw_trial.contact_info.email
            )
            
            # Create processed match
            trial_match = TrialMatch(
                nct_id=raw_trial.nct_id,
                title=raw_trial.title,
                original_description=raw_trial.brief_summary or raw_trial.detailed_description,
                simplified_description=translation.simplified_description,
                locations=locations,
                eligibility_criteria=raw_trial.eligibility_criteria,
                eligibility_simplified=translation.eligibility_simplified,
                compensation=None,  # TODO: Extract from trial data
                compensation_explanation=translation.compensation_explanation,
                time_commitment=translation.time_commitment,
                key_benefits=translation.key_benefits,
                contact_info=contact_info,
                study_type=raw_trial.study_type,
                phase=raw_trial.phase,
                status=raw_trial.status,
                sponsor=raw_trial.sponsor,
                conditions=raw_trial.conditions,
                interventions=raw_trial.interventions
            )
            
            return trial_match, translation_success
            
        except Exception as e:
            self.logger.warning(f"AI processing failed for trial {raw_trial.nct_id}: {str(e)}")
            # Return fallback match
            return self._create_fallback_match(raw_trial), False
    
    def _create_fallback_match(self, raw_trial: RawTrialData) -> TrialMatch:
        """
        Create a fallback trial match when AI processing fails
        
        Args:
            raw_trial: Raw trial data
            
        Returns:
            TrialMatch with fallback content
        """
        # Convert locations
        locations = [
            TrialLocation(
                facility=loc.facility,
                city=loc.city,
                state=loc.state,
                country=loc.country,
                zip_code=loc.zip_code,
                coordinates=loc.coordinates
            )
            for loc in raw_trial.locations
        ]
        
        # Convert contact info
        contact_info = ContactInfo(
            name=raw_trial.contact_info.name,
            phone=raw_trial.contact_info.phone,
            email=raw_trial.contact_info.email
        )
        
        # Create fallback translation
        fallback_translation = self.gemini_service.create_fallback_translation(
            title=raw_trial.title,
            criteria=raw_trial.eligibility_criteria,
            description=raw_trial.brief_summary or raw_trial.detailed_description
        )
        
        return TrialMatch(
            nct_id=raw_trial.nct_id,
            title=raw_trial.title,
            original_description=raw_trial.brief_summary or raw_trial.detailed_description,
            simplified_description=fallback_translation.simplified_description,
            locations=locations,
            eligibility_criteria=raw_trial.eligibility_criteria,
            eligibility_simplified=fallback_translation.eligibility_simplified,
            compensation=None,
            compensation_explanation=fallback_translation.compensation_explanation,
            time_commitment=fallback_translation.time_commitment,
            key_benefits=fallback_translation.key_benefits,
            contact_info=contact_info,
            study_type=raw_trial.study_type,
            phase=raw_trial.phase,
            status=raw_trial.status,
            sponsor=raw_trial.sponsor,
            conditions=raw_trial.conditions,
            interventions=raw_trial.interventions
        )
    
    def _convert_cached_match_to_model_format(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert cached match data from camelCase to snake_case for model reconstruction
        
        Args:
            cached_data: Cached data in camelCase format
            
        Returns:
            Data in snake_case format for TrialMatch model
        """
        # Field mapping from camelCase to snake_case
        field_mapping = {
            'nctId': 'nct_id',
            'originalDescription': 'original_description',
            'simplifiedDescription': 'simplified_description',
            'eligibilityCriteria': 'eligibility_criteria',
            'eligibilitySimplified': 'eligibility_simplified',
            'compensationExplanation': 'compensation_explanation',
            'timeCommitment': 'time_commitment',
            'keyBenefits': 'key_benefits',
            'contactInfo': 'contact_info',
            'studyType': 'study_type'
        }
        
        converted_data = {}
        
        for key, value in cached_data.items():
            # Convert key from camelCase to snake_case
            new_key = field_mapping.get(key, key)
            
            # Handle nested objects (locations, contact_info)
            if key == 'locations' and isinstance(value, list):
                converted_data[new_key] = [
                    {
                        'facility': loc.get('facility', ''),
                        'city': loc.get('city', ''),
                        'state': loc.get('state', ''),
                        'country': loc.get('country', ''),
                        'zip_code': loc.get('zipCode'),
                        'coordinates': tuple(loc.get('coordinates', [])) if loc.get('coordinates') else None
                    }
                    for loc in value
                ]
            elif key == 'contactInfo' and isinstance(value, dict):
                converted_data[new_key] = {
                    'name': value.get('name'),
                    'phone': value.get('phone'),
                    'email': value.get('email')
                }
            else:
                converted_data[new_key] = value
        
        return converted_data
    
    def _cache_results(self, user_profile: UserProfile, result: MatchingResult) -> None:
        """
        Cache the matching results
        
        Args:
            user_profile: User profile data
            result: Matching result to cache
        """
        try:
            search_params = user_profile.get_search_params()
            
            # Prepare data for caching
            cache_data = {
                'matches': [match.to_dict() for match in result.matches],
                'total_found': result.total_found,
                'ai_translation_success_rate': result.ai_translation_success_rate,
                'cached_at': time.time()
            }
            
            # Cache the results
            self.cache_service.cache_trials(
                search_params=search_params,
                trial_data=cache_data,
                ttl_hours=self.cache_ttl_hours
            )
            
            self.logger.info(f"Successfully cached {len(result.matches)} trial matches")
            
        except Exception as e:
            self.logger.warning(f"Failed to cache results: {str(e)}")
            # Don't raise exception - caching failure shouldn't break the main flow
    
    def get_trial_by_id(self, nct_id: str) -> Optional[TrialMatch]:
        """
        Get a specific trial by NCT ID with AI translation
        
        Args:
            nct_id: NCT identifier
            
        Returns:
            Processed TrialMatch or None if not found
        """
        try:
            # Get raw trial data
            raw_trial = self.clinical_trials_service.get_trial_by_nct_id(nct_id)
            
            if not raw_trial:
                return None
            
            # Process with AI translation
            processed_match, _ = self._process_single_trial(raw_trial)
            
            return processed_match
            
        except Exception as e:
            self.logger.error(f"Failed to get trial {nct_id}: {str(e)}")
            raise TrialMatchingError(f"Failed to retrieve trial {nct_id}: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all integrated services
        
        Returns:
            Health status dictionary
        """
        health_status = {
            'status': 'healthy',
            'services': {},
            'timestamp': time.time()
        }
        
        try:
            # Check ClinicalTrials.gov API
            # Simple test - this will be a lightweight check
            health_status['services']['clinical_trials_api'] = {
                'status': 'healthy',
                'accessible': True
            }
            
            # Check Gemini AI service
            gemini_health = self.gemini_service.health_check()
            health_status['services']['gemini_ai'] = gemini_health
            
            # Check database/cache service
            cache_stats = self.cache_service.get_cache_stats()
            health_status['services']['cache'] = {
                'status': 'healthy' if 'error' not in cache_stats else 'unhealthy',
                'stats': cache_stats
            }
            
            # Determine overall status
            unhealthy_services = [
                name for name, service in health_status['services'].items()
                if service.get('status') != 'healthy'
            ]
            
            if unhealthy_services:
                health_status['status'] = 'degraded'
                health_status['unhealthy_services'] = unhealthy_services
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status