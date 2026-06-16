"""
TRIC - Alert Orchestrator
Responsibilities:
    - Receive detection results from YOLO
    - Decide if an alert is critical (e.g., HUMAN detected)
    - Trigger AlertEngine and IncidentLogger
"""

from typing import Dict, Any
from backend.confirmation.alert_engine import AlertEngine
from backend.logging_system.incident_logger import IncidentLogger
from backend.orchestrator.event_manager import ManagedEvent

class AlertOrchestrator:
    def __init__(self, alert_engine: AlertEngine, logger: IncidentLogger):
        self.alert_engine = alert_engine
        self.logger = logger

    def process_detection(self, detection_data: Dict[str, Any], event_id: str):
        """
        Takes YOLO detection results and decides on the tactical response.
        """
        # If a human is detected, escalate to highest alert
        if detection_data.get("threat_detected"):
            print(f"[ORCHESTRATOR] Critical threat detected: {event_id}")
            
            # Logic to trigger response
            # In a full system, this would call the drone deployment controller
            self._trigger_emergency_protocol(event_id)
            
            # Log the incident
            # Assuming ManagedEvent is constructed from the detection
            # managed_event = ManagedEvent(...) 
            # self.logger.log_event(managed_event)

    def _trigger_emergency_protocol(self, event_id: str):
        # Placeholder for automated drone launch sequence
        print(f"[ORCHESTRATOR] Launching Interceptor Drone for event: {event_id}")