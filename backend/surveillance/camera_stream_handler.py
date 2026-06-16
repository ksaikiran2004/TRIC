"""
TRIC - Camera Stream Handler
Responsibilities:
    - Ingest live feed from drone/phone
    - Pre-process frames for inference
    - Manage stream health and connectivity
"""

import cv2
import numpy as np
from typing import Optional, Tuple

class CameraStreamHandler:
    def __init__(self, source: str = 0):
        # source 0 is usually the default webcam, 
        # or it could be an RTSP/HTTP URL from your phone
        self.cap = cv2.VideoCapture(source)
        
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Grabs the most recent frame from the feed.
        """
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        """
        Closes the stream when the mission ends.
        """
        self.cap.release()