"""Pytest configuration and fixtures."""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from flask import Flask
from flask_cors import CORS
from errors import register_error_handlers
from config import get_config
from services.token_storage import token_storage
from services.jwt_service import jwt_service
from utils.rate_limiter import rate_limiter


@pytest.fixture(scope='function')
def test_config():
    """Create test configuration with isolated storage."""
    # Create temporary storage directory
    test_storage = tempfile.mkdtemp(prefix='temp_monitor_test_')
    
    # Override config for testing
    Config = get_config()
    original_storage_dir = Config.STORAGE_DIR
    original_users_file = Config.USERS_JSON_FILE
    
    # Set test paths
    Config.STORAGE_DIR = Path(test_storage)
    Config.USERS_JSON_FILE = Config.STORAGE_DIR / 'test_users.json'
    
    # Ensure test storage directory exists
    Config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    yield Config
    
    # Cleanup: Remove test storage directory and all its contents
    Config.STORAGE_DIR = original_storage_dir
    Config.USERS_JSON_FILE = original_users_file
    try:
        shutil.rmtree(test_storage, ignore_errors=True)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture(scope='function')
def app(test_config):
    """Create Flask application for testing with isolated storage."""
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    
    # IMPORTANT: Import routes AFTER config is updated so UserService uses test storage
    # This ensures UserService in routes.auth uses the updated Config.USERS_JSON_FILE
    from routes.auth import auth_bp
    from routes.health import health_bp
    from routes.readings import readings_bp
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Clear token storage and rate limiter (in-memory, reset between tests)
    token_storage.active_refresh_tokens.clear()
    token_storage.blacklisted_tokens.clear()
    rate_limiter.failed_attempts.clear()
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(readings_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Enable CORS
    CORS(app)
    
    yield app
    
    # Post-test cleanup: Clear in-memory state
    token_storage.active_refresh_tokens.clear()
    token_storage.blacklisted_tokens.clear()
    rate_limiter.failed_attempts.clear()
    
    # Cleanup: Remove all users from test storage
    try:
        from services.user_service import UserService
        user_service = UserService()
        user_service.storage.write([])  # Clear all users
    except Exception:
        pass


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers():
    """Helper to create auth headers."""
    def _create_headers(token: str) -> dict:
        return {'Authorization': f'Bearer {token}'}
    return _create_headers


@pytest.fixture(scope='function')
def test_user(test_config):
    """Create a test user in isolated storage and clean up after."""
    # Import here to ensure Config is already updated by test_config fixture
    from services.user_service import UserService
    
    # Create fresh UserService instance that will use the updated Config
    # This ensures it reads from the test storage, not production
    user_service = UserService()
    
    username = 'testuser'
    password = 'testpass123'
    
    # Remove user if exists (cleanup from previous test)
    try:
        users = user_service.storage.read()
        users = [u for u in users if u.get('username') != username]
        user_service.storage.write(users)
    except Exception:
        pass
    
    # Create user
    try:
        if not user_service.user_exists(username):
            user_service.create_user(username, password)
    except Exception as e:
        # If creation fails, log and continue
        import logging
        logging.getLogger(__name__).warning(f"Failed to create test user: {e}")
    
    yield {'username': username, 'password': password}
    
    # Cleanup: Remove test user from storage
    try:
        users = user_service.storage.read()
        users = [u for u in users if u.get('username') != username]
        user_service.storage.write(users)
    except Exception:
        pass  # Ignore cleanup errors

