"""
Unit tests for blink classification.
"""
import pytest
import time
import numpy as np
from unittest.mock import Mock, patch

from core.blink_classifier import (
    BlinkClassifier, BlinkType, GapType, BlinkEvent, GapEvent
)

class TestBlinkClassifier:
    """Test cases for BlinkClassifier."""
    
    @pytest.fixture
    def default_thresholds(self):
        """Default thresholds for testing."""
        return {
            "short_max_ms": 350,
            "long_min_ms": 351,
            "long_max_ms": 900,
            "symbol_gap_max_ms": 450,
            "word_gap_min_ms": 1100
        }
    
    @pytest.fixture
    def classifier(self, default_thresholds):
        """Create a BlinkClassifier instance for testing."""
        return BlinkClassifier(default_thresholds, ear_threshold=0.25)
    
    def test_short_blink_detection(self, classifier):
        """Test detection of short blinks."""
        # Simulate a short blink: EAR drops below threshold for 200ms
        events = []
        
        # Start of blink
        events.extend(classifier.process_ear_sample(0.15, 0.0))  # Below threshold
        time.sleep(0.1)  # 100ms
        events.extend(classifier.process_ear_sample(0.12, 0.1))  # Still below
        time.sleep(0.1)  # 100ms
        events.extend(classifier.process_ear_sample(0.10, 0.2))  # Still below
        time.sleep(0.1)  # 100ms
        # End of blink
        events.extend(classifier.process_ear_sample(0.30, 0.3))  # Above threshold
        
        # Should detect one short blink
        assert len(events) == 1
        assert events[0].blink_type == BlinkType.SHORT
        assert 200 <= events[0].duration_ms <= 300  # Allow some tolerance
        assert events[0].ear_value == 0.30
    
    def test_long_blink_detection(self, classifier):
        """Test detection of long blinks."""
        events = []
        
        # Start of long blink
        events.extend(classifier.process_ear_sample(0.15, 0.0))  # Below threshold
        time.sleep(0.2)  # 200ms
        events.extend(classifier.process_ear_sample(0.12, 0.2))  # Still below
        time.sleep(0.2)  # 200ms
        events.extend(classifier.process_ear_sample(0.10, 0.4))  # Still below
        time.sleep(0.2)  # 200ms
        # End of blink
        events.extend(classifier.process_ear_sample(0.30, 0.6))  # Above threshold
        
        # Should detect one long blink
        assert len(events) == 1
        assert events[0].blink_type == BlinkType.LONG
        assert 600 <= events[0].duration_ms <= 700  # Allow some tolerance
        assert events[0].ear_value == 0.30
    
    def test_symbol_gap_detection(self, classifier):
        """Test detection of symbol gaps between blinks."""
        events = []
        
        # First blink
        events.extend(classifier.process_ear_sample(0.15, 0.0))  # Start blink
        events.extend(classifier.process_ear_sample(0.30, 0.1))  # End blink (100ms)
        
        # Wait for symbol gap (500ms - should trigger symbol gap)
        events.extend(classifier.process_ear_sample(0.35, 0.6))  # Normal eye state
        
        # Second blink
        events.extend(classifier.process_ear_sample(0.15, 0.7))  # Start second blink
        events.extend(classifier.process_ear_sample(0.30, 0.8))  # End second blink
        
        # Should have 2 blink events and 1 symbol gap event
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        gap_events = classifier.get_recent_gaps()
        
        assert len(blink_events) == 2
        assert len(gap_events) == 1
        assert gap_events[0].gap_type == GapType.SYMBOL_GAP
    
    def test_word_gap_detection(self, classifier):
        """Test detection of word gaps."""
        events = []
        
        # First word: "yes" (S S)
        events.extend(classifier.process_ear_sample(0.15, 0.0))  # Start first S
        events.extend(classifier.process_ear_sample(0.30, 0.1))  # End first S
        events.extend(classifier.process_ear_sample(0.15, 0.3))  # Start second S
        events.extend(classifier.process_ear_sample(0.30, 0.4))  # End second S
        
        # Wait for word gap (1200ms - should trigger word gap)
        events.extend(classifier.process_ear_sample(0.35, 1.6))  # Normal eye state
        
        # Second word: "no" (L)
        events.extend(classifier.process_ear_sample(0.15, 1.7))  # Start L
        events.extend(classifier.process_ear_sample(0.30, 1.9))  # End L
        
        # Should have 3 blink events and 1 word gap event
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        gap_events = classifier.get_recent_gaps()
        
        assert len(blink_events) == 3
        assert len(gap_events) == 1
        assert gap_events[0].gap_type == GapType.WORD_GAP
    
    def test_sequence_tracking(self, classifier):
        """Test tracking of blink sequences."""
        # Simulate "yes" pattern: S S
        classifier.process_ear_sample(0.15, 0.0)  # Start first S
        classifier.process_ear_sample(0.30, 0.1)  # End first S
        classifier.process_ear_sample(0.35, 0.2)  # Normal state
        classifier.process_ear_sample(0.15, 0.3)  # Start second S
        classifier.process_ear_sample(0.30, 0.4)  # End second S
        
        # Check current sequence (no gaps, so both blinks in same sequence)
        sequence = classifier.get_current_sequence()
        assert sequence == [BlinkType.SHORT, BlinkType.SHORT]
        
        # Add word gap
        classifier.process_ear_sample(0.35, 1.5)  # Word gap
        
        # Sequence should be cleared after word gap
        sequence = classifier.get_current_sequence()
        assert sequence == []
    
    def test_clear_sequence(self, classifier):
        """Test clearing of blink sequences."""
        # Add some blinks
        classifier.process_ear_sample(0.15, 0.0)
        classifier.process_ear_sample(0.30, 0.1)
        classifier.process_ear_sample(0.15, 0.2)
        classifier.process_ear_sample(0.30, 0.3)
        
        # Check sequence exists
        sequence = classifier.get_current_sequence()
        assert len(sequence) == 2
        
        # Clear sequence
        classifier.clear_sequence()
        
        # Check sequence is cleared
        sequence = classifier.get_current_sequence()
        assert len(sequence) == 0
        assert len(classifier.events) == 0
        assert len(classifier.gap_events) == 0
    
    def test_invalid_blink_duration(self, classifier):
        """Test handling of invalid blink durations."""
        events = []
        
        # Very long blink (should be ignored)
        events.extend(classifier.process_ear_sample(0.15, 0.0))  # Start blink
        time.sleep(1.0)  # 1000ms - too long
        events.extend(classifier.process_ear_sample(0.30, 1.0))  # End blink
        
        # Should not detect any blink events
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        assert len(blink_events) == 0
    
    def test_no_blink_when_above_threshold(self, classifier):
        """Test that no blinks are detected when EAR is above threshold."""
        events = []
        
        # All samples above threshold
        events.extend(classifier.process_ear_sample(0.30, 0.0))
        events.extend(classifier.process_ear_sample(0.35, 0.1))
        events.extend(classifier.process_ear_sample(0.40, 0.2))
        
        # Should not detect any blink events
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        assert len(blink_events) == 0
    
    def test_get_stats(self, classifier):
        """Test getting classification statistics."""
        # Initially no stats
        stats = classifier.get_stats()
        assert stats["total_blinks"] == 0
        assert stats["short_blinks"] == 0
        assert stats["long_blinks"] == 0
        assert stats["avg_duration_ms"] == 0.0
        
        # Add some blinks
        classifier.process_ear_sample(0.15, 0.0)  # Start S
        classifier.process_ear_sample(0.30, 0.1)  # End S
        classifier.process_ear_sample(0.15, 0.2)  # Start L
        classifier.process_ear_sample(0.30, 0.6)  # End L (400ms - should be long)
        
        # Check stats
        stats = classifier.get_stats()
        assert stats["total_blinks"] == 2
        assert stats["short_blinks"] == 1
        assert stats["long_blinks"] == 1
        assert stats["avg_duration_ms"] > 0
        assert stats["current_sequence_length"] == 2
    
    def test_reset(self, classifier):
        """Test resetting the classifier."""
        # Add some data
        classifier.process_ear_sample(0.15, 0.0)
        classifier.process_ear_sample(0.30, 0.1)
        
        # Reset
        classifier.reset()
        
        # Check everything is cleared
        assert len(classifier.events) == 0
        assert len(classifier.gap_events) == 0
        assert classifier.state.is_blinking == False
        assert classifier.state.blink_start_time is None
        assert classifier.state.last_blink_time is None
        assert classifier.state.last_event_time is None

