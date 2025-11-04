"""Temperature reading routes."""
from typing import Tuple, Any, Optional
from flask import Blueprint, jsonify, request, abort, Response
from config import get_config
from models.reading import Reading
from utils.validators import validate_temperature, validate_limit, validate_offset
from exceptions import ValidationError, UnprocessableEntityError
from constants import HTTP_BAD_REQUEST, HTTP_CREATED, HTTP_OK

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
        abort(HTTP_BAD_REQUEST)
    
    data: dict[str, Any] = request.json or {}
    valueC: Any = data.get('valueC')
    recordedAt: Optional[str] = data.get('recordedAt')
    
    # Validate required fields
    if valueC is None:
        raise ValidationError('valueC is required', field='valueC')
    
    # Validate temperature
    try:
        temp_value = float(valueC)
    except (ValueError, TypeError):
        raise ValidationError('valueC must be a number', field='valueC')
    
    is_valid, error_message = validate_temperature(temp_value)
    if not is_valid:
        raise UnprocessableEntityError(error_message, details={'field': 'valueC', 'value': temp_value})
    
    # Create reading model (ready for service integration)
    # TODO: Integrate with reading_service when storage is implemented
    reading = Reading(
        tempC=float(valueC),
        recordedAt=recordedAt or Reading.create_now(float(valueC)).recordedAt
    )
    
    # create_reading(reading)  # Will be implemented with reading_service
    return jsonify({'message': 'Reading created', 'reading': reading.to_dict()}), HTTP_CREATED


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
    }), HTTP_OK

