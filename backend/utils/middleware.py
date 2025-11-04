"""Middleware for Flask application."""
import time
import logging
from typing import Callable
from flask import request, g

logger = logging.getLogger(__name__)


def request_logging_middleware(app) -> None:
    """
    Add request/response logging middleware to Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def log_request_info() -> None:
        """Log incoming request information."""
        g.start_time = time.time()
        
        logger.info(
            f"Incoming request: {request.method} {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }
        )
    
    @app.after_request
    def log_response_info(response) -> None:
        """Log response information."""
        duration = time.time() - g.get('start_time', 0)
        
        logger.info(
            f"Response: {request.method} {request.path} - {response.status_code} ({duration:.3f}s)",
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': duration
            }
        )
        
        return response
    
    @app.errorhandler(500)
    def log_internal_error(error: Exception) -> None:
        """Log internal server errors."""
        logger.error(
            f"Internal server error: {str(error)}",
            exc_info=True,
            extra={
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr
            }
        )

