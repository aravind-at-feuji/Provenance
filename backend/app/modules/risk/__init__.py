"""
app/modules/risk — Deterministic Risk Engine.

CRITICAL ARCHITECTURE INVARIANT:
No LLM calls or agents.* imports anywhere in this module.
"""

from app.modules.risk.models import RiskAssessment, RiskModelVersion
from app.modules.risk.scoring import (
    DEFAULT_THRESHOLDS,
    DEFAULT_WEIGHTS,
    RiskScoreResult,
    calculate_dependency_strength,
    calculate_event_severity,
    calculate_evidence_quality,
    calculate_exposure_multiplier,
    calculate_impact_score,
    calculate_urgency_multiplier,
    determine_severity_band,
    reconstruct_score_from_factors,
    score_risk,
)

__all__ = [
    "DEFAULT_THRESHOLDS",
    "DEFAULT_WEIGHTS",
    "RiskAssessment",
    "RiskModelVersion",
    "RiskScoreResult",
    "calculate_dependency_strength",
    "calculate_event_severity",
    "calculate_evidence_quality",
    "calculate_exposure_multiplier",
    "calculate_impact_score",
    "calculate_urgency_multiplier",
    "determine_severity_band",
    "reconstruct_score_from_factors",
    "score_risk",
]
