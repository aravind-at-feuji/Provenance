"""
app/modules/risk/scoring.py — Pure deterministic risk scoring arithmetic.

ARCHITECTURE & COMPLIANCE:
- Arch reference: §Part I (§9) Business Impact & Risk Engine, §Part Z Phase 11.
- Deterministic only: scores must be reproducible and explainable.
- MULTIPLICATIVE GATES:
    impact_score = 100
                 × event_severity            (0–1)
                 × dependency_strength       (0–1)   ← multiplicative gate
                 × evidence_quality          (0–1)   ← multiplicative gate
                 × (1 + urgency_multiplier)          (0–0.5)
                 × exposure_multiplier               (0.8–1.5)
- CRITICAL IMPORT CONSTRAINT:
    NO LLM imports (agents.*, litellm, openai, anthropic) are allowed in this package.
    Enforced by import-linter rule in pyproject.toml and CI checks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping


# ── Default Model Weights & Thresholds (v1) ───────────────────────────────────

DEFAULT_WEIGHTS: dict[str, Any] = {
    "event_severity": {
        "sanction_designation": 1.00,
        "export_prohibition": 0.90,
        "insolvency_filing": 0.90,
        "export_restriction": 0.75,
        "quota_imposition": 0.70,
        "facility_disruption": 0.65,
        "credit_downgrade": 0.55,
        "tariff_change": 0.50,
        "regulatory_proposal": 0.30,
        "default": 0.40,
    },
    "severity_signal_adjustments": {
        "severe": 0.10,
        "high": 0.05,
        "moderate": 0.00,
        "low": -0.10,
    },
    "tier_decay": {
        "1": 1.00,
        "2": 0.60,
        "3": 0.35,
        "4": 0.20,
        "5": 0.10,
    },
    "single_source_boost": 1.30,
    "source_reliability": {
        "high": 1.00,
        "medium": 0.75,
        "low": 0.50,
    },
    "corroboration_base": 0.70,
    "corroboration_per_source": 0.10,
    "corroboration_cap": 1.00,
    "urgency_multiplier": {
        "in_force_now": 0.50,
        "within_7d": 0.45,
        "within_30d": 0.35,
        "within_90d": 0.20,
        "beyond_90d": 0.10,
        "no_date": 0.15,
    },
    "exposure_multiplier": {
        "no_spend_data": 1.00,
        "log_scale_min": 0.80,
        "log_scale_max": 1.50,
        "default_min_spend": 10_000.0,
        "default_max_spend": 10_000_000.0,
    },
    "confidence_human_judgment_threshold": 0.50,
}

DEFAULT_THRESHOLDS: dict[str, float] = {
    "CRITICAL": 75.0,
    "HIGH": 55.0,
    "MEDIUM": 35.0,
    "LOW": 15.0,
    "BELOW_THRESHOLD": 0.0,
}


@dataclass(frozen=True)
class RiskScoreResult:
    """Immutable output of a deterministic risk score computation."""

    impact_score: float
    severity_band: str
    confidence: float
    needs_human_judgment: bool
    factors: dict[str, Any]
    completeness: dict[str, str]
    model_version: str


# ── Individual Factor Calculators ─────────────────────────────────────────────


def calculate_event_severity(
    event_type: str,
    severity_signal: str | None = None,
    weights: Mapping[str, Any] | None = None,
    completeness: dict[str, str] | None = None,
) -> float:
    """
    Calculate event_severity factor in range [0.0, 1.0].
    Lookup by event_type + additive adjustment from LLM-classified severity_signal.
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    sev_map = w.get("event_severity", DEFAULT_WEIGHTS["event_severity"])
    sig_map = w.get(
        "severity_signal_adjustments", DEFAULT_WEIGHTS["severity_signal_adjustments"]
    )

    clean_type = (event_type or "").lower().strip()
    base = float(sev_map.get(clean_type, sev_map.get("default", 0.40)))

    adj = 0.0
    if severity_signal:
        clean_sig = severity_signal.lower().strip()
        adj = float(sig_map.get(clean_sig, 0.0))
    elif completeness is not None:
        completeness["severity_signal"] = "missing"

    return max(0.0, min(1.0, round(base + adj, 4)))


