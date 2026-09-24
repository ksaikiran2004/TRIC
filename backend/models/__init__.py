"""Domain model exports for the TRIC platform.

This keeps legacy imports working while newer CCTV-centric modules use more
specific model groupings.
"""

from .sensor_model import (
    ConfirmedEvent,
    DetectionEvent,
    Sensor,
    SensorStatus,
    SensorType,
)

__all__ = [
    "ConfirmedEvent",
    "DetectionEvent",
    "Sensor",
    "SensorStatus",
    "SensorType",
]
