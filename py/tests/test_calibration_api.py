"""
Unit tests for calibration API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app
from core.calibration import reset_calibration_manager


class TestCalibrationAPI:
    """Test calibration API endpoints."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_calibration_manager()
        self.client = TestClient(app)
    
    def test_set_calibration_profile_valid(self):
        """Test setting a valid calibration profile."""
        response = self.client.post("/api/calibration/set", json={"profile": "slow"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Profile set to 'slow'"
        assert data["profile"] == "slow"
        assert data["description"] == "For users with slower blink patterns"
        assert data["thresholds"]["short_max_ms"] == 500
    
    def test_set_calibration_profile_invalid(self):
        """Test setting an invalid calibration profile."""
        response = self.client.post("/api/calibration/set", json={"profile": "invalid"})
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid profile" in data["detail"]
        assert "Available profiles" in data["detail"]
    
    def test_get_active_profile(self):
        """Test getting the active profile."""
        # Set a profile first
        self.client.post("/api/calibration/set", json={"profile": "slow"})
        
        response = self.client.get("/api/calibration/active")
        
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] == "slow"
        assert data["description"] == "For users with slower blink patterns"
    
    def test_get_current_thresholds(self):
        """Test getting current thresholds."""
        # Set a profile first
        self.client.post("/api/calibration/set", json={"profile": "slow"})
        
        response = self.client.get("/api/calibration/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] == "slow"
        assert data["thresholds"]["short_max_ms"] == 500
        assert data["thresholds"]["long_min_ms"] == 501
        assert data["thresholds"]["long_max_ms"] == 1200
        assert data["thresholds"]["symbol_gap_max_ms"] == 600
        assert data["thresholds"]["word_gap_min_ms"] == 1500
    
    def test_get_calibration_info(self):
        """Test getting calibration information."""
        response = self.client.get("/api/calibration/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_profile" in data
        assert "available_profiles" in data
        assert "current_thresholds" in data
        assert "slow" in data["available_profiles"]
        assert "medium" in data["available_profiles"]
    
    def test_reset_calibration(self):
        """Test resetting calibration to default."""
        # Set a profile first
        self.client.post("/api/calibration/set", json={"profile": "slow"})
        
        response = self.client.post("/api/calibration/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Calibration reset to default profile"
        assert data["profile"] == "medium"
        assert data["description"] == "Standard timing for typical users"


class TestCustomCalibrationAPI:
    """Test custom calibration API endpoints."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_calibration_manager()
        self.client = TestClient(app)
    
    def test_set_custom_calibration_valid(self):
        """Test setting valid custom calibration."""
        request_data = {
            "short_max_ms": 400,
            "long_min_ms": 401,
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        
        response = self.client.post("/api/calibration/custom", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Custom calibration profile set successfully"
        assert data["profile"] == "custom"
        assert data["description"] == "Custom calibration profile"
        assert data["is_custom"] is True
        assert data["thresholds"]["short_max_ms"] == 400
        assert data["thresholds"]["long_min_ms"] == 401
        assert data["thresholds"]["long_max_ms"] == 1000
        assert data["thresholds"]["symbol_gap_max_ms"] == 500
        assert data["thresholds"]["word_gap_min_ms"] == 1200
    
    def test_set_custom_calibration_invalid_ranges(self):
        """Test setting custom calibration with invalid ranges."""
        # Test short_max_ms too low
        request_data = {
            "short_max_ms": 50,  # Too low
            "long_min_ms": 401,
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        
        response = self.client.post("/api/calibration/custom", json=request_data)
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "validation error" in data["detail"][0]["type"] or "greater than or equal to" in str(data["detail"])
    
    def test_set_custom_calibration_logical_validation(self):
        """Test custom calibration logical validation."""
        # Test short_max_ms >= long_min_ms
        request_data = {
            "short_max_ms": 500,
            "long_min_ms": 400,  # Less than short_max_ms
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        
        response = self.client.post("/api/calibration/custom", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "Invalid custom threshold values" in data["detail"]
    
    def test_get_custom_calibration_exists(self):
        """Test getting custom calibration when it exists."""
        # Set custom calibration first
        request_data = {
            "short_max_ms": 400,
            "long_min_ms": 401,
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        self.client.post("/api/calibration/custom", json=request_data)
        
        response = self.client.get("/api/calibration/custom")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Custom calibration profile retrieved"
        assert data["profile"] == "custom"
        assert data["is_custom"] is True
        assert data["thresholds"]["short_max_ms"] == 400
    
    def test_get_custom_calibration_not_exists(self):
        """Test getting custom calibration when it doesn't exist."""
        response = self.client.get("/api/calibration/custom")
        
        assert response.status_code == 404
        data = response.json()
        assert "No custom calibration profile set" in data["detail"]
    
    def test_clear_custom_calibration(self):
        """Test clearing custom calibration."""
        # Set custom calibration first
        request_data = {
            "short_max_ms": 400,
            "long_min_ms": 401,
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        self.client.post("/api/calibration/custom", json=request_data)
        
        response = self.client.delete("/api/calibration/custom")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Custom calibration profile cleared"
        assert data["profile"] == "medium"  # Should reset to default
    
    def test_custom_calibration_edge_cases(self):
        """Test custom calibration with edge case values."""
        # Test minimum valid values
        request_data = {
            "short_max_ms": 100,  # Minimum
            "long_min_ms": 200,   # Minimum
            "long_max_ms": 500,   # Minimum
            "symbol_gap_max_ms": 200,  # Minimum
            "word_gap_min_ms": 500     # Minimum
        }
        
        response = self.client.post("/api/calibration/custom", json=request_data)
        assert response.status_code == 200
        
        # Test maximum valid values
        request_data = {
            "short_max_ms": 2000,  # Maximum
            "long_min_ms": 3000,   # Maximum
            "long_max_ms": 5000,   # Maximum
            "symbol_gap_max_ms": 2000,  # Maximum
            "word_gap_min_ms": 5000     # Maximum
        }
        
        response = self.client.post("/api/calibration/custom", json=request_data)
        assert response.status_code == 200
    
    def test_custom_calibration_validation_all_fields(self):
        """Test validation for all threshold fields."""
        # Test each field with invalid values
        invalid_tests = [
            {"short_max_ms": 50, "long_min_ms": 200, "long_max_ms": 500, "symbol_gap_max_ms": 200, "word_gap_min_ms": 500},  # short_max_ms too low
            {"short_max_ms": 3000, "long_min_ms": 200, "long_max_ms": 500, "symbol_gap_max_ms": 200, "word_gap_min_ms": 500},  # short_max_ms too high
            {"short_max_ms": 400, "long_min_ms": 100, "long_max_ms": 500, "symbol_gap_max_ms": 200, "word_gap_min_ms": 500},  # long_min_ms too low
            {"short_max_ms": 400, "long_min_ms": 4000, "long_max_ms": 500, "symbol_gap_max_ms": 200, "word_gap_min_ms": 500},  # long_min_ms too high
            {"short_max_ms": 400, "long_min_ms": 200, "long_max_ms": 300, "symbol_gap_max_ms": 200, "word_gap_min_ms": 500},  # long_max_ms too low
            {"short_max_ms": 400, "long_min_ms": 200, "long_max_ms": 6000, "symbol_gap_max_ms": 200, "word_gap_min_ms": 500},  # long_max_ms too high
            {"short_max_ms": 400, "long_min_ms": 200, "long_max_ms": 500, "symbol_gap_max_ms": 100, "word_gap_min_ms": 500},  # symbol_gap_max_ms too low
            {"short_max_ms": 400, "long_min_ms": 200, "long_max_ms": 500, "symbol_gap_max_ms": 3000, "word_gap_min_ms": 500},  # symbol_gap_max_ms too high
            {"short_max_ms": 400, "long_min_ms": 200, "long_max_ms": 500, "symbol_gap_max_ms": 200, "word_gap_min_ms": 300},  # word_gap_min_ms too low
            {"short_max_ms": 400, "long_min_ms": 200, "long_max_ms": 500, "symbol_gap_max_ms": 200, "word_gap_min_ms": 6000},  # word_gap_min_ms too high
        ]
        
        for test_data in invalid_tests:
            response = self.client.post("/api/calibration/custom", json=test_data)
            # Pydantic validation happens first, so we expect 422 for range violations
            assert response.status_code in [400, 422], f"Expected 400 or 422 for {test_data}, got {response.status_code}"
            data = response.json()
            # Check for either our custom validation message or Pydantic validation error
            assert ("Invalid custom threshold values" in data["detail"] or 
                    "validation error" in str(data["detail"]) or 
                    "greater than or equal to" in str(data["detail"]) or
                    "less than or equal to" in str(data["detail"]))
    
    def test_custom_calibration_integration_with_regular_profiles(self):
        """Test that custom calibration works with regular profile switching."""
        # Set custom calibration
        request_data = {
            "short_max_ms": 400,
            "long_min_ms": 401,
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        response = self.client.post("/api/calibration/custom", json=request_data)
        assert response.status_code == 200
        
        # Verify custom is now active
        response = self.client.get("/api/calibration/active")
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] == "custom"
        
        # Switch to regular profile
        response = self.client.post("/api/calibration/set", json={"profile": "slow"})
        assert response.status_code == 200
        
        # Verify slow is now active
        response = self.client.get("/api/calibration/active")
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] == "slow"
        
        # Custom should still exist
        response = self.client.get("/api/calibration/custom")
        assert response.status_code == 200
        data = response.json()
        assert data["profile"] == "custom"
    
    def test_custom_calibration_available_profiles(self):
        """Test that custom profile appears in available profiles when set."""
        # Initially no custom profile
        response = self.client.get("/api/calibration/info")
        assert response.status_code == 200
        data = response.json()
        assert "custom" not in data["available_profiles"]
        
        # Set custom calibration
        request_data = {
            "short_max_ms": 400,
            "long_min_ms": 401,
            "long_max_ms": 1000,
            "symbol_gap_max_ms": 500,
            "word_gap_min_ms": 1200
        }
        response = self.client.post("/api/calibration/custom", json=request_data)
        assert response.status_code == 200
        
        # Now custom should be available
        response = self.client.get("/api/calibration/info")
        assert response.status_code == 200
        data = response.json()
        assert "custom" in data["available_profiles"]
        assert data["available_profiles"]["custom"] == "Custom calibration profile"


if __name__ == "__main__":
    pytest.main([__file__])
