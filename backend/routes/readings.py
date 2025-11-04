"""Temperature reading routes."""
from flask import Blueprint, jsonify, request, abort
from config import get_config
from models.reading import Reading

# Get configuration
Config = get_config()

# Create a Blueprint for readings routes
readings_bp = Blueprint('readings', __name__)


@readings_bp.route('/api/reading', methods=['POST'])
def create_reading():
    """Create a new reading."""
    # Validate JSON content type
    if not request.is_json:
        abort(400)
    
    valueC = request.json.get('valueC')
    recordedAt = request.json.get('recordedAt')
    
    # Validate required fields
    if valueC is None:
        abort(400)
    
    # Validate valueC is within reasonable temperature range
    if not isinstance(valueC, (int, float)) or valueC < Config.TEMP_MIN_CELSIUS or valueC > Config.TEMP_MAX_CELSIUS:
        abort(422)  # Triggers 422 (Unprocessable Entity) error handler
    
    # Create reading model (ready for service integration)
    # TODO: Integrate with reading_service when storage is implemented
    reading = Reading(
        tempC=float(valueC),
        recordedAt=recordedAt or Reading.create_now(float(valueC)).recordedAt
    )
    
    # create_reading(reading)  # Will be implemented with reading_service
    return jsonify({'message': 'Reading created', 'reading': reading.to_dict()}), 201


@readings_bp.route('/api/readings', methods=['GET'])
def get_readings():
    """Get all readings."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get limit and offset with defaults from config, enforce max limit
    try:
        limit = int(request.args.get('limit', Config.API_READINGS_DEFAULT_LIMIT))
        limit = min(limit, Config.API_READINGS_MAX_LIMIT)  # Enforce max limit
    except (ValueError, TypeError):
        limit = Config.API_READINGS_DEFAULT_LIMIT
    
    try:
        offset = int(request.args.get('offset', Config.API_READINGS_DEFAULT_OFFSET))
    except (ValueError, TypeError):
        offset = Config.API_READINGS_DEFAULT_OFFSET
    # readings = get_readings(start_date, end_date, limit, offset)
    return jsonify({'message': 'Readings retrieved'}), 200

