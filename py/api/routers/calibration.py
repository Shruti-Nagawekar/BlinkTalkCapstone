"""
Calibration API endpoints for BlinkTalk system.
Handles profile switching and threshold management.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.calibration import get_calibration_manager, CalibrationManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/calibration", tags=["calibration"])

class CalibrationProfileRequest(BaseModel):
    """Request model for setting calibration profile."""
    profile: str = Field(..., description="Profile name to set", example="slow")

class CalibrationProfileResponse(BaseModel):
    """Response model for calibration profile operations."""
    message: str
    profile: str
    description: str
    thresholds: Dict[str, int]

class CalibrationThresholdsResponse(BaseModel):
    """Response model for threshold values."""
    profile: str
    thresholds: Dict[str, int]

class CalibrationInfoResponse(BaseModel):
    """Response model for calibration information."""
    active_profile: str
    available_profiles: Dict[str, str]
    current_thresholds: Dict[str, int]

class CustomCalibrationRequest(BaseModel):
    """Request model for setting custom calibration thresholds."""
    short_max_ms: int = Field(..., ge=100, le=2000, description="Maximum duration for short blinks (100-2000ms)")
    long_min_ms: int = Field(..., ge=200, le=3000, description="Minimum duration for long blinks (200-3000ms)")
    long_max_ms: int = Field(..., ge=500, le=5000, description="Maximum duration for long blinks (500-5000ms)")
    symbol_gap_max_ms: int = Field(..., ge=200, le=2000, description="Maximum gap between symbols (200-2000ms)")
    word_gap_min_ms: int = Field(..., ge=500, le=5000, description="Minimum gap between words (500-5000ms)")

class CustomCalibrationResponse(BaseModel):
    """Response model for custom calibration operations."""
    message: str
    profile: str
    description: str
    thresholds: Dict[str, int]
    is_custom: bool

@router.post("/set", response_model=CalibrationProfileResponse)
async def set_calibration_profile(request: CalibrationProfileRequest):
    """
    Set the active calibration profile.
    
    This endpoint allows switching between different calibration profiles
    (slow, medium) which adjust the timing thresholds for blink detection.
    
    Args:
        request: Calibration profile request with profile name
        
    Returns:
        Calibration profile response with updated information
        
    Raises:
        HTTPException: If profile name is invalid
    """
    try:
        calibration_manager = get_calibration_manager()
        
        # Validate profile name
        if not calibration_manager.is_valid_profile(request.profile):
            available_profiles = list(calibration_manager.get_available_profiles().keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profile '{request.profile}'. Available profiles: {available_profiles}"
            )
        
        # Set the profile
        success = calibration_manager.set_profile(request.profile)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set calibration profile"
            )
        
        # Get updated profile info
        profile_info = calibration_manager.get_profile_info(request.profile)
        if not profile_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve profile information"
            )
        
        logger.info(f"Calibration profile set to: {request.profile}")
        
        return CalibrationProfileResponse(
            message=f"Profile set to '{request.profile}'",
            profile=profile_info["name"],
            description=profile_info["description"],
            thresholds=profile_info["thresholds"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting calibration profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while setting calibration profile"
        )

@router.get("/active", response_model=CalibrationProfileResponse)
async def get_active_profile():
    """
    Get the currently active calibration profile.
    
    Returns:
        Calibration profile response with current profile information
    """
    try:
        calibration_manager = get_calibration_manager()
        active_profile = calibration_manager.get_active_profile()
        
        # Get profile info
        profile_info = calibration_manager.get_profile_info(active_profile)
        if not profile_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve active profile information"
            )
        
        return CalibrationProfileResponse(
            message=f"Active profile: {active_profile}",
            profile=profile_info["name"],
            description=profile_info["description"],
            thresholds=profile_info["thresholds"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting active profile"
        )

@router.get("/thresholds", response_model=CalibrationThresholdsResponse)
async def get_current_thresholds():
    """
    Get the current threshold values from the active profile.
    
    Returns:
        Calibration thresholds response with current threshold values
    """
    try:
        calibration_manager = get_calibration_manager()
        active_profile = calibration_manager.get_active_profile()
        thresholds = calibration_manager.get_thresholds()
        
        return CalibrationThresholdsResponse(
            profile=active_profile,
            thresholds=thresholds
        )
        
    except Exception as e:
        logger.error(f"Error getting current thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting current thresholds"
        )

@router.get("/info", response_model=CalibrationInfoResponse)
async def get_calibration_info():
    """
    Get comprehensive calibration information.
    
    Returns:
        Calibration info response with all available information
    """
    try:
        calibration_manager = get_calibration_manager()
        stats = calibration_manager.get_stats()
        available_profiles = calibration_manager.get_available_profiles()
        
        return CalibrationInfoResponse(
            active_profile=stats["active_profile"],
            available_profiles=available_profiles,
            current_thresholds=stats["current_thresholds"]
        )
        
    except Exception as e:
        logger.error(f"Error getting calibration info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting calibration info"
        )

@router.post("/reset", response_model=CalibrationProfileResponse)
async def reset_calibration():
    """
    Reset calibration to default profile (medium).
    
    Returns:
        Calibration profile response with reset profile information
    """
    try:
        calibration_manager = get_calibration_manager()
        calibration_manager.reset_to_default()
        
        # Get updated profile info
        active_profile = calibration_manager.get_active_profile()
        profile_info = calibration_manager.get_profile_info(active_profile)
        if not profile_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve reset profile information"
            )
        
        logger.info("Calibration reset to default profile")
        
        return CalibrationProfileResponse(
            message="Calibration reset to default profile",
            profile=profile_info["name"],
            description=profile_info["description"],
            thresholds=profile_info["thresholds"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while resetting calibration"
        )

@router.post("/custom", response_model=CustomCalibrationResponse)
async def set_custom_calibration(request: CustomCalibrationRequest):
    """
    Set custom calibration thresholds.
    
    This endpoint allows setting custom threshold values for blink detection
    instead of using predefined profiles. The values are validated for reasonable
    ranges and logical consistency.
    
    Args:
        request: Custom calibration request with threshold values
        
    Returns:
        Custom calibration response with updated information
        
    Raises:
        HTTPException: If threshold values are invalid
    """
    try:
        calibration_manager = get_calibration_manager()
        
        # Set custom profile with validation
        success = calibration_manager.set_custom_profile(
            short_max_ms=request.short_max_ms,
            long_min_ms=request.long_min_ms,
            long_max_ms=request.long_max_ms,
            symbol_gap_max_ms=request.symbol_gap_max_ms,
            word_gap_min_ms=request.word_gap_min_ms
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid custom threshold values. Please check the ranges and logical consistency."
            )
        
        # Switch to custom profile
        switch_success = calibration_manager.set_profile("custom")
        if not switch_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to switch to custom profile"
            )
        
        # Get updated profile info
        profile_info = calibration_manager.get_profile_info("custom")
        if not profile_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve custom profile information"
            )
        
        logger.info(f"Custom calibration profile set: {profile_info['thresholds']}")
        
        return CustomCalibrationResponse(
            message="Custom calibration profile set successfully",
            profile=profile_info["name"],
            description=profile_info["description"],
            thresholds=profile_info["thresholds"],
            is_custom=profile_info["is_custom"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting custom calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while setting custom calibration"
        )

@router.get("/custom", response_model=CustomCalibrationResponse)
async def get_custom_calibration():
    """
    Get the current custom calibration profile.
    
    Returns:
        Custom calibration response with current custom profile information
        
    Raises:
        HTTPException: If no custom profile is set
    """
    try:
        calibration_manager = get_calibration_manager()
        custom_profile = calibration_manager.get_custom_profile()
        
        if custom_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No custom calibration profile set"
            )
        
        # Get profile info
        profile_info = calibration_manager.get_profile_info("custom")
        if not profile_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve custom profile information"
            )
        
        return CustomCalibrationResponse(
            message="Custom calibration profile retrieved",
            profile=profile_info["name"],
            description=profile_info["description"],
            thresholds=profile_info["thresholds"],
            is_custom=profile_info["is_custom"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting custom calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting custom calibration"
        )

@router.delete("/custom", response_model=CalibrationProfileResponse)
async def clear_custom_calibration():
    """
    Clear the custom calibration profile and reset to default.
    
    Returns:
        Calibration profile response with reset profile information
    """
    try:
        calibration_manager = get_calibration_manager()
        calibration_manager.clear_custom_profile()
        
        # Get updated profile info
        active_profile = calibration_manager.get_active_profile()
        profile_info = calibration_manager.get_profile_info(active_profile)
        if not profile_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve reset profile information"
            )
        
        logger.info("Custom calibration profile cleared")
        
        return CalibrationProfileResponse(
            message="Custom calibration profile cleared",
            profile=profile_info["name"],
            description=profile_info["description"],
            thresholds=profile_info["thresholds"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing custom calibration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while clearing custom calibration"
        )