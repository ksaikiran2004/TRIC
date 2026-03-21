"""
TRIC - Log Formatter

Responsibilities:
    - Standardize incident data for API/UI/logging
    - Convert ManagedEvent and metadata into consistent schema
    - Provide batch formatting utilities
"""

from typing import Dict, Any, List

from backend.orchestrator.event_manager import ManagedEvent


class LogFormatter:
    """
    Pure transformation utility for incident data.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format_event(self, event: ManagedEvent) -> Dict[str, Any]:
        lat, lon = event.location

        return {
            "event_id": event.event_id or "",
            "track_id": event.track_id or "",
            "latitude": float(lat),
            "longitude": float(lon),
            "direction": str(event.direction).upper(),
            "speed": float(event.speed),
            "confidence": float(event.confidence),
            "timestamp": float(event.timestamp),
            "status": self._normalize_status(event.status),
        }

    def format_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        lat, lon = self._extract_location(metadata)

        return {
            "event_id": metadata.get("event_id", ""),
            "track_id": metadata.get("track_id", ""),
            "latitude": float(lat),
            "longitude": float(lon),
            "direction": str(metadata.get("direction", "UNKNOWN")).upper(),
            "speed": float(metadata.get("speed", 0.0)),
            "confidence": float(metadata.get("confidence", 0.0)),
            "timestamp": float(metadata.get("timestamp", 0.0)),
            "status": self._normalize_status(metadata.get("status")),
        }

    def format_many(self, metadata_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.format_metadata(m) for m in metadata_list]

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _extract_location(self, metadata: Dict[str, Any]) -> (float, float):
        location = metadata.get("location", [0.0, 0.0])

        if isinstance(location, (list, tuple)) and len(location) == 2:
            return float(location[0]), float(location[1])

        return 0.0, 0.0

    def _normalize_status(self, status: Any) -> str:
        if status is None:
            return "UNKNOWN"

        if hasattr(status, "value"):
            return str(status.value).upper()

        return str(status).upper()