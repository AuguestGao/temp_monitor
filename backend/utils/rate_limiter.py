"""Rate limiting for authentication endpoints."""
import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from config import get_config

Config = get_config()
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for tracking and limiting failed authentication attempts."""
    
    def __init__(self):
        """Initialize rate limiter with in-memory storage."""
        # Track failed attempts: {identifier: {'attempts': count, 'first_attempt': timestamp, 'locked_until': timestamp}}
        self.failed_attempts: Dict[str, Dict] = defaultdict(lambda: {
            'attempts': 0,
            'first_attempt': None,
            'locked_until': None
        })
    
    def _get_identifier(self, ip_address: str, username: Optional[str] = None) -> str:
        """
        Get identifier for rate limiting (IP or IP+username).
        
        Args:
            ip_address: Client IP address
            username: Optional username for login attempts
            
        Returns:
            Identifier string
        """
        if username:
            return f"{ip_address}:{username.lower()}"
        return ip_address
    
    def _is_locked(self, identifier: str) -> bool:
        """
        Check if identifier is currently locked.
        
        Args:
            identifier: Rate limit identifier
            
        Returns:
            True if locked, False otherwise
        """
        entry = self.failed_attempts[identifier]
        if entry['locked_until'] and entry['locked_until'] > time.time():
            return True
        # Clear lock if expired
        if entry['locked_until'] and entry['locked_until'] <= time.time():
            entry['locked_until'] = None
            entry['attempts'] = 0
            entry['first_attempt'] = None
        return False
    
    def _get_lockout_duration(self, attempts: int) -> int:
        """
        Calculate lockout duration based on number of attempts.
        
        Args:
            attempts: Number of failed attempts
            
        Returns:
            Lockout duration in seconds
        """
        if attempts >= Config.RATE_LIMIT_MAX_ATTEMPTS:
            # Progressive lockout: 15 minutes for max attempts, increases with each lockout
            base_duration = Config.RATE_LIMIT_LOCKOUT_DURATION
            return base_duration
        return 0
    
    def check_rate_limit(self, ip_address: str, username: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request should be rate limited.
        
        Args:
            ip_address: Client IP address
            username: Optional username for login attempts
            
        Returns:
            Tuple of (is_allowed, error_message, retry_after_seconds)
        """
        identifier = self._get_identifier(ip_address, username)
        entry = self.failed_attempts[identifier]
        
        # Check if currently locked
        if self._is_locked(identifier):
            retry_after = int(entry['locked_until'] - time.time())
            error_msg = f"Too many failed attempts. Please try again in {retry_after} seconds."
            logger.warning(f"Rate limit exceeded for {identifier}: {entry['attempts']} attempts")
            return False, error_msg, retry_after
        
        # Check if within time window
        current_time = time.time()
        if entry['first_attempt']:
            time_since_first = current_time - entry['first_attempt']
            if time_since_first > Config.RATE_LIMIT_WINDOW_SECONDS:
                # Reset if window expired
                entry['attempts'] = 0
                entry['first_attempt'] = None
        
        return True, None, None
    
    def record_failed_attempt(self, ip_address: str, username: Optional[str] = None) -> None:
        """
        Record a failed authentication attempt.
        
        Args:
            ip_address: Client IP address
            username: Optional username for login attempts
        """
        identifier = self._get_identifier(ip_address, username)
        entry = self.failed_attempts[identifier]
        current_time = time.time()
        
        # Initialize or reset if window expired
        if not entry['first_attempt'] or (current_time - entry['first_attempt']) > Config.RATE_LIMIT_WINDOW_SECONDS:
            entry['first_attempt'] = current_time
            entry['attempts'] = 0
        
        entry['attempts'] += 1
        
        # Apply lockout if threshold reached
        if entry['attempts'] >= Config.RATE_LIMIT_MAX_ATTEMPTS:
            lockout_duration = self._get_lockout_duration(entry['attempts'])
            entry['locked_until'] = current_time + lockout_duration
            logger.warning(
                f"Rate limit lockout applied for {identifier}: "
                f"{entry['attempts']} attempts, locked for {lockout_duration}s"
            )
    
    def reset_attempts(self, ip_address: str, username: Optional[str] = None) -> bool:
        """
        Reset failed attempts for an identifier.
        
        Args:
            ip_address: Client IP address
            username: Optional username for login attempts
            
        Returns:
            True if reset was successful, False if identifier not found
        """
        identifier = self._get_identifier(ip_address, username)
        if identifier in self.failed_attempts:
            self.failed_attempts[identifier] = {
                'attempts': 0,
                'first_attempt': None,
                'locked_until': None
            }
            logger.info(f"Rate limit reset for {identifier}")
            return True
        return False
    
    def reset_all(self) -> int:
        """
        Reset all rate limits.
        
        Returns:
            Number of identifiers reset
        """
        count = len(self.failed_attempts)
        self.failed_attempts.clear()
        logger.info(f"All rate limits reset ({count} identifiers)")
        return count
    
    def get_status(self, ip_address: str, username: Optional[str] = None) -> Dict:
        """
        Get rate limit status for an identifier.
        
        Args:
            ip_address: Client IP address
            username: Optional username for login attempts
            
        Returns:
            Dictionary with rate limit status
        """
        identifier = self._get_identifier(ip_address, username)
        entry = self.failed_attempts[identifier]
        
        status = {
            'attempts': entry['attempts'],
            'max_attempts': Config.RATE_LIMIT_MAX_ATTEMPTS,
            'is_locked': self._is_locked(identifier),
            'remaining_attempts': max(0, Config.RATE_LIMIT_MAX_ATTEMPTS - entry['attempts'])
        }
        
        if entry['locked_until']:
            status['locked_until'] = entry['locked_until']
            status['retry_after'] = int(entry['locked_until'] - time.time())
        else:
            status['locked_until'] = None
            status['retry_after'] = None
        
        if entry['first_attempt']:
            window_remaining = Config.RATE_LIMIT_WINDOW_SECONDS - (time.time() - entry['first_attempt'])
            status['window_remaining'] = max(0, int(window_remaining))
        else:
            status['window_remaining'] = None
        
        return status


# Global rate limiter instance
rate_limiter = RateLimiter()

