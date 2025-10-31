"""
Flask application for temperature monitoring system.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
from routes.auth import auth_bp
from routes.health import health_bp
from routes.readings import readings_bp
from errors import register_error_handlers

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for frontend integration
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Get configuration from environment variables
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Register API blueprints
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(readings_bp)

# Register error handlers
register_error_handlers(app)


if __name__ == '__main__':
    # Run the Flask app with auto-reload enabled
    # Flask automatically reloads on file changes when debug=True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=True)
