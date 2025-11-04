"""Authentication routes."""
from typing import Tuple, Any
from flask import Blueprint, jsonify, request, abort, Response
from services.user_service import UserService
from utils.validators import validate_username, validate_password
from utils.rate_limiter import rate_limiter
from exceptions import ValidationError, AuthenticationError, NotFoundError, RateLimitError
from constants import HTTP_BAD_REQUEST, HTTP_CREATED, HTTP_OK

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
        abort(HTTP_BAD_REQUEST)  # Returns standard error response {'error': 'Bad request'} from error handler
    
    ip_address = request.remote_addr or 'unknown'
    
    # Check rate limit
    is_allowed, error_msg, retry_after = rate_limiter.check_rate_limit(ip_address)
    if not is_allowed:
        raise RateLimitError(error_msg, retry_after=retry_after)
    
    data: dict[str, Any] = request.json or {}
    username: str = data.get('username', '')
    password: str = data.get('password', '')

    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        rate_limiter.record_failed_attempt(ip_address)
        raise ValidationError(username_error, field='username')

    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        rate_limiter.record_failed_attempt(ip_address)
        raise ValidationError(password_error, field='password')

    try:
        user_service.create_user(username, password)
        # Reset rate limit on successful signup
        rate_limiter.reset_attempts(ip_address)
        return jsonify({'message': 'User signed up'}), HTTP_CREATED
    except ValidationError as e:
        rate_limiter.record_failed_attempt(ip_address)
        raise


@auth_bp.route('/api/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """
    Login a user.
    
    Returns:
        JSON response with status code
    """
    if not request.is_json:
        abort(HTTP_BAD_REQUEST)
    
    ip_address = request.remote_addr or 'unknown'
    data: dict[str, Any] = request.json or {}
    username: str = data.get('username', '')
    password: str = data.get('password', '')
    
    # Check rate limit (by IP and username for login)
    is_allowed, error_msg, retry_after = rate_limiter.check_rate_limit(ip_address, username)
    if not is_allowed:
        raise RateLimitError(error_msg, retry_after=retry_after)
    
    # Validate username
    is_valid_username, username_error = validate_username(username)
    if not is_valid_username:
        rate_limiter.record_failed_attempt(ip_address, username)
        raise ValidationError(username_error, field='username')

    # Validate password
    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        rate_limiter.record_failed_attempt(ip_address, username)
        raise ValidationError(password_error, field='password')

    # Check if user exists
    if not user_service.user_exists(username):
        rate_limiter.record_failed_attempt(ip_address, username)
        raise NotFoundError('User', identifier=username)

    # Verify password
    if not user_service.verify_password(username, password):
        rate_limiter.record_failed_attempt(ip_address, username)
        raise AuthenticationError('Invalid password')
    
    # Reset rate limit on successful login
    rate_limiter.reset_attempts(ip_address, username)
    return jsonify({'message': 'Login successful'}), HTTP_OK


@auth_bp.route('/api/rate-limit/reset', methods=['POST'])
def reset_rate_limit() -> Tuple[Response, int]:
    """
    Reset rate limits for the current IP address or all limits.
    
    Request body (optional):
    {
        "reset_key": "reset-key-change-in-production",  // Required for reset_all
        "username": "username"  // Optional, to reset specific username
    }
    
    Returns:
        JSON response with status code
    """
    from config import get_config
    Config = get_config()
    
    ip_address = request.remote_addr or 'unknown'
    data: dict[str, Any] = request.json or {} if request.is_json else {}
    reset_key = data.get('reset_key')
    username = data.get('username')
    
    # Check if requesting to reset all (requires reset key)
    if reset_key and reset_key == Config.RATE_LIMIT_RESET_KEY:
        count = rate_limiter.reset_all()
        return jsonify({
            'message': f'All rate limits reset',
            'reset_count': count
        }), HTTP_OK
    
    # Reset for specific IP/username
    if username:
        success = rate_limiter.reset_attempts(ip_address, username)
        if success:
            return jsonify({
                'message': f'Rate limit reset for IP {ip_address} and username {username}'
            }), HTTP_OK
        else:
            return jsonify({
                'message': 'No rate limit found for this IP and username'
            }), HTTP_OK
    
    # Reset for current IP only
    success = rate_limiter.reset_attempts(ip_address)
    if success:
        return jsonify({
            'message': f'Rate limit reset for IP {ip_address}'
        }), HTTP_OK
    else:
        return jsonify({
            'message': 'No rate limit found for this IP'
        }), HTTP_OK
