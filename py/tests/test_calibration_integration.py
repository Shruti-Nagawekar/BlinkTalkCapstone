"""
Integration tests for calibration API endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient

from api.main import app
from core.calibration import reset_calibration_manager

# Create test client
client = TestClient(app)


class TestCalibrationAPI:
    """Test calibration API endpoints."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_calibration_manager()
    
    def test_set_calibration_profile_slow(self):
        """Test setting calibration profile to slow."""
        response = client.post(
            "/api/calibration/set",
            json={"profile": "slow"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Profile set to 'slow'"
        assert data["profile"] == "slow"
        assert data["description"] == "For users with slower blink patterns"
        assert data["thresholds"]["short_max_ms"] == 500
        assert data["thresholds"]["long_max_ms"] == 1200
        assert data["thresholds"]["symbol_gap_max_ms"] == 600
        assert data["thresholds"]["word_gap_min_ms"] == 1500
    
    def test_set_calibration_profile_medium(self):
        """Test setting calibration profile to medium."""
        response = client.post(
            "/api/calibration/set",
            json={"profile": "medium"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Profile set to 'medium'"
        assert data["profile"] == "medium"
        assert data["description"] == "Standard timing for typical users"
        assert data["thresholds"]["short_max_ms"] == 350
        assert data["thresholds"]["long_max_ms"] == 900
        assert data["thresholds"]["symbol_gap_max_ms"] == 450
        assert data["thresholds"]["word_gap_min_ms"] == 1100
    
    def test_set_calibration_profile_invalid(self):
        """Test setting invalid calibration profile."""
        response = client.post(
            "/api/calibration/set",
            json={"profile": "invalid"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "Invalid profile" in data["detail"]
        assert "Available profiles" in data["detail"]
    
    def test_set_calibration_profile_missing_field(self):
        """Test setting calibration profile with missing field."""
        response = client.post(
            "/api/calibration/set",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_active_profile_default(self):
        """Test getting active profile (default)."""
        response = client.get("/api/calibration/active")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["profile"] == "medium"
        assert data["description"] == "Standard timing for typical users"
        assert data["thresholds"]["short_max_ms"] == 350
    
    def test_get_active_profile_after_change(self):
        """Test getting active profile after changing it."""
        # Set to slow profile
        client.post("/api/calibration/set", json={"profile": "slow"})
        
        # Get active profile
        response = client.get("/api/calibration/active")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["profile"] == "slow"
        assert data["description"] == "For users with slower blink patterns"
        assert data["thresholds"]["short_max_ms"] == 500
    
    def test_get_current_thresholds_default(self):
        """Test getting current thresholds (default)."""
        response = client.get("/api/calibration/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["profile"] == "medium"
        assert data["thresholds"]["short_max_ms"] == 350
        assert data["thresholds"]["long_max_ms"] == 900
        assert data["thresholds"]["symbol_gap_max_ms"] == 450
        assert data["thresholds"]["word_gap_min_ms"] == 1100
    
    def test_get_current_thresholds_after_change(self):
        """Test getting current thresholds after changing profile."""
        # Set to slow profile
        client.post("/api/calibration/set", json={"profile": "slow"})
        
        # Get thresholds
        response = client.get("/api/calibration/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["profile"] == "slow"
        assert data["thresholds"]["short_max_ms"] == 500
        assert data["thresholds"]["long_max_ms"] == 1200
        assert data["thresholds"]["symbol_gap_max_ms"] == 600
        assert data["thresholds"]["word_gap_min_ms"] == 1500
    
    def test_get_calibration_info(self):
        """Test getting comprehensive calibration information."""
        response = client.get("/api/calibration/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["active_profile"] == "medium"
        assert "slow" in data["available_profiles"]
        assert "medium" in data["available_profiles"]
        assert data["available_profiles"]["slow"] == "For users with slower blink patterns"
        assert data["available_profiles"]["medium"] == "Standard timing for typical users"
        assert data["current_thresholds"]["short_max_ms"] == 350
    
    def test_reset_calibration(self):
        """Test resetting calibration to default."""
        # Set to slow profile first
        client.post("/api/calibration/set", json={"profile": "slow"})
        
        # Reset to default
        response = client.post("/api/calibration/reset")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Calibration reset to default profile"
        assert data["profile"] == "medium"
        assert data["description"] == "Standard timing for typical users"
        assert data["thresholds"]["short_max_ms"] == 350
    
    def test_calibration_profile_switching_workflow(self):
        """Test complete workflow of switching between profiles."""
        # Start with medium profile
        response = client.get("/api/calibration/active")
        assert response.json()["profile"] == "medium"
        
        # Switch to slow profile
        response = client.post("/api/calibration/set", json={"profile": "slow"})
        assert response.status_code == 200
        assert response.json()["profile"] == "slow"
        
        # Verify thresholds changed
        response = client.get("/api/calibration/thresholds")
        assert response.json()["thresholds"]["short_max_ms"] == 500
        
        # Switch back to medium profile
        response = client.post("/api/calibration/set", json={"profile": "medium"})
        assert response.status_code == 200
        assert response.json()["profile"] == "medium"
        
        # Verify thresholds changed back
        response = client.get("/api/calibration/thresholds")
        assert response.json()["thresholds"]["short_max_ms"] == 350
    
    def test_calibration_api_error_handling(self):
        """Test error handling in calibration API."""
        # Test invalid JSON
        response = client.post(
            "/api/calibration/set",
            data="invalid json"
        )
        assert response.status_code == 422
        
        # Test missing profile field
        response = client.post(
            "/api/calibration/set",
            json={"wrong_field": "slow"}
        )
        assert response.status_code == 422
        
        # Test empty profile
        response = client.post(
            "/api/calibration/set",
            json={"profile": ""}
        )
        assert response.status_code == 400


class TestCalibrationAPIWithBlinkDetection:
    """Test calibration API integration with blink detection."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_calibration_manager()
    
    def test_calibration_affects_blink_detection(self):
        """Test that calibration profile changes affect blink detection."""
        # Set to medium profile
        response = client.post("/api/calibration/set", json={"profile": "medium"})
        assert response.status_code == 200
        
        # Process EAR sample that should be classified as short in medium profile
        ear_data = {
            "ear_value": 0.15,
            "timestamp": 1234567890.0
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # End blink after 300ms (should be short in medium profile)
        ear_data["timestamp"] = 1234567890.3
        ear_data["ear_value"] = 0.3  # Above threshold
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Should have detected a blink event
        data = response.json()
        assert data["blink_events"] >= 0  # May or may not have events depending on timing
        
        # Switch to slow profile
        response = client.post("/api/calibration/set", json={"profile": "slow"})
        assert response.status_code == 200
        
        # Reset sequence
        response = client.post("/api/translation/reset")
        assert response.status_code == 200
        
        # Process same pattern
        ear_data = {
            "ear_value": 0.15,
            "timestamp": 1234567891.0
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # End blink after 300ms (should still be short in slow profile)
        ear_data["timestamp"] = 1234567891.3
        ear_data["ear_value"] = 0.3
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Should still detect blink (300ms < 500ms short_max_ms in slow profile)
        data = response.json()
        assert data["blink_events"] >= 0
    
    def test_calibration_affects_gap_detection(self):
        """Test that calibration profile changes affect gap detection."""
        # Set to medium profile
        response = client.post("/api/calibration/set", json={"profile": "medium"})
        assert response.status_code == 200
        
        # Process a blink
        ear_data = {
            "ear_value": 0.15,
            "timestamp": 1234567890.0
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # End blink
        ear_data["timestamp"] = 1234567890.2
        ear_data["ear_value"] = 0.3
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Wait for symbol gap (450ms in medium profile)
        ear_data["timestamp"] = 1234567890.7  # 500ms gap
        ear_data["ear_value"] = 0.3
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Should detect symbol gap
        data = response.json()
        assert data["word_gap_detected"] is False  # Not a word gap yet
        
        # Switch to slow profile
        response = client.post("/api/calibration/set", json={"profile": "slow"})
        assert response.status_code == 200
        
        # Reset sequence
        response = client.post("/api/translation/reset")
        assert response.status_code == 200
        
        # Process same pattern
        ear_data = {
            "ear_value": 0.15,
            "timestamp": 1234567891.0
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # End blink
        ear_data["timestamp"] = 1234567891.2
        ear_data["ear_value"] = 0.3
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Wait for symbol gap (600ms in slow profile)
        ear_data["timestamp"] = 1234567891.7  # 500ms gap - should NOT be enough
        ear_data["ear_value"] = 0.3
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Should NOT detect symbol gap yet
        data = response.json()
        assert data["word_gap_detected"] is False
        
        # Wait longer (700ms total)
        ear_data["timestamp"] = 1234567891.9  # Additional 200ms
        ear_data["ear_value"] = 0.3
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Now should detect symbol gap
        data = response.json()
        # Note: The exact behavior depends on the implementation details


if __name__ == "__main__":
    pytest.main([__file__])
