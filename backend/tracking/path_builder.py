"""
TRIC - Path Builder

Responsibilities:
    - Convert IntrusionTrack → Path
    - Preserve temporal order
    - Compute distance, duration, and average speed
    - Provide batch path construction
"""

from dataclasses import dataclass
from typing import List, Tuple
import uuid
import math

from backend.models.sensor_model import ConfirmedEvent
from backend.tracking.intrusion_tracker import IntrusionTrack
from backend.config import Config


# =========================================================
# DATA MODELS
# =========================================================

@dataclass(frozen=True)
class PathPoint:
    latitude: float
    longitude: float
    timestamp: float


@dataclass(frozen=True)
class Path:
    path_id: str
    track_id: str
    points: Tuple[PathPoint, ...]

    total_distance_m: float
    duration_s: float
    avg_speed_mps: float


# =========================================================
# UTILITY: HAVERSINE DISTANCE
# =========================================================

EARTH_RADIUS_M = Config.paths.EARTH_RADIUS_M


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute distance between two geo points in meters.
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


# =========================================================
# PATH BUILDER
# =========================================================

class PathBuilder:
    """
    Converts intrusion tracks into movement paths.
    Pure transformation layer (no mutation).
    """

    # -----------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------

    @staticmethod
    def build_path(track: IntrusionTrack) -> Path:
        """
        Build a Path from a single IntrusionTrack.
        """

        if not track.events:
            return Path(
                path_id=str(uuid.uuid4()),
                track_id=track.track_id,
                points=(),
                total_distance_m=0.0,
                duration_s=0.0,
                avg_speed_mps=0.0,
            )

        # Step 1: Sort events by timestamp (defensive)
        sorted_events = sorted(track.events, key=lambda e: e.timestamp)

        # Step 2: Convert to PathPoints (immutable)
        points: Tuple[PathPoint, ...] = tuple(
            PathPoint(
                latitude=e.latitude,
                longitude=e.longitude,
                timestamp=e.timestamp,
            )
            for e in sorted_events
        )

        # Step 3: Compute total distance
        total_distance = PathBuilder._compute_total_distance(points)

        # Step 4: Compute duration (safe)
        duration = PathBuilder._compute_duration(points)

        # Step 5: Compute average speed
        avg_speed = total_distance / duration if duration > 0 else 0.0

        return Path(
            path_id=str(uuid.uuid4()),
            track_id=track.track_id,
            points=points,
            total_distance_m=total_distance,
            duration_s=duration,
            avg_speed_mps=avg_speed,
        )

    @staticmethod
    def build_all_paths(tracks: List[IntrusionTrack]) -> List[Path]:
        """
        Build paths for multiple tracks.
        """
        return [PathBuilder.build_path(track) for track in tracks]

    # -----------------------------------------------------
    # INTERNAL HELPERS
    # -----------------------------------------------------

    @staticmethod
    def _compute_total_distance(points: Tuple[PathPoint, ...]) -> float:
        """
        Sum Haversine distances between consecutive points.
        """
        if len(points) < 2:
            return 0.0

        total = 0.0

        for i in range(1, len(points)):
            p1 = points[i - 1]
            p2 = points[i]

            total += haversine_distance(
                p1.latitude, p1.longitude,
                p2.latitude, p2.longitude
            )

        return total

    @staticmethod
    def _compute_duration(points: Tuple[PathPoint, ...]) -> float:
        """
        Compute non-negative time difference between first and last point.
        """
        if len(points) < 2:
            return 0.0

        duration = points[-1].timestamp - points[0].timestamp
        return max(0.0, duration)