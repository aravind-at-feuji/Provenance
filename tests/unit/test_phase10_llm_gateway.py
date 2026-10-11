"""
tests/unit/test_phase10_llm_gateway.py — Unit tests for LLMGateway, token budget, caching, and audit runs.

Architecture reference: §C.5, §J.3, §Part Z Phase 10.
Acceptance criteria:
  - Cache hit on identical content avoids model call
  - Budget rejection works (BudgetExceededError)
  - Task model routing works correctly
  - agent_runs table audit logs persisted
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel
from sqlalchemy import create_engine, select, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import DefaultClause

from agents.extraction import EventExtractionAgent
from agents.gateway import BudgetExceededError, LLMGateway
from agents.schemas.event_extraction import EventExtraction, EventTypeEnum
import app.modules.organizations.models
from app.modules.ai.models import AgentRun
from app.modules.ai.provider import MockProvider

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


class SimpleOutput(BaseModel):
    status: str
    score: float


class AsyncSessionMockAdapter:
    """Async session adapter wrapping synchronous SQLite session for testing."""

    def __init__(self, sync_session: Session) -> None:
        self._s = sync_session

    async def execute(self, statement, *args, **kwargs):
        return self._s.execute(statement, *args, **kwargs)

    def add(self, instance):
        self._s.add(instance)

    async def flush(self):
        self._s.flush()

    async def commit(self):
        self._s.commit()


@pytest.fixture
def sqlite_agent_runs_db():
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE agent_runs (
                    id TEXT PRIMARY KEY,
                    org_id TEXT REFERENCES organizations(id),
                    agent_name TEXT NOT NULL,
                    workflow_run_id TEXT,
                    input_ref TEXT,
                    output_ref TEXT,
                    model TEXT,
                    prompt_version TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    cost_usd REAL,
                    latency_ms INTEGER,
                    status TEXT,
                    error TEXT,
                    langfuse_trace_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        )

    session_cls = sessionmaker(bind=engine)
    session = session_cls()
    try:
        yield AsyncSessionMockAdapter(session)
    finally:
        session.close()


@pytest.mark.asyncio
async def test_cache_hit_on_identical_content_avoids_provider_call():
    """Verify content-hash cache returns stored result without invoking AI provider."""
    mock_provider = MockProvider()
    gateway = LLMGateway(provider=mock_provider)

    prompt = "Classify this supply chain event: US export restriction on quantum chips."

    # Call 1: Cache Miss
    res1 = await gateway.execute_structured(
        task="extraction",
        prompt=prompt,
        schema=SimpleOutput,
        use_cache=True,
    )
    assert mock_provider.call_count == 1
    assert isinstance(res1, SimpleOutput)

    # Call 2: Identical prompt -> Cache Hit
    res2 = await gateway.execute_structured(
        task="extraction",
        prompt=prompt,
        schema=SimpleOutput,
        use_cache=True,
    )
    # Provider call count MUST NOT increment
    assert mock_provider.call_count == 1
    assert res2.status == res1.status
    assert res2.score == res1.score

    # Call 3: Different prompt -> Cache Miss
    res3 = await gateway.execute_structured(
        task="extraction",
        prompt="Different event text",
        schema=SimpleOutput,
        use_cache=True,
    )
    assert mock_provider.call_count == 2


@pytest.mark.asyncio
async def test_tenant_monthly_budget_rejection():
    """Verify tenant exceeding monthly token budget is rejected before calling model."""
    mock_provider = MockProvider()
    gateway = LLMGateway(provider=mock_provider)
    org_id = uuid.uuid4()

    # Set strict tenant monthly token budget of 2,000 tokens
    gateway.set_tenant_budget(org_id, budget=2000)
    gateway.reset_tenant_usage(org_id)

    # Call 1: prompt length 400 chars (~100 tokens), estimated ~100 tokens
    res1 = await gateway.execute_structured(
        task="extraction",
        prompt="A" * 400,
        schema=SimpleOutput,
        org_id=org_id,
        use_cache=False,
    )
    assert mock_provider.call_count == 1
    used_after_1 = gateway.get_tenant_usage(org_id)
    assert used_after_1 > 0

    # Simulate accumulated tokens reaching 2,500 (exceeding 2,000 budget)
    gateway._shared_tenant_usage[org_id] = 2500

    # Call 2: Must be rejected with BudgetExceededError BEFORE provider call
    with pytest.raises(BudgetExceededError) as exc_info:
        await gateway.execute_structured(
            task="extraction",
            prompt="Another prompt",
            schema=SimpleOutput,
            org_id=org_id,
            use_cache=False,
        )

    # Provider call count must still be 1 (never called when budget exceeded)
    assert mock_provider.call_count == 1
    assert exc_info.value.org_id == org_id
    assert exc_info.value.budget == 2000
    assert exc_info.value.used == 2500


@pytest.mark.asyncio
async def test_agent_run_audit_logged_to_database(sqlite_agent_runs_db):
    """Verify agent execution writes audit row to agent_runs table."""
    mock_provider = MockProvider()
    db = sqlite_agent_runs_db
    gateway = LLMGateway(db=db, provider=mock_provider)
    org_id = uuid.uuid4()
    run_id = uuid.uuid4()

    result = await gateway.execute_structured(
        task="extraction",
        prompt="Audit test event extraction",
        schema=SimpleOutput,
        org_id=org_id,
        workflow_run_id=run_id,
        prompt_version="v1",
        use_cache=False,
    )

    # Check agent_runs table
    stmt = select(AgentRun).where(AgentRun.org_id == org_id)
    res = await db.execute(stmt)
    records = res.scalars().all()
    assert len(records) == 1

    run_row = records[0]
    assert run_row.agent_name == "extraction"
    assert run_row.workflow_run_id == run_id
    assert run_row.status == "success"
    assert run_row.prompt_tokens > 0
    assert run_row.completion_tokens > 0
    assert run_row.latency_ms >= 0


def test_task_model_routing():
    """Verify task strings correctly route to configured model names."""
    gateway = LLMGateway(provider=MockProvider())

    assert gateway.resolve_model_for_task("event_extraction") != ""
    assert gateway.resolve_model_for_task("entity_resolution") != ""
    assert gateway.resolve_model_for_task("alert_explanation") != ""
    assert gateway.resolve_model_for_task("investigation") != ""


@pytest.mark.asyncio
async def test_schema_failure_routes_to_needs_review():
    """Verify schema-failure after max retries produces needs_review, never an invalid event."""
    mock_provider = MockProvider()
    # Script provider to return unparseable garbage text on all attempts
    mock_provider.add_response("INVALID NON JSON GARBAGE")
    mock_provider.add_response("STILL BROKEN GARBAGE")
    mock_provider.add_response("FINAL BROKEN GARBAGE")

    gateway = LLMGateway(provider=mock_provider)
    agent = EventExtractionAgent(gateway=gateway)

    result = await agent.extract(
        title="Sanctions announcement",
        body_text="Treasury designated Entity X under Executive Order 14024.",
        max_retries=2,
    )

    # Must be marked needs_review and extraction must be None (never a corrupt partial event)
    assert result.status == "needs_review"
    assert result.extraction is None
    assert len(result.validation_errors) > 0
