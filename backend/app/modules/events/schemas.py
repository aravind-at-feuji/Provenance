"""
app/modules/events/schemas.py — Pydantic schemas for events and source records.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class EventEntityOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    company_id: uuid.UUID | None = None
    raw_mention: str
    role: str | None = None
    resolution_confidence: int | None = None
    resolution_method: str | None = None
    evidence_span: dict[str, Any] | None = None


class EventSourceRecordOut(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    external_id: str | None = None
    canonical_url: str | None = None
    title: str | None = None
    published_date: date | None = None
    retrieved_at: datetime
    source_type: str | None = None
    reliability: str | None = None


class EventOut(BaseModel):
    id: uuid.UUID
    event_cluster_key: str
    event_type: str
    jurisdictions: list[str] = Field(default_factory=list)
    affected_materials: list[str] = Field(default_factory=list)
    affected_hs_codes: list[str] = Field(default_factory=list)
    effective_date: date | None = None
    expiry_date: date | None = None
    published_date: date | None = None
    summary: str
    severity_signal: str | None = None
    confidence: int | None = None
    corroboration_count: int = 1
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class EventDetailOut(EventOut):
    entities: list[EventEntityOut] = Field(default_factory=list)
    source_records: list[EventSourceRecordOut] = Field(default_factory=list)


class EventListOut(BaseModel):
    items: list[EventOut]
    next_cursor: str | None = None
    total_count: int | None = None
