"""Error handlers for the Flask application."""
import logging
from typing import Tuple
from flask import Flask, jsonify, Response
from exceptions import APIException

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
    
    @app.errorhandler(400)
    def bad_request(error: Exception) -> Tuple[Response, int]:
        """Handle 400 Bad Request errors."""
        error_message = str(error) if str(error) else 'Bad request'
        logger.warning(f"Bad request: {error_message}")
        return jsonify({'error': error_message}), 400
    
    @app.errorhandler(404)
    def not_found(error: Exception) -> Tuple[Response, int]:
        """Handle 404 Not Found errors."""
        error_message = str(error) if str(error) else 'Not found'
        logger.info(f"Not found: {error_message}")
        return jsonify({'error': error_message}), 404
    
    @app.errorhandler(500)
    def internal_error(error: Exception) -> Tuple[Response, int]:
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(401)
    def unauthorized(error: Exception) -> Tuple[Response, int]:
        """Handle 401 Unauthorized errors."""
        error_message = str(error) if str(error) else 'Unauthorized'
        logger.warning(f"Unauthorized: {error_message}")
        return jsonify({'error': error_message}), 401
    
    @app.errorhandler(403)
    def forbidden(error: Exception) -> Tuple[Response, int]:
        """Handle 403 Forbidden errors."""
        error_message = str(error) if str(error) else 'Forbidden'
        logger.warning(f"Forbidden: {error_message}")
        return jsonify({'error': error_message}), 403
    
    @app.errorhandler(422)
    def unprocessable_entity(error: Exception) -> Tuple[Response, int]:
        """Handle 422 Unprocessable Entity errors."""
        error_message = str(error) if str(error) else 'Unprocessable entity'
        logger.warning(f"Unprocessable entity: {error_message}")
        return jsonify({'error': error_message}), 422

