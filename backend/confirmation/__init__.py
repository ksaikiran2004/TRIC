"""Backward-compatible exports for the legacy confirmation layer.

The production refactor is moving this concept toward the intelligence layer,
while existing code paths continue to import from backend.confirmation.
"""

from .alert_engine import AlertEngine
from .multi_sensor_confirmation import MultiSensorConfirmation

__all__ = ["AlertEngine", "MultiSensorConfirmation"]
