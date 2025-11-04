"""Error handlers for the Flask application."""
import logging
from typing import Tuple
from flask import Flask, jsonify, Response
from exceptions import APIException
from constants import (
    HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_UNPROCESSABLE_ENTITY,
    HTTP_INTERNAL_SERVER_ERROR
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers with the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(APIException)
    def handle_api_exception(error: APIException) -> Tuple[Response, int]:
        """Handle custom API exceptions."""
        logger.warning(
            f"API exception: {error.message}",
            extra={'status_code': error.status_code, 'details': error.details}
        )
        return jsonify(error.to_dict()), error.status_code
    
    @app.errorhandler(HTTP_BAD_REQUEST)
    def bad_request(error: Exception) -> Tuple[Response, int]:
        """Handle 400 Bad Request errors."""
        error_message = str(error) if str(error) else 'Bad request'
        logger.warning(f"Bad request: {error_message}")
        return jsonify({'error': error_message}), HTTP_BAD_REQUEST
    
    @app.errorhandler(HTTP_NOT_FOUND)
    def not_found(error: Exception) -> Tuple[Response, int]:
        """Handle 404 Not Found errors."""
        error_message = str(error) if str(error) else 'Not found'
        logger.info(f"Not found: {error_message}")
        return jsonify({'error': error_message}), HTTP_NOT_FOUND
    
    @app.errorhandler(HTTP_INTERNAL_SERVER_ERROR)
    def internal_error(error: Exception) -> Tuple[Response, int]:
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), HTTP_INTERNAL_SERVER_ERROR
    
    @app.errorhandler(HTTP_UNAUTHORIZED)
    def unauthorized(error: Exception) -> Tuple[Response, int]:
        """Handle 401 Unauthorized errors."""
        error_message = str(error) if str(error) else 'Unauthorized'
        logger.warning(f"Unauthorized: {error_message}")
        return jsonify({'error': error_message}), HTTP_UNAUTHORIZED
    
    @app.errorhandler(HTTP_FORBIDDEN)
    def forbidden(error: Exception) -> Tuple[Response, int]:
        """Handle 403 Forbidden errors."""
        error_message = str(error) if str(error) else 'Forbidden'
        logger.warning(f"Forbidden: {error_message}")
        return jsonify({'error': error_message}), HTTP_FORBIDDEN
    
    @app.errorhandler(HTTP_UNPROCESSABLE_ENTITY)
    def unprocessable_entity(error: Exception) -> Tuple[Response, int]:
        """Handle 422 Unprocessable Entity errors."""
        error_message = str(error) if str(error) else 'Unprocessable entity'
        logger.warning(f"Unprocessable entity: {error_message}")
        return jsonify({'error': error_message}), HTTP_UNPROCESSABLE_ENTITY

