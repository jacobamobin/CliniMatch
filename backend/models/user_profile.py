"""
User Profile Data Models for CliniMatch

These models define the structure for user input data used in trial matching.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json


@dataclass
class LocationData:
    """Data class for user location information"""
    city: str
    state: str
    country: str = "United States"
    zip_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'zip_code': self.zip_code
        }


@dataclass
class LifestyleData:
    """Data class for user lifestyle information"""
    smoking: bool = False
    drinking: str = "never"  # "never", "occasional", "regular"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'smoking': self.smoking,
            'drinking': self.drinking
        }


@dataclass
class UserProfile:
    """Data class for complete user profile used in trial matching"""
    age: int
    conditions: List[str]
    medications: List[str]
    location: LocationData
    lifestyle: LifestyleData
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'age': self.age,
            'conditions': self.conditions,
            'medications': self.medications,
            'location': self.location.to_dict(),
            'lifestyle': self.lifestyle.to_dict()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), sort_keys=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from dictionary"""
        location_data = data.get('location', {})
        lifestyle_data = data.get('lifestyle', {})
        
        return cls(
            age=data['age'],
            conditions=data.get('conditions', []),
            medications=data.get('medications', []),
            location=LocationData(
                city=location_data.get('city', ''),
                state=location_data.get('state', ''),
                country=location_data.get('country', 'United States'),
                zip_code=location_data.get('zip_code')
            ),
            lifestyle=LifestyleData(
                smoking=lifestyle_data.get('smoking', False),
                drinking=lifestyle_data.get('drinking', 'never')
            )
        )
    
    def get_search_params(self) -> Dict[str, Any]:
        """Get parameters suitable for ClinicalTrials.gov API search"""
        return {
            'conditions': self.conditions,
            'location': {
                'city': self.location.city,
                'state': self.location.state,
                'country': self.location.country
            },
            'age': self.age
        }