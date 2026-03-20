"""
TRIC - Intrusion Tracker
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import uuid
import math
import time

from backend.models.sensor_model import ConfirmedEvent
from backend.simulation.simulation_controller import SimulationResult


# =========================================================
# CONFIG
# =========================================================

DISTANCE_THRESHOLD_METERS = 150.0
TIME_THRESHOLD_SECONDS = 10.0


# =========================================================
# UTILITY
# =========================================================

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# =========================================================
# DATA STRUCTURE
# =========================================================

@dataclass
class IntrusionTrack:
    track_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: List[ConfirmedEvent] = field(default_factory=list)

    last_lat: Optional[float] = None
    last_lon: Optional[float] = None
    last_timestamp: Optional[float] = None

    is_active: bool = True

    def add_event(self, event: ConfirmedEvent):
        # Prevent backward time corruption
        if self.last_timestamp is not None and event.timestamp < self.last_timestamp:
            return

        # Prevent duplicate insertion
        if self.events and self.events[-1].event_id == event.event_id:
            return

        self.events.append(event)
        self.last_lat = event.latitude
        self.last_lon = event.longitude
        self.last_timestamp = event.timestamp
        self.is_active = True

    def mark_inactive(self):
        self.is_active = False

    @property
    def length(self) -> int:
        return len(self.events)


# =========================================================
# MAIN TRACKER
# =========================================================

class IntrusionTracker:
    def __init__(
        self,
        distance_threshold: float = DISTANCE_THRESHOLD_METERS,
        time_threshold: float = TIME_THRESHOLD_SECONDS,
    ):
        self.distance_threshold = distance_threshold
        self.time_threshold = time_threshold

        self.active_tracks: Dict[str, IntrusionTrack] = {}
        self.inactive_tracks: Dict[str, IntrusionTrack] = {}

    # =====================================================
    # PUBLIC API
    # =====================================================

    def process_result(self, result: SimulationResult) -> Optional[IntrusionTrack]:
        event = result.event
        current_time = result.timestamp

        if event is None:
            self.update_tracks(current_time=current_time)
            return None

        matched_track = self._find_matching_track(event)

        if matched_track:
            matched_track.add_event(event)
            updated_track = matched_track
        else:
            new_track = self._create_new_track(event)
            self.active_tracks[new_track.track_id] = new_track
            updated_track = new_track

        self.update_tracks(current_time=event.timestamp)

        return updated_track

    def update_tracks(self, current_time: Optional[float] = None):
        if current_time is None:
            current_time = time.time()

        for track in self.active_tracks.values():
            if track.last_timestamp is None:
                continue

            if (current_time - track.last_timestamp) > self.time_threshold:
                track.mark_inactive()

                if track.track_id not in self.inactive_tracks:
                    self.inactive_tracks[track.track_id] = track

        self.active_tracks = {
            tid: t for tid, t in self.active_tracks.items() if t.is_active
        }

    def prune_inactive_tracks(self, max_age: float = 300):
        """
        Remove old inactive tracks to prevent memory growth.
        Should be called periodically (not every step).
        """
        current_time = time.time()

        self.inactive_tracks = {
            tid: t
            for tid, t in self.inactive_tracks.items()
            if t.last_timestamp is not None and (current_time - t.last_timestamp) <= max_age
        }

    def get_active_tracks(self) -> List[IntrusionTrack]:
        return list(self.active_tracks.values())

    def get_all_tracks(self) -> List[IntrusionTrack]:
        return list(self.active_tracks.values()) + list(self.inactive_tracks.values())

    # =====================================================
    # INTERNALS
    # =====================================================

    def _find_matching_track(self, event: ConfirmedEvent) -> Optional[IntrusionTrack]:
        best_match = None
        best_distance = float("inf")

        for track in self.active_tracks.values():
            if track.last_timestamp is None:
                continue

            # Enforce forward-only time progression
            if event.timestamp < track.last_timestamp:
                continue

            time_diff = event.timestamp - track.last_timestamp
            if time_diff > self.time_threshold:
                continue

            distance = haversine_distance(
                event.latitude,
                event.longitude,
                track.last_lat,
                track.last_lon,
            )

            if distance <= self.distance_threshold and distance < best_distance:
                best_distance = distance
                best_match = track

        return best_match

    def _create_new_track(self, event: ConfirmedEvent) -> IntrusionTrack:
        track = IntrusionTrack()
        track.add_event(event)
        return track