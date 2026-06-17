"""
TRIC - Detection Parser
Cleans and formats raw YOLO inference data for the Orchestrator.
"""
from typing import Dict, Any, List

class DetectionParser:
    @staticmethod
    def parse(raw_detections: List[Dict[str, Any]], confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Filters out low-confidence noise and standardizes the output."""
        valid_threats = []
        
        for det in raw_detections:
            if det.get("confidence", 0.0) >= confidence_threshold:
                valid_threats.append({
                    "threat_type": str(det.get("type", "UNKNOWN")).upper(),
                    "confidence": float(det.get("confidence", 0.0)),
                    "bounding_box": det.get("bbox", [])
                })
                
        return valid_threats