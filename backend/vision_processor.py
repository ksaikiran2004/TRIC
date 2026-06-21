# TRIC C4ISR - TACTICAL VISION & CLASSIFICATION ENGINE
import cv2
import math
from ultralytics import YOLO

class TacticalVisionProcessor:
    """
    Handles real-time stream ingestion, YOLOv8 inference, threat classification, 
    and tactical HUD frame generation for the TRIC C4ISR dashboard.
    """
    def __init__(self):
        print(">>> [TRIC-VISION] INITIALIZING YOLOv8-SMALL NEURAL ENGINE...")
        # yolov8s.pt balances accuracy with Ryzen 3 APU limits
        self.model = YOLO('yolov8s.pt') 
        
        # Threat Classification Matrix (COCO Dataset mapping)
        self.TARGET_CLASSES = {
            0: {"type": "HUMAN INTRUDER", "color": (0, 0, 255), "threat": "HIGH"},    # Red
            2: {"type": "LIGHT VEHICLE", "color": (0, 255, 255), "threat": "ELEVATED"}, # Yellow
            3: {"type": "MOTORCYCLE", "color": (0, 255, 255), "threat": "ELEVATED"},    # Yellow
            5: {"type": "HEAVY TRANSPORT", "color": (0, 165, 255), "threat": "ELEVATED"},# Orange
            7: {"type": "TRANSPORT TRUCK", "color": (0, 165, 255), "threat": "ELEVATED"} # Orange
        }

    def process_frame(self, frame):
        """
        Primary execution loop for frame analysis.
        Returns the annotated frame matrix and the telemetry payload dictionary.
        """
        if frame is None:
            return None, self._generate_telemetry("CLEAR", 0.0, "SCANNING")

        # 1. Execute Neural Inference (stream=True optimizes memory buffer)
        results = self.model(frame, stream=True, verbose=False)
        
        target_detected = False
        highest_conf = 0.0
        primary_target_type = "UNKNOWN"

        # 2. Parse Tensor Results
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # 3. Filter against Threat Matrix
                if cls_id in self.TARGET_CLASSES:
                    target_detected = True
                    target_data = self.TARGET_CLASSES[cls_id]
                    
                    if conf > highest_conf:
                        highest_conf = conf
                        primary_target_type = target_data["type"]

                    # 4. Render HUD Overlay
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    frame = self._draw_tactical_hud(
                        frame, x1, y1, x2, y2, 
                        target_data["color"], 
                        target_data["type"], 
                        conf
                    )

        # 5. Package JSON Telemetry for WebSocket Uplink
        if target_detected:
            payload = self._generate_telemetry(primary_target_type, highest_conf, "ENGAGED")
        else:
            payload = self._generate_telemetry("CLEAR", 1.0, "SCANNING")

        return frame, payload

    def _draw_tactical_hud(self, frame, x1, y1, x2, y2, color, label_text, conf):
        """
        Renders military-style targeting brackets and telemetry overlays.
        """
        length = 20  # Bracket arm length
        thickness = 2
        
        # Draw Corner Targeting Brackets
        # Top-Left
        cv2.line(frame, (x1, y1), (x1 + length, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + length), color, thickness)
        # Top-Right
        cv2.line(frame, (x2, y1), (x2 - length, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + length), color, thickness)
        # Bottom-Left
        cv2.line(frame, (x1, y2), (x1 + length, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - length), color, thickness)
        # Bottom-Right
        cv2.line(frame, (x2, y2), (x2 - length, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - length), color, thickness)
        
        # Central Crosshair Lock
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        cv2.circle(frame, (cx, cy), 3, color, -1)
        
        # Telemetry Text Background Box (for readability)
        label = f"TRK: {label_text} [{math.ceil(conf * 100)}%]"
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.rectangle(frame, (x1, y1 - 20), (x1 + w, y1), (0, 0, 0), -1)
        
        # Telemetry Text
        cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)
        
        return frame

    def _generate_telemetry(self, target_type, confidence, status):
        """
        Structures the standardized data payload for the frontend UI.
        """
        return {
            "target_type": target_type,
            "confidence": confidence,
            "status": status
        }