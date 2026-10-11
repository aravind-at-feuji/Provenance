"""
/v1/risks — Deterministic risk assessment endpoints, aggregates, and recomputation.

Endpoints:
  GET  /risks/summary             — aggregate risk metrics, band distributions, and top risks
  GET  /risks/assessments         — list risk assessments for current tenant org with faceted filters
  GET  /risks/assessments/{id}    — get single risk assessment with full factor breakdown
  POST /risks/recompute           — trigger deterministic recomputation for org or event
  GET  /risks/models              — list risk model versions
  GET  /risks/models/active       — get currently active risk model version
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import CurrentUser
from app.core.deps import require_permission
from app.core.errors import bad_request, not_found
from app.db.session import get_db
from app.modules.risk.schemas import (
    PaginatedRiskAssessments,
    RiskAssessmentOut,
    RiskModelVersionOut,
    RiskRecomputeRequest,
    RiskRecomputeResponse,
    RiskSummaryOut,
)
from app.modules.risk.service import RiskService

router = APIRouter(prefix="/risks", tags=["risks"])


def _service(db: AsyncSession) -> RiskService:
    return RiskService(db)


def _get_org_id(current_user: CurrentUser) -> uuid.UUID:
    if not current_user.org_id:
        raise bad_request("Tenant organization context (org_id) is required for risk operations")
    return uuid.UUID(current_user.org_id)


@router.get("/summary", response_model=RiskSummaryOut)
async def get_risk_summary(
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    db: AsyncSession = Depends(get_db),
) -> RiskSummaryOut:
    """Dashboard risk metrics, band distributions, and top risks for current tenant."""
    org_id = _get_org_id(current_user)
    service = _service(db)
    return await service.get_summary(org_id=org_id)


@router.get("/assessments", response_model=PaginatedRiskAssessments)
async def list_risk_assessments(
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    severity_band: Annotated[str | None, Query()] = None,
    min_score: Annotated[float | None, Query(ge=0.0, le=100.0)] = None,
    company_id: Annotated[uuid.UUID | None, Query()] = None,
    event_id: Annotated[uuid.UUID | None, Query()] = None,
    needs_human_judgment: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> PaginatedRiskAssessments:
    """List risk assessments with faceted filters and pagination."""
    org_id = _get_org_id(current_user)
    service = _service(db)
    return await service.list_assessments(
        org_id=org_id,
        severity_band=severity_band,
        min_score=min_score,
        company_id=company_id,
        event_id=event_id,
        needs_human_judgment=needs_human_judgment,
        limit=limit,
        offset=offset,
    )


@router.get("/assessments/{assessment_id}", response_model=RiskAssessmentOut)
async def get_risk_assessment(
    assessment_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentOut:
    """Get single risk assessment with full factor arithmetic breakdown."""
    org_id = _get_org_id(current_user)
    service = _service(db)
    assessment = await service.get_assessment(org_id=org_id, assessment_id=assessment_id)
    if not assessment:
        raise not_found(f"Risk assessment {assessment_id} not found in this organization")
    return assessment


@router.post("/recompute", response_model=RiskRecomputeResponse)
async def recompute_risk_assessments(
    body: RiskRecomputeRequest,
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:write"))],
    db: AsyncSession = Depends(get_db),
) -> RiskRecomputeResponse:
    """Trigger deterministic recomputation of risk assessments."""
    service = _service(db)
    org_id = _get_org_id(current_user)

    if body.event_id:
        count = await service.recompute_for_event(body.event_id)
        msg = f"Recomputed {count} risk assessments for event {body.event_id}"
    elif body.org_id or not body.event_id:
        target_org = body.org_id if body.org_id else org_id
        count = await service.recompute_for_org(target_org)
        msg = f"Recomputed {count} risk assessments for organization {target_org}"
    else:
        count = await service.recompute_all()
        msg = f"Recomputed {count} risk assessments globally"

    return RiskRecomputeResponse(
        status="completed",
        recomputed_count=count,
        message=msg,
    )


@router.get("/models", response_model=list[RiskModelVersionOut])
async def list_risk_models(
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    db: AsyncSession = Depends(get_db),
) -> list[RiskModelVersionOut]:
    """List all registered risk model versions."""
    service = _service(db)
    models = await service.repo.list_model_versions()
    return [RiskModelVersionOut.model_validate(m) for m in models]


@router.get("/models/active", response_model=RiskModelVersionOut)
async def get_active_risk_model(
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    db: AsyncSession = Depends(get_db),
) -> RiskModelVersionOut:
    """Get active risk model version weights and thresholds."""
    service = _service(db)
    model = await service.repo.get_active_model_version()
    return RiskModelVersionOut.model_validate(model)
