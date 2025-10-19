import threading
import numpy as np

class FrameBuffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None

    def update(self, frame):
        with self.lock:
            self.frame = frame
            #print(f"FrameInstance.update() called | ID: {id(self)}")
            #if isinstance(frame, np.ndarray):
                #print(f"Frame stored: shape={frame.shape}, dtype={frame.dtype}")
            #else:
                #print("Frame is not a valid NumPy array")

    def get(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

FrameInstance = FrameBuffer()
print(f"FrameInstance created in SharedFrame.py | ID: {id(FrameInstance)}")