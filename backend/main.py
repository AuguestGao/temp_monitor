"""
Flask application for temperature monitoring system.
"""

from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.health import health_bp
from routes.readings import readings_bp
from errors import register_error_handlers
from config import get_config

# Get configuration class based on environment
Config = get_config()

# Initialize Flask app
app: Flask = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Enable CORS for frontend integration
CORS(app)

# Register API blueprints
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(readings_bp)

# Register error handlers
register_error_handlers(app)


if __name__ == '__main__':
    # Run the Flask app with auto-reload enabled
    # Flask automatically reloads on file changes when debug=True
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=Config.DEBUG
    )
