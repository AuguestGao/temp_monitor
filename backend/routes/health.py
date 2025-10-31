"""Health and status routes."""
from flask import Blueprint, jsonify

# Create a Blueprint for health routes
health_bp = Blueprint('health', __name__)


@health_bp.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Temperature Monitor API',
        'version': '0.1.0'
    })


@health_bp.route('/api/health')
def health():
    """API health check endpoint."""
    return jsonify({'status': 'healthy'})

