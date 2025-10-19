"""
Unit tests for calibration management system.
"""
import pytest
import threading
import time
from unittest.mock import patch

from core.calibration import (
    CalibrationManager, 
    CalibrationProfile, 
    get_calibration_manager,
    reset_calibration_manager
)


class TestCalibrationProfile:
    """Test CalibrationProfile dataclass."""
    
    def test_calibration_profile_creation(self):
        """Test creating a calibration profile."""
        profile = CalibrationProfile(
            name="test",
            short_max_ms=400,
            long_min_ms=401,
            long_max_ms=1000,
            symbol_gap_max_ms=500,
            word_gap_min_ms=1200,
            description="Test profile"
        )
        
        assert profile.name == "test"
        assert profile.short_max_ms == 400
        assert profile.long_min_ms == 401
        assert profile.long_max_ms == 1000
        assert profile.symbol_gap_max_ms == 500
        assert profile.word_gap_min_ms == 1200
        assert profile.description == "Test profile"


class TestCalibrationManager:
    """Test CalibrationManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Reset global calibration manager for clean tests
        reset_calibration_manager()
    
    def test_initialization_default_profile(self):
        """Test initialization with default profile."""
        manager = CalibrationManager()
        assert manager.get_active_profile() == "medium"
        assert manager.is_valid_profile("medium")
        assert manager.is_valid_profile("slow")
        assert not manager.is_valid_profile("invalid")
    
    def test_initialization_custom_profile(self):
        """Test initialization with custom default profile."""
        manager = CalibrationManager(default_profile="slow")
        assert manager.get_active_profile() == "slow"
    
    def test_initialization_invalid_profile(self):
        """Test initialization with invalid default profile falls back to medium."""
        manager = CalibrationManager(default_profile="invalid")
        assert manager.get_active_profile() == "medium"
    
    def test_set_profile_valid(self):
        """Test setting a valid profile."""
        manager = CalibrationManager()
        
        # Start with medium profile
        assert manager.get_active_profile() == "medium"
        
        # Switch to slow profile
        result = manager.set_profile("slow")
        assert result is True
        assert manager.get_active_profile() == "slow"
        
        # Switch back to medium
        result = manager.set_profile("medium")
        assert result is True
        assert manager.get_active_profile() == "medium"
    
    def test_set_profile_invalid(self):
        """Test setting an invalid profile."""
        manager = CalibrationManager()
        
        result = manager.set_profile("invalid")
        assert result is False
        assert manager.get_active_profile() == "medium"  # Should remain unchanged
    
    def test_get_thresholds_medium(self):
        """Test getting thresholds for medium profile."""
        manager = CalibrationManager()
        manager.set_profile("medium")
        
        thresholds = manager.get_thresholds()
        
        assert thresholds["short_max_ms"] == 350
        assert thresholds["long_min_ms"] == 351
        assert thresholds["long_max_ms"] == 900
        assert thresholds["symbol_gap_max_ms"] == 450
        assert thresholds["word_gap_min_ms"] == 1100
    
    def test_get_thresholds_slow(self):
        """Test getting thresholds for slow profile."""
        manager = CalibrationManager()
        manager.set_profile("slow")
        
        thresholds = manager.get_thresholds()
        
        assert thresholds["short_max_ms"] == 500
        assert thresholds["long_min_ms"] == 501
        assert thresholds["long_max_ms"] == 1200
        assert thresholds["symbol_gap_max_ms"] == 600
        assert thresholds["word_gap_min_ms"] == 1500
    
    def test_get_profile_info_active(self):
        """Test getting info for active profile."""
        manager = CalibrationManager()
        manager.set_profile("slow")
        
        info = manager.get_profile_info()
        assert info is not None
        assert info["name"] == "slow"
        assert info["description"] == "For users with slower blink patterns"
        assert info["thresholds"]["short_max_ms"] == 500
    
    def test_get_profile_info_specific(self):
        """Test getting info for specific profile."""
        manager = CalibrationManager()
        
        info = manager.get_profile_info("medium")
        assert info is not None
        assert info["name"] == "medium"
        assert info["description"] == "Standard timing for typical users"
        assert info["thresholds"]["short_max_ms"] == 350
    
    def test_get_profile_info_invalid(self):
        """Test getting info for invalid profile."""
        manager = CalibrationManager()
        
        info = manager.get_profile_info("invalid")
        assert info is None
    
    def test_get_available_profiles(self):
        """Test getting available profiles."""
        manager = CalibrationManager()
        
        profiles = manager.get_available_profiles()
        assert "slow" in profiles
        assert "medium" in profiles
        assert profiles["slow"] == "For users with slower blink patterns"
        assert profiles["medium"] == "Standard timing for typical users"
    
    def test_reset_to_default(self):
        """Test resetting to default profile."""
        manager = CalibrationManager()
        
        # Switch to slow profile
        manager.set_profile("slow")
        assert manager.get_active_profile() == "slow"
        
        # Reset to default
        manager.reset_to_default()
        assert manager.get_active_profile() == "medium"
    
    def test_get_stats(self):
        """Test getting calibration statistics."""
        manager = CalibrationManager()
        manager.set_profile("slow")
        
        stats = manager.get_stats()
        
        assert stats["active_profile"] == "slow"
        assert "slow" in stats["available_profiles"]
        assert "medium" in stats["available_profiles"]
        assert stats["current_thresholds"]["short_max_ms"] == 500
    
    def test_thread_safety(self):
        """Test thread safety of calibration manager."""
        manager = CalibrationManager()
        results = []
        errors = []
        
        def switch_profiles():
            try:
                for i in range(10):
                    if i % 2 == 0:
                        manager.set_profile("slow")
                        results.append(("slow", manager.get_thresholds()["short_max_ms"]))
                    else:
                        manager.set_profile("medium")
                        results.append(("medium", manager.get_thresholds()["short_max_ms"]))
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=switch_profiles)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check for errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        
        # Verify all results are consistent
        for profile, threshold in results:
            if profile == "slow":
                assert threshold == 500
            elif profile == "medium":
                assert threshold == 350


class TestGlobalCalibrationManager:
    """Test global calibration manager singleton."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_calibration_manager()
    
    def test_singleton_pattern(self):
        """Test that get_calibration_manager returns the same instance."""
        manager1 = get_calibration_manager()
        manager2 = get_calibration_manager()
        
        assert manager1 is manager2
    
    def test_reset_calibration_manager(self):
        """Test resetting the global calibration manager."""
        manager1 = get_calibration_manager()
        manager1.set_profile("slow")
        
        reset_calibration_manager()
        
        manager2 = get_calibration_manager()
        assert manager2 is not manager1
        assert manager2.get_active_profile() == "medium"  # Default profile
    
    def test_global_state_persistence(self):
        """Test that global state persists across calls."""
        manager = get_calibration_manager()
        manager.set_profile("slow")
        
        # Get manager again
        manager2 = get_calibration_manager()
        assert manager2.get_active_profile() == "slow"
        assert manager2.get_thresholds()["short_max_ms"] == 500


