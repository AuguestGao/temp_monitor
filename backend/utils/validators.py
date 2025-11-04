"""Validation utilities for request data."""
from typing import Optional
from config import get_config

Config = get_config()


def validate_temperature(tempC: float) -> tuple[bool, Optional[str]]:
    """
    Validate temperature value.
    
    Args:
        tempC: Temperature in Celsius
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(tempC, (int, float)):
        return False, "Temperature must be a number"
    
    if tempC < Config.TEMP_MIN_CELSIUS or tempC > Config.TEMP_MAX_CELSIUS:
        return False, f"Temperature must be between {Config.TEMP_MIN_CELSIUS} and {Config.TEMP_MAX_CELSIUS}°C"
    
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validate username.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if not isinstance(username, str):
        return False, "Username must be a string"
    
    username = username.strip()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be no more than 50 characters long"
    
    # Allow alphanumeric and underscore only
    if not username.replace('_', '').isalnum():
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if not isinstance(password, str):
        return False, "Password must be a string"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 128:
        return False, "Password must be no more than 128 characters long"
    
    return True, None


def validate_limit(limit: Optional[int]) -> int:
    """
    Validate and normalize limit parameter.
    
    Args:
        limit: Limit value to validate
        
    Returns:
        Validated limit value
    """
    if limit is None:
        return Config.API_READINGS_DEFAULT_LIMIT
    
    try:
        limit = int(limit)
        return min(max(limit, 1), Config.API_READINGS_MAX_LIMIT)
    except (ValueError, TypeError):
        return Config.API_READINGS_DEFAULT_LIMIT


def validate_offset(offset: Optional[int]) -> int:
    """
    Validate and normalize offset parameter.
    
    Args:
        offset: Offset value to validate
        
    Returns:
        Validated offset value (non-negative)
    """
    if offset is None:
        return Config.API_READINGS_DEFAULT_OFFSET
    
    try:
        offset = int(offset)
        return max(offset, 0)
    except (ValueError, TypeError):
        return Config.API_READINGS_DEFAULT_OFFSET

