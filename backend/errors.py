"""Error handlers for the Flask application."""
from typing import Tuple
from flask import Flask, jsonify, Response


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers with the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error: Exception) -> Tuple[Response, int]:
        """Handle 400 Bad Request errors."""
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(404)
    def not_found(error: Exception) -> Tuple[Response, int]:
        """Handle 404 Not Found errors."""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error: Exception) -> Tuple[Response, int]:
        """Handle 500 Internal Server Error."""
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(401)
    def unauthorized(error: Exception) -> Tuple[Response, int]:
        """Handle 401 Unauthorized errors."""
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error: Exception) -> Tuple[Response, int]:
        """Handle 403 Forbidden errors."""
        return jsonify({'error': 'Forbidden'}), 403
    
    @app.errorhandler(422)
    def unprocessable_entity(error: Exception) -> Tuple[Response, int]:
        """Handle 422 Unprocessable Entity errors."""
        return jsonify({'error': 'Unprocessable entity'}), 422

