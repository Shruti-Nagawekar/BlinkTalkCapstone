"""
Thread-safe latest frame buffer for camera frame ingestion.
"""
import threading
import time
from typing import Optional, Dict, Any, Tuple


class LatestFrameBuffer:
    """
    Thread-safe buffer that stores only the latest frame with metadata.
    
    Provides non-blocking writes and atomic reads of the most recent frame.
    Older frames are automatically overwritten when new ones arrive.
    """
    
    def __init__(self):
        """Initialize empty buffer."""
        self._lock = threading.RLock()
        self._frame: Optional[bytes] = None
        self._meta: Dict[str, Any] = {}
        self._version: int = 0
    
    def set(self, frame_bytes: bytes, meta: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a new frame, overwriting any previous frame.
        
        Args:
            frame_bytes: Raw frame data (typically JPEG bytes)
            meta: Optional metadata dictionary (will be copied)
        """
        if meta is None:
            meta = {}
        
        # Add default metadata
        metadata = {
            'received_at': time.time(),
            'size_bytes': len(frame_bytes),
            'version': self._version + 1,
            **meta
        }
        
        with self._lock:
            self._frame = frame_bytes
            self._meta = metadata.copy()
            self._version += 1
    
    def get(self) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Get the latest frame and metadata atomically.
        
        Returns:
            Tuple of (frame_bytes, metadata_dict)
            Returns (None, {}) if no frame has been stored
        """
        with self._lock:
            # Return copies to prevent external mutation
            frame_copy = self._frame
            meta_copy = self._meta.copy()
            return frame_copy, meta_copy
    
    def clear(self) -> None:
        """Clear the buffer and reset version counter."""
        with self._lock:
            self._frame = None
            self._meta = {}
            self._version += 1
    
    def get_version(self) -> int:
        """Get current version number (for testing/debugging)."""
        with self._lock:
            return self._version
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        with self._lock:
            return self._frame is None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get current metadata without frame data."""
        with self._lock:
            return self._meta.copy()


# Global singleton instance
_frame_buffer = LatestFrameBuffer()


def get_frame_buffer() -> LatestFrameBuffer:
    """Get the global frame buffer instance."""
    return _frame_buffer