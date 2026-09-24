"""Threat validation logic for CCTV-driven incident review."""

from typing import Any, Dict, Optional


class ThreatValidator:
    """Validates whether a detected scenario qualifies for higher operational attention."""

    def validate(
        self,
        risk_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}

        decision = "monitor"
        if risk_score >= 0.75:
            decision = "escalate"
        elif risk_score >= 0.45:
            decision = "investigate"

        return {
            "risk_score": max(0.0, min(float(risk_score), 1.0)),
            "decision": decision,
            "requires_review": decision in {"investigate", "escalate"},
            "metadata": metadata,
        }
