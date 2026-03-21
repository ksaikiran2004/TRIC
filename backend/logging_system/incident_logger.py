"""
TRIC - Incident Logger

Responsibilities:
    - Persist ManagedEvent as structured incident records
    - Maintain one incident per event_id
    - Safely update incident metadata
    - Ensure no data corruption via file locking
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from backend.orchestrator.event_manager import ManagedEvent
from backend.utils.file_lock import file_lock


class IncidentLogger:
    """
    Persistent incident storage manager.
    """

    def __init__(self, base_dir: str = "data/incidents"):
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_event(self, event: ManagedEvent) -> None:
        """
        Create or update an incident record for the given event.
        """
        incident_path = self._get_incident_path(event.event_id)

        if incident_path.exists():
            self.update_event(event)
        else:
            self._create_incident(event)

    def update_event(self, event: ManagedEvent) -> None:
        """
        Update existing incident metadata.
        """
        incident_dir = self._get_incident_path(event.event_id)
        metadata_file = incident_dir / "metadata.json"

        if not incident_dir.exists():
            self._create_incident(event)
            return

        metadata = self._build_metadata(event)
        self._safe_write(metadata_file, metadata)

    def get_incident(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve incident metadata from disk.
        """
        incident_dir = self._get_incident_path(event_id)
        metadata_file = incident_dir / "metadata.json"

        if not metadata_file.exists():
            return None

        with file_lock(metadata_file):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _create_incident(self, event: ManagedEvent) -> None:
        """
        Create a new incident directory and metadata file.
        """
        incident_dir = self._get_incident_path(event.event_id)
        incident_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = incident_dir / "metadata.json"
        metadata = self._build_metadata(event)

        self._safe_write(metadata_file, metadata)

    def _get_incident_path(self, event_id: str) -> Path:
        return self.base_path / event_id

    def _build_metadata(self, event: ManagedEvent) -> Dict[str, Any]:
        """
        Convert ManagedEvent into serializable dict.
        """
        lat, lon = event.location

        return {
            "version": 1,
            "event_id": event.event_id,
            "track_id": event.track_id,
            "location": [lat, lon],
            "direction": str(event.direction),   # safe (string already)
            "speed": float(event.speed),
            "confidence": float(event.confidence),
            "timestamp": float(event.timestamp),
            "status": event.status.value,        # Enum → value
        }

    def _safe_write(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Safely write JSON using atomic write + file lock.
        """
        temp_path = file_path.with_suffix(".tmp")

        with file_lock(file_path):
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                f.flush()

            temp_path.replace(file_path)