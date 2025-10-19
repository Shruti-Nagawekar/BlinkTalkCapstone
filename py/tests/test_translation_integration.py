"""
Integration tests for translation API endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestTranslationIntegration:
    """Integration tests for translation endpoints."""
    
    def test_get_translation_empty(self):
        """Test getting translation when no sequence is complete."""
        response = client.get("/api/translation")
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == ""
    
    def test_process_ear_sample_valid(self):
        """Test processing EAR sample with valid data."""
        ear_data = {
            "ear_value": 0.15,  # Below threshold for blink detection
            "timestamp": 1234567890.0
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        data = response.json()
        
        assert "blink_events" in data
        assert "current_sequence" in data
        assert "word_gap_detected" in data
        assert "sequence_complete" in data
        assert "last_word" in data
    
    def test_process_ear_sample_missing_ear_value(self):
        """Test processing EAR sample with missing ear_value."""
        ear_data = {
            "timestamp": 1234567890.0
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 400
        data = response.json()
        assert "Missing required field: ear_value" in data["detail"]
    
    def test_process_ear_sample_invalid_data(self):
        """Test processing EAR sample with invalid data."""
        ear_data = {
            "ear_value": "not_a_number"
        }
        
        response = client.post("/api/translation/process_ear", json=ear_data)
        # Should return 400 for invalid data
        assert response.status_code == 400
        data = response.json()
        assert "ear_value must be a valid number" in data["detail"]
    
    def test_reset_sequence(self):
        """Test resetting sequence and classifier state."""
        response = client.post("/api/translation/reset")
        assert response.status_code == 200
        data = response.json()
        assert "reset successfully" in data["message"]
    
    def test_ear_processing_sequence_building(self):
        """Test building a complete sequence through EAR processing."""
        # Reset first
        client.post("/api/translation/reset")
        
        # Simulate a sequence of EAR values that would create "S S" pattern
        # This is a simplified test - in reality, we'd need more complex EAR patterns
        
        # First, test with high EAR (no blink)
        ear_data = {"ear_value": 0.3}
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Then test with low EAR (blink start)
        ear_data = {"ear_value": 0.1}
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Then test with high EAR again (blink end)
        ear_data = {"ear_value": 0.3}
        response = client.post("/api/translation/process_ear", json=ear_data)
        assert response.status_code == 200
        
        # Check current sequence
        data = response.json()
        assert "current_sequence" in data
    
    def test_translation_endpoint_after_sequence(self):
        """Test translation endpoint after a sequence is completed."""
        # This test would require a more complex setup to actually complete a sequence
        # For now, just test the endpoint structure
        response = client.get("/api/translation")
        assert response.status_code == 200
        data = response.json()
        assert "output" in data
        assert isinstance(data["output"], str)
    
    def test_multiple_ear_samples(self):
        """Test processing multiple EAR samples in sequence."""
        # Reset first
        client.post("/api/translation/reset")
        
        # Process multiple samples
        for i in range(5):
            ear_data = {
                "ear_value": 0.2 + (i * 0.01),  # Varying EAR values
                "timestamp": 1234567890.0 + i
            }
            response = client.post("/api/translation/process_ear", json=ear_data)
            assert response.status_code == 200
        
        # Check that we can still get translation
        response = client.get("/api/translation")
        assert response.status_code == 200
    
    def test_error_handling(self):
        """Test error handling in translation endpoints."""
        # Test with invalid JSON
        response = client.post("/api/translation/process_ear", data="invalid json")
        assert response.status_code == 422  # Validation error
        
        # Test with empty request
        response = client.post("/api/translation/process_ear", json={})
        assert response.status_code == 400  # Missing required field


class TestFrameProcessingIntegration:
    """Integration tests for frame processing with blink detection."""
    
    def test_process_frame_invalid_base64(self):
        """Test processing frame with invalid base64 data."""
        frame_data = {
            "frame_b64": "invalid_base64_data",
            "user": "test_user"
        }
        
        response = client.post("/api/frame/process", json=frame_data)
        assert response.status_code == 400
        data = response.json()
        assert "Invalid base64 data" in data["detail"]
    
    def test_process_frame_empty_data(self):
        """Test processing frame with empty data."""
        frame_data = {
            "frame_b64": "",
            "user": "test_user"
        }
        
        response = client.post("/api/frame/process", json=frame_data)
        assert response.status_code == 400
        data = response.json()
        assert "Decoded frame is empty" in data["detail"]
    
    def test_process_frame_large_data(self):
        """Test processing frame with data that's too large."""
        # Create a large base64 string (simulate large frame)
        large_data = "A" * (3 * 1024 * 1024)  # 3MB
        import base64
        large_b64 = base64.b64encode(large_data.encode()).decode()
        
        frame_data = {
            "frame_b64": large_b64,
            "user": "test_user"
        }
        
        response = client.post("/api/frame/process", json=frame_data)
        assert response.status_code == 413  # Payload too large
        data = response.json()
        assert "Frame too large" in data["detail"]
    
    def test_process_frame_valid_structure(self):
        """Test processing frame with valid structure (even if no eyes detected)."""
        # Create a simple 1x1 pixel JPEG for testing
        import cv2
        import numpy as np
        import base64
        
        # Create a simple 1x1 pixel image
        img = np.zeros((1, 1, 3), dtype=np.uint8)
        img[0, 0] = [128, 128, 128]  # Gray pixel
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', img)
        frame_b64 = base64.b64encode(buffer).decode()
        
        frame_data = {
            "frame_b64": frame_b64,
            "user": "test_user"
        }
        
        response = client.post("/api/frame/process", json=frame_data)
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "success" in data
        assert "ear_value" in data
        assert "blink_events" in data
        assert "current_sequence" in data
        assert "word_gap_detected" in data
        assert "sequence_complete" in data
        assert "completed_word" in data
        assert "last_word" in data
        
        # Since this is a 1x1 pixel image, eye detection will likely fail
        if not data["success"]:
            assert "Could not detect eyes" in data["message"]
            assert data["ear_value"] is None
