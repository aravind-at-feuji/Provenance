"""
app/modules/risk/service.py — Business logic and orchestration for deterministic risk engine.

ARCHITECTURE & COMPLIANCE:
- Arch reference: §Part I (§9) Business Impact & Risk Engine, §Part Z Phase 11.
- Purely deterministic orchestration. NO LLM calls occur in this service.
- Connects GraphIntersectionEngine with scoring.py and persists to risk_assessments.
- Idempotent recomputation: UNIQUE (org_id, event_id, company_id) updates records.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.models import Event
from app.modules.risk.intersection import GraphIntersectionEngine, GraphIntersectionMatch
from app.modules.risk.models import RiskAssessment, RiskModelVersion
from app.modules.risk.repository import RiskRepository
from app.modules.risk.schemas import (
    PaginatedRiskAssessments,
    RiskAssessmentOut,
    RiskRecomputeResponse,
    RiskSummaryOut,
)
from app.modules.risk.scoring import score_risk


class RiskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RiskRepository(db)
        self.intersection_engine = GraphIntersectionEngine(db)

    async def assess_event(
        self,
        event: Event,
        target_org_id: uuid.UUID | None = None,
    ) -> list[RiskAssessment]:
        """
        Identify intersections for an event and compute deterministic impact scores
        for all affected (tenant, supplier) pairs.
        """
        # 1. Fetch active model weights & thresholds
        model = await self.repo.get_active_model_version()
        weights = model.weights
        thresholds = model.thresholds
        version_str = model.version

        # 2. Find graph intersections
        matches = await self.intersection_engine.find_intersections_for_event(
            event=event,
            target_org_id=target_org_id,
        )

        assessments: list[RiskAssessment] = []
        spend_dist_cache: dict[uuid.UUID, dict[str, float]] = {}

        for match in matches:
            # Cache spend distribution per tenant
            if match.org_id not in spend_dist_cache:
                spend_dist_cache[match.org_id] = await self.repo.get_spend_distribution(
                    match.org_id
                )
            tenant_spend_dist = spend_dist_cache[match.org_id]

            # 3. Deterministic calculation
            result = score_risk(
                event_type=match.event_type,
                severity_signal=match.severity_signal,
                path_confidence=match.path_confidence,
                depth=match.path_depth,
                criticality=match.criticality,
                single_source=match.single_source,
                source_reliability=match.source_reliability,
                entity_resolution_confidence=match.entity_resolution_confidence,
                corroboration_count=match.corroboration_count,
                effective_date=match.effective_date,
                annual_spend_usd=match.annual_spend_usd,
                tenant_spend_distribution=tenant_spend_dist,
                model_version=version_str,
                weights=weights,
                thresholds=thresholds,
            )

            # 4. Idempotent persistence
            record = await self.repo.upsert_assessment(
                org_id=match.org_id,
                event_id=match.event_id,
                company_id=match.company_id,
                impact_score=result.impact_score,
                severity_band=result.severity_band,
                confidence=result.confidence,
                factors=result.factors,
                graph_path=match.graph_path,
                path_depth=match.path_depth,
                path_confidence=match.path_confidence,
                completeness=result.completeness,
                model_version=version_str,
            )
            assessments.append(record)

        await self.db.commit()
        return assessments

    async def recompute_for_event(self, event_id: uuid.UUID) -> int:
        """Recompute risk assessments across all tenants for a single event."""
        stmt = select(Event).where(Event.id == event_id)
        res = await self.db.execute(stmt)
        event = res.scalars().first()
        if not event:
            return 0

        assessments = await self.assess_event(event=event)
        return len(assessments)

    async def recompute_for_org(self, org_id: uuid.UUID) -> int:
        """Recompute risk assessments for all active events affecting an organization."""
        stmt = select(Event).where(Event.status == "active")
        res = await self.db.execute(stmt)
        active_events = res.scalars().all()

        total_recomputed = 0
        for event in active_events:
            assessments = await self.assess_event(event=event, target_org_id=org_id)
            total_recomputed += len(assessments)

        return total_recomputed

    async def recompute_all(self) -> int:
        """Batch recompute for all active events across all organizations."""
        stmt = select(Event).where(Event.status == "active")
        res = await self.db.execute(stmt)
        active_events = res.scalars().all()

        total = 0
        for event in active_events:
            assessments = await self.assess_event(event=event)
            total += len(assessments)

        return total

    async def list_assessments(
        self,
        *,
        org_id: uuid.UUID,
        severity_band: str | None = None,
        min_score: float | None = None,
        company_id: uuid.UUID | None = None,
        event_id: uuid.UUID | None = None,
        needs_human_judgment: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedRiskAssessments:
        """List tenant risk assessments with joined display names and metadata."""
        rows, total = await self.repo.list_assessments(
            org_id=org_id,
            severity_band=severity_band,
            min_score=min_score,
            company_id=company_id,
            event_id=event_id,
            needs_human_judgment=needs_human_judgment,
            limit=limit,
            offset=offset,
        )

        out_items: list[RiskAssessmentOut] = []
        for assessment, company, event in rows:
            out_items.append(
                RiskAssessmentOut(
                    id=assessment.id,
                    org_id=assessment.org_id,
                    event_id=assessment.event_id,
                    company_id=assessment.company_id,
                    impact_score=float(assessment.impact_score),
                    severity_band=assessment.severity_band,
                    confidence=float(assessment.confidence),
                    needs_human_judgment=float(assessment.confidence) < 0.50,
                    factors=assessment.factors,
                    graph_path=assessment.graph_path,
                    path_depth=assessment.path_depth,
                    path_confidence=(
                        float(assessment.path_confidence)
                        if assessment.path_confidence is not None
                        else None
                    ),
                    completeness=assessment.completeness or {},
                    model_version=assessment.model_version,
                    computed_at=assessment.computed_at,
                    company_name=company.legal_name if company else None,
                    event_summary=event.summary if event else None,
                    event_type=event.event_type if event else None,
                )
            )

        return PaginatedRiskAssessments(
            data=out_items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_assessment(
        self, *, org_id: uuid.UUID, assessment_id: uuid.UUID
    ) -> RiskAssessmentOut | None:
        """Retrieve a single risk assessment with full breakdown and joined metadata."""
        row = await self.repo.get_assessment_by_id(
            org_id=org_id, assessment_id=assessment_id
        )
        if not row:
            return None

        assessment, company, event = row
        return RiskAssessmentOut(
            id=assessment.id,
            org_id=assessment.org_id,
            event_id=assessment.event_id,
            company_id=assessment.company_id,
            impact_score=float(assessment.impact_score),
            severity_band=assessment.severity_band,
            confidence=float(assessment.confidence),
            needs_human_judgment=float(assessment.confidence) < 0.50,
            factors=assessment.factors,
            graph_path=assessment.graph_path,
            path_depth=assessment.path_depth,
            path_confidence=(
                float(assessment.path_confidence)
                if assessment.path_confidence is not None
                else None
            ),
            completeness=assessment.completeness or {},
            model_version=assessment.model_version,
            computed_at=assessment.computed_at,
            company_name=company.legal_name if company else None,
            event_summary=event.summary if event else None,
            event_type=event.event_type if event else None,
        )

    async def get_summary(self, org_id: uuid.UUID) -> RiskSummaryOut:
        """Compute tenant dashboard risk aggregates and top active risks."""
        metrics = await self.repo.get_summary_metrics(org_id)
        rows, _ = await self.repo.list_assessments(
            org_id=org_id,
            limit=5,
            offset=0,
        )

        top_risks = [
            RiskAssessmentOut(
                id=a.id,
                org_id=a.org_id,
                event_id=a.event_id,
                company_id=a.company_id,
                impact_score=float(a.impact_score),
                severity_band=a.severity_band,
                confidence=float(a.confidence),
                needs_human_judgment=float(a.confidence) < 0.50,
                factors=a.factors,
                graph_path=a.graph_path,
                path_depth=a.path_depth,
                path_confidence=float(a.path_confidence) if a.path_confidence is not None else None,
                completeness=a.completeness or {},
                model_version=a.model_version,
                computed_at=a.computed_at,
                company_name=c.legal_name if c else None,
                event_summary=e.summary if e else None,
                event_type=e.event_type if e else None,
            )
            for a, c, e in rows
        ]

        return RiskSummaryOut(
            total_assessed=metrics["total"],
            critical_count=metrics["critical"],
            high_count=metrics["high"],
            medium_count=metrics["medium"],
            low_count=metrics["low"],
            below_threshold_count=metrics["below_threshold"],
            average_impact_score=metrics["avg_score"],
            needs_human_judgment_count=metrics["needs_human_judgment"],
            top_risks=top_risks,
        )
