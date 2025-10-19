"""
Unit tests for eye tracking implementations.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from core.eye_tracker import (
    EyeTracker, DlibEyeTracker, MediaPipeEyeTracker, create_eye_tracker
)

class TestEyeTracker:
    """Test cases for EyeTracker interface."""
    
    def test_abstract_interface(self):
        """Test that EyeTracker is abstract."""
        with pytest.raises(TypeError):
            EyeTracker()
    
    def test_mock_implementation(self):
        """Test mock implementation for testing."""
        class MockEyeTracker(EyeTracker):
            def calculate_ear(self, frame):
                return 0.3
            
            def is_initialized(self):
                return True
        
        tracker = MockEyeTracker()
        assert tracker.is_initialized()
        assert tracker.calculate_ear(np.zeros((100, 100, 3))) == 0.3

class TestDlibEyeTracker:
    """Test cases for DlibEyeTracker."""
    
    @patch('builtins.__import__')
    def test_initialization_success(self, mock_dlib):
        """Test successful initialization with dlib available."""
        # Mock dlib components
        mock_detector = Mock()
        mock_predictor = Mock()
        mock_dlib.get_frontal_face_detector.return_value = mock_detector
        mock_dlib.shape_predictor.return_value = mock_predictor
        
        tracker = DlibEyeTracker()
        
        assert tracker.is_initialized()
        assert tracker.detector == mock_detector
        assert tracker.predictor == mock_predictor
    
    @patch('py.core.eye_tracker.dlib', side_effect=ImportError)
    def test_initialization_import_error(self, mock_dlib):
        """Test initialization when dlib is not available."""
        tracker = DlibEyeTracker()
        
        assert not tracker.is_initialized()
        assert tracker.detector is None
        assert tracker.predictor is None
    
    def test_calculate_ear_not_initialized(self):
        """Test EAR calculation when not initialized."""
        tracker = DlibEyeTracker()
        # Force not initialized
        tracker.initialized = False
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        ear = tracker.calculate_ear(frame)
        
        # Should return mock value
        assert isinstance(ear, float)
        assert 0.2 <= ear <= 0.4
    
    @patch('builtins.__import__')
    def test_calculate_ear_no_faces(self, mock_dlib):
        """Test EAR calculation when no faces detected."""
        # Mock dlib components
        mock_detector = Mock()
        mock_predictor = Mock()
        mock_detector.return_value = []  # No faces detected
        mock_dlib.get_frontal_face_detector.return_value = mock_detector
        mock_dlib.shape_predictor.return_value = mock_predictor
        
        tracker = DlibEyeTracker()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        ear = tracker.calculate_ear(frame)
        assert ear is None
    
    @patch('builtins.__import__')
    def test_calculate_ear_with_faces(self, mock_dlib):
        """Test EAR calculation with faces detected."""
        # Mock dlib components
        mock_detector = Mock()
        mock_predictor = Mock()
        mock_face = Mock()
        mock_landmarks = Mock()
        
        # Mock face detection
        mock_detector.return_value = [mock_face]
        mock_dlib.get_frontal_face_detector.return_value = mock_detector
        
        # Mock landmark prediction
        mock_predictor.return_value = mock_landmarks
        mock_dlib.shape_predictor.return_value = mock_predictor
        
        # Mock landmark points for EAR calculation
        def mock_landmark_part(index):
            mock_point = Mock()
            if index in [36, 37, 38, 39, 40, 41]:  # Left eye
                mock_point.x = 10 + index
                mock_point.y = 20 + index
            elif index in [42, 43, 44, 45, 46, 47]:  # Right eye
                mock_point.x = 30 + index
                mock_point.y = 40 + index
            else:
                mock_point.x = 0
                mock_point.y = 0
            return mock_point
        
        mock_landmarks.part.side_effect = mock_landmark_part
        
        tracker = DlibEyeTracker()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        ear = tracker.calculate_ear(frame)
        assert isinstance(ear, float)
        assert ear > 0
    
    def test_calculate_ear_exception_handling(self):
        """Test EAR calculation exception handling."""
        tracker = DlibEyeTracker()
        tracker.initialized = True
        tracker.detector = Mock()
        tracker.predictor = Mock()
        
        # Mock detector to raise exception
        tracker.detector.side_effect = Exception("Test exception")
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        ear = tracker.calculate_ear(frame)
        
        assert ear is None

class TestMediaPipeEyeTracker:
    """Test cases for MediaPipeEyeTracker."""
    
    @patch('builtins.__import__')
    def test_initialization_success(self, mock_mp):
        """Test successful initialization with MediaPipe available."""
        # Mock MediaPipe components
        mock_face_mesh = Mock()
        mock_drawing = Mock()
        mock_mp.solutions.face_mesh = mock_face_mesh
        mock_mp.solutions.drawing_utils = mock_drawing
        mock_face_mesh.FaceMesh.return_value = Mock()
        
        tracker = MediaPipeEyeTracker()
        
        assert tracker.is_initialized()
        assert tracker.mp_face_mesh == mock_face_mesh
        assert tracker.mp_drawing == mock_drawing
    
    @patch('py.core.eye_tracker.mp', side_effect=ImportError)
    def test_initialization_import_error(self, mock_mp):
        """Test initialization when MediaPipe is not available."""
        tracker = MediaPipeEyeTracker()
        
        assert not tracker.is_initialized()
        assert tracker.mp_face_mesh is None
        assert tracker.face_mesh is None
    
    def test_calculate_ear_not_initialized(self):
        """Test EAR calculation when not initialized."""
        tracker = MediaPipeEyeTracker()
        # Force not initialized
        tracker.initialized = False
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        ear = tracker.calculate_ear(frame)
        
        # Should return mock value
        assert isinstance(ear, float)
        assert 0.2 <= ear <= 0.4
    
    @patch('builtins.__import__')
    def test_calculate_ear_no_faces(self, mock_mp):
        """Test EAR calculation when no faces detected."""
        # Mock MediaPipe components
        mock_face_mesh = Mock()
        mock_drawing = Mock()
        mock_mp.solutions.face_mesh = mock_face_mesh
        mock_mp.solutions.drawing_utils = mock_drawing
        
        # Mock face mesh with no faces
        mock_face_mesh_instance = Mock()
        mock_face_mesh_instance.process.return_value.multi_face_landmarks = None
        mock_face_mesh.FaceMesh.return_value = mock_face_mesh_instance
        
        tracker = MediaPipeEyeTracker()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        ear = tracker.calculate_ear(frame)
        assert ear is None
    
    @patch('builtins.__import__')
    def test_calculate_ear_with_faces(self, mock_mp):
        """Test EAR calculation with faces detected."""
        # Mock MediaPipe components
        mock_face_mesh = Mock()
        mock_drawing = Mock()
        mock_mp.solutions.face_mesh = mock_face_mesh
        mock_mp.solutions.drawing_utils = mock_drawing
        
        # Mock face mesh with landmarks
        mock_landmarks = Mock()
        mock_landmark = Mock()
        
        # Mock landmark points for EAR calculation
        def mock_landmark_attr(idx):
            mock_point = Mock()
            if idx in [33, 160, 158, 133, 153, 144]:  # Left eye
                mock_point.x = 0.1 + idx * 0.01
                mock_point.y = 0.2 + idx * 0.01
            elif idx in [362, 385, 387, 263, 373, 380]:  # Right eye
                mock_point.x = 0.3 + idx * 0.01
                mock_point.y = 0.4 + idx * 0.01
            else:
                mock_point.x = 0.0
                mock_point.y = 0.0
            return mock_point
        
        mock_landmark.landmark = [mock_landmark_attr(i) for i in range(500)]
        mock_landmarks.multi_face_landmarks = [mock_landmark]
        
        mock_face_mesh_instance = Mock()
        mock_face_mesh_instance.process.return_value = mock_landmarks
        mock_face_mesh.FaceMesh.return_value = mock_face_mesh_instance
        
        tracker = MediaPipeEyeTracker()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        ear = tracker.calculate_ear(frame)
        assert isinstance(ear, float)
        assert ear > 0
    
    def test_calculate_ear_exception_handling(self):
        """Test EAR calculation exception handling."""
        tracker = MediaPipeEyeTracker()
        tracker.initialized = True
        tracker.face_mesh = Mock()
        
        # Mock face_mesh to raise exception
        tracker.face_mesh.process.side_effect = Exception("Test exception")
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        ear = tracker.calculate_ear(frame)
        
        assert ear is None

class TestEyeTrackerFactory:
    """Test cases for eye tracker factory function."""
    
    def test_create_dlib_tracker(self):
        """Test creating dlib tracker."""
        tracker = create_eye_tracker("dlib")
        assert isinstance(tracker, DlibEyeTracker)
    
    def test_create_mediapipe_tracker(self):
        """Test creating MediaPipe tracker."""
        tracker = create_eye_tracker("mediapipe")
        assert isinstance(tracker, MediaPipeEyeTracker)
    
    def test_create_mock_tracker(self):
        """Test creating mock tracker."""
        tracker = create_eye_tracker("mock")
        assert isinstance(tracker, EyeTracker)
        assert tracker.is_initialized()
        
        # Test mock functionality
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        ear = tracker.calculate_ear(frame)
        assert isinstance(ear, float)
        assert 0.2 <= ear <= 0.4
    
    def test_create_default_tracker(self):
        """Test creating default tracker."""
        tracker = create_eye_tracker()
        assert isinstance(tracker, DlibEyeTracker)

class TestEyeTrackerIntegration:
    """Integration tests for eye tracking."""
    
    def test_mock_tracker_consistency(self):
        """Test that mock tracker returns consistent results."""
        tracker = create_eye_tracker("mock")
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Multiple calls should return different values (random)
        ears = [tracker.calculate_ear(frame) for _ in range(10)]
        
        # All should be valid EAR values
        assert all(isinstance(ear, float) for ear in ears)
        assert all(0.2 <= ear <= 0.4 for ear in ears)
        
        # Should have some variation (random)
        assert len(set(ears)) > 1
    
    def test_tracker_with_different_frame_sizes(self):
        """Test tracker with different frame sizes."""
        tracker = create_eye_tracker("mock")
        
        # Test different frame sizes
        frame_sizes = [(100, 100, 3), (200, 200, 3), (640, 480, 3)]
        
        for height, width, channels in frame_sizes:
            frame = np.zeros((height, width, channels), dtype=np.uint8)
            ear = tracker.calculate_ear(frame)
            
            assert isinstance(ear, float)
            assert 0.2 <= ear <= 0.4

