"""
Trial Match Data Models for CliniMatch

These models define the structure for processed trial match results.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json


@dataclass
class TrialLocation:
    """Data class for trial location information"""
    facility: str
    city: str
    state: str
    country: str
    zip_code: Optional[str] = None
    coordinates: Optional[tuple] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'facility': self.facility,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'zip_code': self.zip_code,
            'coordinates': list(self.coordinates) if self.coordinates else None
        }


@dataclass
class ContactInfo:
    """Data class for trial contact information"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email
        }


@dataclass
class TrialMatch:
    """Data class for processed trial match results"""
    nct_id: str
    title: str
    original_description: str
    simplified_description: str
    locations: List[TrialLocation]
    eligibility_criteria: str
    eligibility_simplified: str
    compensation: Optional[str] = None
    compensation_explanation: Optional[str] = None
    time_commitment: str = "Not specified"
    key_benefits: str = "Not specified"
    contact_info: Optional[ContactInfo] = None
    study_type: str = ""
    phase: Optional[str] = None
    status: str = ""
    sponsor: str = ""
    conditions: List[str] = None
    interventions: List[str] = None
    
    def __post_init__(self):
        """Initialize default values after creation"""
        if self.conditions is None:
            self.conditions = []
        if self.interventions is None:
            self.interventions = []
        if self.contact_info is None:
            self.contact_info = ContactInfo()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'nctId': self.nct_id,
            'title': self.title,
            'originalDescription': self.original_description,
            'simplifiedDescription': self.simplified_description,
            'locations': [loc.to_dict() for loc in self.locations],
            'eligibilityCriteria': self.eligibility_criteria,
            'eligibilitySimplified': self.eligibility_simplified,
            'compensation': self.compensation,
            'compensationExplanation': self.compensation_explanation,
            'timeCommitment': self.time_commitment,
            'keyBenefits': self.key_benefits,
            'contactInfo': self.contact_info.to_dict() if self.contact_info else None,
            'studyType': self.study_type,
            'phase': self.phase,
            'status': self.status,
            'sponsor': self.sponsor,
            'conditions': self.conditions,
            'interventions': self.interventions
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    def get_primary_location(self) -> Optional[TrialLocation]:
        """Get the primary (first) location for the trial"""
        return self.locations[0] if self.locations else None


@dataclass
class MatchingResult:
    """Data class for complete matching results"""
    matches: List[TrialMatch]
    total_found: int
    processing_time: float
    search_params: Dict[str, Any]
    cached: bool = False
    ai_translation_success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'matches': [match.to_dict() for match in self.matches],
            'totalFound': self.total_found,
            'processingTime': self.processing_time,
            'cached': self.cached,
            'aiTranslationSuccessRate': self.ai_translation_success_rate
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())