"""
TRIC - Trinetra Rapid Interception Command
Phase 1: Sensor & Event Data Models
"""

import uuid
import math
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

class SensorType(Enum):
    SEISMIC = "seismic"
    ACOUSTIC = "acoustic"
    RADAR = "radar"
    INFRARED = "infrared"

class SensorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAULT = "fault"

@dataclass
class DetectionEvent:
    event_id: str
    sensor_id: str
    sensor_type: SensorType
    latitude: float
    longitude: float
    intensity: float
    timestamp: float

@dataclass
class ConfirmedEvent:
    event_id: str
    latitude: float
    longitude: float
    sensors_triggered: List[str]
    sensor_types: List[SensorType]
    confidence_score: float
    timestamp: float

@dataclass
class Sensor:
    sensor_type: SensorType
    latitude: float
    longitude: float
    detection_radius_m: float
    sensitivity_threshold: float = 0.5
    status: SensorStatus = SensorStatus.ACTIVE
    id: str = field(init=False)

    def __post_init__(self):
        self.id = str(uuid.uuid4())

    @staticmethod
    def distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in meters"""
        R = 6371000
        lat1, lat2 = math.radians(lat1), math.radians(lat2)
        dlat = lat2 - lat1
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def detect(self, lat: float, lon: float, intensity: float, event_time: float) -> Optional[DetectionEvent]:
        if self.status != SensorStatus.ACTIVE or intensity < self.sensitivity_threshold:
            return None
            
        dist = self.distance_meters(self.latitude, self.longitude, lat, lon)
        if dist <= self.detection_radius_m:
            return DetectionEvent(
                event_id=str(uuid.uuid4()),
                sensor_id=self.id,
                sensor_type=self.sensor_type,
                latitude=lat,
                longitude=lon,
                intensity=intensity,
                timestamp=event_time
            )
        return None