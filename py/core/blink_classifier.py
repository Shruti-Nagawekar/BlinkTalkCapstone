"""
Blink classification from EAR (Eye Aspect Ratio) time series.
"""
import time
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
from .calibration import get_calibration_manager

class BlinkType(Enum):
    """Types of blink events."""
    SHORT = "S"
    LONG = "L"

class GapType(Enum):
    """Types of gap events."""
    SYMBOL_GAP = "symbol_gap"
    WORD_GAP = "word_gap"

@dataclass
class BlinkEvent:
    """Represents a detected blink event."""
    blink_type: BlinkType
    timestamp: float
    duration_ms: float
    ear_value: float

@dataclass
class GapEvent:
    """Represents a detected gap event."""
    gap_type: GapType
    timestamp: float
    duration_ms: float

@dataclass
class BlinkState:
    """Current state of blink detection."""
    is_blinking: bool = False
    blink_start_time: Optional[float] = None
    blink_start_ear: Optional[float] = None
    last_blink_time: Optional[float] = None
    last_event_time: Optional[float] = None

class BlinkClassifier:
    """
    Classifies blinks from EAR time series data.
    
    Converts continuous EAR values into discrete blink events (Short/Long)
    and gap events (symbol gaps, word gaps) based on timing thresholds.
    """
    
    def __init__(self, thresholds: Optional[Dict[str, int]] = None, ear_threshold: float = 0.25):
        """
        Initialize the blink classifier.
        
        Args:
            thresholds: Dictionary with timing thresholds in milliseconds (optional, uses calibration if None)
            ear_threshold: EAR value below which a blink is detected
        """
        self.ear_threshold = ear_threshold
        self.state = BlinkState()
        self.events: List[BlinkEvent] = []
        self.gap_events: List[GapEvent] = []
        
        # Use calibration manager if no thresholds provided
        if thresholds is None:
            self.calibration_manager = get_calibration_manager()
            self.use_calibration = True
        else:
            self.thresholds = thresholds
            self.use_calibration = False
            # Validate thresholds
            required_keys = ["short_max_ms", "long_min_ms", "long_max_ms", 
                            "symbol_gap_max_ms", "word_gap_min_ms"]
            for key in required_keys:
                if key not in thresholds:
                    raise ValueError(f"Missing required threshold: {key}")
    
    def _get_thresholds(self) -> Dict[str, int]:
        """Get current threshold values (from calibration or fixed)."""
        if self.use_calibration:
            return self.calibration_manager.get_thresholds()
        else:
            return self.thresholds
    
    def process_ear_sample(self, ear_value: float, timestamp: Optional[float] = None) -> List[BlinkEvent]:
        """
        Process a single EAR sample and return any new blink events.
        
        Args:
            ear_value: Current EAR value
            timestamp: Timestamp of the sample (defaults to current time)
            
        Returns:
            List of new blink events detected
        """
        if timestamp is None:
            timestamp = time.time()
        
        new_events = []
        
        # Get current thresholds (may change if calibration profile changes)
        thresholds = self._get_thresholds()
        
        # Check for blink start
        if not self.state.is_blinking and ear_value < self.ear_threshold:
            self.state.is_blinking = True
            self.state.blink_start_time = timestamp
            self.state.blink_start_ear = ear_value
        
        # Check for blink end
        elif self.state.is_blinking and ear_value >= self.ear_threshold:
            if self.state.blink_start_time is not None:
                duration_ms = (timestamp - self.state.blink_start_time) * 1000
                
                # Classify blink type based on duration
                if duration_ms <= thresholds["short_max_ms"]:
                    blink_type = BlinkType.SHORT
                elif (thresholds["long_min_ms"] <= duration_ms <= 
                      thresholds["long_max_ms"]):
                    blink_type = BlinkType.LONG
                else:
                    # Duration too long, treat as noise or invalid
                    self.state.is_blinking = False
                    self.state.blink_start_time = None
                    self.state.blink_start_ear = None
                    return new_events
                
                # Create blink event
                event = BlinkEvent(
                    blink_type=blink_type,
                    timestamp=timestamp,
                    duration_ms=duration_ms,
                    ear_value=ear_value
                )
                
                self.events.append(event)
                new_events.append(event)
                
                # Update state
                self.state.last_blink_time = timestamp
                self.state.last_event_time = timestamp
                self.state.is_blinking = False
                self.state.blink_start_time = None
                self.state.blink_start_ear = None
        
        # Check for gaps (only when not currently blinking and no gap detected yet)
        if (not self.state.is_blinking and 
            self.state.last_event_time is not None and 
            (not self.gap_events or self.gap_events[-1].timestamp < self.state.last_event_time)):
            
            gap_duration_ms = (timestamp - self.state.last_event_time) * 1000
            
            # Check for word gap first (higher priority)
            if gap_duration_ms >= thresholds["word_gap_min_ms"]:
                gap_event = GapEvent(
                    gap_type=GapType.WORD_GAP,
                    timestamp=timestamp,
                    duration_ms=gap_duration_ms
                )
                self.gap_events.append(gap_event)
                self.state.last_event_time = timestamp
                
            # Check for symbol gap (only if not a word gap and not too close to word gap threshold)
            elif (gap_duration_ms >= thresholds["symbol_gap_max_ms"] and 
                  gap_duration_ms < thresholds["word_gap_min_ms"]):
                gap_event = GapEvent(
                    gap_type=GapType.SYMBOL_GAP,
                    timestamp=timestamp,
                    duration_ms=gap_duration_ms
                )
                self.gap_events.append(gap_event)
                self.state.last_event_time = timestamp
        
        return new_events
    
    def get_recent_events(self, max_events: int = 10) -> List[BlinkEvent]:
        """Get the most recent blink events."""
        return self.events[-max_events:] if self.events else []
    
    def get_recent_gaps(self, max_events: int = 10) -> List[GapEvent]:
        """Get the most recent gap events."""
        return self.gap_events[-max_events:] if self.gap_events else []
    
    def get_current_sequence(self) -> List[BlinkType]:
        """
        Get the current sequence of blinks since the last word gap.
        
        Returns:
            List of BlinkType values representing the current word sequence
        """
        sequence = []
        last_word_gap_time = None
        
        # Find the last word gap
        for gap in reversed(self.gap_events):
            if gap.gap_type == GapType.WORD_GAP:
                last_word_gap_time = gap.timestamp
                break
        
        # Collect blinks since the last word gap
        for event in self.events:
            if last_word_gap_time is None or event.timestamp > last_word_gap_time:
                sequence.append(event.blink_type)
        
        return sequence
    
    def clear_sequence(self) -> None:
        """Clear the current sequence (called after word recognition)."""
        self.events.clear()
        self.gap_events.clear()
        self.state.last_event_time = None
        self.state.last_blink_time = None
    
    def reset(self) -> None:
        """Reset the classifier state."""
        self.state = BlinkState()
        self.events.clear()
        self.gap_events.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        current_sequence = self.get_current_sequence()
        
        if not current_sequence:
            return {
                "total_blinks": 0,
                "short_blinks": 0,
                "long_blinks": 0,
                "avg_duration_ms": 0.0,
                "current_sequence_length": 0
            }
        
        short_count = sum(1 for blink_type in current_sequence if blink_type == BlinkType.SHORT)
        long_count = sum(1 for blink_type in current_sequence if blink_type == BlinkType.LONG)
        
        # Calculate average duration for current sequence only
        sequence_events = []
        last_word_gap_time = None
        
        # Find the last word gap
        for gap in reversed(self.gap_events):
            if gap.gap_type == GapType.WORD_GAP:
                last_word_gap_time = gap.timestamp
                break
        
        # Collect events in current sequence
        for event in self.events:
            if last_word_gap_time is None or event.timestamp > last_word_gap_time:
                sequence_events.append(event)
        
        avg_duration = sum(e.duration_ms for e in sequence_events) / len(sequence_events) if sequence_events else 0.0
        
        return {
            "total_blinks": len(current_sequence),
            "short_blinks": short_count,
            "long_blinks": long_count,
            "avg_duration_ms": avg_duration,
            "current_sequence_length": len(current_sequence)
        }

