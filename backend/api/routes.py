"""
Flask API Routes for CliniMatch

This module contains the API endpoints for trial matching functionality.
"""

from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
import logging
from typing import Dict, Any

from services.trial_matching_service import TrialMatchingService, TrialMatchingError
from models.trial_match import MatchingResult
from models.user_profile import UserProfile, LocationData, LifestyleData

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize services (can be overridden for testing)
trial_matching_service = None

def get_trial_matching_service():
    """Get or create trial matching service instance"""
    global trial_matching_service
    if trial_matching_service is None:
        trial_matching_service = TrialMatchingService()
    return trial_matching_service


class LocationSchema(Schema):
    """Schema for location validation"""
    city = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    state = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    country = fields.Str(load_default="United States")
    zip_code = fields.Str(allow_none=True)


class LifestyleSchema(Schema):
    """Schema for lifestyle validation"""
    smoking = fields.Bool(load_default=False)
    drinking = fields.Str(validate=lambda x: x in ["never", "occasional", "regular"], load_default="never")


class UserProfileSchema(Schema):
    """Schema for user profile validation"""
    age = fields.Int(required=True, validate=lambda x: 0 < x < 120)
    conditions = fields.List(fields.Str(), required=True, validate=lambda x: len(x) > 0)
    medications = fields.List(fields.Str(), load_default=[])
    location = fields.Nested(LocationSchema, required=True)
    lifestyle = fields.Nested(LifestyleSchema, load_default=LifestyleSchema().load({}))
    page = fields.Int(load_default=1, validate=lambda x: x > 0)
    limit = fields.Int(load_default=20, validate=lambda x: 1 <= x <= 50)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for system monitoring
    
    Returns:
        JSON response with system health status
    """
    try:
        # Get health status from trial matching service
        service = get_trial_matching_service()
        health_status = service.health_check()
        
        return jsonify({
            'status': 'healthy',
            'service': 'clinimatch-backend',
            'version': '1.0.0',
            'services': health_status.get('services', {}),
            'timestamp': health_status.get('timestamp')
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'clinimatch-backend',
            'error': str(e),
            'version': '1.0.0'
        }), 500


@api_bp.route('/match', methods=['POST'])
def match_trials():
    """
    Trial matching endpoint
    
    Accepts user profile data and returns matching clinical trials.
    
    Request Body:
        JSON object with user profile data
        
    Returns:
        JSON response with matching trials and metadata
    """
    logger.info("🔍 Received trial matching request")
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 400
        
        # Get request data
        data = request.get_json()
        logger.info(f"📝 Request data: {data}")
        
        if not data:
            return jsonify({
                'error': 'Request body is required'
            }), 400
        
        # Validate request data
        schema = UserProfileSchema()
        try:
            validated_data = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'error': 'Validation failed',
                'details': e.messages
            }), 400
        
        # Create UserProfile object
        location_data = LocationData(
            city=validated_data['location']['city'],
            state=validated_data['location']['state'],
            country=validated_data['location'].get('country', 'United States'),
            zip_code=validated_data['location'].get('zip_code')
        )
        
        lifestyle_data = LifestyleData(
            smoking=validated_data['lifestyle'].get('smoking', False),
            drinking=validated_data['lifestyle'].get('drinking', 'never')
        )
        
        user_profile = UserProfile(
            age=validated_data['age'],
            conditions=validated_data['conditions'],
            medications=validated_data.get('medications', []),
            location=location_data,
            lifestyle=lifestyle_data
        )
        
        # Log the request
        logger.info(f"Processing trial match request for user age {user_profile.age} in {user_profile.location.city}, {user_profile.location.state}")
        
        # Find matching trials
        service = get_trial_matching_service()
        result = service.find_matching_trials(user_profile)
        
        # Get pagination parameters
        page = validated_data.get('page', 1)
        limit = validated_data.get('limit', 20)
        
        # Ensure result is always a MatchingResult object
        if not hasattr(result, 'to_dict'):
            logger.error(f"Expected MatchingResult object, got {type(result)}")
            raise ValueError("Trial matching service returned unexpected data format")
        
        # Get data from MatchingResult object
        total_found = result.total_found
        all_matches = result.matches
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_matches = all_matches[start_idx:end_idx]
        
        # Create paginated result
        paginated_result = MatchingResult(
            matches=paginated_matches,
            total_found=total_found,
            processing_time=result.processing_time,
            search_params=result.search_params,
            cached=result.cached,
            ai_translation_success_rate=result.ai_translation_success_rate
        )
        
        result_dict = paginated_result.to_dict()
            
        response_data = {
            'success': True,
            'data': result_dict,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_found,
                'total_pages': (total_found + limit - 1) // limit,
                'has_next': end_idx < total_found,
                'has_prev': page > 1
            },
            'message': f'Found {total_found} matching trials (showing {len(paginated_matches)} on page {page})'
        }
        
        # Add additional metadata
        if result.cached:
            response_data['message'] += ' (from cache)'
        
        logger.info(f"Trial matching completed: {result.total_found} trials found in {result.processing_time:.2f}s")
        
        return jsonify(response_data), 200
        
    except TrialMatchingError as e:
        logger.error(f"Trial matching error: {str(e)}")
        return jsonify({
            'error': 'Trial matching failed',
            'message': str(e),
            'error_type': getattr(e, 'error_type', 'MATCHING_ERROR')
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in trial matching: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while processing your request'
        }), 500


@api_bp.route('/trial/<nct_id>', methods=['GET'])
def get_trial_by_id(nct_id: str):
    """
    Get specific trial by NCT ID
    
    Args:
        nct_id: NCT identifier for the trial
        
    Returns:
        JSON response with trial details
    """
    try:
        # Validate NCT ID format
        if not nct_id or not nct_id.startswith('NCT'):
            return jsonify({
                'error': 'Invalid NCT ID format. Must start with "NCT"'
            }), 400
        
        logger.info(f"Fetching trial details for NCT ID: {nct_id}")
        
        # Get trial details
        service = get_trial_matching_service()
        trial = service.get_trial_by_id(nct_id)
        
        if not trial:
            return jsonify({
                'error': 'Trial not found',
                'message': f'No trial found with NCT ID: {nct_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': trial.to_dict()
        }), 200
        
    except TrialMatchingError as e:
        logger.error(f"Error fetching trial {nct_id}: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch trial',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error fetching trial {nct_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred while fetching trial details'
        }), 500


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist'
    }), 404


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The HTTP method is not supported for this endpoint'
    }), 405


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500 