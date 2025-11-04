"""Custom exception classes for the temperature monitoring system."""
from constants import (
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_UNAUTHORIZED,
    HTTP_FORBIDDEN,
    HTTP_UNPROCESSABLE_ENTITY
)


class APIException(Exception):
    """Base exception class for API errors."""
    
    def __init__(self, message: str, status_code: int = HTTP_BAD_REQUEST, details: dict = None):
        """
        Initialize API exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        result = {'error': self.message}
        if self.details:
            result['details'] = self.details
        return result


class ValidationError(APIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field name that failed validation
            details: Additional error details
        """
        if field:
            details = details or {}
            details['field'] = field
        super().__init__(message, status_code=HTTP_BAD_REQUEST, details=details)


class NotFoundError(APIException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource: str, identifier: str = None):
        """
        Initialize not found error.
        
        Args:
            resource: Resource type that was not found
            identifier: Identifier that was not found
        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        
        details = {'resource': resource}
        if identifier:
            details['identifier'] = identifier
        
        super().__init__(message, status_code=HTTP_NOT_FOUND, details=details)


class AuthenticationError(APIException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
        """
        super().__init__(message, status_code=HTTP_UNAUTHORIZED)


class AuthorizationError(APIException):
    """Exception for authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        """
        Initialize authorization error.
        
        Args:
            message: Error message
        """
        super().__init__(message, status_code=HTTP_FORBIDDEN)


class UnprocessableEntityError(APIException):
    """Exception for unprocessable entity errors."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize unprocessable entity error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message, status_code=HTTP_UNPROCESSABLE_ENTITY, details=details)

