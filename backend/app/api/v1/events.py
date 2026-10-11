"""
/v1/events — Global regulatory and supply-chain disruption events.

Architecture reference: §N.1, §D.2 events.
Endpoints:
  GET /events      — list global events with filtering
  GET /events/{id} — get event detail with entities and corroborating source records
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.base import CurrentUser
from app.core.deps import require_permission
from app.core.errors import not_found
from app.db.session import get_db
from app.modules.events.schemas import (
    EventDetailOut,
    EventEntityOut,
    EventListOut,
    EventOut,
)
from app.modules.events.service import EventsService

router = APIRouter(prefix="/events", tags=["events"])


def _service() -> EventsService:
    return EventsService()


@router.get("", response_model=EventListOut)
async def list_events(
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    event_type: Annotated[str | None, Query()] = None,
    jurisdiction: Annotated[str | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str, Query(alias="status")] = "active",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> EventListOut:
    """List global disruption events with filters."""
    service = _service()
    items, total = await service.list_events(
        db,
        event_type=event_type,
        jurisdiction=jurisdiction,
        severity=severity,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    out_items = [
        EventOut(
            id=item.id,
            event_cluster_key=item.event_cluster_key,
            event_type=item.event_type,
            jurisdictions=item.jurisdictions or [],
            affected_materials=item.affected_materials or [],
            affected_hs_codes=item.affected_hs_codes or [],
            effective_date=item.effective_date,
            expiry_date=item.expiry_date,
            published_date=item.published_date,
            summary=item.summary,
            severity_signal=item.severity_signal,
            confidence=item.confidence,
            corroboration_count=item.corroboration_count,
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]

    return EventListOut(
        items=out_items,
        total_count=total,
    )


@router.get("/{id}", response_model=EventDetailOut)
async def get_event(
    id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_permission("alerts:read"))],
    db: AsyncSession = Depends(get_db),
) -> EventDetailOut:
    """Get single event by ID with extracted entities and corroborating source records."""
    service = _service()
    item = await service.get_event_by_id(db, id)
    if not item:
        raise not_found(f"Event {id} not found")

    entities_out = [
        EventEntityOut(
            id=e.id,
            event_id=e.event_id,
            company_id=e.company_id,
            raw_mention=e.raw_mention,
            role=e.role,
            resolution_confidence=e.resolution_confidence,
            resolution_method=e.resolution_method,
            evidence_span=e.evidence_span,
        )
        for e in item.entities
    ]

    return EventDetailOut(
        id=item.id,
        event_cluster_key=item.event_cluster_key,
        event_type=item.event_type,
        jurisdictions=item.jurisdictions or [],
        affected_materials=item.affected_materials or [],
        affected_hs_codes=item.affected_hs_codes or [],
        effective_date=item.effective_date,
        expiry_date=item.expiry_date,
        published_date=item.published_date,
        summary=item.summary,
        severity_signal=item.severity_signal,
        confidence=item.confidence,
        corroboration_count=item.corroboration_count,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        entities=entities_out,
        source_records=[],
    )
