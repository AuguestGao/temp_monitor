"""Temperature reading routes."""
from typing import Tuple, Any, Optional
from flask import Blueprint, jsonify, request, abort, Response
from config import get_config
from models.reading import Reading
from utils.validators import validate_temperature, validate_limit, validate_offset

# Get configuration
Config = get_config()

# Create a Blueprint for readings routes
readings_bp = Blueprint('readings', __name__)


@readings_bp.route('/api/reading', methods=['POST'])
def create_reading() -> Tuple[Response, int]:
    """
    Create a new reading.
    
    Returns:
        JSON response with status code
    """
    # Validate JSON content type
    if not request.is_json:
        abort(400)
    
    data: dict[str, Any] = request.json or {}
    valueC: Any = data.get('valueC')
    recordedAt: Optional[str] = data.get('recordedAt')
    
    # Validate required fields
    if valueC is None:
        return jsonify({'error': 'valueC is required'}), 400
    
    # Validate temperature
    is_valid, error_message = validate_temperature(float(valueC))
    if not is_valid:
        return jsonify({'error': error_message}), 422
    
    # Create reading model (ready for service integration)
    # TODO: Integrate with reading_service when storage is implemented
    reading = Reading(
        tempC=float(valueC),
        recordedAt=recordedAt or Reading.create_now(float(valueC)).recordedAt
    )
    
    # create_reading(reading)  # Will be implemented with reading_service
    return jsonify({'message': 'Reading created', 'reading': reading.to_dict()}), 201


@readings_bp.route('/api/readings', methods=['GET'])
def get_readings() -> Tuple[Response, int]:
    """
    Get all readings.
    
    Returns:
        JSON response with status code
    """
    start_date: Optional[str] = request.args.get('start_date')
    end_date: Optional[str] = request.args.get('end_date')
    
    # Get limit and offset with validation
    limit: int = validate_limit(request.args.get('limit'))
    offset: int = validate_offset(request.args.get('offset'))
    
    # readings = get_readings(start_date, end_date, limit, offset)
    return jsonify({
        'message': 'Readings retrieved',
        'limit': limit,
        'offset': offset
    }), 200

