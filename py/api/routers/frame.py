"""
Frame ingestion router for camera data.
"""
import base64
import logging
import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.frame_buffer import get_frame_buffer
from core.eye_tracker import create_eye_tracker
from core.blink_classifier import BlinkClassifier, BlinkType, GapType
from core.sequence_engine import SequenceEngine

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum frame size (2MB) to prevent abuse
MAX_FRAME_SIZE = 2 * 1024 * 1024

# Global instances for blink detection
_eye_tracker = None
_blink_classifier = None
_sequence_engine = None

def get_eye_tracker():
    """Get or create the global eye tracker instance."""
    global _eye_tracker
    if _eye_tracker is None:
        _eye_tracker = create_eye_tracker("dlib")  # Default to dlib
        logger.info("Eye tracker initialized")
    return _eye_tracker

def get_blink_classifier():
    """Get or create the global blink classifier instance."""
    global _blink_classifier
    if _blink_classifier is None:
        # Initialize with calibration manager (no fixed thresholds)
        _blink_classifier = BlinkClassifier()
        logger.info("BlinkClassifier initialized with calibration manager")
    
    return _blink_classifier

def get_sequence_engine():
    """Get or create the global sequence engine instance."""
    global _sequence_engine
    if _sequence_engine is None:
        _sequence_engine = SequenceEngine()
        logger.info("Sequence engine initialized")
    return _sequence_engine


class FrameRequest(BaseModel):
    """Request model for frame ingestion."""
    frame_b64: str = Field(..., description="Base64-encoded JPEG frame data")
    user: str = Field(..., description="User identifier for logging")


class FrameResponse(BaseModel):
    """Response model for frame ingestion."""
    ok: bool = Field(..., description="Whether frame was successfully processed")
    bytes: int = Field(..., description="Decoded frame size in bytes")
    message: str = Field(default="", description="Optional message")


def _validate_jpeg_magic(frame_bytes: bytes) -> bool:
    """
    Validate that bytes look like a JPEG file.
    
    Args:
        frame_bytes: Raw frame data
        
    Returns:
        True if appears to be valid JPEG, False otherwise
    """
    if len(frame_bytes) < 2:
        return False
    
    # Check JPEG magic bytes: FF D8 (start) and FF D9 (end)
    starts_with_jpeg = frame_bytes[:2] == b'\xff\xd8'
    ends_with_jpeg = frame_bytes[-2:] == b'\xff\xd9'
    
    return starts_with_jpeg and ends_with_jpeg


@router.post("/frame", response_model=FrameResponse)
async def ingest_frame(request: FrameRequest) -> FrameResponse:
    """
    Ingest a camera frame for processing.
    
    Accepts base64-encoded JPEG data and stores it in the frame buffer
    for downstream blink detection processing.
    """
    try:
        # Validate base64 input
        if not request.frame_b64:
            raise HTTPException(
                status_code=400,
                detail="Empty frame data"
            )
        
        # Decode base64
        try:
            frame_bytes = base64.b64decode(request.frame_b64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 data: {str(e)}"
            )
        
        # Check frame size
        if len(frame_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Decoded frame is empty"
            )
        
        if len(frame_bytes) > MAX_FRAME_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Frame too large: {len(frame_bytes)} bytes (max: {MAX_FRAME_SIZE})"
            )
        
        # Validate JPEG magic (optional warning)
        is_valid_jpeg = _validate_jpeg_magic(frame_bytes)
        if not is_valid_jpeg:
            logger.warning(f"Frame from user {request.user} may not be valid JPEG")
        
        # Store in buffer with metadata
        buffer = get_frame_buffer()
        metadata = {
            'user': request.user,
            'is_valid_jpeg': is_valid_jpeg,
            'original_b64_size': len(request.frame_b64)
        }
        
        buffer.set(frame_bytes, metadata)
        
        # Log successful ingestion
        logger.info(
            f"Frame ingested: user={request.user}, "
            f"size={len(frame_bytes)} bytes, "
            f"version={buffer.get_version()}"
        )
        
        return FrameResponse(
            ok=True,
            bytes=len(frame_bytes),
            message="Frame processed successfully"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error processing frame: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing frame"
        )


