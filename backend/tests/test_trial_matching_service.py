"""
Tests for TrialMatchingService

These tests verify the core trial matching workflow and integration.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from backend.services.trial_matching_service import TrialMatchingService, TrialMatchingError
from backend.models.user_profile import UserProfile, LocationData, LifestyleData
from backend.models.trial_match import TrialMatch, TrialLocation, ContactInfo
from backend.services.clinical_trials_service import RawTrialData
from backend.services.gemini_translation_service import TrialTranslation


class TestTrialMatchingService:
    """Test cases for TrialMatchingService"""
    
    @pytest.fixture
    def sample_user_profile(self):
        """Create a sample user profile for testing"""
        return UserProfile(
            age=45,
            conditions=["diabetes", "hypertension"],
            medications=["metformin", "lisinopril"],
            location=LocationData(
                city="San Francisco",
                state="CA",
                country="United States",
                zip_code="94102"
            ),
            lifestyle=LifestyleData(
                smoking=False,
                drinking="occasional"
            )
        )
    
    @pytest.fixture
    def sample_raw_trial(self):
        """Create a sample raw trial data for testing"""
        return RawTrialData(
            nct_id="NCT12345678",
            title="Diabetes Treatment Study",
            brief_summary="A study testing a new diabetes medication",
            detailed_description="Detailed description of the diabetes study",
            eligibility_criteria="Adults 18-65 with Type 2 diabetes",
            inclusion_criteria=["Adults 18-65 years", "Type 2 diabetes diagnosis"],
            exclusion_criteria=["Pregnancy", "Severe kidney disease"],
            locations=[],
            contact_info=Mock(),
            study_type="Interventional",
            phase="Phase 2",
            status="Recruiting",
            start_date="2024-01-01",
            completion_date="2025-12-31",
            sponsor="Test Sponsor",
            conditions=["Diabetes"],
            interventions=["Test Drug"]
        )
    
    @pytest.fixture
    def sample_translation(self):
        """Create a sample AI translation for testing"""
        return TrialTranslation(
            simplified_description="This study tests a new diabetes medication to see if it works better than current treatments.",
            eligibility_simplified="Adults between 18-65 years old with Type 2 diabetes",
            time_commitment="6 visits over 3 months",
            key_benefits="Free medication and regular health monitoring",
            compensation_explanation="$100 per visit"
        )
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        clinical_service = Mock()
        gemini_service = Mock()
        cache_service = Mock()
        
        return clinical_service, gemini_service, cache_service
    
    def test_generate_search_key(self, sample_user_profile):
        """Test search key generation for cache lookups"""
        service = TrialMatchingService()
        
        # Generate search key
        search_key = service.generate_search_key(sample_user_profile)
        
        # Verify it's a valid MD5 hash
        assert isinstance(search_key, str)
        assert len(search_key) == 32
        assert all(c in '0123456789abcdef' for c in search_key)
        
        # Verify consistency - same profile should generate same key
        search_key2 = service.generate_search_key(sample_user_profile)
        assert search_key == search_key2
    
    def test_generate_search_key_different_profiles(self, sample_user_profile):
        """Test that different profiles generate different search keys"""
        service = TrialMatchingService()
        
        # Original profile
        key1 = service.generate_search_key(sample_user_profile)
        
        # Modified profile
        modified_profile = UserProfile(
            age=50,  # Different age
            conditions=sample_user_profile.conditions,
            medications=sample_user_profile.medications,
            location=sample_user_profile.location,
            lifestyle=sample_user_profile.lifestyle
        )
        key2 = service.generate_search_key(modified_profile)
        
        # Keys should be different
        assert key1 != key2
    
    def test_age_range_grouping(self):
        """Test age range grouping for cache efficiency"""
        service = TrialMatchingService()
        
        # Test different age ranges
        assert service._get_age_range(16) == "under_18"
        assert service._get_age_range(25) == "18_29"
        assert service._get_age_range(35) == "30_49"
        assert service._get_age_range(55) == "50_64"
        assert service._get_age_range(70) == "65_plus"
    
    @patch('backend.services.trial_matching_service.get_cache_service')
    def test_find_matching_trials_with_cache_hit(self, mock_get_cache_service, 
                                                sample_user_profile, mock_services):
        """Test trial matching with cache hit"""
        clinical_service, gemini_service, cache_service = mock_services
        mock_get_cache_service.return_value = cache_service
        
        # Mock cached data
        cached_data = {
            'matches': [{
                'nctId': 'NCT12345678',
                'title': 'Test Trial',
                'originalDescription': 'Original description',
                'simplifiedDescription': 'Simple description',
                'locations': [],
                'eligibilityCriteria': 'Test criteria',
                'eligibilitySimplified': 'Simple criteria',
                'compensation': None,
                'compensationExplanation': None,
                'timeCommitment': '6 visits',
                'keyBenefits': 'Free treatment',
                'contactInfo': None,
                'studyType': 'Interventional',
                'phase': 'Phase 2',
                'status': 'Recruiting',
                'sponsor': 'Test Sponsor',
                'conditions': ['Diabetes'],
                'interventions': ['Test Drug']
            }],
            'total_found': 1,
            'ai_translation_success_rate': 1.0
        }
        cache_service.get_cached_trials.return_value = cached_data
        
        # Create service with mocked dependencies
        service = TrialMatchingService(
            clinical_trials_service=clinical_service,
            gemini_service=gemini_service,
            cache_service=cache_service
        )
        
        # Execute matching
        result = service.find_matching_trials(sample_user_profile)
        
        # Verify results
        assert result.cached is True
        assert result.total_found == 1
        assert len(result.matches) == 1
        assert result.matches[0].nct_id == 'NCT12345678'
        
        # Verify cache was checked but API wasn't called
        cache_service.get_cached_trials.assert_called_once()
        clinical_service.search_trials.assert_not_called()
    
    @patch('backend.services.trial_matching_service.get_cache_service')
    def test_find_matching_trials_with_cache_miss(self, mock_get_cache_service,
                                                 sample_user_profile, sample_raw_trial,
                                                 sample_translation, mock_services):
        """Test trial matching with cache miss"""
        clinical_service, gemini_service, cache_service = mock_services
        mock_get_cache_service.return_value = cache_service
        
        # Mock cache miss
        cache_service.get_cached_trials.return_value = None
        
        # Mock API responses
        clinical_service.search_trials.return_value = [sample_raw_trial]
        gemini_service.translate_with_fallback.return_value = sample_translation
        
        # Mock successful caching
        cache_service.cache_trials.return_value = True
        
        # Create service with mocked dependencies
        service = TrialMatchingService(
            clinical_trials_service=clinical_service,
            gemini_service=gemini_service,
            cache_service=cache_service
        )
        
        # Execute matching
        result = service.find_matching_trials(sample_user_profile)
        
        # Verify results
        assert result.cached is False
        assert result.total_found == 1
        assert len(result.matches) == 1
        assert result.matches[0].nct_id == 'NCT12345678'
        assert result.matches[0].simplified_description == sample_translation.simplified_description
        
        # Verify services were called
        cache_service.get_cached_trials.assert_called_once()
        clinical_service.search_trials.assert_called_once()
        gemini_service.translate_with_fallback.assert_called_once()
        cache_service.cache_trials.assert_called_once()
    
    @patch('backend.services.trial_matching_service.get_cache_service')
    def test_find_matching_trials_no_results(self, mock_get_cache_service,
                                           sample_user_profile, mock_services):
        """Test trial matching when no trials are found"""
        clinical_service, gemini_service, cache_service = mock_services
        mock_get_cache_service.return_value = cache_service
        
        # Mock cache miss and no API results
        cache_service.get_cached_trials.return_value = None
        clinical_service.search_trials.return_value = []
        
        # Create service with mocked dependencies
        service = TrialMatchingService(
            clinical_trials_service=clinical_service,
            gemini_service=gemini_service,
            cache_service=cache_service
        )
        
        # Execute matching
        result = service.find_matching_trials(sample_user_profile)
        
        # Verify results
        assert result.cached is False
        assert result.total_found == 0
        assert len(result.matches) == 0
        assert result.ai_translation_success_rate == 0.0
    
    @patch('backend.services.trial_matching_service.get_cache_service')
    def test_find_matching_trials_api_error(self, mock_get_cache_service,
                                          sample_user_profile, mock_services):
        """Test trial matching when API fails"""
        clinical_service, gemini_service, cache_service = mock_services
        mock_get_cache_service.return_value = cache_service
        
        # Mock cache miss and API error
        cache_service.get_cached_trials.return_value = None
        clinical_service.search_trials.side_effect = Exception("API Error")
        
        # Create service with mocked dependencies
        service = TrialMatchingService(
            clinical_trials_service=clinical_service,
            gemini_service=gemini_service,
            cache_service=cache_service
        )
        
        # Execute matching and expect error
        with pytest.raises(TrialMatchingError) as exc_info:
            service.find_matching_trials(sample_user_profile)
        
        assert "Failed to find matching trials" in str(exc_info.value)
    
    def test_health_check(self, mock_services):
        """Test health check functionality"""
        clinical_service, gemini_service, cache_service = mock_services
        
        # Mock service health checks
        gemini_service.health_check.return_value = {
            'status': 'healthy',
            'api_accessible': True
        }
        cache_service.get_cache_stats.return_value = {
            'total_entries': 10,
            'active_entries': 8
        }
        
        # Create service with mocked dependencies
        service = TrialMatchingService(
            clinical_trials_service=clinical_service,
            gemini_service=gemini_service,
            cache_service=cache_service
        )
        
        # Execute health check
        health_status = service.health_check()
        
        # Verify results
        assert health_status['status'] == 'healthy'
        assert 'services' in health_status
        assert 'clinical_trials_api' in health_status['services']
        assert 'gemini_ai' in health_status['services']
        assert 'cache' in health_status['services']
        assert 'timestamp' in health_status
    
    def test_user_profile_to_search_params(self, sample_user_profile):
        """Test conversion of user profile to search parameters"""
        search_params = sample_user_profile.get_search_params()
        
        expected_params = {
            'conditions': ['diabetes', 'hypertension'],
            'location': {
                'city': 'San Francisco',
                'state': 'CA',
                'country': 'United States'
            },
            'age': 45
        }
        
        assert search_params == expected_params
    
    def test_trial_match_serialization(self):
        """Test TrialMatch serialization to dictionary"""
        trial_match = TrialMatch(
            nct_id="NCT12345678",
            title="Test Trial",
            original_description="Original description",
            simplified_description="Simple description",
            locations=[],
            eligibility_criteria="Test criteria",
            eligibility_simplified="Simple criteria"
        )
        
        trial_dict = trial_match.to_dict()
        
        # Verify required fields
        assert trial_dict['nctId'] == "NCT12345678"
        assert trial_dict['title'] == "Test Trial"
        assert trial_dict['simplifiedDescription'] == "Simple description"
        assert trial_dict['eligibilitySimplified'] == "Simple criteria"
        assert isinstance(trial_dict['locations'], list)