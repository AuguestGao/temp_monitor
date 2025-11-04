"""User service for handling user business logic."""
import bcrypt
from typing import Optional, Tuple
from models.user import User
from storage.file_storage import UserStorage
from exceptions import ValidationError


class UserService:
    """Service for user-related operations."""
    
    def __init__(self):
        """Initialize user service with storage."""
        self.storage = UserStorage()
    
    def get_user(self, username: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            Tuple of (User object, hashed_password) or (None, None) if not found
        """
        user_data = self.storage.get_user_by_username(username)
        if user_data:
            user = User.from_dict(user_data)
            return (user, user_data.get('password'))
        return (None, None)
    
    def user_exists(self, username: str) -> bool:
        """
        Check if a user exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        user, _ = self.get_user(username)
        return user is not None
    
    def create_user(self, username: str, password: str) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Created User object
            
        Raises:
            ValidationError: If username already exists
        """
        if self.user_exists(username):
            raise ValidationError("Username already exists", field='username')
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username=username, password=hashed_password)
        
        self.storage.add_user(username, hashed_password)
        return user
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Verify user password.
        
        Args:
            username: Username
            password: Plain text password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        user, hashed_password = self.get_user(username)
        if user is None or hashed_password is None:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

