"""
Tests for frame buffer functionality and thread safety.
"""
import pytest
import threading
import time
from core.frame_buffer import LatestFrameBuffer, get_frame_buffer


class TestLatestFrameBuffer:
    """Test cases for LatestFrameBuffer class."""
    
    def test_initial_state(self):
        """Test that buffer starts empty."""
        buffer = LatestFrameBuffer()
        assert buffer.is_empty()
        assert buffer.get_version() == 0
        
        frame, meta = buffer.get()
        assert frame is None
        assert meta == {}
    
    def test_set_and_get_single_frame(self):
        """Test setting and getting a single frame."""
        buffer = LatestFrameBuffer()
        test_frame = b"test frame data"
        test_meta = {"user": "test_user", "timestamp": 12345}
        
        buffer.set(test_frame, test_meta)
        
        assert not buffer.is_empty()
        assert buffer.get_version() == 1
        
        frame, meta = buffer.get()
        assert frame == test_frame
        assert meta["user"] == "test_user"
        assert meta["timestamp"] == 12345
        assert meta["size_bytes"] == len(test_frame)
        assert "received_at" in meta
        assert meta["version"] == 1
    
    def test_set_without_metadata(self):
        """Test setting frame without metadata."""
        buffer = LatestFrameBuffer()
        test_frame = b"test frame"
        
        buffer.set(test_frame)
        
        frame, meta = buffer.get()
        assert frame == test_frame
        assert meta["size_bytes"] == len(test_frame)
        assert "received_at" in meta
        assert "version" in meta
    
    def test_overwrite_frame(self):
        """Test that new frames overwrite old ones."""
        buffer = LatestFrameBuffer()
        
        # Set first frame
        buffer.set(b"first frame", {"user": "user1"})
        assert buffer.get_version() == 1
        
        # Set second frame
        buffer.set(b"second frame", {"user": "user2"})
        assert buffer.get_version() == 2
        
        # Should only have second frame
        frame, meta = buffer.get()
        assert frame == b"second frame"
        assert meta["user"] == "user2"
        assert meta["version"] == 2
    
    def test_clear_buffer(self):
        """Test clearing the buffer."""
        buffer = LatestFrameBuffer()
        
        # Set a frame
        buffer.set(b"test frame")
        assert not buffer.is_empty()
        
        # Clear buffer
        buffer.clear()
        assert buffer.is_empty()
        assert buffer.get_version() == 2  # Should increment version
        
        frame, meta = buffer.get()
        assert frame is None
        assert meta == {}
    
    def test_metadata_isolation(self):
        """Test that returned metadata is a copy."""
        buffer = LatestFrameBuffer()
        test_meta = {"user": "test"}
        
        buffer.set(b"test frame", test_meta)
        _, meta = buffer.get()
        
        # Modify the returned metadata
        meta["user"] = "modified"
        
        # Original buffer metadata should be unchanged
        _, meta2 = buffer.get()
        assert meta2["user"] == "test"
    
    def test_concurrent_writes(self):
        """Test thread safety with concurrent writes."""
        buffer = LatestFrameBuffer()
        results = []
        errors = []
        
        def writer(thread_id: int, num_writes: int):
            """Write multiple frames from a thread."""
            try:
                for i in range(num_writes):
                    frame_data = f"thread_{thread_id}_frame_{i}".encode()
                    metadata = {"thread_id": thread_id, "frame_num": i}
                    buffer.set(frame_data, metadata)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(e)
        
        # Start multiple writer threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=writer, args=(thread_id, 10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"
        
        # Buffer should contain the last written frame
        frame, meta = buffer.get()
        assert frame is not None
        assert "thread_id" in meta
        assert "frame_num" in meta
        assert meta["version"] > 0
    
    def test_concurrent_reads_and_writes(self):
        """Test thread safety with concurrent reads and writes."""
        buffer = LatestFrameBuffer()
        read_results = []
        errors = []
        
        def reader(thread_id: int, num_reads: int):
            """Read frames from a thread."""
            try:
                for _ in range(num_reads):
                    frame, meta = buffer.get()
                    read_results.append((thread_id, frame, meta))
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def writer(thread_id: int, num_writes: int):
            """Write frames from a thread."""
            try:
                for i in range(num_writes):
                    frame_data = f"writer_{thread_id}_frame_{i}".encode()
                    buffer.set(frame_data, {"writer": thread_id, "frame": i})
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Start reader and writer threads
        threads = []
        
        # 2 reader threads
        for thread_id in range(2):
            thread = threading.Thread(target=reader, args=(thread_id, 20))
            threads.append(thread)
            thread.start()
        
        # 2 writer threads
        for thread_id in range(2):
            thread = threading.Thread(target=writer, args=(thread_id, 10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors
        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        
        # Should have some read results
        assert len(read_results) > 0
        
        # All reads should be consistent (no partial state)
        for thread_id, frame, meta in read_results:
            if frame is not None:
                assert isinstance(frame, bytes)
                assert isinstance(meta, dict)
                assert "version" in meta


class TestFrameBufferSingleton:
    """Test the global frame buffer singleton."""
    
    def test_singleton_consistency(self):
        """Test that get_frame_buffer returns the same instance."""
        buffer1 = get_frame_buffer()
        buffer2 = get_frame_buffer()
        assert buffer1 is buffer2
    
    def test_singleton_state_persistence(self):
        """Test that singleton maintains state across calls."""
        buffer = get_frame_buffer()
        
        # Set a frame
        buffer.set(b"singleton test", {"test": True})
        
        # Get buffer again and verify state
        buffer2 = get_frame_buffer()
        frame, meta = buffer2.get()
        assert frame == b"singleton test"
        assert meta["test"] is True
