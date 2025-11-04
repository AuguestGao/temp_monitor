"""JWT service for token generation and validation."""
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from config import get_config

Config = get_config()
logger = logging.getLogger(__name__)


class JWTService:
    """Service for JWT token operations."""
    
    def __init__(self):
        """Initialize JWT service."""
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = Config.JWT_ALGORITHM
        self.access_token_expires_in = Config.JWT_ACCESS_TOKEN_EXPIRES_IN
        self.refresh_token_expires_in = Config.JWT_REFRESH_TOKEN_EXPIRES_IN
    
    def generate_access_token(self, username: str) -> str:
        """
        Generate access token for a user.
        
        Args:
            username: Username to include in token
            
        Returns:
            JWT access token string
        """
        payload = {
            'username': username,
            'type': 'access',
            'exp': datetime.now(timezone.utc) + timedelta(seconds=self.access_token_expires_in),
            'iat': datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Generated access token for user: {username}")
        return token
    
    def generate_refresh_token(self, username: str) -> str:
        """
        Generate refresh token for a user.
        
        Args:
            username: Username to include in token
            
        Returns:
            JWT refresh token string
        """
        payload = {
            'username': username,
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) + timedelta(seconds=self.refresh_token_expires_in),
            'iat': datetime.now(timezone.utc)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"Generated refresh token for user: {username}")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={'verify_exp': True, 'verify_signature': True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token without verification (for inspection only).
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None
        """
        try:
            return jwt.decode(token, options={'verify_signature': False})
        except jwt.InvalidTokenError:
            return None
    
    def get_username_from_token(self, token: str) -> Optional[str]:
        """
        Extract username from token.
        
        Args:
            token: JWT token string
            
        Returns:
            Username if token is valid, None otherwise
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get('username')
        return None
    
    def get_token_type(self, token: str) -> Optional[str]:
        """
        Get token type (access or refresh).
        
        Args:
            token: JWT token string
            
        Returns:
            Token type or None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get('type')
        return None


# Global JWT service instance
jwt_service = JWTService()

