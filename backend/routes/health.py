"""Health and status routes."""
from flask import Blueprint, jsonify
from config import get_config

# Get configuration
Config = get_config()

# Create a Blueprint for health routes
health_bp = Blueprint('health', __name__)


@health_bp.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Temperature Monitor API',
        'version': Config.APP_VERSION
    })


@health_bp.route('/api/health')
def health():
    """API health check endpoint."""
    return jsonify({'status': 'healthy'})

