"""
TRIC - YOLO Inference Engine
Handles drone camera feed analysis for real-time threat detection.
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import Dict, Any

class ThreatDetector:
    def __init__(self, model_path: str = "yolov8n.pt"):
        # Load the pre-trained YOLO model
        self.model = YOLO(model_path)
        
        # Define classes relevant to LoC surveillance
        # 0: person (human), 15: cat, 16: dog, 17: horse (wildlife)
        self.target_classes = {0: "human", 15: "animal", 16: "animal", 17: "animal"}

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Runs inference on a single frame from the drone feed.
        """
        results = self.model(frame, verbose=False)
        detections = []

        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                if class_id in self.target_classes:
                    detections.append({
                        "type": self.target_classes[class_id],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    })

        # Logic for high-priority alert
        threat_detected = any(d['type'] == 'human' for d in detections)
        
        return {
            "threat_detected": threat_detected,
            "detections": detections
        }