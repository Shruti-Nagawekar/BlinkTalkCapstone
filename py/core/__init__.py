# Core engine package
from .eye_tracker import EyeTracker, DlibEyeTracker, MediaPipeEyeTracker, create_eye_tracker
from .blink_classifier import BlinkClassifier, BlinkType, GapType, BlinkEvent, GapEvent
from .calibration import CalibrationManager, CalibrationProfile
from .frame_buffer import LatestFrameBuffer, get_frame_buffer

# Only import these if they exist
try:
    from .sequence_engine import SequenceEngine
except ImportError:
    SequenceEngine = None

try:
    from .sequences_loader import SequencesLoader
except ImportError:
    SequencesLoader = None

__all__ = [
    "EyeTracker",
    "DlibEyeTracker", 
    "MediaPipeEyeTracker",
    "create_eye_tracker",
    "BlinkClassifier",
    "BlinkType",
    "GapType", 
    "BlinkEvent",
    "GapEvent",
    "CalibrationManager",
    "CalibrationProfile",
    "LatestFrameBuffer",
    "get_frame_buffer",
    "SequenceEngine",
    "SequencesLoader"
]
