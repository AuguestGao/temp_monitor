"""Authentication routes."""
from typing import Tuple, Any
from flask import Blueprint, jsonify, request, abort, Response
from services.user_service import UserService
from utils.validators import validate_username, validate_password
from exceptions import ValidationError, AuthenticationError, NotFoundError

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
        raise ValidationError(username_error, field='username')

    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        raise ValidationError(password_error, field='password')

    try:
        user_service.create_user(username, password)
        return jsonify({'message': 'User signed up'}), 201
    except ValueError as e:
        raise ValidationError(str(e))


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
        raise ValidationError(username_error, field='username')

    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        raise ValidationError(password_error, field='password')

    # Check if user exists
    if not user_service.user_exists(username):
        raise NotFoundError('User', identifier=username)

    # Verify password
    if not user_service.verify_password(username, password):
        raise AuthenticationError('Invalid password')
    
    return jsonify({'message': 'Login successful'}), 200
