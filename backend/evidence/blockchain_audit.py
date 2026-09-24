"""Tamper-evident evidence logging layer for CCTV intelligence operations."""

import hashlib
import json
from typing import Any, Dict, List


class BlockchainAuditLogger:
    """Stores incident evidence as a simple hash-linked audit trail."""

    def __init__(self):
        self.chain: List[Dict[str, Any]] = []

    def append(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = {"payload": payload, "timestamp": payload.get("timestamp")}
        if self.chain:
            previous_hash = self.chain[-1]["hash"]
            record["previous_hash"] = previous_hash
        record["hash"] = self._compute_hash(record)
        self.chain.append(record)
        return record

    def _compute_hash(self, record: Dict[str, Any]) -> str:
        stable = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(stable).hexdigest()
