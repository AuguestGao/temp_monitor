"""
Flask application for temperature monitoring system.
"""

import logging
from flask import Flask
from flask_cors import CORS
from routes.auth import auth_bp
from routes.health import health_bp
from routes.readings import readings_bp
from errors import register_error_handlers
from config import get_config
from utils.logging_config import setup_logging
from utils.middleware import request_logging_middleware

# Set up logging first
setup_logging()

# Get configuration class based on environment
Config = get_config()

# Initialize Flask app
app: Flask = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Enable CORS for frontend integration
CORS(app)

# Add request/response logging middleware
request_logging_middleware(app)

# Register API blueprints
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(readings_bp)

# Register error handlers
register_error_handlers(app)

# Load CSV data into memory on startup
# This happens when ReadingService is initialized, which creates ReadingStorage
# ReadingStorage loads data in its __init__ method
from services.reading_service import ReadingService
from storage.reading_storage import ReadingStorage
logger = logging.getLogger(__name__)
try:
    # Initialize storage to load CSV data
    storage = ReadingStorage()
    logger.info(f"CSV data loaded on startup: {len(storage._readings_cache)} readings in memory")
except Exception as e:
    logger.error(f"Failed to load CSV data on startup: {e}", exc_info=True)


def run_backend():
    """Entry point for running the development server."""
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=Config.DEBUG
    )


if __name__ == '__main__':
    run_backend()