def calculate_dependency_strength(
    path_confidence: float | None = None,
    depth: int | None = None,
    criticality: int | None = None,
    single_source: bool | None = None,
    weights: Mapping[str, Any] | None = None,
    completeness: dict[str, str] | None = None,
) -> float:
    """
    Calculate dependency_strength factor in range [0.0, 1.0].
    Multiplicative gate:
      = path_confidence × tier_decay[depth] × (0.5 + 0.5 × criticality / 5) × (1.3 if single_source else 1.0)
    Capped at 1.0.
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    tier_map = w.get("tier_decay", DEFAULT_WEIGHTS["tier_decay"])
    ss_boost = float(w.get("single_source_boost", 1.30))

    # Path confidence
    if path_confidence is None:
        p_conf = 1.0
        if completeness is not None:
            completeness["path_confidence"] = "missing"
    else:
        # If passed as 0-100, normalize
        p_conf = float(path_confidence) / 100.0 if path_confidence > 1.0 else float(path_confidence)
    p_conf = max(0.0, min(1.0, p_conf))

    # Tier decay
    if depth is None:
        decay = 1.0
        if completeness is not None:
            completeness["path_depth"] = "missing"
    else:
        depth_key = str(max(1, min(depth, 5)))
        decay = float(tier_map.get(depth_key, 0.10))

    # Criticality: 1 to 5
    if criticality is None:
        crit_val = 3
        if completeness is not None:
            completeness["criticality"] = "missing"
    else:
        crit_val = max(1, min(5, int(criticality)))
    crit_term = 0.5 + 0.5 * (crit_val / 5.0)

    # Single source
    if single_source is None:
        ss_mult = 1.0
        if completeness is not None:
            completeness["single_source"] = "missing"
    else:
        ss_mult = ss_boost if single_source else 1.0

    raw = p_conf * decay * crit_term * ss_mult
    return max(0.0, min(1.0, round(raw, 4)))


def calculate_evidence_quality(
    source_reliability: str | None = None,
    entity_resolution_confidence: float | None = None,
    corroboration_count: int | None = None,
    weights: Mapping[str, Any] | None = None,
    completeness: dict[str, str] | None = None,
) -> float:
    """
    Calculate evidence_quality factor in range [0.0, 1.0].
    Multiplicative gate:
      = source_reliability × entity_resolution_confidence × min(1.0, 0.7 + 0.1 × corroboration_count)
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    rel_map = w.get("source_reliability", DEFAULT_WEIGHTS["source_reliability"])
    c_base = float(w.get("corroboration_base", 0.70))
    c_per = float(w.get("corroboration_per_source", 0.10))
    c_cap = float(w.get("corroboration_cap", 1.00))

    # Source reliability
    if not source_reliability:
        s_rel = 0.75  # default medium
        if completeness is not None:
            completeness["source_reliability"] = "missing"
    else:
        clean_rel = str(source_reliability).lower().strip()
        s_rel = float(rel_map.get(clean_rel, 0.75))

    # Entity resolution confidence
    if entity_resolution_confidence is None:
        e_conf = 0.80
        if completeness is not None:
            completeness["entity_resolution_confidence"] = "missing"
    else:
        e_conf = (
            float(entity_resolution_confidence) / 100.0
            if entity_resolution_confidence > 1.0
            else float(entity_resolution_confidence)
        )
    e_conf = max(0.0, min(1.0, e_conf))

    # Corroboration count
    if corroboration_count is None or corroboration_count < 1:
        c_count = 1
        if completeness is not None and corroboration_count is None:
            completeness["corroboration_count"] = "missing"
    else:
        c_count = int(corroboration_count)

    corrob_mult = min(c_cap, c_base + c_per * c_count)

    raw = s_rel * e_conf * corrob_mult
    return max(0.0, min(1.0, round(raw, 4)))


