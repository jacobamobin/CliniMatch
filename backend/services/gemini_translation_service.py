"""
Gemini AI Translation Service for CliniMatch

This service handles the translation of complex medical language from clinical trials
into plain, understandable language for patients using Google's Gemini AI API.
"""

import json
import logging
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


@dataclass
class TrialTranslation:
    """Data class for translated trial information"""
    simplified_description: str
    eligibility_simplified: str
    time_commitment: str
    key_benefits: str
    compensation_explanation: Optional[str] = None


class GeminiTranslationService:
    """Service for translating medical jargon using Google Gemini AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini translation service
        
        Args:
            api_key: Google Gemini API key. If None, will try to get from environment
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model - using gemini-1.5-flash as it's the current stable model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Configure safety settings to be less restrictive for medical content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _create_translation_prompt(self, title: str, criteria: str, description: str, 
                                 compensation: Optional[str] = None) -> str:
        """
        Create a structured prompt for medical jargon translation
        
        Args:
            title: Clinical trial title
            criteria: Eligibility criteria
            description: Study description
            compensation: Compensation information if available
            
        Returns:
            Formatted prompt string
        """
        compensation_section = ""
        if compensation:
            compensation_section = f"\nCompensation: {compensation}"
        
        prompt = f"""
You are a medical translator helping patients understand clinical trials. Your goal is to make complex medical information accessible to people without medical training.

Please translate the following clinical trial information into plain, conversational English:

Title: {title}
Eligibility Criteria: {criteria}
Study Description: {description}{compensation_section}

Provide your response as a JSON object with exactly these fields:
- "simplifiedDescription": A 2-3 sentence explanation in plain English that a high school graduate could understand
- "eligibilitySimplified": Key requirements without medical jargon, focusing on the most important criteria
- "timeCommitment": Expected time investment for participants (visits, duration, etc.)
- "keyBenefits": What participants might gain from the study (compensation, free treatment, etc.)
- "compensationExplanation": If compensation is mentioned, explain it clearly (or null if not applicable)

Guidelines:
- Use conversational, friendly language
- Avoid medical abbreviations and technical terms
- Focus on what matters most to patients
- Be encouraging but honest about requirements
- Keep explanations concise but complete
- If you're unsure about something, say so rather than guessing

Respond only with valid JSON, no additional text.
"""
        return prompt
    
    def translate_trial_info(self, title: str, criteria: str, description: str, 
                           compensation: Optional[str] = None) -> Optional[TrialTranslation]:
        """
        Translate clinical trial information into patient-friendly language
        
        Args:
            title: Clinical trial title
            criteria: Eligibility criteria
            description: Study description
            compensation: Compensation information if available
            
        Returns:
            TrialTranslation object or None if translation fails
        """
        try:
            prompt = self._create_translation_prompt(title, criteria, description, compensation)
            
            # Generate response from Gemini
            response = self.model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower temperature for more consistent output
                    max_output_tokens=1000,
                )
            )
            
            if not response.text:
                self.logger.error("Empty response from Gemini API")
                return None
            
            # Parse JSON response
            try:
                # Clean response text by removing markdown code block markers
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.endswith('```'):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()
                
                translation_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.error(f"Raw response: {response.text}")
                return None
            
            # Validate required fields
            required_fields = ['simplifiedDescription', 'eligibilitySimplified', 
                             'timeCommitment', 'keyBenefits']
            
            for field in required_fields:
                if field not in translation_data:
                    self.logger.error(f"Missing required field in response: {field}")
                    return None
            
            # Create and return TrialTranslation object
            return TrialTranslation(
                simplified_description=translation_data['simplifiedDescription'],
                eligibility_simplified=translation_data['eligibilitySimplified'],
                time_commitment=translation_data['timeCommitment'],
                key_benefits=translation_data['keyBenefits'],
                compensation_explanation=translation_data.get('compensationExplanation')
            )
            
        except Exception as e:
            self.logger.error(f"Error translating trial info: {e}")
            return None
    
    def create_fallback_translation(self, title: str, criteria: str, description: str, 
                                  compensation: Optional[str] = None) -> TrialTranslation:
        """
        Create a fallback translation when AI processing fails
        
        Args:
            title: Clinical trial title
            criteria: Eligibility criteria
            description: Study description
            compensation: Compensation information if available
            
        Returns:
            TrialTranslation with original text and fallback messages
        """
        return TrialTranslation(
            simplified_description=f"This study is titled '{title}'. {description[:200]}..." if len(description) > 200 else description,
            eligibility_simplified=f"Please review the detailed eligibility criteria: {criteria[:150]}..." if len(criteria) > 150 else criteria,
            time_commitment="Time commitment information not available. Please contact the study team for details.",
            key_benefits="Benefits information not available. Please contact the study team for details.",
            compensation_explanation=compensation if compensation else "Compensation information not available."
        )
    
    def translate_with_fallback(self, title: str, criteria: str, description: str, 
                              compensation: Optional[str] = None) -> TrialTranslation:
        """
        Attempt AI translation with automatic fallback to original text
        
        Args:
            title: Clinical trial title
            criteria: Eligibility criteria
            description: Study description
            compensation: Compensation information if available
            
        Returns:
            TrialTranslation object (either AI-translated or fallback)
        """
        # Try AI translation first
        translation = self.translate_trial_info(title, criteria, description, compensation)
        
        if translation is not None:
            return translation
        
        # Fall back to original text with basic formatting
        self.logger.warning("AI translation failed, using fallback")
        return self.create_fallback_translation(title, criteria, description, compensation)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Gemini API is accessible and working
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Simple test prompt
            test_response = self.model.generate_content(
                "Respond with exactly this JSON: {\"status\": \"healthy\"}",
                safety_settings=self.safety_settings
            )
            
            if test_response.text and "healthy" in test_response.text:
                return {
                    "status": "healthy",
                    "api_accessible": True,
                    "model": "gemini-pro"
                }
            else:
                return {
                    "status": "unhealthy",
                    "api_accessible": True,
                    "error": "Unexpected response format"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e)
            }