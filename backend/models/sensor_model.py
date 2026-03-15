"""
TRIC - Trinetra Rapid Interception Command
Phase 1: Sensor Model & Cross Verification Engine
"""

import uuid
import math
import time
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field


# =========================================================
# ENUMS
# =========================================================

class SensorType(Enum):
    SEISMIC = "seismic"
    ACOUSTIC = "acoustic"
    RADAR = "radar"
    INFRARED = "infrared"


class SensorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAULT = "fault"


# =========================================================
# DATA MODELS
# =========================================================

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


# =========================================================
# SENSOR MODEL
# =========================================================

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

    # -----------------------------------------------------

    @staticmethod
    def distance_meters(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Haversine distance in meters
        """

        R = 6371000

        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)

        dlat = lat2 - lat1
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1) * math.cos(lat2) *
            math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    # -----------------------------------------------------

    def detect(
        self,
        lat: float,
        lon: float,
        intensity: float,
        event_time: float
    ) -> Optional[DetectionEvent]:

        if self.status != SensorStatus.ACTIVE:
            return None

        if intensity < self.sensitivity_threshold:
            return None

        dist = Sensor.distance_meters(
            self.latitude,
            self.longitude,
            lat,
            lon
        )

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


# =========================================================
# ALERT ENGINE
# =========================================================

class AlertEngine:

    MAX_CLUSTER_DISTANCE = 200  # meters

    def __init__(
        self,
        sensors: List[Sensor],
        min_confirmations: int = 2
    ):

        self.sensors = sensors
        self.min_confirmations = min_confirmations
        self.confirmed_events: List[ConfirmedEvent] = []

        # fast lookup for sensors
        self.sensor_map = {s.id: s for s in sensors}

    # -----------------------------------------------------

    def collect_detections(
        self,
        lat: float,
        lon: float,
        intensity: float,
        event_time: float
    ) -> List[DetectionEvent]:

        detections: List[DetectionEvent] = []

        for sensor in self.sensors:

            event = sensor.detect(
                lat,
                lon,
                intensity,
                event_time
            )

            if event:
                detections.append(event)

        return detections

    # -----------------------------------------------------

    def cluster_filter(
        self,
        detections: List[DetectionEvent]
    ) -> List[DetectionEvent]:

        if not detections:
            return []

        if detections[0].sensor_id not in self.sensor_map:
            return []

        base_sensor = self.sensor_map[detections[0].sensor_id]

        # cached coordinates (optimization)
        base_lat = base_sensor.latitude
        base_lon = base_sensor.longitude

        cluster: List[DetectionEvent] = []

        for d in detections:

            sensor = self.sensor_map.get(d.sensor_id)

            if sensor is None:
                continue

            dist = Sensor.distance_meters(
                base_lat,
                base_lon,
                sensor.latitude,
                sensor.longitude
            )

            if dist <= self.MAX_CLUSTER_DISTANCE:
                cluster.append(d)

        return cluster

    # -----------------------------------------------------

    def cross_verify(
        self,
        detections: List[DetectionEvent],
        event_time: float
    ) -> Optional[ConfirmedEvent]:

        clustered = self.cluster_filter(detections)

        if len(clustered) < self.min_confirmations:
            return None

        sensors_triggered = list({d.sensor_id for d in clustered})
        sensor_types = list({d.sensor_type for d in clustered})

        confidence_score = round(
            len(clustered) / self.min_confirmations,
            3
        )

        confidence_score = min(confidence_score, 1.0)

        confirmed_event = ConfirmedEvent(
            event_id=str(uuid.uuid4()),
            latitude=clustered[0].latitude,
            longitude=clustered[0].longitude,
            sensors_triggered=sensors_triggered,
            sensor_types=sensor_types,
            confidence_score=confidence_score,
            timestamp=event_time
        )

        self.confirmed_events.append(confirmed_event)

        return confirmed_event

    # -----------------------------------------------------

    def process_intrusion(
        self,
        lat: float,
        lon: float,
        intensity: float
    ) -> Optional[ConfirmedEvent]:

        event_time = time.time()

        detections = self.collect_detections(
            lat,
            lon,
            intensity,
            event_time
        )

        return self.cross_verify(detections, event_time)