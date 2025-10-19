"""
Eye tracking and EAR (Eye Aspect Ratio) calculation.
"""
import cv2
import numpy as np
from typing import Optional, Tuple
from abc import ABC, abstractmethod

class EyeTracker(ABC):
    """Abstract interface for eye tracking implementations."""
    
    @abstractmethod
    def calculate_ear(self, frame: np.ndarray) -> Optional[float]:
        """
        Calculate Eye Aspect Ratio from a frame.
        
        Args:
            frame: Input image frame as numpy array
            
        Returns:
            EAR value (0.0-1.0) or None if eyes not detected
        """
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if the eye tracker is properly initialized."""
        pass

class DlibEyeTracker(EyeTracker):
    """Eye tracker implementation using dlib."""
    
    def __init__(self):
        self.detector = None
        self.predictor = None
        self.initialized = False
        self._initialize()
    
    def _initialize(self):
        """Initialize dlib face detector and landmark predictor."""
        try:
            import dlib
            # Initialize face detector
            self.detector = dlib.get_frontal_face_detector()
            # Download predictor file if needed
            predictor_path = "shape_predictor_68_face_landmarks.dat"
            self.predictor = dlib.shape_predictor(predictor_path)
            self.initialized = True
        except ImportError:
            print("Warning: dlib not available, falling back to mock implementation")
            self.initialized = False
        except Exception as e:
            print(f"Warning: Could not initialize dlib: {e}")
            self.initialized = False
    
    def calculate_ear(self, frame: np.ndarray) -> Optional[float]:
        """Calculate EAR using dlib facial landmarks."""
        if not self.initialized:
            return self._mock_ear()
        
        try:
            import dlib
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray)
            
            if len(faces) == 0:
                return None
            
            # Get landmarks for the first face
            landmarks = self.predictor(gray, faces[0])
            return self._calculate_ear_from_landmarks(landmarks)
            
        except Exception as e:
            print(f"Error calculating EAR: {e}")
            return None
    
    def _calculate_ear_from_landmarks(self, landmarks) -> float:
        """Calculate EAR from facial landmarks."""
        import dlib
        
        # Eye landmark indices (0-based)
        # Left eye: 36-41, Right eye: 42-47
        left_eye_indices = [36, 37, 38, 39, 40, 41]
        right_eye_indices = [42, 43, 44, 45, 46, 47]
        
        def get_ear(eye_indices):
            # Get eye landmark points
            eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in eye_indices]
            
            # Calculate vertical distances
            vertical_1 = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            vertical_2 = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            
            # Calculate horizontal distance
            horizontal = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            
            # Calculate EAR
            ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
            return ear
        
        # Calculate EAR for both eyes and average
        left_ear = get_ear(left_eye_indices)
        right_ear = get_ear(right_eye_indices)
        
        return (left_ear + right_ear) / 2.0
    
    def _mock_ear(self) -> float:
        """Mock EAR calculation for testing when dlib is not available."""
        # Return a random EAR value between 0.2 and 0.4 (typical range)
        return np.random.uniform(0.2, 0.4)
    
    def is_initialized(self) -> bool:
        return self.initialized

class MediaPipeEyeTracker(EyeTracker):
    """Eye tracker implementation using MediaPipe."""
    
    def __init__(self):
        self.mp_face_mesh = None
        self.mp_drawing = None
        self.face_mesh = None
        self.initialized = False
        self._initialize()
    
    def _initialize(self):
        """Initialize MediaPipe face mesh."""
        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.initialized = True
        except ImportError:
            print("Warning: MediaPipe not available, falling back to mock implementation")
            self.initialized = False
        except Exception as e:
            print(f"Warning: Could not initialize MediaPipe: {e}")
            self.initialized = False
    
    def calculate_ear(self, frame: np.ndarray) -> Optional[float]:
        """Calculate EAR using MediaPipe face mesh."""
        if not self.initialized:
            return self._mock_ear()
        
        try:
            import mediapipe as mp
            import cv2
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks:
                return None
            
            # Get landmarks for the first face
            landmarks = results.multi_face_landmarks[0]
            return self._calculate_ear_from_mediapipe_landmarks(landmarks, frame.shape)
            
        except Exception as e:
            print(f"Error calculating EAR: {e}")
            return None
    
    def _calculate_ear_from_mediapipe_landmarks(self, landmarks, frame_shape) -> float:
        """Calculate EAR from MediaPipe landmarks."""
        # MediaPipe face mesh landmark indices for eyes
        # Left eye: [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        # Right eye: [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        # Simplified eye landmark indices (using key points)
        left_eye_indices = [33, 160, 158, 133, 153, 144]
        right_eye_indices = [362, 385, 387, 263, 373, 380]
        
        def get_ear(eye_indices):
            # Get eye landmark points (normalized coordinates)
            eye_points = []
            for idx in eye_indices:
                landmark = landmarks.landmark[idx]
                x = int(landmark.x * frame_shape[1])
                y = int(landmark.y * frame_shape[0])
                eye_points.append((x, y))
            
            # Calculate vertical distances
            vertical_1 = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
            vertical_2 = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
            
            # Calculate horizontal distance
            horizontal = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
            
            # Calculate EAR
            if horizontal == 0:
                return 0.0
            ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
            return ear
        
        # Calculate EAR for both eyes and average
        left_ear = get_ear(left_eye_indices)
        right_ear = get_ear(right_eye_indices)
        
        return (left_ear + right_ear) / 2.0
    
    def _mock_ear(self) -> float:
        """Mock EAR calculation for testing when MediaPipe is not available."""
        return np.random.uniform(0.2, 0.4)
    
    def is_initialized(self) -> bool:
        return self.initialized

def create_eye_tracker(tracker_type: str = "dlib") -> EyeTracker:
    """
    Factory function to create an eye tracker.
    
    Args:
        tracker_type: "dlib", "mediapipe", or "mock"
        
    Returns:
        EyeTracker instance
    """
    if tracker_type == "dlib":
        return DlibEyeTracker()
    elif tracker_type == "mediapipe":
        return MediaPipeEyeTracker()
    else:
        # Return a mock implementation for testing
        class MockEyeTracker(EyeTracker):
            def calculate_ear(self, frame: np.ndarray) -> Optional[float]:
                return np.random.uniform(0.2, 0.4)
            
            def is_initialized(self) -> bool:
                return True
        
        return MockEyeTracker()

