"""
TRIC - Trinetra Rapid Interception Command
Phase 1: Sensor Model & Cross Verification Engine
"""

import uuid
import math
import time
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, field


# =========================================================
# ENUMS
# =========================================================

class SensorType(Enum):
    SEISMIC = "seismic"
    ACOUSTIC = "acoustic"
    RADAR = "radar"
    INFRARED = "infrared"


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class DetectionEvent:
    event_id: str
    sensor_id: str
    sensor_type: str
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
    confidence_score: float
    timestamp: float


# =========================================================
# SENSOR CLASS
# =========================================================

class Sensor:
    """
    Base Sensor Model
    """

    def __init__(
        self,
        sensor_type: SensorType,
        latitude: float,
        longitude: float,
        detection_radius_m: float,
        sensitivity_threshold: float = 0.5,
    ):
        self.id = str(uuid.uuid4())
        self.sensor_type = sensor_type
        self.latitude = latitude
        self.longitude = longitude
        self.detection_radius_m = detection_radius_m
        self.sensitivity_threshold = sensitivity_threshold
        self.status = "active"

    # -----------------------------------------------------

    def _distance_meters(self, lat: float, lon: float) -> float:
        """
        Approximate Haversine distance in meters.
        """
        R = 6371000  # Earth radius in meters

        lat1 = math.radians(self.latitude)
        lat2 = math.radians(lat)
        delta_lat = math.radians(lat - self.latitude)
        delta_lon = math.radians(lon - self.longitude)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    # -----------------------------------------------------

    def detect(
        self,
        lat: float,
        lon: float,
        intensity: float,
    ) -> Optional[DetectionEvent]:
        """
        Attempt detection based on:
        - distance
        - intensity threshold
        - sensor active status
        """

        if self.status != "active":
            return None

        if intensity < self.sensitivity_threshold:
            return None

        distance = self._distance_meters(lat, lon)

        if distance <= self.detection_radius_m:
            return DetectionEvent(
                event_id=str(uuid.uuid4()),
                sensor_id=self.id,
                sensor_type=self.sensor_type.value,
                latitude=lat,
                longitude=lon,
                intensity=intensity,
                timestamp=time.time(),
            )

        return None


# =========================================================
# ALERT ENGINE
# =========================================================

class AlertEngine:
    """
    Handles:
    - Collection of sensor detections
    - Cross-verification
    - Preliminary confirmation
    """

    def __init__(self, sensors: List[Sensor], min_confirmations: int = 2):
        self.sensors = sensors
        self.min_confirmations = min_confirmations
        self.confirmed_events: List[ConfirmedEvent] = []

    # -----------------------------------------------------

    def collect_detections(
        self,
        lat: float,
        lon: float,
        intensity: float,
    ) -> List[DetectionEvent]:

        detections: List[DetectionEvent] = []

        for sensor in self.sensors:
            event = sensor.detect(lat, lon, intensity)
            if event:
                detections.append(event)

        return detections

    # -----------------------------------------------------

    def cross_verify(
        self,
        detections: List[DetectionEvent],
    ) -> Optional[ConfirmedEvent]:

        if len(detections) < self.min_confirmations:
            return None

        sensors_triggered = list(
            {d.sensor_type for d in detections}
        )

        confidence_score = len(detections) / len(self.sensors)

        confirmed_event = ConfirmedEvent(
            event_id=str(uuid.uuid4()),
            latitude=detections[0].latitude,
            longitude=detections[0].longitude,
            sensors_triggered=sensors_triggered,
            confidence_score=round(confidence_score, 3),
            timestamp=time.time(),
        )

        self.confirmed_events.append(confirmed_event)

        return confirmed_event

    # -----------------------------------------------------

    def process_intrusion(
        self,
        lat: float,
        lon: float,
        intensity: float,
    ) -> Optional[ConfirmedEvent]:
        """
        Phase 1 Flow:
        1. Collect detections
        2. Cross verify
        3. Return confirmed preliminary alert
        """

        detections = self.collect_detections(lat, lon, intensity)
        return self.cross_verify(detections)