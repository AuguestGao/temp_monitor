"""Authentication routes."""
from typing import Tuple, Any
from flask import Blueprint, jsonify, request, abort, Response
from services.user_service import UserService
from utils.validators import validate_username, validate_password

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

# Initialize user service
user_service = UserService()


@auth_bp.route('/api/signup', methods=['POST'])
def signup() -> Tuple[Response, int]:
    """
    Sign up a new user.
    
    Returns:
        JSON response with status code
    """
    # Check if request has JSON
    if not request.is_json:
        abort(400)  # Returns standard error response {'error': 'Bad request'} from error handler
    
    data: dict[str, Any] = request.json or {}
    username: str = data.get('username', '')
    password: str = data.get('password', '')

    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        return jsonify({'error': username_error}), 400

    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        return jsonify({'error': password_error}), 400

    try:
        user_service.create_user(username, password)
        return jsonify({'message': 'User signed up'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@auth_bp.route('/api/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """
    Login a user.
    
    Returns:
        JSON response with status code
    """
    if not request.is_json:
        abort(400)
    
    data: dict[str, Any] = request.json or {}
    username: str = data.get('username', '')
    password: str = data.get('password', '')
    
    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        return jsonify({'error': username_error}), 400

    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        return jsonify({'error': password_error}), 400

    # Check if user exists
    if not user_service.user_exists(username):
        return jsonify({'error': 'Username does not exist'}), 400

    # Verify password
    if user_service.verify_password(username, password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401
