"""
app/modules/risk/repository.py — Data access layer for RiskModelVersion and RiskAssessment.

CRITICAL TENANT ISOLATION:
Every query on risk_assessments MUST be filtered by org_id.
UNIQUE (org_id, event_id, company_id) enables idempotent recomputation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.companies.models import Company
from app.modules.events.models import Event
from app.modules.graph.models import SupplierRelationship
from app.modules.risk.models import RiskAssessment, RiskModelVersion
from app.modules.risk.scoring import DEFAULT_THRESHOLDS, DEFAULT_WEIGHTS


class RiskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Model Versions ────────────────────────────────────────────────────────

    async def get_active_model_version(self) -> RiskModelVersion:
        """Fetch current active risk model version. Fallback to default v1 in-memory if none."""
        stmt = (
            select(RiskModelVersion)
            .where(RiskModelVersion.is_active.is_(True))
            .order_by(RiskModelVersion.created_at.desc())
        )
        res = await self.db.execute(stmt)
        active = res.scalars().first()
        if active:
            return active

        # Check if v1 exists at all
        stmt_v1 = select(RiskModelVersion).where(RiskModelVersion.version == "v1")
        res_v1 = await self.db.execute(stmt_v1)
        v1 = res_v1.scalars().first()
        if v1:
            return v1

        # Return synthesized fallback model version object
        fallback = RiskModelVersion(
            id=uuid.uuid4(),
            version="v1",
            weights=DEFAULT_WEIGHTS,
            thresholds=DEFAULT_THRESHOLDS,
            is_active=True,
            activated_at=datetime.now(),
        )
        return fallback

    async def get_model_version(self, version: str) -> RiskModelVersion | None:
        """Fetch specific risk model version by name."""
        stmt = select(RiskModelVersion).where(RiskModelVersion.version == version)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_model_versions(self) -> list[RiskModelVersion]:
        """List all registered risk model versions."""
        stmt = select(RiskModelVersion).order_by(RiskModelVersion.version.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # ── Risk Assessments ──────────────────────────────────────────────────────

    async def get_assessment(
        self,
        *,
        org_id: uuid.UUID,
        event_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> RiskAssessment | None:
        """Fetch assessment for (org_id, event_id, company_id) triple."""
        stmt = select(RiskAssessment).where(
            RiskAssessment.org_id == org_id,
            RiskAssessment.event_id == event_id,
            RiskAssessment.company_id == company_id,
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_assessment_by_id(
        self,
        *,
        org_id: uuid.UUID,
        assessment_id: uuid.UUID,
    ) -> tuple[RiskAssessment, Company | None, Event | None] | None:
        """Fetch single assessment by ID with tenant guard and joined metadata."""
        stmt = (
            select(RiskAssessment, Company, Event)
            .outerjoin(Company, RiskAssessment.company_id == Company.id)
            .outerjoin(Event, RiskAssessment.event_id == Event.id)
            .where(
                RiskAssessment.id == assessment_id,
                RiskAssessment.org_id == org_id,
            )
        )
        res = await self.db.execute(stmt)
        row = res.first()
        if not row:
            return None
        return row[0], row[1], row[2]

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
    ) -> tuple[list[tuple[RiskAssessment, Company | None, Event | None]], int]:
        """List assessments for a tenant org with filtering and pagination."""
        stmt = (
            select(RiskAssessment, Company, Event)
            .outerjoin(Company, RiskAssessment.company_id == Company.id)
            .outerjoin(Event, RiskAssessment.event_id == Event.id)
            .where(RiskAssessment.org_id == org_id)
        )

        count_stmt = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.org_id == org_id
        )

        if severity_band:
            stmt = stmt.where(RiskAssessment.severity_band == severity_band)
            count_stmt = count_stmt.where(RiskAssessment.severity_band == severity_band)

        if min_score is not None:
            stmt = stmt.where(RiskAssessment.impact_score >= min_score)
            count_stmt = count_stmt.where(RiskAssessment.impact_score >= min_score)

        if company_id is not None:
            stmt = stmt.where(RiskAssessment.company_id == company_id)
            count_stmt = count_stmt.where(RiskAssessment.company_id == company_id)

        if event_id is not None:
            stmt = stmt.where(RiskAssessment.event_id == event_id)
            count_stmt = count_stmt.where(RiskAssessment.event_id == event_id)

        if needs_human_judgment is not None:
            # Check factors confidence < 0.50
            if needs_human_judgment:
                stmt = stmt.where(RiskAssessment.confidence < 0.50)
                count_stmt = count_stmt.where(RiskAssessment.confidence < 0.50)
            else:
                stmt = stmt.where(RiskAssessment.confidence >= 0.50)
                count_stmt = count_stmt.where(RiskAssessment.confidence >= 0.50)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            stmt.order_by(RiskAssessment.impact_score.desc(), RiskAssessment.computed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return [(r[0], r[1], r[2]) for r in res.all()], total

    async def upsert_assessment(
        self,
        *,
        org_id: uuid.UUID,
        event_id: uuid.UUID,
        company_id: uuid.UUID,
        impact_score: float,
        severity_band: str,
        confidence: float,
        factors: dict[str, Any],
        graph_path: dict[str, Any] | list[Any],
        path_depth: int | None,
        path_confidence: float | None,
        completeness: dict[str, Any],
        model_version: str,
    ) -> RiskAssessment:
        """
        Idempotently insert or update risk assessment matching UNIQUE(org_id, event_id, company_id).
        """
        # Format graph_path as JSON-compatible dict or list
        gp_payload = graph_path if isinstance(graph_path, dict) else {"edges": graph_path}

        insert_stmt = (
            pg_insert(RiskAssessment)
            .values(
                org_id=org_id,
                event_id=event_id,
                company_id=company_id,
                impact_score=impact_score,
                severity_band=severity_band,
                confidence=confidence,
                factors=factors,
                graph_path=gp_payload,
                path_depth=path_depth,
                path_confidence=path_confidence,
                completeness=completeness,
                model_version=model_version,
                computed_at=datetime.now(),
            )
            .on_conflict_do_update(
                constraint="uq_risk_assessment",
                set_={
                    "impact_score": impact_score,
                    "severity_band": severity_band,
                    "confidence": confidence,
                    "factors": factors,
                    "graph_path": gp_payload,
                    "path_depth": path_depth,
                    "path_confidence": path_confidence,
                    "completeness": completeness,
                    "model_version": model_version,
                    "computed_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )
            .returning(RiskAssessment)
        )

        res = await self.db.execute(insert_stmt)
        record = res.scalar_one()
        await self.db.flush()
        return record

    async def get_spend_distribution(
        self, org_id: uuid.UUID
    ) -> dict[str, float]:
        """Fetch min and max annual spend across org's active direct suppliers for log scaling."""
        stmt = (
            select(
                func.min(SupplierRelationship.annual_spend_usd),
                func.max(SupplierRelationship.annual_spend_usd),
            )
            .where(
                SupplierRelationship.org_id == org_id,
                SupplierRelationship.deleted_at.is_(None),
                SupplierRelationship.valid_to.is_(None),
                SupplierRelationship.annual_spend_usd.is_not(None),
                SupplierRelationship.annual_spend_usd > 0,
            )
        )
        res = await self.db.execute(stmt)
        row = res.first()
        min_val = float(row[0]) if (row and row[0] is not None) else 10_000.0
        max_val = float(row[1]) if (row and row[1] is not None) else 10_000_000.0
        return {"min": max(100.0, min_val), "max": max(min_val * 10, max_val)}

    async def get_summary_metrics(
        self, org_id: uuid.UUID
    ) -> dict[str, Any]:
        """Calculate dashboard summary aggregates across tenant's risk assessments."""
        stmt = (
            select(
                func.count(RiskAssessment.id),
                func.avg(RiskAssessment.impact_score),
                func.count(func.nullif(RiskAssessment.severity_band != "CRITICAL", True)),
                func.count(func.nullif(RiskAssessment.severity_band != "HIGH", True)),
                func.count(func.nullif(RiskAssessment.severity_band != "MEDIUM", True)),
                func.count(func.nullif(RiskAssessment.severity_band != "LOW", True)),
                func.count(func.nullif(RiskAssessment.severity_band != "BELOW_THRESHOLD", True)),
                func.count(func.nullif(RiskAssessment.confidence >= 0.50, True)),
            )
            .where(RiskAssessment.org_id == org_id)
        )
        res = await self.db.execute(stmt)
        row = res.first()
        if not row:
            return {
                "total": 0,
                "avg_score": 0.0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "below_threshold": 0,
                "needs_human_judgment": 0,
            }

        return {
            "total": int(row[0] or 0),
            "avg_score": round(float(row[1] or 0.0), 2),
            "critical": int(row[2] or 0),
            "high": int(row[3] or 0),
            "medium": int(row[4] or 0),
            "low": int(row[5] or 0),
            "below_threshold": int(row[6] or 0),
            "needs_human_judgment": int(row[7] or 0),
        }
