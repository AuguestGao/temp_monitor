"""Tests for authentication routes."""
import pytest
import time
from constants import (
    HTTP_OK,
    HTTP_CREATED,
    HTTP_BAD_REQUEST,
    HTTP_UNAUTHORIZED,
    HTTP_NOT_FOUND,
    HTTP_TOO_MANY_REQUESTS
)
from services.jwt_service import jwt_service
from services.token_storage import token_storage
from services.user_service import UserService


class TestSignup:
    """Tests for signup endpoint."""
    
    def test_signup_success(self, client):
        """Test successful user signup."""
        username = f'testuser_{int(time.time())}'
        password = 'testpass123'
        
        response = client.post(
            '/api/signup',
            json={'username': username, 'password': password}
        )
        
        assert response.status_code == HTTP_CREATED
        data = response.get_json()
        assert data['message'] == 'User signed up'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert isinstance(data['access_token'], str)
        assert isinstance(data['refresh_token'], str)
    
    def test_signup_duplicate_username(self, client):
        """Test signup with existing username."""
        username = f'testuser_{int(time.time())}'
        password = 'testpass123'
        
        # Create user first
        client.post(
            '/api/signup',
            json={'username': username, 'password': password}
        )
        
        # Try to create again
        response = client.post(
            '/api/signup',
            json={'username': username, 'password': password}
        )
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert 'error' in data
        assert 'already exists' in data['error'].lower()
    
    def test_signup_invalid_username(self, client):
        """Test signup with invalid username."""
        response = client.post(
            '/api/signup',
            json={'username': 'ab', 'password': 'testpass123'}  # Too short
        )
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert 'error' in data
        assert 'username' in data.get('details', {}).get('field', '')
    
    def test_signup_invalid_password(self, client):
        """Test signup with invalid password."""
        response = client.post(
            '/api/signup',
            json={'username': 'testuser', 'password': 'short'}  # Too short
        )
        
        assert response.status_code == HTTP_BAD_REQUEST
        data = response.get_json()
        assert 'error' in data
        assert 'password' in data.get('details', {}).get('field', '')
    
    def test_signup_missing_fields(self, client):
        """Test signup with missing fields."""
        response = client.post(
            '/api/signup',
            json={'username': 'testuser'}
        )
        
        assert response.status_code == HTTP_BAD_REQUEST
    
    def test_signup_not_json(self, client):
        """Test signup without JSON content type."""
        response = client.post(
            '/api/signup',
            data='not json'
        )
        
        assert response.status_code == HTTP_BAD_REQUEST


