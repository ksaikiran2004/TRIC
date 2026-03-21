"""
TRIC - Event Manager

Responsibilities:
    - Aggregate Track, Path, Direction into high-level events
    - Maintain event lifecycle (ACTIVE / INACTIVE)
    - Ensure one event per track (no duplication)
    - Provide clean access to event state
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum
import uuid

from backend.tracking.intrusion_tracker import IntrusionTrack
from backend.tracking.path_builder import Path
from backend.tracking.direction_classifier import DirectionResult
from backend.config import Config


# =========================================================
# ENUMS
# =========================================================

class EventStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# =========================================================
# DATA MODEL
# =========================================================

@dataclass
class ManagedEvent:
    event_id: str
    track_id: str
    location: Tuple[float, float]   # (latitude, longitude)
    direction: str
    speed: float
    confidence: float
    timestamp: float
    status: EventStatus

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "track_id": self.track_id,
            "location": self.location,
            "direction": self.direction,
            "speed": self.speed,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "status": self.status.value,
        }


# =========================================================
# EVENT MANAGER
# =========================================================

class EventManager:
    def __init__(self):
        # track_id → ManagedEvent
        self._events: Dict[str, ManagedEvent] = {}

    # =====================================================
    # CORE PROCESSOR
    # =====================================================

    def process(
        self,
        tracks: List[IntrusionTrack],
        paths: List[Path],
        directions: List[DirectionResult]
    ) -> None:
        """
        Aggregate system outputs into managed events.
        Deterministic and idempotent per input state.
        """

        # Build lookup maps
        path_map = {p.track_id: p for p in paths}
        direction_map = {d.path_id: d for d in directions}

        for track in tracks:
            track_id = track.track_id

            # --- Latest event ---
            if not track.events:
                continue

            latest_event = track.events[-1]
            location = (latest_event.latitude, latest_event.longitude)
            timestamp = latest_event.timestamp

            # --- Linked data ---
            path = path_map.get(track_id)
            direction_result = direction_map.get(path.path_id) if path else None

            # --- Extract attributes ---
            speed = path.avg_speed_mps if path else 0.0

            direction = (
                direction_result.direction.value
                if direction_result
                else "STATIONARY"
            )

            confidence = (
                direction_result.confidence
                if direction_result
                else min(
                    Config.event.MAX_CONFIDENCE,
                    speed / Config.event.SPEED_NORMALIZER
                )
            )

            status = (
                EventStatus.ACTIVE
                if track.is_active
                else EventStatus.INACTIVE
            )

            # =================================================
            # CREATE or UPDATE
            # =================================================

            if track_id in self._events:
                event = self._events[track_id]

                event.location = location
                event.direction = direction
                event.speed = speed
                event.confidence = confidence
                event.timestamp = timestamp
                event.status = status

            else:
                event = ManagedEvent(
                    event_id=str(uuid.uuid4()),
                    track_id=track_id,
                    location=location,
                    direction=direction,
                    speed=speed,
                    confidence=confidence,
                    timestamp=timestamp,
                    status=status,
                )

                self._events[track_id] = event

    # =====================================================
    # ACCESSORS
    # =====================================================

    def get_active_events(self) -> List[ManagedEvent]:
        return [
            e for e in self._events.values()
            if e.status == EventStatus.ACTIVE
        ]

    def get_all_events(self) -> List[ManagedEvent]:
        return list(self._events.values())