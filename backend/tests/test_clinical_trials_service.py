"""
Unit tests for ClinicalTrials.gov API integration service
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.clinical_trials_service import (
    ClinicalTrialsService,
    ClinicalTrialsAPIError,
    RateLimitError,
    RawTrialData,
    TrialLocation,
    ContactInfo
)


class TestClinicalTrialsService:
    """Test cases for ClinicalTrialsService"""
    
    @pytest.fixture
    def service(self):
        """Create a ClinicalTrialsService instance for testing"""
        return ClinicalTrialsService()
    
    @pytest.fixture
    def mock_trial_response(self):
        """Mock API response with trial data"""
        return {
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCT12345678",
                            "briefTitle": "Test Diabetes Study"
                        },
                        "descriptionModule": {
                            "briefSummary": "A study testing new diabetes treatment",
                            "detailedDescription": "Detailed description of the diabetes study"
                        },
                        "eligibilityModule": {
                            "eligibilityCriteria": "Inclusion Criteria:\n- Age 18-65 years\n- Type 2 diabetes\n\nExclusion Criteria:\n- Pregnancy\n- Severe kidney disease"
                        },
                        "contactsLocationsModule": {
                            "locations": [
                                {
                                    "facility": "Test Medical Center",
                                    "city": "San Francisco",
                                    "state": "California",
                                    "country": "United States",
                                    "zip": "94102"
                                }
                            ],
                            "centralContacts": [
                                {
                                    "name": "Dr. Test Contact",
                                    "phone": "555-123-4567",
                                    "email": "test@example.com"
                                }
                            ]
                        },
                        "designModule": {
                            "studyType": "Interventional",
                            "phases": ["Phase 2"]
                        },
                        "statusModule": {
                            "overallStatus": "Recruiting",
                            "startDateStruct": {"date": "2024-01-01"},
                            "completionDateStruct": {"date": "2025-12-31"}
                        },
                        "sponsorCollaboratorsModule": {
                            "leadSponsor": {
                                "name": "Test Pharmaceutical Company"
                            }
                        },
                        "conditionsModule": {
                            "conditions": ["Type 2 Diabetes", "Diabetes Mellitus"]
                        },
                        "armsInterventionsModule": {
                            "interventions": [
                                {"name": "Test Drug A"},
                                {"name": "Placebo"}
                            ]
                        }
                    }
                }
            ]
        }
    
    @pytest.fixture
    def expected_trial_data(self):
        """Expected parsed trial data"""
        return RawTrialData(
            nct_id="NCT12345678",
            title="Test Diabetes Study",
            brief_summary="A study testing new diabetes treatment",
            detailed_description="Detailed description of the diabetes study",
            eligibility_criteria="Inclusion Criteria:\n- Age 18-65 years\n- Type 2 diabetes\n\nExclusion Criteria:\n- Pregnancy\n- Severe kidney disease",
            inclusion_criteria=["Age 18-65 years", "Type 2 diabetes"],
            exclusion_criteria=["Pregnancy", "Severe kidney disease"],
            locations=[
                TrialLocation(
                    facility="Test Medical Center",
                    city="San Francisco",
                    state="California",
                    country="United States",
                    zip_code="94102"
                )
            ],
            contact_info=ContactInfo(
                name="Dr. Test Contact",
                phone="555-123-4567",
                email="test@example.com"
            ),
            study_type="Interventional",
            phase="Phase 2",
            status="Recruiting",
            start_date="2024-01-01",
            completion_date="2025-12-31",
            sponsor="Test Pharmaceutical Company",
            conditions=["Type 2 Diabetes", "Diabetes Mellitus"],
            interventions=["Test Drug A", "Placebo"]
        )

    def test_init(self, service):
        """Test service initialization"""
        assert service.base_url == "https://clinicaltrials.gov/api/v2"
        assert service.min_request_interval == 1.0
        assert service.max_retries == 3
        assert service.retry_delay == 2
        assert 'User-Agent' in service.session.headers
        assert 'Accept' in service.session.headers

    def test_rate_limiting_basic(self, service):
        """Test basic rate limiting setup"""
        # Just verify the rate limiting attributes are set correctly
        assert service.min_request_interval == 1.0
        assert service.max_retries == 3
        assert service.retry_delay == 2

    @patch('services.clinical_trials_service.ClinicalTrialsService._handle_rate_limiting')
    def test_make_request_success(self, mock_rate_limit, service):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        
        with patch.object(service.session, 'get', return_value=mock_response):
            result = service._make_request('studies', {'param': 'value'})
            
            assert result == {"test": "data"}
            mock_rate_limit.assert_called_once()

    @patch('services.clinical_trials_service.ClinicalTrialsService._handle_rate_limiting')
    def test_make_request_404_error(self, mock_rate_limit, service):
        """Test 404 error handling"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.content = b'{"error": "Not found"}'
        
        with patch.object(service.session, 'get', return_value=mock_response):
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                service._make_request('studies', {})
            
            assert exc_info.value.status_code == 404
            assert "Endpoint not found" in str(exc_info.value)

    @patch('services.clinical_trials_service.ClinicalTrialsService._handle_rate_limiting')
    def test_make_request_rate_limit_error(self, mock_rate_limit, service):
        """Test rate limit error handling"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        
        with patch.object(service.session, 'get', return_value=mock_response):
            with pytest.raises(RateLimitError) as exc_info:
                service._make_request('studies', {})
            
            assert exc_info.value.retry_after == 60

    @patch('services.clinical_trials_service.ClinicalTrialsService._handle_rate_limiting')
    def test_make_request_server_error(self, mock_rate_limit, service):
        """Test server error handling"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b'{"error": "Server error"}'
        mock_response.json.return_value = {"error": "Server error"}
        
        with patch.object(service.session, 'get', return_value=mock_response):
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                service._make_request('studies', {})
            
            assert exc_info.value.status_code == 500

    @patch('services.clinical_trials_service.ClinicalTrialsService._handle_rate_limiting')
    def test_make_request_timeout_error(self, mock_rate_limit, service):
        """Test timeout error handling"""
        with patch.object(service.session, 'get', side_effect=Timeout()):
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                service._make_request('studies', {})
            
            assert "timeout" in str(exc_info.value).lower()

    @patch('services.clinical_trials_service.ClinicalTrialsService._handle_rate_limiting')
    def test_make_request_connection_error(self, mock_rate_limit, service):
        """Test connection error handling"""
        with patch.object(service.session, 'get', side_effect=ConnectionError()):
            with pytest.raises(ClinicalTrialsAPIError) as exc_info:
                service._make_request('studies', {})
            
            assert "connection error" in str(exc_info.value).lower()

    def test_search_trials_success(self, service, mock_trial_response):
        """Test successful trial search"""
        with patch.object(service, '_make_request', return_value=mock_trial_response):
            trials = service.search_trials(
                conditions=["diabetes"],
                location={"city": "San Francisco", "state": "CA"},
                age=45,
                max_results=10
            )
            
            assert len(trials) == 1
            trial = trials[0]
            assert trial.nct_id == "NCT12345678"
            assert trial.title == "Test Diabetes Study"
            assert len(trial.locations) == 1
            assert trial.locations[0].city == "San Francisco"

    def test_search_trials_with_conditions(self, service, mock_trial_response):
        """Test search with multiple conditions"""
        with patch.object(service, '_make_request', return_value=mock_trial_response) as mock_request:
            service.search_trials(conditions=["diabetes", "hypertension"])
            
            # Verify the query parameters
            call_args = mock_request.call_args
            params = call_args[0][1]  # Second argument (params)
            
            assert 'query.cond' in params
            assert '"diabetes" OR "hypertension"' == params['query.cond']

    def test_search_trials_with_location(self, service, mock_trial_response):
        """Test search with location parameters"""
        with patch.object(service, '_make_request', return_value=mock_trial_response) as mock_request:
            service.search_trials(location={"city": "Boston", "state": "MA", "country": "US"})
            
            call_args = mock_request.call_args
            params = call_args[0][1]
            
            assert 'query.locn' in params
            assert "Boston, MA, US" == params['query.locn']

    def test_get_trial_by_nct_id_success(self, service, mock_trial_response):
        """Test getting trial by NCT ID"""
        with patch.object(service, '_make_request', return_value=mock_trial_response):
            trial = service.get_trial_by_nct_id("NCT12345678")
            
            assert trial is not None
            assert trial.nct_id == "NCT12345678"
            assert trial.title == "Test Diabetes Study"

    def test_get_trial_by_nct_id_not_found(self, service):
        """Test getting trial by NCT ID when not found"""
        with patch.object(service, '_make_request', return_value={"studies": []}):
            trial = service.get_trial_by_nct_id("NCT99999999")
            
            assert trial is None

    def test_parse_trial_data(self, service, mock_trial_response, expected_trial_data):
        """Test parsing of trial data"""
        study_data = mock_trial_response["studies"][0]
        parsed_trial = service._parse_trial_data(study_data)
        
        assert parsed_trial.nct_id == expected_trial_data.nct_id
        assert parsed_trial.title == expected_trial_data.title
        assert parsed_trial.brief_summary == expected_trial_data.brief_summary
        assert parsed_trial.study_type == expected_trial_data.study_type
        assert parsed_trial.phase == expected_trial_data.phase
        assert parsed_trial.status == expected_trial_data.status
        assert parsed_trial.sponsor == expected_trial_data.sponsor
        assert parsed_trial.conditions == expected_trial_data.conditions
        assert parsed_trial.interventions == expected_trial_data.interventions
        
        # Check location parsing
        assert len(parsed_trial.locations) == 1
        location = parsed_trial.locations[0]
        expected_location = expected_trial_data.locations[0]
        assert location.facility == expected_location.facility
        assert location.city == expected_location.city
        assert location.state == expected_location.state
        assert location.country == expected_location.country
        assert location.zip_code == expected_location.zip_code
        
        # Check contact info parsing
        contact = parsed_trial.contact_info
        expected_contact = expected_trial_data.contact_info
        assert contact.name == expected_contact.name
        assert contact.phone == expected_contact.phone
        assert contact.email == expected_contact.email

    def test_parse_eligibility_criteria(self, service):
        """Test parsing of eligibility criteria"""
        criteria_text = """
        Inclusion Criteria:
        - Age 18-65 years
        - Diagnosed with Type 2 diabetes
        - BMI between 25-40
        
        Exclusion Criteria:
        - Pregnancy or nursing
        - Severe kidney disease
        - History of heart attack
        """
        
        inclusion, exclusion = service._parse_eligibility_criteria(criteria_text)
        
        assert len(inclusion) == 3
        assert "age 18-65 years" in inclusion
        assert "diagnosed with type 2 diabetes" in inclusion
        assert "bmi between 25-40" in inclusion
        
        assert len(exclusion) == 3
        assert "pregnancy or nursing" in exclusion
        assert "severe kidney disease" in exclusion
        assert "history of heart attack" in exclusion

    def test_parse_eligibility_criteria_numbered(self, service):
        """Test parsing of numbered eligibility criteria"""
        criteria_text = """
        Inclusion Criteria:
        1. Age 18 to 65 years
        2. Type 2 diabetes diagnosis
        3. Stable medication regimen
        
        Exclusion Criteria:
        1. Pregnancy
        2. Severe renal impairment
        """
        
        inclusion, exclusion = service._parse_eligibility_criteria(criteria_text)
        
        assert len(inclusion) == 3
        assert "Age 18 to 65 years" in inclusion
        assert "Type 2 diabetes diagnosis" in inclusion
        assert "Stable medication regimen" in inclusion
        
        assert len(exclusion) == 2
        assert "Pregnancy" in exclusion
        assert "Severe renal impairment" in exclusion

    def test_is_age_eligible(self, service):
        """Test age eligibility checking"""
        # Create a mock trial with age criteria
        trial = RawTrialData(
            nct_id="NCT12345678",
            title="Test Study",
            brief_summary="",
            detailed_description="",
            eligibility_criteria="Age 18-65 years old",
            inclusion_criteria=[],
            exclusion_criteria=[],
            locations=[],
            contact_info=ContactInfo(),
            study_type="",
            phase=None,
            status="",
            start_date=None,
            completion_date=None,
            sponsor="",
            conditions=[],
            interventions=[]
        )
        
        # Test ages within range
        assert service._is_age_eligible(trial, 25) == True
        assert service._is_age_eligible(trial, 18) == True
        assert service._is_age_eligible(trial, 65) == True
        
        # Test ages outside range
        assert service._is_age_eligible(trial, 17) == False
        assert service._is_age_eligible(trial, 66) == False

    def test_is_age_eligible_minimum_age(self, service):
        """Test age eligibility with minimum age criteria"""
        trial = RawTrialData(
            nct_id="NCT12345678",
            title="Test Study",
            brief_summary="",
            detailed_description="",
            eligibility_criteria="18 years or older",
            inclusion_criteria=[],
            exclusion_criteria=[],
            locations=[],
            contact_info=ContactInfo(),
            study_type="",
            phase=None,
            status="",
            start_date=None,
            completion_date=None,
            sponsor="",
            conditions=[],
            interventions=[]
        )
        
        assert service._is_age_eligible(trial, 18) == True
        assert service._is_age_eligible(trial, 25) == True
        assert service._is_age_eligible(trial, 17) == False

    def test_search_trials_api_error(self, service):
        """Test search trials with API error"""
        with patch.object(service, '_make_request', side_effect=ClinicalTrialsAPIError("API Error")):
            with pytest.raises(ClinicalTrialsAPIError):
                service.search_trials(conditions=["diabetes"])

    def test_search_trials_parsing_error(self, service):
        """Test search trials with parsing error in one trial"""
        # Mock response with one good trial and one bad trial
        mock_response = {
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCT12345678",
                            "briefTitle": "Good Study"
                        },
                        "descriptionModule": {
                            "briefSummary": "A good study"
                        },
                        "eligibilityModule": {},
                        "contactsLocationsModule": {},
                        "designModule": {},
                        "statusModule": {},
                        "sponsorCollaboratorsModule": {},
                        "conditionsModule": {},
                        "armsInterventionsModule": {}
                    }
                },
                {
                    "protocolSection": None  # This will cause parsing error
                }
            ]
        }
        
        with patch.object(service, '_make_request', return_value=mock_response):
            trials = service.search_trials(conditions=["diabetes"])
            
            # Should return only the successfully parsed trial
            assert len(trials) == 1
            assert trials[0].nct_id == "NCT12345678"