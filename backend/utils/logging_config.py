"""Logging configuration for the temperature monitoring system."""
import logging
import sys
from pathlib import Path
from config import get_config

Config = get_config()


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to DEBUG if Config.DEBUG is True, otherwise INFO.
    
    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = 'DEBUG' if Config.DEBUG else 'INFO'
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = Config.BASE_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (app.log)
    log_file = logs_dir / 'app.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (errors.log)
    error_log_file = logs_dir / 'errors.log'
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)  # Only errors and above
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

