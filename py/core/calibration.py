"""
Calibration management for BlinkTalk system.
Handles profile switching and threshold management.
"""
import logging
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class CalibrationProfile:
    """Represents a calibration profile with timing thresholds."""
    name: str
    short_max_ms: int
    long_min_ms: int
    long_max_ms: int
    symbol_gap_max_ms: int
    word_gap_min_ms: int
    description: str
    is_custom: bool = False  # Flag to identify custom profiles

class CalibrationManager:
    """
    Manages calibration profiles and provides thread-safe access to thresholds.
    
    This class handles switching between different calibration profiles (slow, medium)
    and provides the current threshold values to other components.
    """
    
    # Define available calibration profiles
    CALIBRATION_PROFILES = {
        "slow": CalibrationProfile(
            name="slow",
            short_max_ms=500,      # Increased from 350ms
            long_min_ms=501,       # Increased from 351ms
            long_max_ms=1200,      # Increased from 900ms
            symbol_gap_max_ms=600, # Increased from 450ms
            word_gap_min_ms=1500,  # Increased from 1100ms
            description="For users with slower blink patterns"
        ),
        "medium": CalibrationProfile(
            name="medium",
            short_max_ms=350,      # Default from sequences_v1.json
            long_min_ms=351,       # Default from sequences_v1.json
            long_max_ms=900,       # Default from sequences_v1.json
            symbol_gap_max_ms=450, # Default from sequences_v1.json
            word_gap_min_ms=1100,  # Default from sequences_v1.json
            description="Standard timing for typical users"
        )
    }
    
    def __init__(self, default_profile: str = "medium"):
        """
        Initialize the calibration manager.
        
        Args:
            default_profile: Name of the default profile to use
        """
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._active_profile = default_profile
        self._custom_profile = None  # Store custom profile data
        
        # Validate default profile
        if default_profile not in self.CALIBRATION_PROFILES:
            logger.warning(f"Invalid default profile '{default_profile}', using 'medium'")
            self._active_profile = "medium"
        
        # Initialize with default profile thresholds
        self._current_thresholds = self._get_profile_thresholds(self._active_profile)
        
        logger.info(f"CalibrationManager initialized with profile: {self._active_profile}")
    
    def set_profile(self, profile_name: str) -> bool:
        """
        Switch to the specified calibration profile.
        
        Args:
            profile_name: Name of the profile to switch to
            
        Returns:
            True if profile was set successfully, False otherwise
        """
        with self._lock:
            if profile_name == "custom":
                if self._custom_profile is None:
                    logger.error("No custom profile set")
                    return False
                self._active_profile = "custom"
                self._current_thresholds = self._get_custom_thresholds()
                logger.info("Switched to custom calibration profile")
                return True
            elif profile_name not in self.CALIBRATION_PROFILES:
                logger.error(f"Invalid profile name: {profile_name}")
                return False
            
            old_profile = self._active_profile
            self._active_profile = profile_name
            self._current_thresholds = self._get_profile_thresholds(profile_name)
            
            logger.info(f"Calibration profile changed from '{old_profile}' to '{profile_name}'")
            return True
    
    def get_active_profile(self) -> str:
        """
        Get the currently active profile name.
        
        Returns:
            Name of the active profile
        """
        with self._lock:
            return self._active_profile
    
    def get_thresholds(self) -> Dict[str, int]:
        """
        Get current threshold values.
        
        Returns:
            Dictionary of current threshold values
        """
        with self._lock:
            return self._current_thresholds.copy()
    
    def get_profile_info(self, profile_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific profile or the active profile.
        
        Args:
            profile_name: Name of profile to get info for (None for active profile)
            
        Returns:
            Dictionary with profile information or None if profile not found
        """
        with self._lock:
            if profile_name is None:
                profile_name = self._active_profile
            
            if profile_name == "custom":
                if self._custom_profile is None:
                    return None
                profile = self._custom_profile
            elif profile_name not in self.CALIBRATION_PROFILES:
                return None
            else:
                profile = self.CALIBRATION_PROFILES[profile_name]
            
            return {
                "name": profile.name,
                "description": profile.description,
                "thresholds": {
                    "short_max_ms": profile.short_max_ms,
                    "long_min_ms": profile.long_min_ms,
                    "long_max_ms": profile.long_max_ms,
                    "symbol_gap_max_ms": profile.symbol_gap_max_ms,
                    "word_gap_min_ms": profile.word_gap_min_ms
                },
                "is_custom": getattr(profile, 'is_custom', False)
            }
    
    def get_available_profiles(self) -> Dict[str, str]:
        """
        Get list of available profiles with descriptions.
        
        Returns:
            Dictionary mapping profile names to descriptions
        """
        with self._lock:
            profiles = {
                name: profile.description 
                for name, profile in self.CALIBRATION_PROFILES.items()
            }
            
            # Add custom profile if it exists
            if self._custom_profile is not None:
                profiles["custom"] = self._custom_profile.description
            
            return profiles
    
    def reset_to_default(self) -> None:
        """Reset to the default profile (medium)."""
        with self._lock:
            self.set_profile("medium")
            logger.info("Reset to default calibration profile: medium")
    
    def _get_profile_thresholds(self, profile_name: str) -> Dict[str, int]:
        """
        Get threshold values for a specific profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary of threshold values
        """
        profile = self.CALIBRATION_PROFILES[profile_name]
        return {
            "short_max_ms": profile.short_max_ms,
            "long_min_ms": profile.long_min_ms,
            "long_max_ms": profile.long_max_ms,
            "symbol_gap_max_ms": profile.symbol_gap_max_ms,
            "word_gap_min_ms": profile.word_gap_min_ms
        }
    
    def is_valid_profile(self, profile_name: str) -> bool:
        """
        Check if a profile name is valid.
        
        Args:
            profile_name: Name to check
            
        Returns:
            True if profile exists, False otherwise
        """
        return profile_name in self.CALIBRATION_PROFILES or profile_name == "custom"
    
    def set_custom_profile(self, short_max_ms: int, long_min_ms: int, long_max_ms: int, 
                          symbol_gap_max_ms: int, word_gap_min_ms: int) -> bool:
        """
        Set custom calibration thresholds.
        
        Args:
            short_max_ms: Maximum duration for short blinks
            long_min_ms: Minimum duration for long blinks
            long_max_ms: Maximum duration for long blinks
            symbol_gap_max_ms: Maximum gap between symbols
            word_gap_min_ms: Minimum gap between words
            
        Returns:
            True if custom profile was set successfully, False otherwise
        """
        with self._lock:
            # Validate threshold ranges
            if not self._validate_custom_thresholds(short_max_ms, long_min_ms, long_max_ms, 
                                                  symbol_gap_max_ms, word_gap_min_ms):
                return False
            
            # Create custom profile
            self._custom_profile = CalibrationProfile(
                name="custom",
                short_max_ms=short_max_ms,
                long_min_ms=long_min_ms,
                long_max_ms=long_max_ms,
                symbol_gap_max_ms=symbol_gap_max_ms,
                word_gap_min_ms=word_gap_min_ms,
                description="Custom calibration profile",
                is_custom=True
            )
            
            # Update current thresholds if custom is active
            if self._active_profile == "custom":
                self._current_thresholds = self._get_custom_thresholds()
            
            logger.info(f"Custom calibration profile set: {self._custom_profile}")
            return True
    
    def _validate_custom_thresholds(self, short_max_ms: int, long_min_ms: int, long_max_ms: int,
                                  symbol_gap_max_ms: int, word_gap_min_ms: int) -> bool:
        """
        Validate custom threshold values for reasonable ranges.
        
        Args:
            short_max_ms: Maximum duration for short blinks
            long_min_ms: Minimum duration for long blinks
            long_max_ms: Maximum duration for long blinks
            symbol_gap_max_ms: Maximum gap between symbols
            word_gap_min_ms: Minimum gap between words
            
        Returns:
            True if thresholds are valid, False otherwise
        """
        # Basic range validation
        if not (100 <= short_max_ms <= 2000):
            logger.error(f"Invalid short_max_ms: {short_max_ms} (must be 100-2000)")
            return False
        
        if not (200 <= long_min_ms <= 3000):
            logger.error(f"Invalid long_min_ms: {long_min_ms} (must be 200-3000)")
            return False
        
        if not (500 <= long_max_ms <= 5000):
            logger.error(f"Invalid long_max_ms: {long_max_ms} (must be 500-5000)")
            return False
        
        if not (200 <= symbol_gap_max_ms <= 2000):
            logger.error(f"Invalid symbol_gap_max_ms: {symbol_gap_max_ms} (must be 200-2000)")
            return False
        
        if not (500 <= word_gap_min_ms <= 5000):
            logger.error(f"Invalid word_gap_min_ms: {word_gap_min_ms} (must be 500-5000)")
            return False
        
        # Logical validation
        if short_max_ms >= long_min_ms:
            logger.error(f"short_max_ms ({short_max_ms}) must be less than long_min_ms ({long_min_ms})")
            return False
        
        if long_min_ms >= long_max_ms:
            logger.error(f"long_min_ms ({long_min_ms}) must be less than long_max_ms ({long_max_ms})")
            return False
        
        if symbol_gap_max_ms >= word_gap_min_ms:
            logger.error(f"symbol_gap_max_ms ({symbol_gap_max_ms}) must be less than word_gap_min_ms ({word_gap_min_ms})")
            return False
        
        return True
    
    def _get_custom_thresholds(self) -> Dict[str, int]:
        """
        Get threshold values for custom profile.
        
        Returns:
            Dictionary of custom threshold values
        """
        if self._custom_profile is None:
            raise ValueError("No custom profile set")
        
        return {
            "short_max_ms": self._custom_profile.short_max_ms,
            "long_min_ms": self._custom_profile.long_min_ms,
            "long_max_ms": self._custom_profile.long_max_ms,
            "symbol_gap_max_ms": self._custom_profile.symbol_gap_max_ms,
            "word_gap_min_ms": self._custom_profile.word_gap_min_ms
        }
    
    def get_custom_profile(self) -> Optional[CalibrationProfile]:
        """
        Get the current custom profile.
        
        Returns:
            Custom profile if set, None otherwise
        """
        with self._lock:
            return self._custom_profile
    
    def clear_custom_profile(self) -> None:
        """
        Clear the custom profile.
        """
        with self._lock:
            self._custom_profile = None
            if self._active_profile == "custom":
                # Switch back to medium if custom was active
                self.set_profile("medium")
            logger.info("Custom calibration profile cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get calibration manager statistics.
        
        Returns:
            Dictionary with calibration statistics
        """
        with self._lock:
            available_profiles = list(self.CALIBRATION_PROFILES.keys())
            if self._custom_profile is not None:
                available_profiles.append("custom")
            
            return {
                "active_profile": self._active_profile,
                "available_profiles": available_profiles,
                "current_thresholds": self._current_thresholds.copy(),
                "has_custom_profile": self._custom_profile is not None
            }

# Global calibration manager instance
_calibration_manager = None
_calibration_lock = threading.Lock()

def get_calibration_manager() -> CalibrationManager:
    """
    Get the global calibration manager instance (singleton pattern).
    
    Returns:
        The global CalibrationManager instance
    """
    global _calibration_manager
    
    if _calibration_manager is None:
        with _calibration_lock:
            if _calibration_manager is None:
                _calibration_manager = CalibrationManager()
    
    return _calibration_manager

def reset_calibration_manager() -> None:
    """Reset the global calibration manager (for testing)."""
    global _calibration_manager
    
    with _calibration_lock:
        _calibration_manager = None