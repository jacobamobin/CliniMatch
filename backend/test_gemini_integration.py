#!/usr/bin/env python3
"""
Integration test for Gemini Translation Service
This script tests the service with realistic data but mocked API responses.
"""

import json
from unittest.mock import Mock, patch
from services.gemini_translation_service import GeminiTranslationService


def test_realistic_translation():
    """Test the service with realistic clinical trial data"""
    
    # Sample realistic clinical trial data
    trial_data = {
        "title": "A Phase 3, Randomized, Double-Blind, Placebo-Controlled Study of Investigational Drug XYZ-456 in Adults with Type 2 Diabetes Mellitus",
        "criteria": """
        Inclusion Criteria:
        - Male or female subjects aged 18-75 years
        - Diagnosed with Type 2 diabetes mellitus for ≥6 months
        - HbA1c ≥7.0% and ≤10.5% at screening
        - BMI ≥25 kg/m² and ≤45 kg/m²
        - On stable metformin therapy (≥1500 mg/day) for ≥3 months
        
        Exclusion Criteria:
        - Type 1 diabetes mellitus or secondary diabetes
        - History of diabetic ketoacidosis or hyperosmolar coma
        - eGFR <60 mL/min/1.73m²
        - Active malignancy within 5 years
        - Pregnancy or breastfeeding
        """,
        "description": """
        This is a multicenter, randomized, double-blind, placebo-controlled, parallel-group study to evaluate the efficacy and safety of XYZ-456 as add-on therapy to metformin in adult subjects with inadequately controlled Type 2 diabetes mellitus. The primary efficacy endpoint is the change from baseline in HbA1c at Week 24. Secondary endpoints include changes in fasting plasma glucose, body weight, and safety parameters. The study duration is 52 weeks with a 4-week follow-up period.
        """,
        "compensation": "Participants will receive $200 per completed visit, with up to 12 visits over 56 weeks, for a maximum compensation of $2,400"
    }
    
    # Expected AI response (what we would expect from Gemini)
    expected_ai_response = {
        "simplifiedDescription": "This study tests a new diabetes medication called XYZ-456 to see if it helps control blood sugar better when added to metformin. You'll take either the new medicine or a fake pill (placebo) for about a year, and researchers will check how well it works.",
        "eligibilitySimplified": "You can join if you're 18-75 years old, have had Type 2 diabetes for at least 6 months, your blood sugar isn't well controlled (HbA1c 7-10.5%), you're overweight, and you're already taking metformin. You can't join if you have Type 1 diabetes, kidney problems, cancer, or are pregnant.",
        "timeCommitment": "About 12 visits over 14 months (56 weeks), with each visit taking 2-4 hours for tests and check-ups",
        "keyBenefits": "Free diabetes monitoring and lab tests, potential access to a new treatment that might help control your diabetes better, and compensation for your time and travel",
        "compensationExplanation": "You'll receive $200 for each visit you complete, which could total up to $2,400 if you finish the entire study"
    }
    
    # Test with mocked API
    with patch('google.generativeai.configure'), \
         patch('google.generativeai.GenerativeModel') as mock_model_class:
        
        # Set up the mock
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(expected_ai_response)
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # Create service and test translation
        service = GeminiTranslationService(api_key="test_key")
        
        result = service.translate_trial_info(
            trial_data["title"],
            trial_data["criteria"],
            trial_data["description"],
            trial_data["compensation"]
        )
        
        # Verify the result
        assert result is not None
        print("✅ Translation successful!")
        print(f"📝 Simplified Description: {result.simplified_description}")
        print(f"👥 Eligibility: {result.eligibility_simplified}")
        print(f"⏰ Time Commitment: {result.time_commitment}")
        print(f"🎁 Benefits: {result.key_benefits}")
        print(f"💰 Compensation: {result.compensation_explanation}")
        
        # Test fallback mechanism
        mock_model.generate_content.side_effect = Exception("API Error")
        
        fallback_result = service.translate_with_fallback(
            trial_data["title"],
            trial_data["criteria"],
            trial_data["description"],
            trial_data["compensation"]
        )
        
        assert fallback_result is not None
        print("\n✅ Fallback mechanism working!")
        print(f"📝 Fallback Description: {fallback_result.simplified_description[:100]}...")
        
        # Test health check
        mock_model.generate_content.side_effect = None
        mock_response.text = '{"status": "healthy"}'
        mock_model.generate_content.return_value = mock_response
        
        health = service.health_check()
        assert health["status"] == "healthy"
        print("\n✅ Health check passed!")
        
        print("\n🎉 All integration tests passed!")


if __name__ == "__main__":
    test_realistic_translation()