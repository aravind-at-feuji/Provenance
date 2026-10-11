"""
tests/unit/test_phase10_semantic_clustering.py — Semantic event clustering and deduplication tests.

Architecture reference: §F.3 Layer 3, §Phase 10 Acceptance Criteria.
Acceptance criterion: "40 articles about one ban produce ONE event with corroboration_count ≈ 40."
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import DefaultClause

from agents.clustering import EventClusterManager, compute_event_cluster_key
from agents.schemas.event_extraction import (
    EntityMention,
    EventExtraction,
    EventTypeEnum,
    TextSpan,
)
from app.modules.events.models import Event, EventEntity, EventSourceRecord

# Setup SQLite compatibility for PostgreSQL dialect types in unit tests
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(DefaultClause, "sqlite")
def compile_default_sqlite(element, compiler, **kw):
    return ""


@pytest.fixture
def sqlite_events_db():
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE events (
                    id TEXT PRIMARY KEY,
                    event_cluster_key TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    jurisdictions TEXT NOT NULL,
                    affected_materials TEXT NOT NULL,
                    affected_hs_codes TEXT NOT NULL,
                    effective_date DATE,
                    expiry_date DATE,
                    published_date DATE,
                    summary TEXT NOT NULL,
                    severity_signal TEXT,
                    confidence INTEGER,
                    corroboration_count INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    superseded_by TEXT,
                    extracted_by_model TEXT,
                    prompt_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE event_source_records (
                    event_id TEXT NOT NULL,
                    source_record_id TEXT NOT NULL,
                    PRIMARY KEY (event_id, source_record_id)
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE event_entities (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    company_id TEXT,
                    raw_mention TEXT NOT NULL,
                    role TEXT,
                    resolution_confidence INTEGER,
                    resolution_method TEXT,
                    evidence_span TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT
                );
                """
            )
        )

    session_cls = sessionmaker(bind=engine)
    session = session_cls()
    try:
        yield session
    finally:
        session.close()


def test_compute_event_cluster_key_deterministic_and_normalized():
    """Verify cluster key is stable, case-insensitive, and order-insensitive."""
    key1 = compute_event_cluster_key(
        event_type="export_prohibition",
        jurisdictions=["CN", "cn"],
        affected_materials=["gallium", "germanium"],
        effective_date=date(2025, 8, 1),
    )
    key2 = compute_event_cluster_key(
        event_type="EXPORT_PROHIBITION ",
        jurisdictions=["cn"],
        affected_materials=["germanium", "Gallium "],
        effective_date=date(2025, 8, 1),
    )
    # Different material order or case must produce identical key
    assert key1 == key2
    assert len(key1) == 32


def test_40_articles_produce_one_event_with_corroboration_40(sqlite_events_db: Session):
    """
    CRITICAL ACCEPTANCE TEST:
    40 news articles from different outlets reporting the same export ban produce
    ONE event in the database with corroboration_count = 40.
    """
    db = sqlite_events_db
    cluster_mgr = EventClusterManager(cluster_window_hours=72)

    # 40 distinct source records from different news publishers
    media_outlets = [
        "Reuters", "Bloomberg", "Financial Times", "Wall Street Journal", "Caixin",
        "Xinhua", "South China Morning Post", "Nikkei Asia", "The Hindu", "Economic Times",
        "Associated Press", "BBC News", "AFP", "Kyodo News", "Yonhap",
        "Straits Times", "Le Monde", "Handelsblatt", "CNBC", "MarketWatch",
        "Mining.com", "Metal Bulletin", "Argus Media", "Platts", "Fastmarkets",
        "Chemical Week", "Supply Chain Dive", "Electronics Weekly", "EE Times", "Tom's Hardware",
        "The Register", "Ars Technica", "Semiconductor Today", "Automotive News", "Defense News",
        "Nikkei Tech", "Business Standard", "Mint", "Globe and Mail", "Taipei Times",
    ]
    assert len(media_outlets) == 40

    source_record_ids = [uuid.uuid4() for _ in range(40)]

    for idx, outlet in enumerate(media_outlets):
        # Every outlet phrases their summary slightly differently, but the underlying core facts are identical
        extraction = EventExtraction(
            is_relevant=True,
            event_type=EventTypeEnum.EXPORT_PROHIBITION,
            jurisdictions=["CN"],
            affected_materials=["gallium", "germanium"],
            effective_date=date(2025, 8, 1),
            summary=f"Report from {outlet}: China bans export of critical semiconductor minerals gallium and germanium.",
            confidence=0.90,
            evidence_spans=[
                TextSpan(start=0, end=15, text="Report from " + outlet[:3])
            ],
        )

        event, was_created = cluster_mgr.process_sync(
            db=db,
            extraction=extraction,
            source_record_id=source_record_ids[idx],
            model_name="gemini-1.5-flash",
        )

        if idx == 0:
            assert was_created is True
        else:
            assert was_created is False

    # VERIFICATION:
    # 1. Exactly ONE event exists in the database
    all_events = db.execute(select(Event)).scalars().all()
    assert len(all_events) == 1, f"Expected exactly 1 event, but found {len(all_events)}"

    canonical_event = all_events[0]
    # 2. Corroboration count is exactly 40
    assert canonical_event.corroboration_count == 40
    assert canonical_event.event_type == "export_prohibition"
    assert canonical_event.jurisdictions == ["CN"]
    assert "gallium" in canonical_event.affected_materials
    assert "germanium" in canonical_event.affected_materials

    # 3. Exactly 40 corroborating source record links exist
    all_links = db.execute(select(EventSourceRecord)).scalars().all()
    assert len(all_links) == 40
    linked_src_ids = {link.source_record_id for link in all_links}
    for src_id in source_record_ids:
        assert src_id in linked_src_ids


def test_distinct_events_are_not_clustered_together(sqlite_events_db: Session):
    """Verify that genuinely different events generate distinct Event rows."""
    db = sqlite_events_db
    cluster_mgr = EventClusterManager(cluster_window_hours=72)

    # Event 1: China export prohibition on gallium
    e1 = EventExtraction(
        is_relevant=True,
        event_type=EventTypeEnum.EXPORT_PROHIBITION,
        jurisdictions=["CN"],
        affected_materials=["gallium"],
        effective_date=date(2025, 8, 1),
        summary="China restricts gallium exports.",
    )
    event1, created1 = cluster_mgr.process_sync(db, e1, uuid.uuid4())
    assert created1 is True

    # Event 2: US tariff change on steel (different type, country, material)
    e2 = EventExtraction(
        is_relevant=True,
        event_type=EventTypeEnum.TARIFF_CHANGE,
        jurisdictions=["US"],
        affected_materials=["steel"],
        effective_date=date(2025, 9, 1),
        summary="US increases import tariff on foreign steel products.",
    )
    event2, created2 = cluster_mgr.process_sync(db, e2, uuid.uuid4())
    assert created2 is True

    # Total events in DB must be 2
    events_in_db = db.execute(select(Event)).scalars().all()
    assert len(events_in_db) == 2
    assert event1.id != event2.id
    assert event1.event_cluster_key != event2.event_cluster_key