def calculate_urgency_multiplier(
    effective_date: date | str | None = None,
    as_of_date: date | None = None,
    weights: Mapping[str, Any] | None = None,
    completeness: dict[str, str] | None = None,
) -> float:
    """
    Calculate urgency_multiplier in range [0.0, 0.50].
    Proximity of effective_date relative to as_of_date (defaults to today):
      - In force now: 0.50
      - <= 7 days:    0.45
      - <= 30 days:   0.35
      - <= 90 days:   0.20
      - > 90 days:    0.10
      - None / missing: 0.15
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    urg_map = w.get("urgency_multiplier", DEFAULT_WEIGHTS["urgency_multiplier"])

    if effective_date is None:
        if completeness is not None:
            completeness["effective_date"] = "missing"
        return float(urg_map.get("no_date", 0.15))

    if isinstance(effective_date, str):
        try:
            eff = date.fromisoformat(effective_date)
        except ValueError:
            if completeness is not None:
                completeness["effective_date"] = "unparseable"
            return float(urg_map.get("no_date", 0.15))
    else:
        eff = effective_date

    ref_date = as_of_date if as_of_date is not None else date.today()

    if eff <= ref_date:
        return float(urg_map.get("in_force_now", 0.50))

    delta_days = (eff - ref_date).days
    if delta_days <= 7:
        return float(urg_map.get("within_7d", 0.45))
    elif delta_days <= 30:
        return float(urg_map.get("within_30d", 0.35))
    elif delta_days <= 90:
        return float(urg_map.get("within_90d", 0.20))
    else:
        return float(urg_map.get("beyond_90d", 0.10))


def calculate_exposure_multiplier(
    annual_spend_usd: float | None = None,
    tenant_spend_distribution: Mapping[str, float] | None = None,
    weights: Mapping[str, Any] | None = None,
    completeness: dict[str, str] | None = None,
) -> float:
    """
    Calculate exposure_multiplier in range [0.80, 1.50].
    Annual spend on log scale, normalized within tenant's spend distribution.
    No spend data -> 1.00, and completeness flags the gap.
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    exp_cfg = w.get("exposure_multiplier", DEFAULT_WEIGHTS["exposure_multiplier"])

    if annual_spend_usd is None or annual_spend_usd <= 0:
        if completeness is not None:
            completeness["annual_spend_usd"] = "missing"
        return float(exp_cfg.get("no_spend_data", 1.00))

    log_min = float(exp_cfg.get("log_scale_min", 0.80))
    log_max = float(exp_cfg.get("log_scale_max", 1.50))

    # Determine reference bounds for normalization
    if tenant_spend_distribution:
        min_spend = float(tenant_spend_distribution.get("min", exp_cfg.get("default_min_spend", 10_000.0)))
        max_spend = float(tenant_spend_distribution.get("max", exp_cfg.get("default_max_spend", 10_000_000.0)))
    else:
        min_spend = float(exp_cfg.get("default_min_spend", 10_000.0))
        max_spend = float(exp_cfg.get("default_max_spend", 10_000_000.0))

    # Guard against negative or equal min/max
    min_spend = max(1.0, min_spend)
    max_spend = max(min_spend * 1.001, max_spend)

    spend_clamped = max(min_spend, min(max_spend, float(annual_spend_usd)))
    log_s = math.log10(spend_clamped)
    log_min_s = math.log10(min_spend)
    log_max_s = math.log10(max_spend)

    ratio = (log_s - log_min_s) / (log_max_s - log_min_s)
    val = log_min + (log_max - log_min) * ratio
    return max(log_min, min(log_max, round(val, 4)))


def determine_severity_band(
    impact_score: float,
    thresholds: Mapping[str, float] | None = None,
) -> str:
    """
    Map impact_score to severity band:
      CRITICAL >= 75 | HIGH 55–74 | MEDIUM 35–54 | LOW 15–34 | BELOW_THRESHOLD < 15
    """
    t = thresholds if thresholds is not None else DEFAULT_THRESHOLDS
    critical_t = float(t.get("CRITICAL", 75.0))
    high_t = float(t.get("HIGH", 55.0))
    medium_t = float(t.get("MEDIUM", 35.0))
    low_t = float(t.get("LOW", 15.0))

    if impact_score >= critical_t:
        return "CRITICAL"
    elif impact_score >= high_t:
        return "HIGH"
    elif impact_score >= medium_t:
        return "MEDIUM"
    elif impact_score >= low_t:
        return "LOW"
    else:
        return "BELOW_THRESHOLD"


def calculate_impact_score(
    event_severity: float,
    dependency_strength: float,
    evidence_quality: float,
    urgency_multiplier: float,
    exposure_multiplier: float,
) -> float:
    """
    Core deterministic multiplicative scoring formula:
      impact_score = 100 × event_severity × dependency_strength × evidence_quality
                         × (1 + urgency_multiplier) × exposure_multiplier
    Capped at [0.0, 100.0], rounded to 2 decimal places.
    """
    raw = (
        100.0
        * event_severity
        * dependency_strength
        * evidence_quality
        * (1.0 + urgency_multiplier)
        * exposure_multiplier
    )
    return max(0.0, min(100.0, round(raw, 2)))


# ── Full Scoring Orchestrator ─────────────────────────────────────────────────


