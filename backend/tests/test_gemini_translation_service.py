"""
Unit tests for Gemini Translation Service
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import os

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.gemini_translation_service import GeminiTranslationService, TrialTranslation


class TestGeminiTranslationService:
    """Test cases for GeminiTranslationService"""
    
    @pytest.fixture
    def mock_api_key(self):
        """Fixture providing a mock API key"""
        return "test_api_key_12345"
    
    @pytest.fixture
    def service(self, mock_api_key):
        """Fixture providing a GeminiTranslationService instance"""
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel'):
            return GeminiTranslationService(api_key=mock_api_key)
    
    @pytest.fixture
    def sample_trial_data(self):
        """Fixture providing sample clinical trial data"""
        return {
            "title": "Phase II Study of Novel Diabetes Treatment",
            "criteria": "Inclusion: Adults aged 18-65 with Type 2 diabetes mellitus, HbA1c >7.0%, BMI 25-40 kg/m². Exclusion: Pregnancy, severe renal impairment (eGFR <30), active malignancy.",
            "description": "This is a randomized, double-blind, placebo-controlled study to evaluate the efficacy and safety of XYZ-123 in patients with inadequately controlled Type 2 diabetes mellitus. Primary endpoint is change in HbA1c from baseline to week 24.",
            "compensation": "$150 per visit, up to $900 total"
        }
    
    @pytest.fixture
    def sample_ai_response(self):
        """Fixture providing a sample AI response"""
        return {
            "simplifiedDescription": "This study tests a new diabetes medication to see if it works better than current treatments. Participants will take either the new medicine or a placebo for 6 months.",
            "eligibilitySimplified": "You can join if you're 18-65 years old, have Type 2 diabetes that isn't well controlled, and are overweight but not extremely obese.",
            "timeCommitment": "About 6-8 visits over 6 months, each visit takes 2-3 hours",
            "keyBenefits": "Free diabetes monitoring, potential access to new treatment, and compensation for your time",
            "compensationExplanation": "You'll receive $150 for each visit you complete, which could total up to $900"
        }
    
    def test_init_with_api_key(self, mock_api_key):
        """Test service initialization with provided API key"""
        with patch('google.generativeai.configure') as mock_configure, \
             patch('google.generativeai.GenerativeModel') as mock_model:
            
            service = GeminiTranslationService(api_key=mock_api_key)
            
            mock_configure.assert_called_once_with(api_key=mock_api_key)
            mock_model.assert_called_once_with('gemini-pro')
            assert service.api_key == mock_api_key
    
    def test_init_with_env_api_key(self, mock_api_key):
        """Test service initialization with API key from environment"""
        with patch.dict(os.environ, {'GEMINI_API_KEY': mock_api_key}), \
             patch('google.generativeai.configure') as mock_configure, \
             patch('google.generativeai.GenerativeModel'):
            
            service = GeminiTranslationService()
            
            mock_configure.assert_called_once_with(api_key=mock_api_key)
            assert service.api_key == mock_api_key
    
    def test_init_without_api_key(self):
        """Test service initialization fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
                GeminiTranslationService()
    
    def test_create_translation_prompt(self, service, sample_trial_data):
        """Test prompt creation for translation"""
        prompt = service._create_translation_prompt(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"],
            sample_trial_data["compensation"]
        )
        
        assert sample_trial_data["title"] in prompt
        assert sample_trial_data["criteria"] in prompt
        assert sample_trial_data["description"] in prompt
        assert sample_trial_data["compensation"] in prompt
        assert "JSON object" in prompt
        assert "simplifiedDescription" in prompt
        assert "eligibilitySimplified" in prompt
    
    def test_create_translation_prompt_without_compensation(self, service, sample_trial_data):
        """Test prompt creation without compensation information"""
        prompt = service._create_translation_prompt(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"]
        )
        
        assert sample_trial_data["title"] in prompt
        assert sample_trial_data["criteria"] in prompt
        assert sample_trial_data["description"] in prompt
        assert "Compensation:" not in prompt
    
    def test_translate_trial_info_success(self, service, sample_trial_data, sample_ai_response):
        """Test successful trial information translation"""
        # Mock the AI response
        mock_response = Mock()
        mock_response.text = json.dumps(sample_ai_response)
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.translate_trial_info(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"],
            sample_trial_data["compensation"]
        )
        
        assert result is not None
        assert isinstance(result, TrialTranslation)
        assert result.simplified_description == sample_ai_response["simplifiedDescription"]
        assert result.eligibility_simplified == sample_ai_response["eligibilitySimplified"]
        assert result.time_commitment == sample_ai_response["timeCommitment"]
        assert result.key_benefits == sample_ai_response["keyBenefits"]
        assert result.compensation_explanation == sample_ai_response["compensationExplanation"]
    
    def test_translate_trial_info_empty_response(self, service, sample_trial_data):
        """Test handling of empty AI response"""
        mock_response = Mock()
        mock_response.text = ""
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.translate_trial_info(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"]
        )
        
        assert result is None
    
    def test_translate_trial_info_invalid_json(self, service, sample_trial_data):
        """Test handling of invalid JSON response"""
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.translate_trial_info(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"]
        )
        
        assert result is None
    
    def test_translate_trial_info_missing_fields(self, service, sample_trial_data):
        """Test handling of response with missing required fields"""
        incomplete_response = {
            "simplifiedDescription": "Test description",
            # Missing other required fields
        }
        
        mock_response = Mock()
        mock_response.text = json.dumps(incomplete_response)
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.translate_trial_info(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"]
        )
        
        assert result is None
    
    def test_translate_trial_info_api_exception(self, service, sample_trial_data):
        """Test handling of API exceptions"""
        service.model.generate_content = Mock(side_effect=Exception("API Error"))
        
        result = service.translate_trial_info(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"]
        )
        
        assert result is None
    
    def test_create_fallback_translation(self, service, sample_trial_data):
        """Test creation of fallback translation"""
        result = service.create_fallback_translation(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"],
            sample_trial_data["compensation"]
        )
        
        assert isinstance(result, TrialTranslation)
        assert sample_trial_data["title"] in result.simplified_description
        assert "Time commitment information not available" in result.time_commitment
        assert "Benefits information not available" in result.key_benefits
        assert result.compensation_explanation == sample_trial_data["compensation"]
    
    def test_create_fallback_translation_long_text(self, service):
        """Test fallback translation with long text truncation"""
        long_description = "A" * 300  # Long description
        long_criteria = "B" * 200     # Long criteria
        
        result = service.create_fallback_translation(
            "Test Title",
            long_criteria,
            long_description
        )
        
        # Check that truncation occurred (indicated by "...")
        assert "..." in result.simplified_description
        assert "..." in result.eligibility_simplified
        
        # Check that the original long text is included but truncated
        assert long_description[:100] in result.simplified_description
        assert long_criteria[:100] in result.eligibility_simplified
    
    def test_translate_with_fallback_success(self, service, sample_trial_data, sample_ai_response):
        """Test translate_with_fallback when AI translation succeeds"""
        mock_response = Mock()
        mock_response.text = json.dumps(sample_ai_response)
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.translate_with_fallback(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"],
            sample_trial_data["compensation"]
        )
        
        assert isinstance(result, TrialTranslation)
        assert result.simplified_description == sample_ai_response["simplifiedDescription"]
    
    def test_translate_with_fallback_failure(self, service, sample_trial_data):
        """Test translate_with_fallback when AI translation fails"""
        service.model.generate_content = Mock(side_effect=Exception("API Error"))
        
        result = service.translate_with_fallback(
            sample_trial_data["title"],
            sample_trial_data["criteria"],
            sample_trial_data["description"],
            sample_trial_data["compensation"]
        )
        
        assert isinstance(result, TrialTranslation)
        assert sample_trial_data["title"] in result.simplified_description
        assert "Time commitment information not available" in result.time_commitment
    
    def test_health_check_success(self, service):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.text = '{"status": "healthy"}'
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.health_check()
        
        assert result["status"] == "healthy"
        assert result["api_accessible"] is True
        assert result["model"] == "gemini-pro"
    
    def test_health_check_unexpected_response(self, service):
        """Test health check with unexpected response"""
        mock_response = Mock()
        mock_response.text = "Unexpected response"
        service.model.generate_content = Mock(return_value=mock_response)
        
        result = service.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["api_accessible"] is True
        assert "Unexpected response format" in result["error"]
    
    def test_health_check_api_exception(self, service):
        """Test health check when API throws exception"""
        service.model.generate_content = Mock(side_effect=Exception("Connection failed"))
        
        result = service.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["api_accessible"] is False
        assert "Connection failed" in result["error"]


class TestTrialTranslation:
    """Test cases for TrialTranslation data class"""
    
    def test_trial_translation_creation(self):
        """Test TrialTranslation object creation"""
        translation = TrialTranslation(
            simplified_description="Test description",
            eligibility_simplified="Test eligibility",
            time_commitment="Test time",
            key_benefits="Test benefits",
            compensation_explanation="Test compensation"
        )
        
        assert translation.simplified_description == "Test description"
        assert translation.eligibility_simplified == "Test eligibility"
        assert translation.time_commitment == "Test time"
        assert translation.key_benefits == "Test benefits"
        assert translation.compensation_explanation == "Test compensation"
    
    def test_trial_translation_optional_compensation(self):
        """Test TrialTranslation with optional compensation field"""
        translation = TrialTranslation(
            simplified_description="Test description",
            eligibility_simplified="Test eligibility",
            time_commitment="Test time",
            key_benefits="Test benefits"
        )
        
        assert translation.compensation_explanation is None


if __name__ == "__main__":
    pytest.main([__file__])