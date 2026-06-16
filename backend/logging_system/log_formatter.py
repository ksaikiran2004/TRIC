"""
TRIC - Log Formatter
Handles structural formatting of incident logs for UI/Audit display.
"""

from datetime import datetime
from typing import Dict, Any

class LogFormatter:
    @staticmethod
    def format_for_ui(raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw incident metadata into a format optimized for the 
        Tactical Dashboard 'Event Logs' panel.
        """
        # Convert timestamp to human-readable
        ts = raw_metadata.get("timestamp", 0)
        readable_time = datetime.fromtimestamp(ts).strftime('%H:%M:%S %d-%m-%Y')

        return {
            "id": raw_metadata.get("event_id"),
            "time": readable_time,
            "status": raw_metadata.get("status", "UNKNOWN").upper(),
            "summary": f"Target detected at {raw_metadata.get('location')}",
            "severity": "CRITICAL" if raw_metadata.get("confidence", 0) > 0.8 else "WARNING"
        }

    @staticmethod
    def format_for_audit(raw_metadata: Dict[str, Any]) -> str:
        """
        Creates a raw string for archival/audit file storage.
        """
        return f"[{raw_metadata.get('event_id')}] - {raw_metadata.get('status')} - Conf: {raw_metadata.get('confidence')}"