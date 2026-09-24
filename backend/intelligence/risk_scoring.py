"""Risk scoring for CCTV-driven intelligence generation."""

from typing import Any, Dict, Optional


class ThreatRiskScorer:
    """Produces a normalized risk score for a tracked event."""

    def __init__(self, base_score: float = 0.0):
        self.base_score = base_score

    def score(
        self,
        entity_type: Optional[str] = None,
        camera_count: int = 1,
        confidence: float = 0.0,
        direction_change: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        context = context or {}

        score = float(self.base_score)
        entity_factor = {"person": 0.35, "vehicle": 0.25, "unknown": 0.15}.get(
            (entity_type or "unknown").lower(), 0.1
        )
        score += entity_factor
        score += min(camera_count * 0.12, 0.45)
        score += max(0.0, min(confidence, 1.0)) * 0.35
        if direction_change:
            score += 0.12

        if context.get("vehicle_whitelisted"):
            score -= 0.25
        if context.get("face_recognition_hook"):
            score += 0.15
        if context.get("anpr_match"):
            score += 0.2

        return max(0.0, min(score, 1.0))
