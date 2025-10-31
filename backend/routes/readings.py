"""Temperature reading routes."""
from flask import Blueprint, jsonify, request, abort

# Create a Blueprint for readings routes
readings_bp = Blueprint('readings', __name__)


@readings_bp.route('/api/reading', methods=['POST'])
def create_reading():
    """Create a new reading."""
    # Validate JSON content type
    if not request.is_json:
        abort(400)
    
    room = request.json.get('room')
    valueC = request.json.get('valueC')
    recordedAt = request.json.get('recordedAt')
    source = request.json.get('source')
    
    # Validate required fields
    if not room or valueC is None:
        abort(400)
    
    # Validate valueC is within reasonable temperature range
    if not isinstance(valueC, (int, float)) or valueC < -55 or valueC > 125:
        abort(422)  # Triggers 422 (Unprocessable Entity) error handler
    
    # create_reading(room, valueC, recordedAt, source)
    return jsonify({'message': 'Reading created'}), 201


@readings_bp.route('/api/readings', methods=['GET'])
def get_readings():
    """Get all readings."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    room = request.args.get('room')
    limit = request.args.get('limit', 1000)
    offset = request.args.get('offset', 0)
    # readings = get_readings(start_date, end_date, room, limit, offset)
    return jsonify({'message': 'Readings retrieved'}), 200

