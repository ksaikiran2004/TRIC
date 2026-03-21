"""
TRIC - API Routes

Responsibilities:
    - Expose incidents via REST API
    - Use LogFormatter for standardized output
    - Provide read-only access to incident data
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Dict, Any

from backend.logging_system.log_formatter import LogFormatter
from backend.utils.file_lock import file_lock


router = APIRouter()
formatter = LogFormatter()

BASE_PATH = Path("data/incidents")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _read_metadata(file_path: Path) -> Dict[str, Any]:
    try:
        with file_lock(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_all_metadata() -> List[Dict[str, Any]]:
    if not BASE_PATH.exists():
        return []

    results = []

    for incident_dir in BASE_PATH.iterdir():
        if not incident_dir.is_dir():
            continue

        metadata_file = incident_dir / "metadata.json"

        if metadata_file.exists():
            data = _read_metadata(metadata_file)
            if data:
                results.append(data)

    return results


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/incidents")
def get_all_incidents() -> List[Dict[str, Any]]:
    metadata_list = _get_all_metadata()

    formatted = formatter.format_many(metadata_list)

    return sorted(
        formatted,
        key=lambda x: x["timestamp"],
        reverse=True
    )


@router.get("/incidents/{event_id}")
def get_incident(event_id: str) -> Dict[str, Any]:
    incident_dir = BASE_PATH / event_id
    metadata_file = incident_dir / "metadata.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Incident not found")

    metadata = _read_metadata(metadata_file)

    if not metadata:
        raise HTTPException(status_code=500, detail="Corrupted incident data")

    return formatter.format_metadata(metadata)