@router.get("/frame/latest")
async def get_latest_frame() -> Dict[str, Any]:
    """
    Get the latest frame metadata (for debugging).
    
    Returns metadata without the actual frame data to avoid
    large responses in logs/debugging.
    """
    buffer = get_frame_buffer()
    frame_bytes, metadata = buffer.get()
    
    if frame_bytes is None:
        return {
            "frame_available": False,
            "message": "No frame available"
        }
    
    return {
        "frame_available": True,
        "metadata": metadata,
        "frame_size_bytes": len(frame_bytes)
    }

@router.post("/frame/process")
async def process_frame_for_blinks(request: FrameRequest) -> Dict[str, Any]:
    """
    Process a frame for blink detection and sequence building.
    
    This endpoint takes a frame, processes it for eye tracking,
    detects blinks, and updates the sequence engine.
    
    Args:
        request: FrameRequest containing base64-encoded frame data
        
    Returns:
        Dictionary with processing results including blink events and sequence state
    """
    try:
        # Decode frame
        try:
            frame_bytes = base64.b64decode(request.frame_b64)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 data: {str(e)}"
            )
        
        # Check frame size
        if len(frame_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Decoded frame is empty"
            )
        
        if len(frame_bytes) > MAX_FRAME_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Frame too large: {len(frame_bytes)} bytes (max: {MAX_FRAME_SIZE})"
            )
        
        # Get instances
        eye_tracker = get_eye_tracker()
        blink_classifier = get_blink_classifier()
        sequence_engine = get_sequence_engine()
        
        # Process frame for EAR
        # Convert frame bytes to numpy array
        import cv2
        import numpy as np
        
        try:
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return {
                "success": False,
                "message": f"Could not decode frame as image: {str(e)}",
                "ear_value": None,
                "blink_events": 0,
                "current_sequence": sequence_engine.get_current_sequence(),
                "sequence_complete": sequence_engine.is_sequence_complete()
            }
        
        if frame is None:
            return {
                "success": False,
                "message": "Could not decode frame as image",
                "ear_value": None,
                "blink_events": 0,
                "current_sequence": sequence_engine.get_current_sequence(),
                "sequence_complete": sequence_engine.is_sequence_complete()
            }
        
        ear_value = eye_tracker.calculate_ear(frame)
        
        if ear_value is None:
            return {
                "success": False,
                "message": "Could not detect eyes in frame",
                "ear_value": None,
                "blink_events": 0,
                "current_sequence": sequence_engine.get_current_sequence(),
                "sequence_complete": sequence_engine.is_sequence_complete()
            }
        
        # Process EAR through blink classifier
        timestamp = time.time()
        blink_events = blink_classifier.process_ear_sample(ear_value, timestamp)
        
        # Process blink events through sequence engine
        word_gap_detected = False
        completed_word = None
        
        for event in blink_events:
            if event.blink_type == BlinkType.SHORT:
                sequence_engine.add_blink("S")
            elif event.blink_type == BlinkType.LONG:
                sequence_engine.add_blink("L")
        
        # Check for word gaps
        recent_gaps = blink_classifier.get_recent_gaps(max_events=1)
        if recent_gaps and recent_gaps[0].gap_type == GapType.WORD_GAP:
            word_gap_detected = True
            completed_word = sequence_engine.finalize_sequence()
            if completed_word:
                logger.info(f"Word completed via word gap: '{completed_word}'")
        
        return {
            "success": True,
            "ear_value": ear_value,
            "blink_events": len(blink_events),
            "current_sequence": sequence_engine.get_current_sequence(),
            "word_gap_detected": word_gap_detected,
            "sequence_complete": sequence_engine.is_sequence_complete(),
            "completed_word": completed_word,
            "last_word": sequence_engine.get_last_word() if sequence_engine.is_sequence_complete() else ""
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing frame for blinks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing frame"
        )