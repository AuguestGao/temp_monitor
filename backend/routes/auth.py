"""Authentication routes."""
from typing import Tuple, Any
from flask import Blueprint, jsonify, request, abort, Response
from services.user_service import UserService
from services.jwt_service import jwt_service
from services.token_storage import token_storage
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
        
        # Generate tokens
        access_token = jwt_service.generate_access_token(username)
        refresh_token = jwt_service.generate_refresh_token(username)
        
        # Store refresh token
        token_storage.add_refresh_token(username, refresh_token)
        
        return jsonify({
            'message': 'User signed up',
            'access_token': access_token,
            'refresh_token': refresh_token
        }), HTTP_CREATED
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
    
    # Generate tokens
    access_token = jwt_service.generate_access_token(username)
    refresh_token = jwt_service.generate_refresh_token(username)
    
    # Store refresh token
    token_storage.add_refresh_token(username, refresh_token)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token
    }), HTTP_OK


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


@auth_bp.route('/api/refresh-token', methods=['POST'])
@require_refresh_token
def refresh_token() -> Tuple[Response, int]:
    """
    Refresh access token using refresh token.
    
    Requires: Authorization header with Bearer <refresh_token>
    
    Returns:
        JSON response with new access token and refresh token
    """
    username = g.current_user
    old_refresh_token = g.refresh_token
    
    # Generate new tokens
    new_access_token = jwt_service.generate_access_token(username)
    new_refresh_token = jwt_service.generate_refresh_token(username)
    
    # Revoke old refresh token and add new one
    token_storage.revoke_refresh_token(username, old_refresh_token)
    token_storage.add_refresh_token(username, new_refresh_token)
    
    return jsonify({
        'message': 'Token refreshed',
        'access_token': new_access_token,
        'refresh_token': new_refresh_token
    }), HTTP_OK


@auth_bp.route('/api/logout', methods=['POST'])
def logout() -> Tuple[Response, int]:
    """
    Logout user and revoke tokens.
    
    Request body (optional):
    {
        "revoke_all": true  // If true, revoke all tokens for user (logout all devices)
    }
    
    Returns:
        JSON response with status code
    """
    from utils.auth_middleware import extract_token_from_header
    
    # Try to get token, but don't require auth (logout should be idempotent)
    access_token = extract_token_from_header()
    
    if access_token:
        # Verify token to get username
        payload = jwt_service.verify_token(access_token)
        if payload and not token_storage.is_token_blacklisted(access_token):
            username = payload.get('username')
            token_type = payload.get('type')
            
            if token_type == 'access' and username:
                # Blacklist current access token
                token_storage.blacklist_token(access_token)
                
                data: dict[str, Any] = request.json or {} if request.is_json else {}
                revoke_all = data.get('revoke_all', False)
                
                # Revoke refresh token or all tokens
                if revoke_all:
                    count = token_storage.revoke_all_user_tokens(username)
                    return jsonify({
                        'message': 'Logged out from all devices',
                        'revoked_tokens': count
                    }), HTTP_OK
    
    # Return success even if token invalid (idempotent)
    return jsonify({
        'message': 'Logged out successfully'
    }), HTTP_OK
