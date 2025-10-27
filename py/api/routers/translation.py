"""
Translation router for getting blink sequence results.
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from core.sequence_engine import SequenceEngine
from core.blink_classifier import BlinkClassifier, BlinkType, GapType
from core.translation_statistics import get_translation_statistics

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Global sequence engine instance
_sequence_engine: SequenceEngine = None
_blink_classifier: BlinkClassifier = None

def get_sequence_engine() -> SequenceEngine:
    """Get or create the global sequence engine instance."""
    global _sequence_engine
    if _sequence_engine is None:
        _sequence_engine = SequenceEngine()
    return _sequence_engine

def get_blink_classifier() -> BlinkClassifier:
    """Get or create the global blink classifier instance."""
    global _blink_classifier
    if _blink_classifier is None:
        # Initialize with calibration manager (no fixed thresholds)
        _blink_classifier = BlinkClassifier()
        logger.info("BlinkClassifier initialized with calibration manager")
    
    return _blink_classifier

@router.get("/translation")
async def get_translation() -> Dict[str, str]:
    """
    Get the latest translation result.
    
    Returns:
        Dictionary with "output" key containing the translated word or empty string
    """
    try:
        engine = get_sequence_engine()
        
        # Check if we have a completed sequence
        if engine.is_sequence_complete():
            word = engine.get_last_word()
            logger.info(f"Returning completed translation: '{word}'")
            
            # Record successful translation
            stats = get_translation_statistics()
            stats.record_translation(word)
            
            # Clear the sequence after returning the result
            engine.clear_sequence()
            
            return {"output": word}
        else:
            # No completed sequence available
            return {"output": ""}
            
    except Exception as e:
        logger.error(f"Error getting translation: {str(e)}")
        
        # Record failed translation
        stats = get_translation_statistics()
        stats.record_failure(str(e))
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error getting translation"
        )

@router.post("/translation/process_ear")
async def process_ear_sample(ear_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an EAR sample for blink detection and sequence building.
    
    This endpoint allows external systems to feed EAR data directly
    for testing and integration purposes.
    
    Args:
        ear_data: Dictionary containing 'ear_value' and optional 'timestamp'
        
    Returns:
        Dictionary with processing results
    """
    try:
        ear_value = ear_data.get('ear_value')
        timestamp = ear_data.get('timestamp')
        
        if ear_value is None:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: ear_value"
            )
        
        # Process through blink classifier
        classifier = get_blink_classifier()
        
        # Ensure ear_value is a float
        try:
            ear_value = float(ear_value)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail="ear_value must be a valid number"
            )
        
        blink_events = classifier.process_ear_sample(ear_value, timestamp)
        
        # Process blink events through sequence engine
        engine = get_sequence_engine()
        word_gap_detected = False
        
        for event in blink_events:
            if event.blink_type == BlinkType.SHORT:
                engine.add_blink("S")
            elif event.blink_type == BlinkType.LONG:
                engine.add_blink("L")
        
        # Check for word gaps
        recent_gaps = classifier.get_recent_gaps(max_events=1)
        if recent_gaps and recent_gaps[0].gap_type == GapType.WORD_GAP:
            word_gap_detected = True
            word = engine.finalize_sequence()
            if word:
                logger.info(f"Word completed via word gap: '{word}'")
        
        return {
            "blink_events": len(blink_events),
            "current_sequence": engine.get_current_sequence(),
            "word_gap_detected": word_gap_detected,
            "sequence_complete": engine.is_sequence_complete(),
            "last_word": engine.get_last_word() if engine.is_sequence_complete() else ""
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing EAR sample: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing EAR sample"
        )

@router.post("/translation/reset")
async def reset_sequence() -> Dict[str, str]:
    """
    Reset the current sequence and classifier state.
    
    Returns:
        Confirmation message
    """
    try:
        engine = get_sequence_engine()
        classifier = get_blink_classifier()
        
        engine.clear_sequence()
        classifier.reset()
        
        logger.info("Sequence and classifier state reset")
        return {"message": "Sequence reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting sequence: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error resetting sequence"
        )

@router.get("/translation/stats")
async def get_translation_stats() -> Dict[str, Any]:
    """
    Get translation statistics.
    
    Returns comprehensive statistics including:
    - Total translations
    - Success/failure rates
    - Average processing time
    - Word frequency
    - Recent errors
    """
    try:
        stats = get_translation_statistics()
        return stats.get_stats()
        
    except Exception as e:
        logger.error(f"Error getting translation stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error getting statistics"
        )
