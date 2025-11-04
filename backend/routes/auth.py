"""Authentication routes."""
from flask import Blueprint, jsonify, request, abort
from services.user_service import UserService

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

# Initialize user service
user_service = UserService()


@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    """Sign up a new user."""
    # Check if request has JSON
    if not request.is_json:
        abort(400)  # Returns standard error response {'error': 'Bad request'} from error handler
    
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        abort(400)

    try:
        user_service.create_user(username, password)
        return jsonify({'message': 'User signed up'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400



@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Login a user."""
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        abort(400)

    # Check if user exists
    if not user_service.user_exists(username):
        return jsonify({'error': 'Username does not exist'}), 400

    # Verify password
    if user_service.verify_password(username, password):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401
