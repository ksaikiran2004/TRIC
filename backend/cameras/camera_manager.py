"""Camera registry and stream management for IP CCTV networks."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CameraStream:
    camera_id: str
    source: str
    status: str = "online"
    fps: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CameraManager:
    """Maintains all camera streams and their operational metadata."""

    def __init__(self):
        self.cameras: Dict[str, CameraStream] = {}

    def register_camera(self, camera_id: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> CameraStream:
        stream = CameraStream(camera_id=camera_id, source=source, metadata=metadata or {})
        self.cameras[camera_id] = stream
        return stream

    def get_camera(self, camera_id: str) -> Optional[CameraStream]:
        return self.cameras.get(camera_id)

    def list_cameras(self) -> List[CameraStream]:
        return list(self.cameras.values())
