"""
app/modules/events/service.py — Events service for ingestion, extraction, and queries.

Architecture reference: §D.2 events, §F.1, §F.3.
Events are global reference data (not tenant-scoped).
"""

from __future__ import annotations

import uuid
from typing import Any, Sequence

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload

from agents.clustering import EventClusterManager
from agents.extraction import EventExtractionAgent
from agents.schemas.event_extraction import EventExtraction
from app.modules.events.models import Event, EventEntity, EventSourceRecord, SourceRecord

logger = structlog.get_logger(__name__)


class EventsService:
    """Service handling events search, detail retrieval, and extraction pipeline."""

    def __init__(
        self,
        cluster_manager: EventClusterManager | None = None,
        extraction_agent: EventExtractionAgent | None = None,
    ) -> None:
        self.cluster_manager = cluster_manager or EventClusterManager()
        self.extraction_agent = extraction_agent

    async def get_event_by_id(
        self, db: AsyncSession, event_id: uuid.UUID
    ) -> Event | None:
        """Fetch event with entities and linked source records."""
        stmt = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                selectinload(Event.entities),
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_events(
        self,
        db: AsyncSession,
        *,
        event_type: str | None = None,
        jurisdiction: str | None = None,
        severity: str | None = None,
        status: str = "active",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Event], int]:
        """List active global events with filtering."""
        query = select(Event).where(Event.status == status)

        if event_type:
            query = query.where(Event.event_type == event_type)
        if severity:
            query = query.where(Event.severity_signal == severity)

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # Order by newest
        query = query.order_by(Event.created_at.desc()).offset(offset).limit(limit)
        res = await db.execute(query)
        items = list(res.scalars().all())

        return items, total

    async def process_source_record_extraction(
        self,
        db: AsyncSession,
        source_record: SourceRecord,
    ) -> Event | None:
        """
        Extract event from source_record, validate, cluster, and link.
        """
        if not self.extraction_agent:
            self.extraction_agent = EventExtractionAgent(db=db)

        # Prepare text inputs
        title = source_record.title
        body_text = None
        if source_record.normalized and isinstance(source_record.normalized, dict):
            body_text = (
                source_record.normalized.get("body")
                or source_record.normalized.get("content")
                or source_record.normalized.get("abstract")
                or source_record.normalized.get("summary")
            )

        extraction_res = await self.extraction_agent.extract(
            title=title,
            body_text=body_text,
            source_url=source_record.canonical_url,
            source_type=source_record.source_type or "live",
            published_date=str(source_record.published_date) if source_record.published_date else None,
            source_reliability=source_record.reliability or "high",
        )

        if extraction_res.status == "needs_review" or not extraction_res.extraction:
            source_record.processing_status = "needs_review"
            await db.flush()
            logger.info(
                "source_record_marked_needs_review",
                source_record_id=str(source_record.id),
                errors=extraction_res.validation_errors,
            )
            return None

        extraction = extraction_res.extraction
        if not extraction.is_relevant:
            source_record.processing_status = "ignored_not_relevant"
            await db.flush()
            return None

        # Cluster and link
        event, created = await self.cluster_manager.process_async(
            db=db,
            extraction=extraction,
            source_record_id=source_record.id,
            model_name=extraction_res.model_used,
            prompt_version=extraction_res.prompt_version,
        )

        source_record.processing_status = "processed"
        await db.flush()
        return event
