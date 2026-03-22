"""
TRIC - Multi Sensor Confirmation Module

FILE: backend/confirmation/multi_sensor_confirmation.py

Responsibility:
Validate intrusion events using multiple sensor confirmations.
"""

from typing import List, Optional
import time
import uuid

from backend.config import Config
from backend.models.sensor_model import Sensor, ConfirmedEvent
from backend.utils.geo_utils import haversine_distance


class MultiSensorConfirmation:
    """
    Handles validation of intrusion events using multiple sensors.
    """

    def confirm_intrusion(
        self,
        sensors: List[Sensor],
        intrusion_lat: float,
        intrusion_lon: float,
        intensity: float
    ) -> Optional[ConfirmedEvent]:
        """
        Confirm intrusion using multiple sensor inputs.
        """

        if not sensors:
            return None

        detection_radius = Config.confirmation.DETECTION_RADIUS
        min_sensors = Config.confirmation.MIN_SENSORS
        min_intensity = Config.confirmation.MIN_INTENSITY

        # Step 1: Intensity threshold check
        if intensity < min_intensity:
            return None

        valid_sensors = []

        # Step 2: Distance filtering
        for sensor in sensors:
            distance = haversine_distance(
                intrusion_lat,
                intrusion_lon,
                sensor.latitude,
                sensor.longitude
            )

            if distance <= detection_radius:
                valid_sensors.append(sensor)

        # Step 3: Minimum sensor count check
        if len(valid_sensors) < min_sensors:
            return None

        # Step 4: Build ConfirmedEvent
        sensor_ids = [sensor.sensor_id for sensor in valid_sensors]

        confidence_score = self._compute_confidence(
            sensor_count=len(valid_sensors),
            intensity=intensity,
            min_sensors=min_sensors,
            min_intensity=min_intensity
        )

        return ConfirmedEvent(
            event_id=str(uuid.uuid4()),
            latitude=intrusion_lat,
            longitude=intrusion_lon,
            timestamp=time.time(),
            sensors_involved=sensor_ids,
            confidence_score=confidence_score
        )

    def _compute_confidence(
        self,
        sensor_count: int,
        intensity: float,
        min_sensors: int,
        min_intensity: float
    ) -> float:
        """
        Compute confidence score based on sensor count and intensity.
        """

        # Normalize sensor contribution
        sensor_score = min(1.0, sensor_count / max(min_sensors, 1))

        # Normalize intensity contribution
        intensity_score = min(1.0, intensity / max(min_intensity, 1e-6))

        # Weighted combination
        confidence = (0.6 * sensor_score) + (0.4 * intensity_score)

        return min(1.0, confidence)