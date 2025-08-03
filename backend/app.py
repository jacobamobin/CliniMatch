from flask import Flask, jsonify
from flask_cors import CORS
import os
from config import config
from utils.database import get_db_connection
from api.routes import api_bp

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Configure CORS for React frontend
    CORS(app, origins=["http://localhost:3000", "http://localhost:3001"], supports_credentials=True)
    
    # Register API blueprint
    app.register_blueprint(api_bp)
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)