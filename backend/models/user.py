"""User data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User model representing a system user."""
    username: str
    password: str  # Hashed password
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'username': self.username,
            'password': self.password
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['User']:
        """Create User from dictionary."""
        if not data or 'username' not in data or 'password' not in data:
            return None
        return cls(
            username=data['username'],
            password=data['password']
        )

