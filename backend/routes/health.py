"""Health and status routes."""
from typing import Tuple
from flask import Blueprint, jsonify, Response
from config import get_config
from constants import HTTP_OK

# Get configuration
Config = get_config()

# Create a Blueprint for health routes
health_bp = Blueprint('health', __name__)


@health_bp.route('/')
def index() -> Tuple[Response, int]:
    """
    Health check endpoint.
    
    Returns:
        JSON response with API status and version, and HTTP status code
    """
    return jsonify({
        'status': 'ok',
        'message': 'Temperature Monitor API',
        'version': Config.APP_VERSION
    }), HTTP_OK


@health_bp.route('/api/health')
def health() -> Tuple[Response, int]:
    """
    API health check endpoint.
    
    Returns:
        JSON response with health status and HTTP status code
    """
    return jsonify({'status': 'healthy'}), HTTP_OK

