"""Arduino control routes."""
import logging
from typing import Tuple
from flask import Blueprint, jsonify, Response
from services.arduino_service import ArduinoService
from utils.auth_middleware import require_auth
from constants import HTTP_OK, HTTP_INTERNAL_SERVER_ERROR

logger = logging.getLogger(__name__)

# Create a Blueprint for Arduino routes
arduino_bp = Blueprint('arduino', __name__)

# Initialize Arduino service
arduino_service = ArduinoService()


@arduino_bp.route('/api/arduino/start', methods=['POST'])
@require_auth
def start_arduino() -> Tuple[Response, int]:
    """
    Send START command to Arduino.
    
    Returns:
        JSON response with success status and message
    """
    logger.info("Received START command request")
    
    success, message = arduino_service.start()
    
    if success:
        return jsonify({
            'message': message,
            'status': 'success'
        }), HTTP_OK
    else:
        return jsonify({
            'message': message,
            'status': 'error'
        }), HTTP_INTERNAL_SERVER_ERROR


@arduino_bp.route('/api/arduino/stop', methods=['POST'])
@require_auth
def stop_arduino() -> Tuple[Response, int]:
    """
    Send STOP command to Arduino.
    
    Returns:
        JSON response with success status and message
    """
    logger.info("Received STOP command request")
    
    success, message = arduino_service.stop()
    
    if success:
        return jsonify({
            'message': message,
            'status': 'success'
        }), HTTP_OK
    else:
        return jsonify({
            'message': message,
            'status': 'error'
        }), HTTP_INTERNAL_SERVER_ERROR


@arduino_bp.route('/api/arduino/toggle', methods=['POST'])
@require_auth
def toggle_arduino() -> Tuple[Response, int]:
    """
    Send TOGGLE command to Arduino.
    
    Returns:
        JSON response with success status and message
    """
    logger.info("Received TOGGLE command request")
    
    success, message = arduino_service.toggle()
    
    if success:
        return jsonify({
            'message': message,
            'status': 'success'
        }), HTTP_OK
    else:
        return jsonify({
            'message': message,
            'status': 'error'
        }), HTTP_INTERNAL_SERVER_ERROR