class TestBlinkClassifierSyntheticData:
    """Test cases using synthetic EAR data."""
    
    def test_deterministic_synthetic_sequence(self):
        """Test with deterministic synthetic EAR data."""
        thresholds = {
            "short_max_ms": 350,
            "long_min_ms": 351,
            "long_max_ms": 900,
            "symbol_gap_max_ms": 450,
            "word_gap_min_ms": 1100
        }
        classifier = BlinkClassifier(thresholds, ear_threshold=0.25)
        
        # Synthetic EAR data: "yes" pattern (S S)
        # Timestamps: 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
        # EAR values: 0.3, 0.1, 0.3, 0.1, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3
        synthetic_data = [
            (0.0, 0.3),  # Normal
            (0.1, 0.1),  # Start S
            (0.2, 0.3),  # End S
            (0.3, 0.1),  # Start S
            (0.4, 0.3),  # End S
            (0.5, 0.3),  # Normal
            (0.6, 0.3),  # Normal
            (0.7, 0.3),  # Normal
            (0.8, 0.3),  # Normal
            (0.9, 0.3),  # Normal
            (1.0, 0.3),  # Normal
        ]
        
        events = []
        for timestamp, ear_value in synthetic_data:
            events.extend(classifier.process_ear_sample(ear_value, timestamp))
        
        # Should detect 2 short blinks
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        assert len(blink_events) == 2
        assert all(e.blink_type == BlinkType.SHORT for e in blink_events)
        
        # Check sequence
        sequence = classifier.get_current_sequence()
        assert sequence == [BlinkType.SHORT, BlinkType.SHORT]
    
    def test_deterministic_long_blink_sequence(self):
        """Test with deterministic long blink data."""
        thresholds = {
            "short_max_ms": 350,
            "long_min_ms": 351,
            "long_max_ms": 900,
            "symbol_gap_max_ms": 450,
            "word_gap_min_ms": 1100
        }
        classifier = BlinkClassifier(thresholds, ear_threshold=0.25)
        
        # Synthetic EAR data: "no" pattern (L)
        synthetic_data = [
            (0.0, 0.3),  # Normal
            (0.1, 0.1),  # Start L
            (0.2, 0.1),  # Still blinking
            (0.3, 0.1),  # Still blinking
            (0.4, 0.1),  # Still blinking
            (0.5, 0.3),  # End L (400ms duration)
        ]
        
        events = []
        for timestamp, ear_value in synthetic_data:
            events.extend(classifier.process_ear_sample(ear_value, timestamp))
        
        # Should detect 1 long blink
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        assert len(blink_events) == 1
        assert blink_events[0].blink_type == BlinkType.LONG
        assert 350 <= blink_events[0].duration_ms <= 450  # Allow tolerance
    
    def test_complex_sequence_with_gaps(self):
        """Test complex sequence with symbol and word gaps."""
        thresholds = {
            "short_max_ms": 350,
            "long_min_ms": 351,
            "long_max_ms": 900,
            "symbol_gap_max_ms": 450,
            "word_gap_min_ms": 1100
        }
        classifier = BlinkClassifier(thresholds, ear_threshold=0.25)
        
        # Complex sequence: "yes" (S S) + word gap + "no" (L)
        synthetic_data = [
            # First word: "yes" (S S)
            (0.0, 0.3),   # Normal
            (0.1, 0.1),   # Start S1
            (0.2, 0.3),   # End S1
            (0.3, 0.1),   # Start S2
            (0.4, 0.3),   # End S2
            # Word gap (1200ms)
            (0.5, 0.3),   # Normal
            (0.6, 0.3),   # Normal
            (0.7, 0.3),   # Normal
            (0.8, 0.3),   # Normal
            (0.9, 0.3),   # Normal
            (1.0, 0.3),   # Normal
            (1.1, 0.3),   # Normal
            (1.2, 0.3),   # Normal
            (1.3, 0.3),   # Normal
            (1.4, 0.3),   # Normal
            (1.5, 0.3),   # Normal
            (1.6, 0.3),   # Normal
            (1.7, 0.3),   # Normal
            (1.8, 0.3),   # Normal
            (1.9, 0.3),   # Normal
            (2.0, 0.3),   # Normal
            (2.1, 0.3),   # Normal
            # Second word: "no" (L)
            (2.2, 0.1),   # Start L
            (2.3, 0.1),   # Still blinking
            (2.4, 0.1),   # Still blinking
            (2.5, 0.1),   # Still blinking
            (2.6, 0.3),   # End L (400ms - should be long)
        ]
        
        events = []
        for timestamp, ear_value in synthetic_data:
            events.extend(classifier.process_ear_sample(ear_value, timestamp))
        
        # Should detect 3 blinks and 1 symbol gap
        blink_events = [e for e in events if isinstance(e, BlinkEvent)]
        gap_events = classifier.get_recent_gaps()
        
        assert len(blink_events) == 3
        assert len(gap_events) == 1
        assert gap_events[0].gap_type == GapType.SYMBOL_GAP
        
        # Check blink types
        assert blink_events[0].blink_type == BlinkType.SHORT  # S1
        assert blink_events[1].blink_type == BlinkType.SHORT  # S2
        assert blink_events[2].blink_type == BlinkType.LONG   # L

