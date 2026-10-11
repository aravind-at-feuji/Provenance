"""
tests/unit/test_phase11_risk_engine_integration.py — Integration and Service tests for Phase 11 Risk Engine.

Architecture reference: §Part I (§9) Business Impact & Risk Engine, §Part Z Phase 11.
Acceptance criteria:
  - Graph intersection accurately discovers exposed tenant supply paths
  - Recompute job updates existing risk assessment records (idempotent)
  - Full factor breakdown and completeness ledger persisted correctly
  - Risk summary aggregates match expected counts and severity distributions
  - API endpoints respond with correct schemas and tenant guard
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.base import CurrentUser
from app.core.deps import get_current_user, require_permission
from app.main import app
from app.modules.companies.models import Company
from app.modules.events.models import Event, EventEntity
from app.modules.graph.models import SupplierRelationship
from app.modules.risk.intersection import GraphIntersectionEngine, GraphIntersectionMatch
from app.modules.risk.models import RiskAssessment, RiskModelVersion
from app.modules.risk.repository import RiskRepository
from app.modules.risk.schemas import (
    PaginatedRiskAssessments,
    RiskAssessmentOut,
    RiskModelVersionOut,
    RiskSummaryOut,
)
from app.modules.risk.scoring import DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS, score_risk
from app.modules.risk.service import RiskService


# ── 1. Repository Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_risk_repository_active_model_fallback():
    mock_db = AsyncMock()
    # Mock no active version in DB
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    repo = RiskRepository(mock_db)
    model = await repo.get_active_model_version()
    assert model.version == "v1"
    assert model.is_active is True
    assert "event_severity" in model.weights
    assert "CRITICAL" in model.thresholds


@pytest.mark.asyncio
async def test_risk_repository_upsert_assessment():
    mock_db = AsyncMock()
    aid = uuid.uuid4()
    org_id = uuid.uuid4()
    event_id = uuid.uuid4()
    company_id = uuid.uuid4()

    fake_assessment = RiskAssessment(
        id=aid,
        org_id=org_id,
        event_id=event_id,
        company_id=company_id,
        impact_score=85.0,
        severity_band="CRITICAL",
        confidence=0.92,
        factors={"event_severity": 1.0, "dependency_strength": 0.85},
        graph_path={"edges": []},
        path_depth=1,
        path_confidence=1.0,
        completeness={},
        model_version="v1",
        computed_at=datetime.now(),
    )

    mock_result = MagicMock()
    mock_result.scalar_one.return_value = fake_assessment
    mock_db.execute.return_value = mock_result

    repo = RiskRepository(mock_db)
    record = await repo.upsert_assessment(
        org_id=org_id,
        event_id=event_id,
        company_id=company_id,
        impact_score=85.0,
        severity_band="CRITICAL",
        confidence=0.92,
        factors={"event_severity": 1.0, "dependency_strength": 0.85},
        graph_path=[],
        path_depth=1,
        path_confidence=1.0,
        completeness={},
        model_version="v1",
    )

    assert record.id == aid
    assert record.impact_score == 85.0
    assert record.severity_band == "CRITICAL"
    mock_db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_risk_repository_get_spend_distribution_defaults():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = (None, None)
    mock_db.execute.return_value = mock_result

    repo = RiskRepository(mock_db)
    dist = await repo.get_spend_distribution(uuid.uuid4())
    assert dist["min"] >= 100.0
    assert dist["max"] > dist["min"]


# ── 2. Graph Intersection Engine Tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_graph_intersection_empty_when_no_entities():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute.return_value = mock_result

    engine = GraphIntersectionEngine(mock_db)
    fake_event = Event(id=uuid.uuid4(), event_type="tariff_change", summary="New tariff")
    matches = await engine.find_intersections_for_event(fake_event)
    assert matches == []


@pytest.mark.asyncio
async def test_graph_intersection_matches_direct_supplier():
    mock_db = AsyncMock()
    org_id = uuid.uuid4()
    company_id = uuid.uuid4()
    event_id = uuid.uuid4()

    fake_company = Company(id=company_id, legal_name="Henan Specialty Alloys Co")
    fake_entity = EventEntity(
        id=uuid.uuid4(),
        event_id=event_id,
        company_id=company_id,
        raw_mention="Henan Specialty Alloys",
        role="subject",
        resolution_confidence=95.0,
    )

    # 1st execute: entity_res
    res_entity = MagicMock()
    res_entity.all.return_value = [(fake_entity, fake_company)]

    # 2nd execute: source reliability
    res_rel = MagicMock()
    res_rel.all.return_value = [("high",)]

    # 3rd execute: candidate orgs
    res_orgs = MagicMock()
    res_orgs.all.return_value = [(org_id,)]

    mock_db.execute.side_effect = [res_entity, res_rel, res_orgs]

    engine = GraphIntersectionEngine(mock_db)
    # Mock find_paths returning a path to tenant
    engine.graph_repo.find_paths = AsyncMock(
        return_value=[
            {
                "edge_id": uuid.uuid4(),
                "from_company_id": company_id,
                "to_org_id": org_id,
                "depth": 1,
                "path_confidence": 0.98,
                "criticality": 4,
                "annual_spend_usd": 1_500_000.0,
                "category": "Raw Materials",
            }
        ]
    )
    engine._is_single_source = AsyncMock(return_value=True)

    fake_event = Event(
        id=event_id,
        event_type="export_restriction",
        severity_signal="high",
        effective_date=date(2026, 11, 1),
        corroboration_count=2,
        summary="Export restriction on alloys",
    )

    matches = await engine.find_intersections_for_event(fake_event)
    assert len(matches) == 1
    match = matches[0]
    assert match.org_id == org_id
    assert match.company_id == company_id
    assert match.criticality == 4
    assert match.single_source is True
    assert match.source_reliability == "high"


# ── 3. RiskService Orchestration & Recompute Tests ─────────────────────────────


@pytest.mark.asyncio
async def test_risk_service_assess_event_end_to_end():
    mock_db = AsyncMock()
    service = RiskService(mock_db)

    # Mock active model version
    service.repo.get_active_model_version = AsyncMock(
        return_value=RiskModelVersion(
            id=uuid.uuid4(),
            version="v1",
            weights=DEFAULT_WEIGHTS,
            thresholds=DEFAULT_THRESHOLDS,
            is_active=True,
        )
    )
    service.repo.get_spend_distribution = AsyncMock(return_value={"min": 10_000.0, "max": 10_000_000.0})

    org_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    ev_id = uuid.uuid4()

    fake_match = GraphIntersectionMatch(
        org_id=org_id,
        event_id=ev_id,
        company_id=comp_id,
        company_name="Acme Microelectronics",
        path_depth=1,
        path_confidence=1.0,
        graph_path=[{"from": "Acme", "type": "supplies_to"}],
        criticality=5,
        annual_spend_usd=5_000_000.0,
        single_source=True,
        source_reliability="high",
        entity_resolution_confidence=0.98,
        corroboration_count=3,
        event_type="sanction_designation",
        severity_signal="severe",
        effective_date=date(2026, 10, 11),
    )

    service.intersection_engine.find_intersections_for_event = AsyncMock(return_value=[fake_match])

    fake_assessment = RiskAssessment(
        id=uuid.uuid4(),
        org_id=org_id,
        event_id=ev_id,
        company_id=comp_id,
        impact_score=100.0,
        severity_band="CRITICAL",
        confidence=0.98,
        factors={"event_severity": 1.0},
        graph_path={"edges": []},
        model_version="v1",
        computed_at=datetime.now(),
    )
    service.repo.upsert_assessment = AsyncMock(return_value=fake_assessment)

    fake_event = Event(id=ev_id, event_type="sanction_designation", summary="Sanctions hit")
    assessments = await service.assess_event(fake_event)

    assert len(assessments) == 1
    assert assessments[0].impact_score == 100.0
    assert assessments[0].severity_band == "CRITICAL"
    service.repo.upsert_assessment.assert_awaited_once()
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_risk_service_recompute_for_event():
    mock_db = AsyncMock()
    service = RiskService(mock_db)

    ev_id = uuid.uuid4()
    fake_event = Event(id=ev_id, event_type="export_prohibition", summary="Ban")

    res_event = MagicMock()
    res_event.scalars.return_value.first.return_value = fake_event
    mock_db.execute.return_value = res_event

    service.assess_event = AsyncMock(return_value=[MagicMock(), MagicMock()])
    count = await service.recompute_for_event(ev_id)
    assert count == 2


# ── 4. API Endpoints Tests ────────────────────────────────────────────────────


@pytest.fixture
def mock_current_user():
    org_id = str(uuid.uuid4())
    return CurrentUser(
        user_id="user_test_123",
        org_id=org_id,
        clerk_org_id=f"org_{org_id}",
        role="org_admin",
    )


@pytest.mark.asyncio
async def test_api_get_risk_summary(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[require_permission("alerts:read")] = lambda: mock_current_user

    mock_summary = RiskSummaryOut(
        total_assessed=12,
        critical_count=3,
        high_count=4,
        medium_count=3,
        low_count=2,
        below_threshold_count=0,
        average_impact_score=68.5,
        needs_human_judgment_count=1,
        top_risks=[],
    )

    with patch("app.api.v1.risks._service") as mock_service_factory:
        mock_srv = MagicMock()
        mock_srv.get_summary = AsyncMock(return_value=mock_summary)
        mock_service_factory.return_value = mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/v1/risks/summary")
            assert res.status_code == 200
            data = res.json()
            assert data["total_assessed"] == 12
            assert data["critical_count"] == 3
            assert data["average_impact_score"] == 68.5

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_list_risk_assessments(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[require_permission("alerts:read")] = lambda: mock_current_user

    aid = uuid.uuid4()
    org_id = uuid.UUID(mock_current_user.org_id)
    ev_id = uuid.uuid4()
    comp_id = uuid.uuid4()

    mock_paginated = PaginatedRiskAssessments(
        data=[
            RiskAssessmentOut(
                id=aid,
                org_id=org_id,
                event_id=ev_id,
                company_id=comp_id,
                impact_score=88.5,
                severity_band="CRITICAL",
                confidence=0.94,
                needs_human_judgment=False,
                factors={"event_severity": 1.0},
                graph_path=[],
                path_depth=1,
                path_confidence=0.98,
                completeness={},
                model_version="v1",
                computed_at=datetime.now(),
                company_name="Shenzhen Semi Co",
                event_type="export_prohibition",
            )
        ],
        total=1,
        limit=50,
        offset=0,
    )

    with patch("app.api.v1.risks._service") as mock_service_factory:
        mock_srv = MagicMock()
        mock_srv.list_assessments = AsyncMock(return_value=mock_paginated)
        mock_service_factory.return_value = mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/v1/risks/assessments?severity_band=CRITICAL")
            assert res.status_code == 200
            data = res.json()
            assert data["total"] == 1
            assert data["data"][0]["severity_band"] == "CRITICAL"
            assert data["data"][0]["company_name"] == "Shenzhen Semi Co"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_recompute_endpoint(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[require_permission("alerts:write")] = lambda: mock_current_user

    with patch("app.api.v1.risks._service") as mock_service_factory:
        mock_srv = MagicMock()
        mock_srv.recompute_for_org = AsyncMock(return_value=5)
        mock_service_factory.return_value = mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post("/v1/risks/recompute", json={})
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "completed"
            assert data["recomputed_count"] == 5

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_get_active_model(mock_current_user):
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[require_permission("alerts:read")] = lambda: mock_current_user

    mock_model = RiskModelVersion(
        id=uuid.uuid4(),
        version="v1",
        weights=DEFAULT_WEIGHTS,
        thresholds=DEFAULT_THRESHOLDS,
        is_active=True,
        activated_at=datetime.now(),
    )

    with patch("app.api.v1.risks._service") as mock_service_factory:
        mock_srv = MagicMock()
        mock_repo = MagicMock()
        mock_repo.get_active_model_version = AsyncMock(return_value=mock_model)
        mock_srv.repo = mock_repo
        mock_service_factory.return_value = mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/v1/risks/models/active")
            assert res.status_code == 200
            data = res.json()
            assert data["version"] == "v1"
            assert data["is_active"] is True
            assert "event_severity" in data["weights"]

    app.dependency_overrides.clear()
