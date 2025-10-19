"""
Tests for frame API endpoints.
"""
import pytest
import base64
from fastapi.testclient import TestClient
from api.main import app
from core.frame_buffer import get_frame_buffer

client = TestClient(app)


class TestFrameAPI:
    """Test cases for frame API endpoints."""
    
    def setup_method(self):
        """Clear buffer before each test."""
        buffer = get_frame_buffer()
        buffer.clear()
    
    def test_ingest_frame_success(self):
        """Test successful frame ingestion."""
        # Create a small test JPEG (minimal valid JPEG)
        test_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        test_b64 = base64.b64encode(test_jpeg).decode()
        
        response = client.post(
            "/api/frame",
            json={
                "frame_b64": test_b64,
                "user": "test_user"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["bytes"] == len(test_jpeg)
        assert "message" in data
    
    def test_ingest_frame_missing_fields(self):
        """Test frame ingestion with missing required fields."""
        # Missing frame_b64
        response = client.post(
            "/api/frame",
            json={"user": "test_user"}
        )
        assert response.status_code == 422
        
        # Missing user
        response = client.post(
            "/api/frame",
            json={"frame_b64": "dGVzdA=="}
        )
        assert response.status_code == 422
    
    def test_ingest_frame_empty_data(self):
        """Test frame ingestion with empty data."""
        # Empty frame_b64
        response = client.post(
            "/api/frame",
            json={
                "frame_b64": "",
                "user": "test_user"
            }
        )
        assert response.status_code == 400
        assert "Empty frame data" in response.json()["detail"]
    
    def test_ingest_frame_invalid_base64(self):
        """Test frame ingestion with invalid base64."""
        response = client.post(
            "/api/frame",
            json={
                "frame_b64": "invalid_base64!@#",
                "user": "test_user"
            }
        )
        assert response.status_code == 400
        assert "Invalid base64 data" in response.json()["detail"]
    
    def test_ingest_frame_too_large(self):
        """Test frame ingestion with oversized frame."""
        # Create a large frame (3MB)
        large_frame = b"x" * (3 * 1024 * 1024)
        large_b64 = base64.b64encode(large_frame).decode()
        
        response = client.post(
            "/api/frame",
            json={
                "frame_b64": large_b64,
                "user": "test_user"
            }
        )
        assert response.status_code == 413
        assert "Frame too large" in response.json()["detail"]
    
    def test_ingest_frame_non_jpeg_warning(self):
        """Test frame ingestion with non-JPEG data (should warn but succeed)."""
        # Create non-JPEG data
        non_jpeg = b"this is not a jpeg file"
        non_jpeg_b64 = base64.b64encode(non_jpeg).decode()
        
        response = client.post(
            "/api/frame",
            json={
                "frame_b64": non_jpeg_b64,
                "user": "test_user"
            }
        )
        
        # Should still succeed but with warning
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["bytes"] == len(non_jpeg)
    
    def test_ingest_frame_updates_buffer(self):
        """Test that frame ingestion updates the frame buffer."""
        buffer = get_frame_buffer()
        
        # Initially empty
        assert buffer.is_empty()
        
        # Ingest a frame
        test_data = b"test frame data"
        test_b64 = base64.b64encode(test_data).decode()
        
        response = client.post(
            "/api/frame",
            json={
                "frame_b64": test_b64,
                "user": "test_user"
            }
        )
        
        assert response.status_code == 200
        
        # Buffer should now contain the frame
        assert not buffer.is_empty()
        frame, meta = buffer.get()
        assert frame == test_data
        assert meta["user"] == "test_user"
        assert meta["size_bytes"] == len(test_data)
        assert meta["is_valid_jpeg"] is False  # Not a real JPEG
    
    def test_get_latest_frame_endpoint(self):
        """Test the debug endpoint for getting latest frame metadata."""
        # Initially no frame
        response = client.get("/api/frame/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["frame_available"] is False
        
        # Ingest a frame
        test_data = b"test frame"
        test_b64 = base64.b64encode(test_data).decode()
        
        client.post(
            "/api/frame",
            json={
                "frame_b64": test_b64,
                "user": "test_user"
            }
        )
        
        # Now should have frame metadata
        response = client.get("/api/frame/latest")
        assert response.status_code == 200
        data = response.json()
        assert data["frame_available"] is True
        assert data["frame_size_bytes"] == len(test_data)
        assert "metadata" in data
        assert data["metadata"]["user"] == "test_user"
    
    def test_frame_overwrite_behavior(self):
        """Test that new frames overwrite old ones in buffer."""
        buffer = get_frame_buffer()
        
        # Get initial version
        initial_version = buffer.get_version()
        
        # Ingest first frame
        first_data = b"first frame"
        first_b64 = base64.b64encode(first_data).decode()
        
        response1 = client.post(
            "/api/frame",
            json={
                "frame_b64": first_b64,
                "user": "user1"
            }
        )
        assert response1.status_code == 200
        
        # Ingest second frame
        second_data = b"second frame"
        second_b64 = base64.b64encode(second_data).decode()
        
        response2 = client.post(
            "/api/frame",
            json={
                "frame_b64": second_b64,
                "user": "user2"
            }
        )
        assert response2.status_code == 200
        
        # Buffer should only contain second frame
        frame, meta = buffer.get()
        assert frame == second_data
        assert meta["user"] == "user2"
        assert meta["version"] == initial_version + 2  # Should be 2 versions ahead
    
    def test_concurrent_frame_ingestion(self):
        """Test concurrent frame ingestion (stress test)."""
        import threading
        import time
        
        results = []
        errors = []
        
        def ingest_frame(thread_id: int, num_frames: int):
            """Ingest multiple frames from a thread."""
            try:
                for i in range(num_frames):
                    frame_data = f"thread_{thread_id}_frame_{i}".encode()
                    frame_b64 = base64.b64encode(frame_data).decode()
                    
                    response = client.post(
                        "/api/frame",
                        json={
                            "frame_b64": frame_b64,
                            "user": f"user_{thread_id}"
                        }
                    )
                    results.append(response.status_code)
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=ingest_frame, args=(thread_id, 5))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Errors during concurrent ingestion: {errors}"
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        
        # Buffer should contain the last frame
        buffer = get_frame_buffer()
        frame, meta = buffer.get()
        assert frame is not None
        assert "user_" in meta["user"]
