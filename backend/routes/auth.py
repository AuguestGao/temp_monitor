"""Authentication routes."""
import json
import bcrypt
from flask import Blueprint, jsonify, request, abort
from config import get_config

# Get configuration
Config = get_config()

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/signup', methods=['POST'])
def signup():
    """Sign up a new user."""
    # Check if request has JSON
    if not request.is_json:
        abort(400) # Returns standard error response {'error': 'Bad request'} from error handler
    
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        abort(400)

    if get_user(username)[0] is not None:
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    add_user_to_json_file(username, hashed_password)

    # signup_user(email, password)
    return jsonify({'message': 'User signed up'}), 201



@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Login a user."""
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not username or not password:
        abort(400)

    username, hashed_password = get_user(username)


    if username is None:
        return jsonify({'error': 'Username does not exist'}), 400


    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401



def read_users_json_file():
    """
    Read users from a JSON file and return as a list of dictionaries.
    
    Returns:
        list: List of user dictionaries. Returns empty list if file doesn't exist or is empty.
    """
    json_file_path = Config.USERS_JSON_FILE
    
    # Return empty list if file doesn't exist
    if not json_file_path.exists():
        return []
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            # Parse JSON - expects array of objects like: [{"username": "user1", "password": "pass1"}, ...]
            data = json.load(file)
            # Ensure it's a list (in case JSON contains a single dict, wrap it)
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                return []
    except json.JSONDecodeError:
        # If JSON is invalid, return empty list
        return []
    except Exception as e:
        # Handle any other errors
        print(f"Error reading users file: {e}")
        return []

def add_user_to_json_file(username, hashed_password):
    """
    Add a user to a JSON file.
    
    Args:
        username: The username of the user to add.
        hashed_password: The hashed password of the user to add.
    """
    users = read_users_json_file()
    users.append({'username': username, 'password': hashed_password})
    write_users_json_file(users)

def write_users_json_file(users):
    """
    Write users to a JSON file. Creates the file and directory if they don't exist.
    Replaces any existing content.
    
    Args:
        users: The list of users to write to the file.
    """
    json_file_path = Config.USERS_JSON_FILE
    
    # Create storage directory if it doesn't exist
    Config.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write to file (mode 'w' creates file if it doesn't exist and replaces old content)
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(users, file, ensure_ascii=False, indent=4)

def get_user(username):
    """
    Check if a username exists in the JSON file.
    
    Args:
        username: The username to check.
    """
    users = read_users_json_file()
    for user in users:
        if user.get('username') == username:
            return (user, user.get('password'))
    return (None, None)
