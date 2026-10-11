"""
agents/clustering.py — Semantic event clustering & multi-source deduplication.

Architecture reference: §F.3 Layer 3 Semantic dedupe across sources, §M.1 events table.
"40 articles about one ban produce one event with corroboration_count ≈ 40,
rather than creating 40 events and 40 alerts."
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Sequence

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from agents.schemas.event_extraction import EventExtraction
from app.modules.events.models import Event, EventEntity, EventSourceRecord

logger = structlog.get_logger(__name__)


def compute_event_cluster_key(
    event_type: str,
    jurisdictions: Sequence[str],
    affected_materials: Sequence[str],
    effective_date: date | str | None = None,
) -> str:
    """
    Compute deterministic event_cluster_key for cross-source semantic deduplication.
    Normalized on (event_type, jurisdictions, normalized_materials, effective_date).
    """
    norm_type = str(event_type).lower().strip()
    norm_juris = ",".join(sorted(set(j.upper().strip() for j in jurisdictions if j.strip())))
    norm_materials = ",".join(
        sorted(set(m.lower().strip() for m in affected_materials if m.strip()))
    )
    norm_date = str(effective_date).strip() if effective_date else "no_date"

    composite = f"{norm_type}|{norm_juris}|{norm_materials}|{norm_date}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()[:32]


class EventClusterManager:
    """
    Manages semantic clustering of incoming extracted events into deduplicated global Event entities.
    """

    def __init__(self, cluster_window_hours: int = 72) -> None:
        self.cluster_window_hours = cluster_window_hours

    def process_sync(
        self,
        db: Session,
        extraction: EventExtraction,
        source_record_id: uuid.UUID,
        model_name: str | None = None,
        prompt_version: str = "v1",
    ) -> tuple[Event, bool]:
        """
        Synchronous processing for Celery sync workers and unit test runner.
        Returns: (event, was_created)
        """
        cluster_key = compute_event_cluster_key(
            event_type=extraction.event_type.value if hasattr(extraction.event_type, "value") else str(extraction.event_type),
            jurisdictions=extraction.jurisdictions,
            affected_materials=extraction.affected_materials,
            effective_date=extraction.effective_date,
        )

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.cluster_window_hours)

        # 1. Search for active matching event within clustering time window
        stmt = (
            select(Event)
            .where(
                Event.event_cluster_key == cluster_key,
                Event.status == "active",
                Event.created_at >= cutoff,
            )
            .order_by(Event.created_at.desc())
        )
        existing_event = db.execute(stmt).scalars().first()

        if existing_event:
            # 2. Corroborate existing event
            existing_event.corroboration_count += 1

            # Check if source record already attached
            link_stmt = select(EventSourceRecord).where(
                EventSourceRecord.event_id == existing_event.id,
                EventSourceRecord.source_record_id == source_record_id,
            )
            if not db.execute(link_stmt).scalars().first():
                link = EventSourceRecord(
                    event_id=existing_event.id,
                    source_record_id=source_record_id,
                )
                db.add(link)

            db.flush()
            logger.info(
                "event_corroborated",
                event_id=str(existing_event.id),
                cluster_key=cluster_key,
                corroboration_count=existing_event.corroboration_count,
            )
            return existing_event, False

        # 3. Create new Event
        event_id = uuid.uuid4()
        conf_int = int(round(extraction.confidence * 100)) if extraction.confidence is not None else 85

        new_event = Event(
            id=event_id,
            event_cluster_key=cluster_key,
            event_type=extraction.event_type.value if hasattr(extraction.event_type, "value") else str(extraction.event_type),
            jurisdictions=extraction.jurisdictions,
            affected_materials=extraction.affected_materials,
            affected_hs_codes=extraction.affected_hs_codes,
            effective_date=extraction.effective_date,
            expiry_date=extraction.expiry_date,
            summary=extraction.summary,
            severity_signal=extraction.severity_signal,
            confidence=conf_int,
            corroboration_count=1,
            status="active",
            extracted_by_model=model_name,
            prompt_version=prompt_version,
        )
        db.add(new_event)

        # Link source record
        link = EventSourceRecord(
            event_id=event_id,
            source_record_id=source_record_id,
        )
        db.add(link)

        # Add entity mentions
        for mention in extraction.affected_entities:
            entity_row = EventEntity(
                id=uuid.uuid4(),
                event_id=event_id,
                company_id=None,  # Resolved downstream in Phase 9 cascade
                raw_mention=mention.name,
                role=mention.role,
                resolution_confidence=None,
                resolution_method=None,
                evidence_span=mention.text_span.model_dump(),
            )
            db.add(entity_row)

        db.flush()
        logger.info(
            "event_created_from_cluster",
            event_id=str(event_id),
            cluster_key=cluster_key,
        )
        return new_event, True

    async def process_async(
        self,
        db: AsyncSession,
        extraction: EventExtraction,
        source_record_id: uuid.UUID,
        model_name: str | None = None,
        prompt_version: str = "v1",
    ) -> tuple[Event, bool]:
        """
        Asynchronous processing for async FastAPI pipelines.
        Returns: (event, was_created)
        """
        cluster_key = compute_event_cluster_key(
            event_type=extraction.event_type.value if hasattr(extraction.event_type, "value") else str(extraction.event_type),
            jurisdictions=extraction.jurisdictions,
            affected_materials=extraction.affected_materials,
            effective_date=extraction.effective_date,
        )

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.cluster_window_hours)

        stmt = (
            select(Event)
            .where(
                Event.event_cluster_key == cluster_key,
                Event.status == "active",
                Event.created_at >= cutoff,
            )
            .order_by(Event.created_at.desc())
        )
        res = await db.execute(stmt)
        existing_event = res.scalars().first()

        if existing_event:
            existing_event.corroboration_count += 1
            link_stmt = select(EventSourceRecord).where(
                EventSourceRecord.event_id == existing_event.id,
                EventSourceRecord.source_record_id == source_record_id,
            )
            link_res = await db.execute(link_stmt)
            if not link_res.scalars().first():
                link = EventSourceRecord(
                    event_id=existing_event.id,
                    source_record_id=source_record_id,
                )
                db.add(link)

            await db.flush()
            return existing_event, False

        event_id = uuid.uuid4()
        conf_int = int(round(extraction.confidence * 100)) if extraction.confidence is not None else 85

        new_event = Event(
            id=event_id,
            event_cluster_key=cluster_key,
            event_type=extraction.event_type.value if hasattr(extraction.event_type, "value") else str(extraction.event_type),
            jurisdictions=extraction.jurisdictions,
            affected_materials=extraction.affected_materials,
            affected_hs_codes=extraction.affected_hs_codes,
            effective_date=extraction.effective_date,
            expiry_date=extraction.expiry_date,
            summary=extraction.summary,
            severity_signal=extraction.severity_signal,
            confidence=conf_int,
            corroboration_count=1,
            status="active",
            extracted_by_model=model_name,
            prompt_version=prompt_version,
        )
        db.add(new_event)

        link = EventSourceRecord(
            event_id=event_id,
            source_record_id=source_record_id,
        )
        db.add(link)

        for mention in extraction.affected_entities:
            entity_row = EventEntity(
                id=uuid.uuid4(),
                event_id=event_id,
                company_id=None,
                raw_mention=mention.name,
                role=mention.role,
                resolution_confidence=None,
                resolution_method=None,
                evidence_span=mention.text_span.model_dump(),
            )
            db.add(entity_row)

        await db.flush()
        return new_event, True