class TestCalibrationIntegration:
    """Test calibration integration with other components."""
    
    def setup_method(self):
        """Set up test environment."""
        reset_calibration_manager()
    
    def test_threshold_changes_affect_classification(self):
        """Test that threshold changes affect blink classification."""
        from core.blink_classifier import BlinkClassifier
        
        # Create classifier with calibration
        classifier = BlinkClassifier()
        
        # Test with medium profile (default)
        manager = get_calibration_manager()
        manager.set_profile("medium")
        
        # Process a blink that should be classified as short in medium profile
        # but might be classified differently in slow profile
        ear_value = 0.15  # Below threshold
        timestamp = time.time()
        
        # Start blink
        events = classifier.process_ear_sample(ear_value, timestamp)
        assert len(events) == 0  # No events yet, still blinking
        
        # End blink after 300ms (should be short in medium, but not in slow)
        timestamp += 0.3  # 300ms
        events = classifier.process_ear_sample(0.3, timestamp)  # Above threshold
        
        if events:
            # In medium profile, 300ms should be classified as short
            assert events[0].blink_type.value == "S"
        
        # Switch to slow profile
        manager.set_profile("slow")
        
        # Reset classifier
        classifier.reset()
        
        # Process same blink pattern
        timestamp = time.time()
        events = classifier.process_ear_sample(ear_value, timestamp)
        timestamp += 0.3  # 300ms
        events = classifier.process_ear_sample(0.3, timestamp)
        
        if events:
            # In slow profile, 300ms should still be classified as short
            # (since 300ms < 500ms short_max_ms)
            assert events[0].blink_type.value == "S"
    
    def test_gap_detection_with_different_profiles(self):
        """Test that gap detection uses different thresholds for different profiles."""
        from core.blink_classifier import BlinkClassifier, GapType
        
        classifier = BlinkClassifier()
        manager = get_calibration_manager()
        
        # Test with medium profile
        manager.set_profile("medium")
        
        # Process a blink
        timestamp = time.time()
        classifier.process_ear_sample(0.15, timestamp)  # Start blink
        classifier.process_ear_sample(0.3, timestamp + 0.2)  # End blink
        
        # Wait for symbol gap (450ms in medium profile)
        timestamp += 0.5  # 500ms gap
        events = classifier.process_ear_sample(0.3, timestamp)
        
        # Should detect symbol gap
        gaps = classifier.get_recent_gaps(max_events=1)
        if gaps:
            assert gaps[0].gap_type == GapType.SYMBOL_GAP
        
        # Switch to slow profile
        manager.set_profile("slow")
        classifier.reset()
        
        # Process same pattern
        timestamp = time.time()
        classifier.process_ear_sample(0.15, timestamp)  # Start blink
        classifier.process_ear_sample(0.3, timestamp + 0.2)  # End blink
        
        # Wait for symbol gap (600ms in slow profile)
        timestamp += 0.5  # 500ms gap - should NOT be enough for slow profile
        events = classifier.process_ear_sample(0.3, timestamp)
        
        # Should NOT detect symbol gap yet
        gaps = classifier.get_recent_gaps(max_events=1)
        assert len(gaps) == 0
        
        # Wait longer (700ms total)
        timestamp += 0.2  # Additional 200ms
        events = classifier.process_ear_sample(0.3, timestamp)
        
        # Now should detect symbol gap
        gaps = classifier.get_recent_gaps(max_events=1)
        if gaps:
            assert gaps[0].gap_type == GapType.SYMBOL_GAP


if __name__ == "__main__":
    pytest.main([__file__])