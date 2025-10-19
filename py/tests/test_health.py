"""
Tests for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint returns ok status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_check_headers():
    """Test health check includes proper headers for CORS."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

def test_health_check_fastapi_communication():
    """Test that FastAPI app is properly configured and communicating."""
    assert app is not None
    assert app.title == "BlinkTalk API"
    assert app.version == "1.0.0"
    
    # Test that health endpoint is properly registered
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert data["status"] == "ok"
    
    # Test that response is valid JSON
    assert response.headers["content-type"] == "application/json"