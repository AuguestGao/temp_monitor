"""Timezone conversion utilities."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Timezone constants
TORONTO_TZ = ZoneInfo('America/Toronto')
UTC_TZ = ZoneInfo('UTC')


def convert_toronto_to_utc(toronto_datetime_str: str) -> datetime:
    """
    Convert a Toronto timezone datetime string to UTC datetime.
    Handles daylight saving time automatically via zoneinfo.
    
    Args:
        toronto_datetime_str: ISO format datetime string in Toronto timezone
                             (e.g., "2025-11-04T10:00:00" or "2025-11-04T10:00:00-05:00")
        
    Returns:
        UTC datetime object
        
    Raises:
        ValueError: If datetime string cannot be parsed
    """
    # Parse the datetime string
    # Remove 'Z' if present (replace with +00:00 for parsing, then we'll override)
    datetime_str = toronto_datetime_str.replace('Z', '+00:00')
    
    try:
        dt = datetime.fromisoformat(datetime_str)
    except ValueError:
        # Try parsing without timezone info
        try:
            dt = datetime.fromisoformat(toronto_datetime_str)
        except ValueError as e:
            logger.error(f"Failed to parse datetime string: {toronto_datetime_str}")
            raise ValueError(f"Invalid datetime format: {e}") from e
    
    # If datetime has timezone info, remove it and treat as Toronto time
    # (Input is always in Toronto time per requirements)
    if dt.tzinfo is not None:
        # Remove timezone info and treat as naive Toronto time
        dt = dt.replace(tzinfo=None)
    
    # Attach Toronto timezone (zoneinfo handles DST automatically)
    dt_toronto = dt.replace(tzinfo=TORONTO_TZ)
    
    # Convert to UTC
    return dt_toronto.astimezone(UTC_TZ)


def convert_utc_to_toronto(utc_datetime_str: str) -> str:
    """
    Convert a UTC datetime string to Toronto timezone datetime string.
    Handles daylight saving time automatically via zoneinfo.
    
    Args:
        utc_datetime_str: ISO format datetime string in UTC
                        (e.g., "2025-11-04T04:04:25.206644Z" or "2025-11-04T04:04:25+00:00")
        
    Returns:
        ISO format datetime string in Toronto timezone
        (e.g., "2025-11-04T00:04:25.206644-04:00" for EDT or "-05:00" for EST)
        
    Raises:
        ValueError: If datetime string cannot be parsed
    """
    try:
        # Parse the UTC datetime string
        # Handle 'Z' suffix (UTC indicator)
        datetime_str = utc_datetime_str.replace('Z', '+00:00')
        dt_utc = datetime.fromisoformat(datetime_str)
        
        # Ensure it's in UTC
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=UTC_TZ)
        
        # Convert to Toronto timezone
        dt_toronto = dt_utc.astimezone(TORONTO_TZ)
        
        # Return as ISO format string with timezone offset
        return dt_toronto.isoformat()
    except ValueError as e:
        logger.error(f"Failed to parse UTC datetime string: {utc_datetime_str}")
        raise ValueError(f"Invalid UTC datetime format: {e}") from e

