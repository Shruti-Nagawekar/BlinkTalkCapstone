"""
Integration tests for blink detection system.
"""
import pytest
import time
import numpy as np
from unittest.mock import Mock, patch

from core.eye_tracker import create_eye_tracker
from core.blink_classifier import BlinkClassifier, BlinkType, GapType
from core.calibration import CalibrationManager

class TestBlinkDetectionIntegration:
    """Integration tests for the complete blink detection system."""
    
    @pytest.fixture
    def calibration_manager(self):
        """Create a calibration manager for testing."""
        return CalibrationManager()
    
    @pytest.fixture
    def eye_tracker(self):
        """Create an eye tracker for testing."""
        return create_eye_tracker("mock")
    
    @pytest.fixture
    def blink_classifier(self, calibration_manager):
        """Create a blink classifier with calibration thresholds."""
        thresholds = calibration_manager.get_thresholds()
        return BlinkClassifier(thresholds, ear_threshold=0.25)
    
    def test_end_to_end_blink_detection(self, eye_tracker, blink_classifier):
        """Test complete end-to-end blink detection pipeline."""
        # Simulate camera frames with synthetic EAR data
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Simulate "yes" pattern (S S)
        events = []
        
        # First short blink
        ear = eye_tracker.calculate_ear(frame)  # Normal state
        events.extend(blink_classifier.process_ear_sample(ear, time.time()))
        
        time.sleep(0.1)
        events.extend(blink_classifier.process_ear_sample(0.15, time.time()))  # Start S
        time.sleep(0.1)
        events.extend(blink_classifier.process_ear_sample(0.30, time.time()))  # End S
        
        # Gap between blinks
        time.sleep(0.2)
        events.extend(blink_classifier.process_ear_sample(0.35, time.time()))  # Normal
        
        # Second short blink
        time.sleep(0.1)
        events.extend(blink_classifier.process_ear_sample(0.15, time.time()))  # Start S
        time.sleep(0.1)
        events.extend(blink_classifier.process_ear_sample(0.30, time.time()))  # End S
        
        # Check results
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 2
        assert all(e.blink_type == BlinkType.SHORT for e in blink_events)
        
        # Check sequence
        sequence = blink_classifier.get_current_sequence()
        assert sequence == [BlinkType.SHORT, BlinkType.SHORT]
    
    def test_calibration_profile_switching(self, calibration_manager, blink_classifier):
        """Test that calibration profile switching affects blink classification."""
        # Test with medium profile (default)
        medium_thresholds = calibration_manager.get_thresholds()
        assert medium_thresholds["short_max_ms"] == 350
        
        # Switch to slow profile
        calibration_manager.set_profile("slow")
        slow_thresholds = calibration_manager.get_thresholds()
        assert slow_thresholds["short_max_ms"] == 400
        assert slow_thresholds["long_min_ms"] == 401
        
        # Create new classifier with slow thresholds
        slow_classifier = BlinkClassifier(slow_thresholds, ear_threshold=0.25)
        
        # Test that slow profile allows longer short blinks
        events = []
        events.extend(slow_classifier.process_ear_sample(0.15, 0.0))  # Start blink
        events.extend(slow_classifier.process_ear_sample(0.30, 0.38))  # End blink (380ms)
        
        # Should be classified as short with slow profile
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 1
        assert blink_events[0].blink_type == BlinkType.SHORT
        
        # Same duration with medium profile should be long
        medium_classifier = BlinkClassifier(medium_thresholds, ear_threshold=0.25)
        events = []
        events.extend(medium_classifier.process_ear_sample(0.15, 0.0))  # Start blink
        events.extend(medium_classifier.process_ear_sample(0.30, 0.38))  # End blink (380ms)
        
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 1
        assert blink_events[0].blink_type == BlinkType.LONG
    
    def test_synthetic_ear_trace_processing(self, blink_classifier):
        """Test processing of synthetic EAR traces."""
        # Create synthetic EAR trace for "hungry" pattern (L S)
        timestamps = np.linspace(0, 2.0, 21)  # 2 seconds, 0.1s intervals
        ear_values = np.array([
            0.3, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.3, 0.3, 0.3,  # Long blink (0.5s)
            0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3,  # Gap
            0.1, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3   # Short blink (0.1s)
        ])
        
        events = []
        for timestamp, ear_value in zip(timestamps, ear_values):
            events.extend(blink_classifier.process_ear_sample(ear_value, timestamp))
        
        # Should detect L S pattern
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 2
        assert blink_events[0].blink_type == BlinkType.LONG
        assert blink_events[1].blink_type == BlinkType.SHORT
        
        # Check sequence
        sequence = blink_classifier.get_current_sequence()
        assert sequence == [BlinkType.LONG, BlinkType.SHORT]
    
    def test_noise_handling(self, blink_classifier):
        """Test handling of noisy EAR data."""
        # Create noisy EAR trace
        timestamps = np.linspace(0, 1.0, 11)
        ear_values = np.array([
            0.3, 0.25, 0.2, 0.15, 0.1, 0.12, 0.08, 0.15, 0.2, 0.25, 0.3
        ])
        
        events = []
        for timestamp, ear_value in zip(timestamps, ear_values):
            events.extend(blink_classifier.process_ear_sample(ear_value, timestamp))
        
        # Should detect one short blink despite noise
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 1
        assert blink_events[0].blink_type == BlinkType.SHORT
    
    def test_multiple_word_sequences(self, blink_classifier):
        """Test processing multiple word sequences."""
        # First word: "yes" (S S)
        events = []
        events.extend(blink_classifier.process_ear_sample(0.15, 0.0))  # Start S1
        events.extend(blink_classifier.process_ear_sample(0.30, 0.1))  # End S1
        events.extend(blink_classifier.process_ear_sample(0.15, 0.2))  # Start S2
        events.extend(blink_classifier.process_ear_sample(0.30, 0.3))  # End S2
        
        # Word gap
        events.extend(blink_classifier.process_ear_sample(0.35, 1.5))  # Word gap
        
        # Second word: "no" (L)
        events.extend(blink_classifier.process_ear_sample(0.15, 1.6))  # Start L
        events.extend(blink_classifier.process_ear_sample(0.30, 1.9))  # End L
        
        # Check all events
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        gap_events = [e for e in events if hasattr(e, 'gap_type')]
        
        assert len(blink_events) == 3
        assert len(gap_events) == 1
        assert gap_events[0].gap_type == GapType.WORD_GAP
        
        # Check sequence (should include all blinks)
        sequence = blink_classifier.get_current_sequence()
        assert sequence == [BlinkType.SHORT, BlinkType.SHORT, BlinkType.LONG]
    
    def test_performance_with_high_frequency_data(self, blink_classifier):
        """Test performance with high-frequency EAR data."""
        # Generate high-frequency data (100Hz)
        duration = 1.0  # 1 second
        sample_rate = 100  # 100Hz
        num_samples = int(duration * sample_rate)
        
        timestamps = np.linspace(0, duration, num_samples)
        
        # Create EAR trace with multiple blinks
        ear_values = np.full(num_samples, 0.3)  # Normal state
        
        # Add short blinks at specific times
        blink_times = [0.2, 0.4, 0.6, 0.8]
        for blink_time in blink_times:
            start_idx = int(blink_time * sample_rate)
            end_idx = int((blink_time + 0.1) * sample_rate)
            ear_values[start_idx:end_idx] = 0.1
        
        # Process all samples
        start_time = time.time()
        events = []
        for timestamp, ear_value in zip(timestamps, ear_values):
            events.extend(blink_classifier.process_ear_sample(ear_value, timestamp))
        processing_time = time.time() - start_time
        
        # Should process quickly (less than 1 second for 100 samples)
        assert processing_time < 1.0
        
        # Should detect 4 short blinks
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 4
        assert all(e.blink_type == BlinkType.SHORT for e in blink_events)
    
    def test_edge_cases(self, blink_classifier):
        """Test edge cases and boundary conditions."""
        events = []
        
        # Test exactly at threshold boundary
        events.extend(blink_classifier.process_ear_sample(0.25, 0.0))  # Exactly at threshold
        events.extend(blink_classifier.process_ear_sample(0.24, 0.1))  # Just below
        events.extend(blink_classifier.process_ear_sample(0.25, 0.2))  # Back to threshold
        
        # Should detect one short blink
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 1
        
        # Test very short blink (should still be detected)
        events = []
        events.extend(blink_classifier.process_ear_sample(0.15, 0.0))  # Start
        events.extend(blink_classifier.process_ear_sample(0.30, 0.05))  # End (50ms)
        
        blink_events = [e for e in events if hasattr(e, 'blink_type')]
        assert len(blink_events) == 1
        assert blink_events[0].blink_type == BlinkType.SHORT
    
    def test_statistics_tracking(self, blink_classifier):
        """Test that statistics are properly tracked."""
        # Add some blinks
        events = []
        events.extend(blink_classifier.process_ear_sample(0.15, 0.0))  # Start S
        events.extend(blink_classifier.process_ear_sample(0.30, 0.1))  # End S
        events.extend(blink_classifier.process_ear_sample(0.15, 0.2))  # Start L
        events.extend(blink_classifier.process_ear_sample(0.30, 0.5))  # End L
        
        # Check statistics
        stats = blink_classifier.get_stats()
        assert stats["total_blinks"] == 2
        assert stats["short_blinks"] == 1
        assert stats["long_blinks"] == 1
        assert stats["avg_duration_ms"] > 0
        assert stats["current_sequence_length"] == 2

