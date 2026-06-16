"""
TRIC - Trinetra Rapid Interception Command
Incident & Action Logging Models
"""

import uuid
import time
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

# Importing the TacticalAlert we just created
from backend.models.alert_model import TacticalAlert

class IncidentStatus(Enum):
    OPEN = "open"
    DRONE_DISPATCHED = "drone_dispatched"
    VISUAL_CONFIRMED = "visual_confirmed"
    NEUTRALIZED = "neutralized"
    CLOSED = "closed"

@dataclass
class ActionLog:
    action_type: str  # e.g., "DRONE_LAUNCH", "YOLO_VERIFICATION", "TECHNICIAN_OVERRIDE"
    timestamp: float
    details: str

@dataclass
class Incident:
    alert: TacticalAlert
    status: IncidentStatus = IncidentStatus.OPEN
    actions_taken: List[ActionLog] = field(default_factory=list)
    incident_id: str = field(init=False)
    start_time: float = field(init=False)
    end_time: Optional[float] = None

    def __post_init__(self):
        # Generates a master record ID like 'INC-9F8E7D6C'
        self.incident_id = f"INC-{str(uuid.uuid4())[:8].upper()}"
        self.start_time = time.time()

    def add_action(self, action_type: str, details: str):
        """Logs a new action against this incident"""
        action = ActionLog(action_type=action_type, timestamp=time.time(), details=details)
        self.actions_taken.append(action)

    def close_incident(self):
        """Marks the incident as resolved and logs the end time"""
        self.status = IncidentStatus.CLOSED
        self.end_time = time.time()

    def to_dict(self):
        """Converts the full incident history for JSON database storage"""
        return {
            "incident_id": self.incident_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "alert_reference": self.alert.alert_id,
            "actions": [{"type": a.action_type, "time": a.timestamp, "details": a.details} for a in self.actions_taken]
        }