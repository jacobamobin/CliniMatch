"""
Tests for Flask API Routes

These tests verify the API endpoints work correctly with proper validation and error handling.
"""

import pytest
import json
from unittest.mock import Mock, patch
from backend.app import create_app
from backend.models.user_profile import UserProfile, LocationData, LifestyleData
from backend.models.trial_match import TrialMatch, MatchingResult


class TestAPIRoutes:
    """Test cases for API routes"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "age": 45,
            "conditions": ["diabetes", "hypertension"],
            "medications": ["metformin", "lisinopril"],
            "location": {
                "city": "San Francisco",
                "state": "CA",
                "country": "United States",
                "zip_code": "94102"
            },
            "lifestyle": {
                "smoking": False,
                "drinking": "occasional"
            }
        }
    
    @pytest.fixture
    def sample_trial_match(self):
        """Sample trial match for testing"""
        return TrialMatch(
            nct_id="NCT12345678",
            title="Diabetes Treatment Study",
            original_description="Original description",
            simplified_description="Simple description",
            locations=[],
            eligibility_criteria="Test criteria",
            eligibility_simplified="Simple criteria",
            compensation=None,
            compensation_explanation=None,
            time_commitment="6 visits",
            key_benefits="Free treatment",
            contact_info=None,
            study_type="Interventional",
            phase="Phase 2",
            status="Recruiting",
            sponsor="Test Sponsor",
            conditions=["Diabetes"],
            interventions=["Test Drug"]
        )
    
    @pytest.fixture
    def sample_matching_result(self, sample_trial_match):
        """Sample matching result for testing"""
        return MatchingResult(
            matches=[sample_trial_match],
            total_found=1,
            processing_time=0.5,
            search_params={},
            cached=False,
            ai_translation_success_rate=1.0
        )
    
    def test_health_check_success(self, client):
        """Test health check endpoint success"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            mock_service.health_check.return_value = {
                'status': 'healthy',
                'services': {
                    'clinical_trials_api': {'status': 'healthy'},
                    'gemini_ai': {'status': 'healthy'},
                    'cache': {'status': 'healthy'}
                },
                'timestamp': 1234567890
            }
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert data['service'] == 'clinimatch-backend'
            assert 'services' in data
            assert 'timestamp' in data
    
    def test_health_check_failure(self, client):
        """Test health check endpoint failure"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            mock_service.health_check.side_effect = Exception("Service unavailable")
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/health')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'unhealthy'
            assert 'error' in data
    
    def test_match_trials_success(self, client, sample_user_data, sample_matching_result):
        """Test successful trial matching"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            # Ensure the mock returns a proper MatchingResult object
            mock_service.find_matching_trials.return_value = sample_matching_result
            mock_get_service.return_value = mock_service
            
            response = client.post(
                '/api/match',
                data=json.dumps(sample_user_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'data' in data
            assert 'message' in data
            assert data['data']['totalFound'] == 1
    
    def test_match_trials_invalid_content_type(self, client, sample_user_data):
        """Test trial matching with invalid content type"""
        response = client.post(
            '/api/match',
            data=json.dumps(sample_user_data),
            content_type='text/plain'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Content-Type must be application/json' in data['error']
    
    def test_match_trials_missing_body(self, client):
        """Test trial matching with missing request body"""
        response = client.post('/api/match')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Request body is required' in data['error']
    
    def test_match_trials_validation_error(self, client):
        """Test trial matching with validation errors"""
        invalid_data = {
            "age": -5,  # Invalid age
            "conditions": [],  # Empty conditions
            "location": {
                "city": "",  # Empty city
                "state": "CA"
            }
        }
        
        response = client.post(
            '/api/match',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Validation failed' in data['error']
        assert 'details' in data
    
    def test_match_trials_service_error(self, client, sample_user_data):
        """Test trial matching when service fails"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            from backend.services.trial_matching_service import TrialMatchingError
            mock_service = Mock()
            mock_service.find_matching_trials.side_effect = TrialMatchingError("API Error")
            mock_get_service.return_value = mock_service
            
            response = client.post(
                '/api/match',
                data=json.dumps(sample_user_data),
                content_type='application/json'
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Trial matching failed' in data['error']
    
    def test_get_trial_by_id_success(self, client, sample_trial_match):
        """Test successful trial retrieval by NCT ID"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_trial_by_id.return_value = sample_trial_match
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/trial/NCT12345678')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'data' in data
            assert data['data']['nctId'] == 'NCT12345678'
    
    def test_get_trial_by_id_invalid_format(self, client):
        """Test trial retrieval with invalid NCT ID format"""
        response = client.get('/api/trial/INVALID123')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid NCT ID format' in data['error']
    
    def test_get_trial_by_id_not_found(self, client):
        """Test trial retrieval when trial not found"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            mock_service.get_trial_by_id.return_value = None
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/trial/NCT99999999')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Trial not found' in data['error']
    
    def test_get_trial_by_id_service_error(self, client):
        """Test trial retrieval when service fails"""
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            from backend.services.trial_matching_service import TrialMatchingError
            mock_service = Mock()
            mock_service.get_trial_by_id.side_effect = TrialMatchingError("Service Error")
            mock_get_service.return_value = mock_service
            
            response = client.get('/api/trial/NCT12345678')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Failed to fetch trial' in data['error']
    
    def test_404_error_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Endpoint not found' in data['error']
    
    def test_405_error_handler(self, client):
        """Test 405 error handler"""
        response = client.put('/api/health')  # PUT not allowed on health endpoint
        
        assert response.status_code == 405
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Method not allowed' in data['error']
    
    def test_cached_response_indicator(self, client, sample_user_data, sample_matching_result):
        """Test that cached responses are properly indicated"""
        # Set cached flag to True
        sample_matching_result.cached = True
        
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_matching_trials.return_value = sample_matching_result
            mock_get_service.return_value = mock_service
            
            response = client.post(
                '/api/match',
                data=json.dumps(sample_user_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert '(from cache)' in data['message']
    
    def test_user_profile_validation_edge_cases(self, client):
        """Test edge cases in user profile validation"""
        # Test with minimum required fields
        minimal_data = {
            "age": 25,
            "conditions": ["diabetes"],
            "location": {
                "city": "New York",
                "state": "NY"
            }
        }
        
        with patch('backend.api.routes.get_trial_matching_service') as mock_get_service:
            mock_service = Mock()
            mock_service.find_matching_trials.return_value = Mock(
                to_dict=lambda: {"totalFound": 0, "matches": []},
                total_found=0,
                processing_time=0.1,
                cached=False,
                ai_translation_success_rate=0.0
            )
            mock_get_service.return_value = mock_service
            
            response = client.post(
                '/api/match',
                data=json.dumps(minimal_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True 