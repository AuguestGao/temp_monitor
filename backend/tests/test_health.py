"""Tests for health routes."""
import pytest
from constants import HTTP_OK


def test_index_endpoint(client):
    """Test the root health check endpoint."""
    response = client.get('/')
    
    assert response.status_code == HTTP_OK
    assert response.is_json
    data = response.get_json()
    
    assert data['status'] == 'ok'
    assert data['message'] == 'Temperature Monitor API'
    assert 'version' in data
    assert isinstance(data['version'], str)


def test_health_endpoint(client):
    """Test the /api/health endpoint."""
    response = client.get('/api/health')
    
    assert response.status_code == HTTP_OK
    assert response.is_json
    data = response.get_json()
    
    assert data['status'] == 'healthy'


def test_health_endpoint_method_not_allowed(client):
    """Test that POST method is not allowed on health endpoints."""
    response = client.post('/api/health')
    assert response.status_code == 405  # Method Not Allowed


def test_index_endpoint_method_not_allowed(client):
    """Test that POST method is not allowed on index endpoint."""
    response = client.post('/')
    assert response.status_code == 405  # Method Not Allowed

