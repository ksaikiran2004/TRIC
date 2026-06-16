"""
TRIC - Trinetra Rapid Interception Command
Alert Data Models
"""

import uuid
import time
from enum import Enum
from dataclasses import dataclass, field

# Importing the ConfirmedEvent we just created
from backend.models.sensor_model import ConfirmedEvent

class AlertSeverity(Enum):
    LOW = "low"               # Animal suspected, low confidence
    MEDIUM = "medium"         # Unconfirmed movement, multiple sensors triggered
    HIGH = "high"             # Confirmed human presence via AI
    CRITICAL = "critical"     # Armed human detected / Immediate interception required

class AlertStatus(Enum):
    ACTIVE = "active"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_ALARM = "false_alarm"

@dataclass
class TacticalAlert:
    severity: AlertSeverity
    latitude: float
    longitude: float
    description: str
    confirmed_event: ConfirmedEvent
    status: AlertStatus = AlertStatus.ACTIVE
    alert_id: str = field(init=False)
    timestamp: float = field(init=False)

    def __post_init__(self):
        # Generates a clean, tactical ID like 'ALT-A1B2C3D4'
        self.alert_id = f"ALT-{str(uuid.uuid4())[:8].upper()}"
        self.timestamp = time.time()
        
    def to_dict(self):
        """Converts the alert to a dictionary for JSON/WebSocket transmission"""
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "description": self.description,
            "coordinates": {"lat": self.latitude, "lng": self.longitude},
            "timestamp": self.timestamp,
            "event_reference": self.confirmed_event.event_id
        }