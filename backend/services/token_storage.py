"""Token storage for managing active refresh tokens and blacklisted tokens."""
import logging
from typing import Set, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class TokenStorage:
    """Storage for managing JWT tokens."""
    
    def __init__(self):
        """Initialize token storage."""
        # Active refresh tokens: {username: Set[refresh_token]}
        self.active_refresh_tokens: defaultdict[str, Set[str]] = defaultdict(set)
        
        # Blacklisted tokens (access tokens and revoked refresh tokens)
        self.blacklisted_tokens: Set[str] = set()
    
    def add_refresh_token(self, username: str, refresh_token: str) -> None:
        """
        Add a refresh token to active tokens.
        
        Args:
            username: Username
            refresh_token: Refresh token string
        """
        self.active_refresh_tokens[username].add(refresh_token)
        logger.debug(f"Added refresh token for user: {username}")
    
    def is_refresh_token_active(self, username: str, refresh_token: str) -> bool:
        """
        Check if refresh token is active.
        
        Args:
            username: Username
            refresh_token: Refresh token string
            
        Returns:
            True if token is active, False otherwise
        """
        return refresh_token in self.active_refresh_tokens.get(username, set())
    
    def revoke_refresh_token(self, username: str, refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            username: Username
            refresh_token: Refresh token string
            
        Returns:
            True if token was revoked, False if not found
        """
        if username in self.active_refresh_tokens:
            removed = self.active_refresh_tokens[username].discard(refresh_token)
            if removed or refresh_token in self.active_refresh_tokens.get(username, set()):
                # Add to blacklist
                self.blacklisted_tokens.add(refresh_token)
                logger.info(f"Revoked refresh token for user: {username}")
                return True
        return False
    
    def revoke_all_user_tokens(self, username: str) -> int:
        """
        Revoke all refresh tokens for a user (logout all devices).
        
        Args:
            username: Username
            
        Returns:
            Number of tokens revoked
        """
        if username in self.active_refresh_tokens:
            tokens = self.active_refresh_tokens[username].copy()
            count = len(tokens)
            
            # Add all tokens to blacklist
            self.blacklisted_tokens.update(tokens)
            
            # Clear user's tokens
            del self.active_refresh_tokens[username]
            
            logger.info(f"Revoked all tokens for user: {username} ({count} tokens)")
            return count
        return 0
    
    def blacklist_token(self, token: str) -> None:
        """
        Add a token to blacklist (typically access token on logout).
        
        Args:
            token: Token string to blacklist
        """
        self.blacklisted_tokens.add(token)
        logger.debug("Token added to blacklist")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            token: Token string to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        return token in self.blacklisted_tokens
    
    def cleanup_expired_tokens(self) -> None:
        """
        Clean up expired tokens from blacklist.
        Note: This is a simple cleanup - in production, you might want
        to check token expiration before removing from blacklist.
        """
        # For now, we keep blacklisted tokens until they naturally expire
        # In a production system, you might want to periodically clean up
        # tokens that are past their expiration time
        pass


# Global token storage instance
token_storage = TokenStorage()

