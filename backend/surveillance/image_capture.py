"""
TRIC - Evidence Capture
Saves physical image files when critical threats are detected.
"""
import cv2
from datetime import datetime
from pathlib import Path

class ImageCapture:
    def __init__(self, save_dir: str = "data/evidence"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save_threat_frame(self, frame, event_id: str) -> str:
        """Saves the frame and returns the file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"threat_{event_id}_{timestamp}.jpg"
        filepath = self.save_dir / filename
        
        # Save image to disk
        cv2.imwrite(str(filepath), frame)
        print(f"[EVIDENCE] Frame saved: {filepath}")
        
        return str(filepath)