def score_risk(
    *,
    event_type: str,
    severity_signal: str | None = None,
    path_confidence: float | None = 1.0,
    depth: int | None = 1,
    criticality: int | None = 3,
    single_source: bool | None = False,
    source_reliability: str | None = "medium",
    entity_resolution_confidence: float | None = 0.80,
    corroboration_count: int | None = 1,
    effective_date: date | str | None = None,
    annual_spend_usd: float | None = None,
    tenant_spend_distribution: Mapping[str, float] | None = None,
    model_version: str = "v1",
    weights: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, float] | None = None,
    as_of_date: date | None = None,
) -> RiskScoreResult:
    """
    Orchestrate full deterministic impact score computation for an (org, event, supplier) triple.
    Returns RiskScoreResult with complete factor breakdown and completeness ledger.
    """
    completeness: dict[str, str] = {}
    w = weights if weights is not None else DEFAULT_WEIGHTS
    t = thresholds if thresholds is not None else DEFAULT_THRESHOLDS

    # 1. Factors
    ev_sev = calculate_event_severity(
        event_type=event_type,
        severity_signal=severity_signal,
        weights=w,
        completeness=completeness,
    )
    dep_str = calculate_dependency_strength(
        path_confidence=path_confidence,
        depth=depth,
        criticality=criticality,
        single_source=single_source,
        weights=w,
        completeness=completeness,
    )
    evi_qual = calculate_evidence_quality(
        source_reliability=source_reliability,
        entity_resolution_confidence=entity_resolution_confidence,
        corroboration_count=corroboration_count,
        weights=w,
        completeness=completeness,
    )
    urg_mult = calculate_urgency_multiplier(
        effective_date=effective_date,
        as_of_date=as_of_date,
        weights=w,
        completeness=completeness,
    )
    exp_mult = calculate_exposure_multiplier(
        annual_spend_usd=annual_spend_usd,
        tenant_spend_distribution=tenant_spend_distribution,
        weights=w,
        completeness=completeness,
    )

    # 2. Final score & severity band
    score = calculate_impact_score(
        event_severity=ev_sev,
        dependency_strength=dep_str,
        evidence_quality=evi_qual,
        urgency_multiplier=urg_mult,
        exposure_multiplier=exp_mult,
    )
    band = determine_severity_band(score, thresholds=t)

    # 3. Confidence & human judgment threshold
    # Confidence reflects evidence quality and graph path certainty
    p_conf_norm = (
        float(path_confidence) / 100.0
        if (path_confidence is not None and path_confidence > 1.0)
        else (float(path_confidence) if path_confidence is not None else 1.0)
    )
    confidence = max(0.0, min(1.0, round(evi_qual * p_conf_norm, 2)))

    human_judg_t = float(w.get("confidence_human_judgment_threshold", 0.50))
    needs_human_judgment = confidence < human_judg_t

    # 4. Factors JSONB payload (exact breakdown allowing mathematical reconstruction)
    eff_date_str = effective_date.isoformat() if isinstance(effective_date, date) else effective_date
    factors: dict[str, Any] = {
        "event_severity": ev_sev,
        "dependency_strength": dep_str,
        "evidence_quality": evi_qual,
        "urgency_multiplier": urg_mult,
        "exposure_multiplier": exp_mult,
        "inputs": {
            "event_type": event_type,
            "severity_signal": severity_signal,
            "path_confidence": path_confidence,
            "depth": depth,
            "criticality": criticality,
            "single_source": single_source,
            "source_reliability": source_reliability,
            "entity_resolution_confidence": entity_resolution_confidence,
            "corroboration_count": corroboration_count,
            "effective_date": eff_date_str,
            "annual_spend_usd": annual_spend_usd,
        },
    }

    return RiskScoreResult(
        impact_score=score,
        severity_band=band,
        confidence=confidence,
        needs_human_judgment=needs_human_judgment,
        factors=factors,
        completeness=completeness,
        model_version=model_version,
    )


def reconstruct_score_from_factors(
    factors: Mapping[str, Any],
    model_version: str = "v1",  # noqa: ARG001
) -> float:
    """
    Reconstruct impact_score exactly from the stored factors JSONB.
    Used by audit, explainability, and determinism verification.
    """
    ev_sev = float(factors["event_severity"])
    dep_str = float(factors["dependency_strength"])
    evi_qual = float(factors["evidence_quality"])
    urg_mult = float(factors["urgency_multiplier"])
    exp_mult = float(factors["exposure_multiplier"])

    return calculate_impact_score(
        event_severity=ev_sev,
        dependency_strength=dep_str,
        evidence_quality=evi_qual,
        urgency_multiplier=urg_mult,
        exposure_multiplier=exp_mult,
    )
