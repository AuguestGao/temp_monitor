"""
Configuration management for the temperature monitoring system.

This module provides configuration settings with environment variable support.
All settings can be overridden via environment variables.
"""
import os
from pathlib import Path
from typing import List, Type


class Config:
    """Configuration class with default settings."""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Server configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Application info
    APP_VERSION = os.environ.get('APP_VERSION', '0.1.0')
    
    # Storage paths (relative to backend directory)
    BASE_DIR = Path(__file__).parent
    STORAGE_DIR = BASE_DIR / 'storage'
    USERS_JSON_FILE = STORAGE_DIR / 'users.json'
    TEMP_DATA_CSV_FILE = STORAGE_DIR / 'temp_data.csv'
    
    # API configuration
    API_READINGS_DEFAULT_LIMIT = int(os.environ.get('API_READINGS_DEFAULT_LIMIT', 1000))
    API_READINGS_MAX_LIMIT = int(os.environ.get('API_READINGS_MAX_LIMIT', 10000))
    API_READINGS_DEFAULT_OFFSET = int(os.environ.get('API_READINGS_DEFAULT_OFFSET', 0))
    
    # Temperature validation
    TEMP_MIN_CELSIUS = float(os.environ.get('TEMP_MIN_CELSIUS', -55.0))
    TEMP_MAX_CELSIUS = float(os.environ.get('TEMP_MAX_CELSIUS', 125.0))
    
    # Serial communication configuration
    SERIAL_BAUD_RATE = int(os.environ.get('SERIAL_BAUD_RATE', 9600))
    SERIAL_TIMEOUT = float(os.environ.get('SERIAL_TIMEOUT', 1.0))
    SERIAL_READ_DELAY = float(os.environ.get('SERIAL_READ_DELAY', 0.1))
    
    # Arduino vendor IDs for auto-detection
    ARDUINO_VENDOR_IDS = [0x2341, 0x2A03, 0x239A]  # Arduino, Adafruit, etc.
    
    # Rate limiting configuration
    RATE_LIMIT_MAX_ATTEMPTS = int(os.environ.get('RATE_LIMIT_MAX_ATTEMPTS', 5))
    RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('RATE_LIMIT_WINDOW_SECONDS', 300))  # 5 minutes
    RATE_LIMIT_LOCKOUT_DURATION = int(os.environ.get('RATE_LIMIT_LOCKOUT_DURATION', 900))  # 15 minutes
    RATE_LIMIT_RESET_KEY = os.environ.get('RATE_LIMIT_RESET_KEY', 'clear')
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)  # Use SECRET_KEY if not set
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRES_IN = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_IN', 900))  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES_IN = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_IN', 604800))  # 7 days


def get_default_serial_ports() -> List[str]:
    """
    Get default serial port names based on the operating system.
    
    Returns:
        List of default serial port names for the current platform.
    """
    import platform
    system = platform.system()
    
    if system == 'Windows':
        return ['COM3', 'COM4', 'COM5']
    elif system == 'Linux':
        # Raspberry Pi common ports
        return ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/ttyAMA0']
    elif system == 'Darwin':  # macOS
        return ['/dev/tty.usbserial', '/dev/tty.usbmodem']
    else:
        return []


def get_config() -> Type[Config]:
    """
    Get configuration class.
    
    Returns:
        Config class type
    """
    return Config

