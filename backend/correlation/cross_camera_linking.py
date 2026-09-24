"""Cross-camera tracker linking for a CCTV-first operational picture."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


class CrossCameraLinker:
    """Links observations across camera feeds using entity and spatial heuristics."""

    def __init__(self):
        self._entity_index: Dict[str, Dict[str, Any]] = {}
        self._camera_links: Dict[str, List[Tuple[str, float]]] = defaultdict(list)

    def register_entity(self, entity_id: str, camera_id: str, timestamp: float, metadata: Optional[Dict[str, Any]] = None):
        payload = {"camera_id": camera_id, "timestamp": timestamp, "metadata": metadata or {}}
        self._entity_index.setdefault(entity_id, []).append(payload)
        self._camera_links[camera_id].append((entity_id, timestamp))

    def link(self, entity_id: str, camera_id: str, timestamp: float, metadata: Optional[Dict[str, Any]] = None) -> bool:
        history = self._entity_index.get(entity_id, [])
        for prior in history:
            if prior["camera_id"] == camera_id:
                return False
            if abs(prior["timestamp"] - timestamp) <= 30:
                self.register_entity(entity_id, camera_id, timestamp, metadata)
                return True
        self.register_entity(entity_id, camera_id, timestamp, metadata)
        return True

    def get_entity_history(self, entity_id: str) -> List[Dict[str, Any]]:
        return list(self._entity_index.get(entity_id, []))

    def get_camera_links(self, camera_id: str) -> List[Tuple[str, float]]:
        return list(self._camera_links.get(camera_id, []))
