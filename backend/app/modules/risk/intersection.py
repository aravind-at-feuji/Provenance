"""
app/modules/risk/intersection.py — Graph intersection engine connecting events to tenant supply graphs.

ARCHITECTURE & COMPLIANCE:
- Arch reference: §Part I.2 Flow, §Part D.2 risk / graph, §Part Z Phase 11.
- Deterministic SQL queries to identify which tenants and direct/indirect suppliers
  intersect the entities affected by an external Event.
- Cycle-guarded recursive paths with confidence products and depth tracking.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.companies.models import Company
from app.modules.events.models import DataSource, Event, EventEntity, EventSourceRecord, SourceRecord
from app.modules.graph.models import SupplierRelationship


@dataclass(frozen=True)
class GraphIntersectionMatch:
    """Represents a deterministic intersection between an Event and a tenant's graph."""

    org_id: uuid.UUID
    event_id: uuid.UUID
    company_id: uuid.UUID
    company_name: str | None
    path_depth: int
    path_confidence: float
    graph_path: list[dict[str, Any]]
    criticality: int
    annual_spend_usd: float | None
    single_source: bool
    source_reliability: str
    entity_resolution_confidence: float
    corroboration_count: int
    event_type: str
    severity_signal: str | None
    effective_date: date | None


class GraphIntersectionEngine:
    """Engine for determining graph intersection between Events and tenant supply networks."""

    def __init__(self, db: AsyncSession, graph_repo: Any = None) -> None:
        self.db = db
        if graph_repo is not None:
            self.graph_repo = graph_repo
        else:
            from app.modules.graph.repository import GraphRepository

            self.graph_repo = GraphRepository(db)

    async def find_intersections_for_event(
        self,
        event: Event,
        target_org_id: uuid.UUID | None = None,
    ) -> list[GraphIntersectionMatch]:
        """
        Find all tenant supply networks that intersect the entities mentioned in this event.
        If target_org_id is specified, limits to that specific organization.
        """
        # 1. Fetch resolved entities for this event
        stmt = (
            select(EventEntity, Company)
            .outerjoin(Company, EventEntity.company_id == Company.id)
            .where(
                EventEntity.event_id == event.id,
                EventEntity.company_id.is_not(None),
            )
        )
        entity_res = await self.db.execute(stmt)
        entity_rows = entity_res.all()

        if not entity_rows:
            return []

        # 2. Derive source reliability from corroborating source records
        source_rel = await self._get_event_source_reliability(event.id)

        matches: list[GraphIntersectionMatch] = []

        for entity, company in entity_rows:
            company_id = entity.company_id
            if not company_id:
                continue

            company_name = company.legal_name if company else entity.raw_mention
            e_conf = (
                float(entity.resolution_confidence) / 100.0
                if (entity.resolution_confidence is not None and entity.resolution_confidence > 1.0)
                else (float(entity.resolution_confidence) if entity.resolution_confidence is not None else 0.85)
            )

            # 3. Find tenant orgs that contain this company in their supply graph
            org_ids = await self._find_candidate_orgs_for_company(
                company_id=company_id, target_org_id=target_org_id
            )

            for org_id in org_ids:
                # 4. Traversal: find shortest / highest confidence exposure path to tenant
                paths = await self.graph_repo.find_paths(
                    org_id=org_id,
                    from_company_id=company_id,
                    max_depth=5,
                    limit=10,
                )

                if not paths:
                    # Check if there is a direct supplier relationship with to_org_id == org_id
                    direct_edge = await self._get_direct_edge(org_id, company_id)
                    if direct_edge:
                        matches.append(
                            GraphIntersectionMatch(
                                org_id=org_id,
                                event_id=event.id,
                                company_id=company_id,
                                company_name=company_name,
                                path_depth=direct_edge.tier or 1,
                                path_confidence=float(direct_edge.confidence or 1.0),
                                graph_path=[
                                    {
                                        "from": company_name,
                                        "to_org": str(org_id),
                                        "type": direct_edge.relationship_type,
                                        "confidence": float(direct_edge.confidence or 1.0),
                                        "criticality": direct_edge.criticality or 3,
                                        "source": direct_edge.source or "user_declared",
                                    }
                                ],
                                criticality=direct_edge.criticality or 3,
                                annual_spend_usd=(
                                    float(direct_edge.annual_spend_usd)
                                    if direct_edge.annual_spend_usd is not None
                                    else None
                                ),
                                single_source=await self._is_single_source(org_id, direct_edge.category),
                                source_reliability=source_rel,
                                entity_resolution_confidence=e_conf,
                                corroboration_count=event.corroboration_count or 1,
                                event_type=event.event_type,
                                severity_signal=event.severity_signal,
                                effective_date=event.effective_date,
                            )
                        )
                    continue

                # Select best path (highest path_confidence, then lowest depth)
                best_path = paths[0]
                depth = int(best_path.get("depth", 1))
                path_conf = float(best_path.get("path_confidence", 1.0))
                criticality = int(best_path.get("criticality") or 3)
                spend = (
                    float(best_path["annual_spend_usd"])
                    if best_path.get("annual_spend_usd") is not None
                    else None
                )

                # Format graph path
                serialized_path = self._format_graph_path(best_path, company_name)
                is_single = await self._is_single_source(org_id, best_path.get("category"))

                matches.append(
                    GraphIntersectionMatch(
                        org_id=org_id,
                        event_id=event.id,
                        company_id=company_id,
                        company_name=company_name,
                        path_depth=depth,
                        path_confidence=path_conf,
                        graph_path=serialized_path,
                        criticality=criticality,
                        annual_spend_usd=spend,
                        single_source=is_single,
                        source_reliability=source_rel,
                        entity_resolution_confidence=e_conf,
                        corroboration_count=event.corroboration_count or 1,
                        event_type=event.event_type,
                        severity_signal=event.severity_signal,
                        effective_date=event.effective_date,
                    )
                )

        return matches

    async def _find_candidate_orgs_for_company(
        self,
        company_id: uuid.UUID,
        target_org_id: uuid.UUID | None,
    ) -> list[uuid.UUID]:
        """Find all organizations whose graph contains edges originating from or connecting to company_id."""
        if target_org_id:
            return [target_org_id]

        stmt = (
            select(SupplierRelationship.org_id)
            .where(
                SupplierRelationship.deleted_at.is_(None),
                SupplierRelationship.valid_to.is_(None),
                (SupplierRelationship.from_company_id == company_id)
                | (SupplierRelationship.to_company_id == company_id),
            )
            .distinct()
        )
        res = await self.db.execute(stmt)
        return [row[0] for row in res.all()]

    async def _get_direct_edge(
        self, org_id: uuid.UUID, company_id: uuid.UUID
    ) -> SupplierRelationship | None:
        """Fetch direct edge if company supplies directly to org."""
        stmt = (
            select(SupplierRelationship)
            .where(
                SupplierRelationship.org_id == org_id,
                SupplierRelationship.from_company_id == company_id,
                SupplierRelationship.deleted_at.is_(None),
                SupplierRelationship.valid_to.is_(None),
            )
            .order_by(SupplierRelationship.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def _is_single_source(
        self, org_id: uuid.UUID, category: str | None
    ) -> bool:
        """Determines if the supplier is single source in its category for this org."""
        if not category:
            return False
        stmt = (
            select(SupplierRelationship)
            .where(
                SupplierRelationship.org_id == org_id,
                SupplierRelationship.category == category,
                SupplierRelationship.deleted_at.is_(None),
                SupplierRelationship.valid_to.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        suppliers_in_cat = res.scalars().all()
        return len(suppliers_in_cat) == 1

    async def _get_event_source_reliability(self, event_id: uuid.UUID) -> str:
        """Find the highest reliability of data sources that contributed to this event."""
        stmt = (
            select(DataSource.reliability)
            .join(SourceRecord, SourceRecord.source_id == DataSource.id)
            .join(EventSourceRecord, EventSourceRecord.source_record_id == SourceRecord.id)
            .where(EventSourceRecord.event_id == event_id)
        )
        res = await self.db.execute(stmt)
        rels = [row[0] for row in res.all() if row[0]]

        if "high" in rels:
            return "high"
        elif "medium" in rels:
            return "medium"
        elif "low" in rels:
            return "low"
        return "medium"

    def _format_graph_path(
        self, path_dict: dict[str, Any], initial_name: str | None
    ) -> list[dict[str, Any]]:
        """Format raw recursive CTE result into readable graph path edges."""
        edge_id = path_dict.get("edge_id")
        return [
            {
                "from": initial_name or str(path_dict.get("from_company_id")),
                "type": path_dict.get("relationship_type", "supplies_to"),
                "to": str(path_dict.get("to_company_id") or path_dict.get("to_org_id")),
                "depth": path_dict.get("depth", 1),
                "confidence": float(path_dict.get("confidence", 1.0)),
                "source": path_dict.get("source", "graph_inference"),
                "edge_id": str(edge_id) if edge_id else None,
            }
        ]
