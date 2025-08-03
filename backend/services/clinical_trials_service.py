"""
ClinicalTrials.gov API Integration Service

This service handles communication with the ClinicalTrials.gov REST API,
including data retrieval, parsing, and error handling.
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrialLocation:
    """Data class for trial location information"""
    facility: str
    city: str
    state: str
    country: str
    zip_code: Optional[str] = None
    coordinates: Optional[tuple] = None


@dataclass
class ContactInfo:
    """Data class for trial contact information"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class RawTrialData:
    """Data class for raw trial data from ClinicalTrials.gov API"""
    nct_id: str
    title: str
    brief_summary: str
    detailed_description: str
    eligibility_criteria: str
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    locations: List[TrialLocation]
    contact_info: ContactInfo
    study_type: str
    phase: Optional[str]
    status: str
    start_date: Optional[str]
    completion_date: Optional[str]
    sponsor: str
    conditions: List[str]
    interventions: List[str]


class ClinicalTrialsAPIError(Exception):
    """Custom exception for ClinicalTrials.gov API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class RateLimitError(ClinicalTrialsAPIError):
    """Exception for rate limiting errors"""
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class ClinicalTrialsService:
    """Service for interacting with ClinicalTrials.gov API"""
    
    def __init__(self, base_url: str = "https://clinicaltrials.gov/api/v2"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CliniMatch/1.0 (Clinical Trial Matching Service)',
            'Accept': 'application/json'
        })
        
        # Rate limiting configuration
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self.max_retries = 3
        self.retry_delay = 2  # Base delay for exponential backoff
    
    def _handle_rate_limiting(self):
        """Implement rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the ClinicalTrials.gov API with error handling and retries"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                self._handle_rate_limiting()
                
                logger.info(f"Making request to {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, params=params, timeout=30)
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError as e:
                        logger.error(f"JSON decode error: {e}")
                        logger.error(f"Response content: {response.text[:500]}")
                        raise ClinicalTrialsAPIError(f"Invalid JSON response: {str(e)}")
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry.")
                        time.sleep(retry_after)
                        continue
                    else:
                        raise RateLimitError(retry_after)
                elif response.status_code == 404:
                    raise ClinicalTrialsAPIError(
                        "Endpoint not found", 
                        status_code=404,
                        response_data=response.json() if response.content else None
                    )
                elif response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}. Retrying in {delay} seconds.")
                        time.sleep(delay)
                        continue
                    else:
                        raise ClinicalTrialsAPIError(
                            f"Server error: {response.status_code}",
                            status_code=response.status_code,
                            response_data=response.json() if response.content else None
                        )
                else:
                    # Other client errors
                    raise ClinicalTrialsAPIError(
                        f"API request failed with status {response.status_code}",
                        status_code=response.status_code,
                        response_data=response.json() if response.content else None
                    )
                    
            except ValueError as e:  # JSON decode error - handle this first
                logger.error(f"JSON decode error: {e}")
                if 'response' in locals():
                    logger.error(f"Response content: {response.text[:500]}")
                raise ClinicalTrialsAPIError(f"Invalid JSON response: {str(e)}")
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request timeout. Retrying in {delay} seconds.")
                    time.sleep(delay)
                    continue
                else:
                    raise ClinicalTrialsAPIError("Request timeout after multiple attempts")
                    
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Connection error. Retrying in {delay} seconds.")
                    time.sleep(delay)
                    continue
                else:
                    raise ClinicalTrialsAPIError("Connection error after multiple attempts")
                    
            except requests.exceptions.RequestException as e:
                raise ClinicalTrialsAPIError(f"Request failed: {str(e)}")
        
        raise ClinicalTrialsAPIError("Max retries exceeded")
    
    def search_trials(self, 
                     conditions: List[str] = None,
                     location: Dict[str, str] = None,
                     age: int = None,
                     max_results: int = 50) -> List[RawTrialData]:
        """
        Search for clinical trials based on criteria
        
        Args:
            conditions: List of medical conditions to search for
            location: Dictionary with city, state, country information
            age: Patient age for eligibility filtering
            max_results: Maximum number of results to return
            
        Returns:
            List of RawTrialData objects
        """
        try:
            # Build search parameters
            params = {
                'format': 'json',
                'markupFormat': 'markdown',
                'countTotal': 'true',
                'pageSize': min(max_results, 1000)  # API limit
            }
            
            # Add condition-based search
            if conditions:
                # Join conditions with OR logic for broader search
                condition_query = ' OR '.join([f'"{condition}"' for condition in conditions])
                params['query.cond'] = condition_query
            
            # Add broader location-based search (country only for wider results)
            if location and location.get('country'):
                # Only use country for broader search, let filtering handle state/city priority
                params['query.locn'] = location['country']
            
            logger.info(f"Searching trials with params: {params}")
            
            # Make the API request
            response_data = self._make_request('studies', params)
            
            # Parse and return results
            trials = []
            studies = response_data.get('studies', [])
            
            logger.info(f"Found {len(studies)} trials from API")
            
            for study_data in studies:
                try:
                    trial = self._parse_trial_data(study_data)
                    
                    # Apply age filtering if specified
                    if age and not self._is_age_eligible(trial, age):
                        continue
                        
                    trials.append(trial)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse trial {study_data.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(trials)} trials")
            return trials
            
        except ClinicalTrialsAPIError:
            raise
        except Exception as e:
            raise ClinicalTrialsAPIError(f"Search failed: {str(e)}")
    
    def get_trial_by_nct_id(self, nct_id: str) -> Optional[RawTrialData]:
        """
        Get a specific trial by its NCT ID
        
        Args:
            nct_id: The NCT identifier for the trial
            
        Returns:
            RawTrialData object or None if not found
        """
        try:
            params = {
                'format': 'json',
                'markupFormat': 'markdown',
                'query.id': nct_id
            }
            
            response_data = self._make_request('studies', params)
            studies = response_data.get('studies', [])
            
            if not studies:
                return None
                
            return self._parse_trial_data(studies[0])
            
        except ClinicalTrialsAPIError:
            raise
        except Exception as e:
            raise ClinicalTrialsAPIError(f"Failed to get trial {nct_id}: {str(e)}")
    
    def _parse_trial_data(self, study_data: Dict[str, Any]) -> RawTrialData:
        """
        Parse raw API response data into structured RawTrialData object
        
        Args:
            study_data: Raw study data from API response
            
        Returns:
            RawTrialData object
        """
        try:
            protocol = study_data.get('protocolSection', {})
            
            # Identification module
            identification = protocol.get('identificationModule', {})
            nct_id = identification.get('nctId', '')
            title = identification.get('briefTitle', '')
            
            # Description module
            description = protocol.get('descriptionModule', {})
            brief_summary = description.get('briefSummary', '')
            detailed_description = description.get('detailedDescription', '')
            
            # Eligibility module
            eligibility = protocol.get('eligibilityModule', {})
            eligibility_criteria = eligibility.get('eligibilityCriteria', '')
            
            # Parse inclusion/exclusion criteria
            inclusion_criteria, exclusion_criteria = self._parse_eligibility_criteria(eligibility_criteria)
            
            # Contacts and locations module
            contacts_locations = protocol.get('contactsLocationsModule', {})
            locations = self._parse_locations(contacts_locations.get('locations', []))
            contact_info = self._parse_contact_info(contacts_locations)
            
            # Design module
            design = protocol.get('designModule', {})
            study_type = design.get('studyType', '')
            phases = design.get('phases', [])
            phase = phases[0] if phases else None
            
            # Status module
            status = protocol.get('statusModule', {})
            overall_status = status.get('overallStatus', '')
            start_date = self._parse_date(status.get('startDateStruct'))
            completion_date = self._parse_date(status.get('completionDateStruct'))
            
            # Sponsor module
            sponsor_collaborators = protocol.get('sponsorCollaboratorsModule', {})
            lead_sponsor = sponsor_collaborators.get('leadSponsor', {})
            sponsor = lead_sponsor.get('name', '')
            
            # Conditions module
            conditions_module = protocol.get('conditionsModule', {})
            conditions = conditions_module.get('conditions', [])
            
            # Arms interventions module
            arms_interventions = protocol.get('armsInterventionsModule', {})
            interventions_data = arms_interventions.get('interventions', [])
            interventions = [intervention.get('name', '') for intervention in interventions_data]
            
            return RawTrialData(
                nct_id=nct_id,
                title=title,
                brief_summary=brief_summary,
                detailed_description=detailed_description,
                eligibility_criteria=eligibility_criteria,
                inclusion_criteria=inclusion_criteria,
                exclusion_criteria=exclusion_criteria,
                locations=locations,
                contact_info=contact_info,
                study_type=study_type,
                phase=phase,
                status=overall_status,
                start_date=start_date,
                completion_date=completion_date,
                sponsor=sponsor,
                conditions=conditions,
                interventions=interventions
            )
            
        except Exception as e:
            raise ClinicalTrialsAPIError(f"Failed to parse trial data: {str(e)}")
    
    def _parse_eligibility_criteria(self, criteria_text: str) -> tuple[List[str], List[str]]:
        """
        Parse eligibility criteria text into inclusion and exclusion lists
        
        Args:
            criteria_text: Raw eligibility criteria text
            
        Returns:
            Tuple of (inclusion_criteria, exclusion_criteria) lists
        """
        inclusion_criteria = []
        exclusion_criteria = []
        
        if not criteria_text:
            return inclusion_criteria, exclusion_criteria
        
        # Split by common section headers
        sections = criteria_text.lower().split('exclusion criteria')
        
        if len(sections) > 1:
            # We have both inclusion and exclusion
            inclusion_text = sections[0].replace('inclusion criteria', '').strip()
            exclusion_text = sections[1].strip()
        else:
            # Check if it starts with exclusion
            if criteria_text.lower().startswith('exclusion'):
                inclusion_text = ''
                exclusion_text = criteria_text.replace('exclusion criteria', '').strip()
            else:
                inclusion_text = criteria_text.replace('inclusion criteria', '').strip()
                exclusion_text = ''
        
        # Parse inclusion criteria
        if inclusion_text:
            inclusion_criteria = self._parse_criteria_list(inclusion_text)
        
        # Parse exclusion criteria
        if exclusion_text:
            exclusion_criteria = self._parse_criteria_list(exclusion_text)
        
        return inclusion_criteria, exclusion_criteria
    
    def _parse_criteria_list(self, criteria_text: str) -> List[str]:
        """Parse a criteria text block into individual criteria items"""
        criteria = []
        
        # Split by common bullet point patterns
        lines = criteria_text.split('\n')
        current_criterion = ''
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts a new criterion
            if (line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')) or
                line[0].isdigit() and '.' in line[:3]):
                
                # Save previous criterion if exists
                if current_criterion:
                    criteria.append(current_criterion.strip())
                
                # Start new criterion (remove bullet point)
                current_criterion = line.lstrip('-•*0123456789. ')
            else:
                # Continue current criterion
                if current_criterion:
                    current_criterion += ' ' + line
                else:
                    current_criterion = line
        
        # Add the last criterion
        if current_criterion:
            criteria.append(current_criterion.strip())
        
        return [c for c in criteria if c and len(c.strip()) > 1]  # Filter out empty strings and single characters
    
    def _parse_locations(self, locations_data: List[Dict[str, Any]]) -> List[TrialLocation]:
        """Parse location data from API response"""
        locations = []
        
        for location_data in locations_data:
            facility = location_data.get('facility', '')
            city = location_data.get('city', '')
            state = location_data.get('state', '')
            country = location_data.get('country', '')
            zip_code = location_data.get('zip', '')
            
            # Skip locations with insufficient data
            if not facility and not city:
                continue
            
            location = TrialLocation(
                facility=facility,
                city=city,
                state=state,
                country=country,
                zip_code=zip_code if zip_code else None
            )
            
            locations.append(location)
        
        return locations
    
    def _parse_contact_info(self, contacts_locations: Dict[str, Any]) -> ContactInfo:
        """Parse contact information from API response"""
        overall_officials = contacts_locations.get('overallOfficials', [])
        central_contacts = contacts_locations.get('centralContacts', [])
        
        # Try to get contact info from central contacts first
        if central_contacts:
            contact = central_contacts[0]
            return ContactInfo(
                name=contact.get('name', ''),
                phone=contact.get('phone', ''),
                email=contact.get('email', '')
            )
        
        # Fall back to overall officials
        if overall_officials:
            official = overall_officials[0]
            return ContactInfo(
                name=official.get('name', ''),
                phone=None,
                email=None
            )
        
        return ContactInfo()
    
    def _parse_date(self, date_struct: Optional[Dict[str, Any]]) -> Optional[str]:
        """Parse date structure from API response"""
        if not date_struct:
            return None
        
        return date_struct.get('date', '')
    
    def _is_age_eligible(self, trial: RawTrialData, age: int) -> bool:
        """
        Check if a patient age is eligible for the trial
        
        Args:
            trial: RawTrialData object
            age: Patient age in years
            
        Returns:
            True if age is eligible, False otherwise
        """
        # This is a simplified age check
        # In a real implementation, you'd parse the eligibility criteria more thoroughly
        criteria_text = trial.eligibility_criteria.lower()
        
        # Look for age ranges in the criteria
        import re
        
        # Pattern to match age ranges like "18-65 years", "18 to 65", etc.
        age_patterns = [
            r'(\d+)\s*[-to]\s*(\d+)\s*years?',
            r'(\d+)\s*[-to]\s*(\d+)',
            r'age[s]?\s*(\d+)\s*[-to]\s*(\d+)',
            r'between\s*(\d+)\s*and\s*(\d+)',
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, criteria_text)
            for match in matches:
                min_age, max_age = int(match[0]), int(match[1])
                if min_age <= age <= max_age:
                    return True
                elif age < min_age or age > max_age:
                    return False
        
        # Look for minimum age requirements
        min_age_patterns = [
            r'(\d+)\s*years?\s*or\s*older',
            r'age\s*(\d+)\s*or\s*older',
            r'minimum\s*age\s*(\d+)',
            r'at\s*least\s*(\d+)\s*years?'
        ]
        
        for pattern in min_age_patterns:
            matches = re.findall(pattern, criteria_text)
            for match in matches:
                min_age = int(match)
                if age >= min_age:
                    return True
                else:
                    return False
        
        # If no specific age criteria found, assume eligible
        return True