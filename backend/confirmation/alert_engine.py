"""
TRIC - Trinetra Rapid Interception Command
Phase 2: Cross Verification & Alert Engine
"""

import uuid
import time
from typing import List, Optional

# Importing our newly separated models
from backend.models.sensor_model import Sensor, DetectionEvent, ConfirmedEvent

class AlertEngine:
    MAX_CLUSTER_DISTANCE = 200  # meters

    def __init__(self, sensors: List[Sensor], min_confirmations: int = 2):
        self.sensors = sensors
        self.min_confirmations = min_confirmations
        self.confirmed_events: List[ConfirmedEvent] = []
        self.sensor_map = {s.id: s for s in sensors}

    def collect_detections(self, lat: float, lon: float, intensity: float, event_time: float) -> List[DetectionEvent]:
        detections = []
        for sensor in self.sensors:
            event = sensor.detect(lat, lon, intensity, event_time)
            if event:
                detections.append(event)
        return detections

    def cluster_filter(self, detections: List[DetectionEvent]) -> List[DetectionEvent]:
        if not detections or detections[0].sensor_id not in self.sensor_map:
            return []

        base_sensor = self.sensor_map[detections[0].sensor_id]
        cluster = []

        for d in detections:
            sensor = self.sensor_map.get(d.sensor_id)
            if sensor:
                dist = Sensor.distance_meters(
                    base_sensor.latitude, base_sensor.longitude,
                    sensor.latitude, sensor.longitude
                )
                if dist <= self.MAX_CLUSTER_DISTANCE:
                    cluster.append(d)
        return cluster

    def cross_verify(self, detections: List[DetectionEvent], event_time: float) -> Optional[ConfirmedEvent]:
        clustered = self.cluster_filter(detections)

        if len(clustered) < self.min_confirmations:
            return None

        sensors_triggered = list({d.sensor_id for d in clustered})
        sensor_types = list({d.sensor_type for d in clustered})
        confidence_score = min(round(len(clustered) / self.min_confirmations, 3), 1.0)

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

    def process_intrusion(self, lat: float, lon: float, intensity: float) -> Optional[ConfirmedEvent]:
        event_time = time.time()
        detections = self.collect_detections(lat, lon, intensity, event_time)
        return self.cross_verify(detections, event_time)