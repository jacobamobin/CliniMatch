import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_PROJECT_ID = os.getenv('SUPABASE_PROJECT_ID')
    
    # External API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # ClinicalTrials.gov API
    CLINICAL_TRIALS_BASE_URL = 'https://clinicaltrials.gov/api/v2'
    
    # Cache settings
    CACHE_TTL_HOURS = 24

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}