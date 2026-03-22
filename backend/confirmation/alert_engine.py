"""
TRIC - Alert Engine

Bridges simulation to multi-sensor confirmation.
"""

from typing import List, Optional

from backend.models.sensor_model import Sensor, ConfirmedEvent
from backend.confirmation.multi_sensor_confirmation import MultiSensorConfirmation


class AlertEngine:
    def __init__(
        self,
        confirmation: MultiSensorConfirmation,
        sensors: List[Sensor]
    ):
        self.confirmation = confirmation
        self.sensors = sensors

    def process_intrusion(
        self,
        intrusion_lat: float,
        intrusion_lon: float,
        intensity: float
    ) -> Optional[ConfirmedEvent]:
        return self.confirmation.confirm_intrusion(
            sensors=self.sensors,
            intrusion_lat=intrusion_lat,
            intrusion_lon=intrusion_lon,
            intensity=intensity
        )