class TestLogin:
    """Tests for login endpoint."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            '/api/login',
            json={
                'username': test_user['username'],
                'password': test_user['password']
            }
        )
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert isinstance(data['access_token'], str)
        assert isinstance(data['refresh_token'], str)
    
    def test_login_invalid_username(self, client):
        """Test login with non-existent username."""
        from constants import HTTP_NOT_FOUND
        
        response = client.post(
            '/api/login',
            json={'username': 'nonexistent', 'password': 'password123'}
        )
        
        assert response.status_code == HTTP_NOT_FOUND
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            '/api/login',
            json={
                'username': test_user['username'],
                'password': 'wrongpassword'
            }
        )
        
        assert response.status_code == HTTP_UNAUTHORIZED
        data = response.get_json()
        assert 'error' in data
        assert 'password' in data['error'].lower()
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        response = client.post(
            '/api/login',
            json={'username': 'testuser'}
        )
        
        assert response.status_code == HTTP_BAD_REQUEST
    
    def test_login_rate_limit(self, client, test_user):
        """Test rate limiting on login."""
        username = test_user['username']
        wrong_password = 'wrongpass'
        
        # Make multiple failed attempts
        for _ in range(6):  # Exceed max attempts (5)
            response = client.post(
                '/api/login',
                json={'username': username, 'password': wrong_password}
            )
        
        # Next attempt should be rate limited
        response = client.post(
            '/api/login',
            json={'username': username, 'password': wrong_password}
        )
        
        assert response.status_code == HTTP_TOO_MANY_REQUESTS
        data = response.get_json()
        assert 'error' in data
        assert 'retry_after' in data.get('details', {})


class TestRefreshToken:
    """Tests for refresh token endpoint."""
    
    def test_refresh_token_success(self, client, test_user, auth_headers):
        """Test successful token refresh."""
        # Login first to get tokens
        login_response = client.post(
            '/api/login',
            json={
                'username': test_user['username'],
                'password': test_user['password']
            }
        )
        
        assert login_response.status_code == HTTP_OK
        old_refresh_token = login_response.get_json()['refresh_token']
        
        # Verify old token is active before refresh
        username = test_user['username']
        assert token_storage.is_refresh_token_active(username, old_refresh_token)
        
        # Add small delay to ensure new token has different timestamp
        time.sleep(1)
        
        # Refresh token
        response = client.post(
            '/api/refresh-token',
            headers=auth_headers(old_refresh_token)
        )
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert data['message'] == 'Token refreshed'
        assert 'access_token' in data
        assert 'refresh_token' in data
        new_refresh_token = data['refresh_token']
        
        # Verify old token is revoked (token rotation)
        assert not token_storage.is_refresh_token_active(username, old_refresh_token), "Old refresh token should be revoked"
        # Verify new token is active
        assert token_storage.is_refresh_token_active(username, new_refresh_token), "New refresh token should be active"
    
    def test_refresh_token_missing(self, client):
        """Test refresh without token."""
        response = client.post('/api/refresh-token')
        
        assert response.status_code == HTTP_UNAUTHORIZED
        data = response.get_json()
        assert 'error' in data
    
    def test_refresh_token_invalid(self, client, auth_headers):
        """Test refresh with invalid token."""
        response = client.post(
            '/api/refresh-token',
            headers=auth_headers('invalid.token.here')
        )
        
        assert response.status_code == HTTP_UNAUTHORIZED
        data = response.get_json()
        assert 'error' in data
    
    def test_refresh_token_expired(self, client, auth_headers):
        """Test refresh with expired token."""
        # Generate expired token (mock)
        from datetime import datetime, timezone, timedelta
        import jwt
        from config import get_config
        
        Config = get_config()
        expired_payload = {
            'username': 'testuser',
            'type': 'refresh',
            'exp': datetime.now(timezone.utc) - timedelta(seconds=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, Config.JWT_SECRET_KEY, algorithm='HS256')
        
        response = client.post(
            '/api/refresh-token',
            headers=auth_headers(expired_token)
        )
        
        assert response.status_code == HTTP_UNAUTHORIZED
    
    def test_refresh_token_revoked(self, client, test_user, auth_headers):
        """Test refresh with revoked token."""
        # Login first to get tokens
        login_response = client.post(
            '/api/login',
            json={
                'username': test_user['username'],
                'password': test_user['password']
            }
        )
        
        assert login_response.status_code == HTTP_OK
        refresh_token = login_response.get_json()['refresh_token']
        
        # Revoke token
        username = test_user['username']
        token_storage.revoke_refresh_token(username, refresh_token)
        
        # Try to refresh
        response = client.post(
            '/api/refresh-token',
            headers=auth_headers(refresh_token)
        )
        
        assert response.status_code == HTTP_UNAUTHORIZED
        data = response.get_json()
        assert 'error' in data
        assert 'revoked' in data['error'].lower() or 'inactive' in data['error'].lower()


class TestLogout:
    """Tests for logout endpoint."""
    
    def test_logout_success(self, client, test_user, auth_headers):
        """Test successful logout."""
        # Login first to get tokens
        login_response = client.post(
            '/api/login',
            json={
                'username': test_user['username'],
                'password': test_user['password']
            }
        )
        
        assert login_response.status_code == HTTP_OK
        access_token = login_response.get_json()['access_token']
        
        # Logout
        response = client.post(
            '/api/logout',
            headers=auth_headers(access_token)
        )
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert data['message'] == 'Logged out successfully'
        
        # Try to use token after logout (should still work - idempotent)
        response = client.post(
            '/api/logout',
            headers=auth_headers(access_token)
        )
        assert response.status_code == HTTP_OK  # Should still work (idempotent)
    
    def test_logout_all_devices(self, client, test_user, auth_headers):
        """Test logout from all devices."""
        # Login first to get tokens
        login_response = client.post(
            '/api/login',
            json={
                'username': test_user['username'],
                'password': test_user['password']
            }
        )
        
        assert login_response.status_code == HTTP_OK
        access_token = login_response.get_json()['access_token']
        refresh_token = login_response.get_json()['refresh_token']
        
        # Logout all
        response = client.post(
            '/api/logout',
            headers=auth_headers(access_token),
            json={'revoke_all': True}
        )
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert 'all devices' in data['message'].lower()
        assert 'revoked_tokens' in data
        
        # Try to refresh (should fail)
        response = client.post(
            '/api/refresh-token',
            headers=auth_headers(refresh_token)
        )
        
        assert response.status_code == HTTP_UNAUTHORIZED
    
    def test_logout_without_token(self, client):
        """Test logout without token (should be idempotent)."""
        response = client.post('/api/logout')
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert data['message'] == 'Logged out successfully'


class TestRateLimitReset:
    """Tests for rate limit reset endpoint."""
    
    def test_reset_rate_limit_current_ip(self, client):
        """Test reset rate limit for current IP."""
        response = client.post('/api/rate-limit/reset')
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert 'message' in data
    
    def test_reset_rate_limit_all(self, client):
        """Test reset all rate limits with key."""
        from config import get_config
        Config = get_config()
        
        response = client.post(
            '/api/rate-limit/reset',
            json={'reset_key': Config.RATE_LIMIT_RESET_KEY}
        )
        
        assert response.status_code == HTTP_OK
        data = response.get_json()
        assert 'all' in data['message'].lower()
        assert 'reset_count' in data

