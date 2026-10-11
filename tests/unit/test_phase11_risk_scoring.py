"""
tests/unit/test_phase11_risk_scoring.py — Unit tests for Phase 11 Deterministic Risk Scoring.

Architecture reference: §Part I (§9) Business Impact & Risk Engine, §Part Z Phase 11.
Acceptance criteria:
  - Every factor unit-tested at boundaries
  - Determinism test: same input 100x -> identical score (100% determinism)
  - Missing-input completeness behaviour
  - factors JSONB reconstructs the score exactly
  - Multiplicative gate verification (zero relevance -> zero score)
  - Assert NO LLM call occurs during scoring
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from typing import Any

import pytest

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


# ── 1. Import Constraint & Zero-LLM Invariant Test ─────────────────────────────


def test_zero_llm_imports_in_risk_module():
    """Architecture requirement: app.modules.risk must NOT import agents or LLM providers."""
    import ast
    import app.modules.risk.scoring as scoring_mod

    with open(scoring_mod.__file__, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=scoring_mod.__file__)

    forbidden_roots = {"agents", "litellm", "openai", "anthropic", "langchain"}
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    for mod in imported_modules:
        root = mod.split(".")[0]
        assert root not in forbidden_roots, f"Forbidden import found in risk.scoring: {mod}"


# ── 2. Boundary Tests: Event Severity ─────────────────────────────────────────


@pytest.mark.parametrize(
    "event_type,expected_base",
    [
        ("sanction_designation", 1.00),
        ("export_prohibition", 0.90),
        ("insolvency_filing", 0.90),
        ("export_restriction", 0.75),
        ("quota_imposition", 0.70),
        ("facility_disruption", 0.65),
        ("credit_downgrade", 0.55),
        ("tariff_change", 0.50),
        ("regulatory_proposal", 0.30),
        ("unknown_future_event", 0.40),  # default
        ("", 0.40),
    ],
)
def test_event_severity_base_lookups(event_type: str, expected_base: float):
    completeness: dict[str, str] = {}
    sev = calculate_event_severity(event_type=event_type, completeness=completeness)
    assert sev == expected_base
    assert completeness.get("severity_signal") == "missing"


def test_event_severity_signal_adjustments():
    # Base 0.75 (export_restriction)
    assert calculate_event_severity("export_restriction", severity_signal="severe") == 0.85
    assert calculate_event_severity("export_restriction", severity_signal="high") == 0.80
    assert calculate_event_severity("export_restriction", severity_signal="moderate") == 0.75
    assert calculate_event_severity("export_restriction", severity_signal="low") == 0.65

    # Clamping boundaries [0.0, 1.0]
    # sanction_designation (1.00) + severe (+0.10) => clamped to 1.00
    assert calculate_event_severity("sanction_designation", severity_signal="severe") == 1.00
    # regulatory_proposal (0.30) + low (-0.10) => 0.20
    assert calculate_event_severity("regulatory_proposal", severity_signal="low") == 0.20


# ── 3. Boundary Tests: Dependency Strength ────────────────────────────────────


def test_dependency_strength_depth_decay():
    # Depths 1 to 5 with confidence 1.0, criticality 3, single_source False
    # crit_factor for 3 is 0.5 + 0.5*(3/5) = 0.8
    s1 = calculate_dependency_strength(path_confidence=1.0, depth=1, criticality=3, single_source=False)
    s2 = calculate_dependency_strength(path_confidence=1.0, depth=2, criticality=3, single_source=False)
    s3 = calculate_dependency_strength(path_confidence=1.0, depth=3, criticality=3, single_source=False)
    s4 = calculate_dependency_strength(path_confidence=1.0, depth=4, criticality=3, single_source=False)
    s5 = calculate_dependency_strength(path_confidence=1.0, depth=5, criticality=3, single_source=False)
    s_beyond = calculate_dependency_strength(path_confidence=1.0, depth=6, criticality=3, single_source=False)

    assert s1 == pytest.approx(1.0 * 1.00 * 0.8 * 1.0, rel=1e-3)  # 0.80
    assert s2 == pytest.approx(1.0 * 0.60 * 0.8 * 1.0, rel=1e-3)  # 0.48
    assert s3 == pytest.approx(1.0 * 0.35 * 0.8 * 1.0, rel=1e-3)  # 0.28
    assert s4 == pytest.approx(1.0 * 0.20 * 0.8 * 1.0, rel=1e-3)  # 0.16
    assert s5 == pytest.approx(1.0 * 0.10 * 0.8 * 1.0, rel=1e-3)  # 0.08
    assert s_beyond == s5  # beyond depth 5 capped to tier 5 decay


def test_dependency_strength_criticality_and_single_source():
    # Criticality 1: 0.5 + 0.5*(1/5) = 0.6
    # Criticality 5: 0.5 + 0.5*(5/5) = 1.0
    c1 = calculate_dependency_strength(path_confidence=1.0, depth=1, criticality=1, single_source=False)
    c5 = calculate_dependency_strength(path_confidence=1.0, depth=1, criticality=5, single_source=False)
    assert c1 == pytest.approx(0.60, rel=1e-3)
    assert c5 == pytest.approx(1.00, rel=1e-3)

    # Single source boost: 1.3
    ss_boosted = calculate_dependency_strength(path_confidence=1.0, depth=2, criticality=3, single_source=True)
    # depth 2: 0.6 * 0.8 * 1.3 = 0.624
    assert ss_boosted == pytest.approx(0.624, rel=1e-3)

    # Multiplicative cap at 1.0
    capped = calculate_dependency_strength(path_confidence=1.0, depth=1, criticality=5, single_source=True)
    assert capped == 1.00


def test_dependency_strength_missing_inputs_completeness():
    completeness: dict[str, str] = {}
    dep = calculate_dependency_strength(completeness=completeness)
    assert completeness["path_confidence"] == "missing"
    assert completeness["path_depth"] == "missing"
    assert completeness["criticality"] == "missing"
    assert completeness["single_source"] == "missing"
    # Default values: p_conf 1.0, depth 1 (decay 1.0), crit 3 (0.8), ss False => 0.80
    assert dep == 0.80


# ── 4. Boundary Tests: Evidence Quality ───────────────────────────────────────


def test_evidence_quality_source_reliability():
    # Corroboration 1: 0.7 + 0.1 = 0.8. e_conf = 1.0
    eq_high = calculate_evidence_quality(source_reliability="high", entity_resolution_confidence=1.0, corroboration_count=1)
    eq_med = calculate_evidence_quality(source_reliability="medium", entity_resolution_confidence=1.0, corroboration_count=1)
    eq_low = calculate_evidence_quality(source_reliability="low", entity_resolution_confidence=1.0, corroboration_count=1)

    assert eq_high == pytest.approx(1.00 * 1.0 * 0.80, rel=1e-3)  # 0.80
    assert eq_med == pytest.approx(0.75 * 1.0 * 0.80, rel=1e-3)   # 0.60
    assert eq_low == pytest.approx(0.50 * 1.0 * 0.80, rel=1e-3)   # 0.40


def test_evidence_quality_corroboration_scaling_and_cap():
    # corroboration 3: 0.7 + 0.1*3 = 1.00
    eq_3 = calculate_evidence_quality(source_reliability="high", entity_resolution_confidence=1.0, corroboration_count=3)
    assert eq_3 == 1.00

    # 40 corroborating outlets: capped at 1.00
    eq_40 = calculate_evidence_quality(source_reliability="high", entity_resolution_confidence=1.0, corroboration_count=40)
    assert eq_40 == 1.00


def test_evidence_quality_percentage_normalization():
    # Confidence given as 95.0 (percentage scale) should normalize to 0.95
    eq_pct = calculate_evidence_quality(source_reliability="high", entity_resolution_confidence=95.0, corroboration_count=3)
    assert eq_pct == pytest.approx(0.95, rel=1e-3)


# ── 5. Boundary Tests: Urgency Multiplier ─────────────────────────────────────


def test_urgency_multiplier_dates():
    ref_date = date(2026, 10, 11)

    # In force now (past date or today)
    assert calculate_urgency_multiplier(date(2026, 10, 10), as_of_date=ref_date) == 0.50
    assert calculate_urgency_multiplier(date(2026, 10, 11), as_of_date=ref_date) == 0.50

    # Within 7 days
    assert calculate_urgency_multiplier(date(2026, 10, 18), as_of_date=ref_date) == 0.45

    # Within 30 days
    assert calculate_urgency_multiplier(date(2026, 11, 10), as_of_date=ref_date) == 0.35

    # Within 90 days
    assert calculate_urgency_multiplier(date(2026, 12, 15), as_of_date=ref_date) == 0.20

    # Beyond 90 days
    assert calculate_urgency_multiplier(date(2027, 4, 1), as_of_date=ref_date) == 0.10

    # None / missing
    completeness: dict[str, str] = {}
    assert calculate_urgency_multiplier(None, completeness=completeness) == 0.15
    assert completeness["effective_date"] == "missing"


# ── 6. Boundary Tests: Exposure Multiplier ────────────────────────────────────


def test_exposure_multiplier_spend_scaling():
    # No spend data -> 1.00
    completeness: dict[str, str] = {}
    assert calculate_exposure_multiplier(None, completeness=completeness) == 1.00
    assert completeness["annual_spend_usd"] == "missing"

    assert calculate_exposure_multiplier(0.0) == 1.00
    assert calculate_exposure_multiplier(-500.0) == 1.00

    # Spend distribution min $10,000, max $10,000,000
    dist = {"min": 10_000.0, "max": 10_000_000.0}
    # At min spend => 0.80
    assert calculate_exposure_multiplier(10_000.0, tenant_spend_distribution=dist) == 0.80
    # Below min spend clamped to 0.80
    assert calculate_exposure_multiplier(500.0, tenant_spend_distribution=dist) == 0.80
    # At max spend => 1.50
    assert calculate_exposure_multiplier(10_000_000.0, tenant_spend_distribution=dist) == 1.50
    # Above max spend clamped to 1.50
    assert calculate_exposure_multiplier(50_000_000.0, tenant_spend_distribution=dist) == 1.50


# ── 7. Multiplicative Gate Verification ───────────────────────────────────────


def test_multiplicative_gates_suppress_irrelevant_or_unsubstantiated_events():
    """
    Arch §I.3 principle: relevance is multiplicative, not additive.
    If dependency_strength or evidence_quality is 0, score MUST be 0 even for severe events.
    """
    # Severe sanction designation (1.00) with zero dependency (upstream unrelated supplier)
    score_no_dep = calculate_impact_score(
        event_severity=1.00,
        dependency_strength=0.00,
        evidence_quality=1.00,
        urgency_multiplier=0.50,
        exposure_multiplier=1.50,
    )
    assert score_no_dep == 0.0

    # Severe event with zero evidence quality
    score_no_evidence = calculate_impact_score(
        event_severity=1.00,
        dependency_strength=1.00,
        evidence_quality=0.00,
        urgency_multiplier=0.50,
        exposure_multiplier=1.50,
    )
    assert score_no_evidence == 0.0


# ── 8. Severity Bands & Human Judgment Label ──────────────────────────────────


@pytest.mark.parametrize(
    "score,expected_band",
    [
        (100.0, "CRITICAL"),
        (75.0, "CRITICAL"),
        (74.99, "HIGH"),
        (55.0, "HIGH"),
        (54.99, "MEDIUM"),
        (35.0, "MEDIUM"),
        (34.99, "LOW"),
        (15.0, "LOW"),
        (14.99, "BELOW_THRESHOLD"),
        (0.0, "BELOW_THRESHOLD"),
    ],
)
def test_severity_bands(score: float, expected_band: str):
    assert determine_severity_band(score) == expected_band


def test_confidence_vs_score_human_judgment_flag():
    """
    Arch §I.3: A high-score alert with low confidence reads 'potentially severe, weak evidence'
    and must be flagged needs_human_judgment=True.
    """
    # Low evidence quality (weak confidence) but severe event
    res = score_risk(
        event_type="sanction_designation",
        path_confidence=0.40,
        depth=1,
        criticality=5,
        source_reliability="low",
        entity_resolution_confidence=0.40,
        corroboration_count=1,
    )
    assert res.confidence < 0.50
    assert res.needs_human_judgment is True


# ── 9. Determinism Test: Same Input 100x -> Identical Score ───────────────────


def test_determinism_100x_identical_score():
    """Acceptance criterion: Determinism 100%. Same input 100 times produces identical score."""
    inputs = {
        "event_type": "export_restriction",
        "severity_signal": "high",
        "path_confidence": 0.95,
        "depth": 2,
        "criticality": 4,
        "single_source": True,
        "source_reliability": "high",
        "entity_resolution_confidence": 0.92,
        "corroboration_count": 3,
        "effective_date": date(2026, 11, 1),
        "annual_spend_usd": 2_500_000.0,
        "as_of_date": date(2026, 10, 11),
    }

    first_run = score_risk(**inputs)
    for _ in range(100):
        run = score_risk(**inputs)
        assert run.impact_score == first_run.impact_score
        assert run.severity_band == first_run.severity_band
        assert run.confidence == first_run.confidence
        assert run.needs_human_judgment == first_run.needs_human_judgment
        assert run.factors == first_run.factors


# ── 10. Exact Factors JSONB Reconstruction Test ───────────────────────────────


def test_factors_jsonb_reconstructs_score_exactly():
    """Acceptance criterion: factors JSONB reconstructs the score exactly."""
    test_cases = [
        {"event_type": "sanction_designation", "criticality": 5, "annual_spend_usd": 5_000_000.0},
        {"event_type": "export_restriction", "depth": 2, "single_source": True},
        {"event_type": "insolvency_filing", "source_reliability": "high", "corroboration_count": 4},
        {"event_type": "tariff_change", "depth": 3, "criticality": 2},
        {"event_type": "regulatory_proposal", "depth": 4, "annual_spend_usd": 15_000.0},
    ]

    for tc in test_cases:
        res = score_risk(**tc)
        reconstructed = reconstruct_score_from_factors(res.factors)
        assert reconstructed == res.impact_score
