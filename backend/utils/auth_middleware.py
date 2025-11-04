"""Authentication middleware for protecting routes."""
import logging
from functools import wraps
from typing import Callable, Any, Optional
from flask import request, g, abort
from services.jwt_service import jwt_service
from services.token_storage import token_storage
from exceptions import AuthenticationError, AuthorizationError
from constants import HTTP_UNAUTHORIZED

logger = logging.getLogger(__name__)


def extract_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Returns:
        Token string or None if not found
    """
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    return None


def get_current_user() -> Optional[str]:
    """
    Get current authenticated user from token.
    
    Returns:
        Username if authenticated, None otherwise
    """
    token = extract_token_from_header()
    
    if not token:
        return None
    
    # Check if token is blacklisted
    if token_storage.is_token_blacklisted(token):
        logger.warning("Attempted to use blacklisted token")
        return None
    
    # Verify and decode token
    payload = jwt_service.verify_token(token)
    
    if not payload:
        return None
    
    # Check token type (should be access token)
    token_type = payload.get('type')
    if token_type != 'access':
        logger.warning(f"Invalid token type for access: {token_type}")
        return None
    
    return payload.get('username')


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    
    Usage:
        @readings_bp.route('/api/readings')
        @require_auth
        def get_readings():
            username = g.current_user  # Access current user
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        token = extract_token_from_header()
        
        if not token:
            raise AuthenticationError('Authentication required. Please provide a valid token.')
        
        # Check if token is blacklisted
        if token_storage.is_token_blacklisted(token):
            raise AuthenticationError('Token has been revoked.')
        
        # Verify token
        payload = jwt_service.verify_token(token)
        
        if not payload:
            raise AuthenticationError('Invalid or expired token.')
        
        # Check token type
        token_type = payload.get('type')
        if token_type != 'access':
            raise AuthenticationError('Invalid token type. Access token required.')
        
        # Store current user in Flask's g object
        g.current_user = payload.get('username')
        g.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_refresh_token(f: Callable) -> Callable:
    """
    Decorator to require refresh token for a route.
    
    Usage:
        @auth_bp.route('/api/refresh')
        @require_refresh_token
        def refresh():
            username = g.current_user
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        token = extract_token_from_header()
        
        if not token:
            raise AuthenticationError('Refresh token required.')
        
        # Check if token is blacklisted
        if token_storage.is_token_blacklisted(token):
            raise AuthenticationError('Refresh token has been revoked.')
        
        # Verify token
        payload = jwt_service.verify_token(token)
        
        if not payload:
            raise AuthenticationError('Invalid or expired refresh token.')
        
        # Check token type
        token_type = payload.get('type')
        if token_type != 'refresh':
            raise AuthenticationError('Invalid token type. Refresh token required.')
        
        username = payload.get('username')
        
        # Check if refresh token is active
        if not token_storage.is_refresh_token_active(username, token):
            raise AuthenticationError('Refresh token has been revoked.')
        
        # Store current user in Flask's g object
        g.current_user = username
        g.token_payload = payload
        g.refresh_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function

