"""
TRIC - Direction Classifier (Refined + Practical Enhancements)

Enhancements:
    - Direction Enum (type safety)
    - to_dict() for serialization
    - Bearing stability guard for small displacement
    - Optional confidence floor (configurable)
"""

from dataclasses import dataclass
from typing import List
from enum import Enum
import math

from backend.tracking.path_builder import Path


# =========================================================
# ENUMS
# =========================================================

class Direction(Enum):
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"
    STATIONARY = "STATIONARY"


# =========================================================
# DATA MODEL
# =========================================================

@dataclass
class DirectionResult:
    path_id: str
    bearing: float
    direction: Direction
    confidence: float
    is_stationary: bool

    def to_dict(self) -> dict:
        return {
            "path_id": self.path_id,
            "bearing": self.bearing,
            "direction": self.direction.value,
            "confidence": self.confidence,
            "is_stationary": self.is_stationary,
        }


# =========================================================
# CLASSIFIER
# =========================================================

class DirectionClassifier:

    # Thresholds (tunable)
    MIN_DISTANCE = 1.0             # meters
    MIN_SPEED = 0.1               # m/s
    CONFIDENCE_DISTANCE = 50.0    # meters

    # Optional tuning flags
    USE_BEARING_STABILITY_GUARD = True
    USE_CONFIDENCE_FLOOR = False
    CONFIDENCE_FLOOR = 0.1

    # -----------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------

    def classify(self, path: Path) -> DirectionResult:
        if not path.points or len(path.points) < 2:
            return DirectionResult(
                path_id=path.path_id,
                bearing=0.0,
                direction=Direction.STATIONARY,
                confidence=0.0,
                is_stationary=True
            )

        start = path.points[0]
        end = path.points[-1]

        # Stationary detection
        is_stationary = (
            path.total_distance_m < self.MIN_DISTANCE or
            path.avg_speed_mps < self.MIN_SPEED
        )

        # Bearing computation with stability guard
        if is_stationary:
            bearing = 0.0
        else:
            if (
                self.USE_BEARING_STABILITY_GUARD and
                path.total_distance_m < self.MIN_DISTANCE * 2
            ):
                bearing = 0.0
            else:
                bearing = self._compute_bearing(
                    start.latitude, start.longitude,
                    end.latitude, end.longitude
                )

        # Direction
        direction = (
            Direction.STATIONARY
            if is_stationary
            else self._bearing_to_direction(bearing)
        )

        # Confidence
        confidence = self._compute_confidence(
            path.total_distance_m,
            is_stationary
        )

        return DirectionResult(
            path_id=path.path_id,
            bearing=bearing,
            direction=direction,
            confidence=confidence,
            is_stationary=is_stationary
        )

    def classify_all(self, paths: List[Path]) -> List[DirectionResult]:
        return [self.classify(p) for p in paths]

    # -----------------------------------------------------
    # CORE METHODS
    # -----------------------------------------------------

    def _compute_bearing(self, lat1, lon1, lat2, lon2) -> float:
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)

        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = (
            math.cos(lat1_rad) * math.sin(lat2_rad)
            - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
        )

        bearing_rad = math.atan2(x, y)
        bearing_deg = math.degrees(bearing_rad)

        return (bearing_deg + 360) % 360

    def _bearing_to_direction(self, bearing: float) -> Direction:
        directions = [
            Direction.N, Direction.NE, Direction.E, Direction.SE,
            Direction.S, Direction.SW, Direction.W, Direction.NW
        ]

        index = int((bearing + 22.5) // 45) % 8
        return directions[index]

    def _compute_confidence(self, distance: float, is_stationary: bool) -> float:
        if is_stationary or distance <= 0:
            return 0.0

        base = min(1.0, distance / self.CONFIDENCE_DISTANCE)

        if self.USE_CONFIDENCE_FLOOR:
            return max(self.CONFIDENCE_FLOOR, base)

        return base