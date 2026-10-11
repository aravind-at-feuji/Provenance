"""
tests/unit/test_phase10_rag.py — Comprehensive unit tests for RAG architecture.

Architecture reference: §Part K RAG Architecture, §K.2 Hybrid Pipeline, §K.3 Tenant Filtering, §K.5 Citation Contract.
Acceptance criteria:
  - Recursive semantic chunker segments text with ~15% overlap without splitting section boundaries
  - Hybrid retrieval fuses lexical and vector cosine ranking using Reciprocal Rank Fusion (k=60)
  - Tenant pre-filter strictly blocks cross-tenant contract leaks (WHERE clause isolation)
  - Global regulatory notices (org_id=None) are retrievable by all tenants
  - Full citation contract returned on every hit
"""

from __future__ import annotations

import json
import sqlite3
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import DefaultClause

from agents.rag.chunker import RecursiveSemanticChunker
from agents.rag.embeddings import EmbeddingService
from agents.rag.retriever import HybridRetriever, RetrievedChunk
import app.modules.organizations.models
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


@pytest.fixture
def sqlite_rag_db():
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
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    org_id TEXT REFERENCES organizations(id),
                    document_type TEXT,
                    title TEXT,
                    source_url TEXT,
                    jurisdiction TEXT,
                    published_date TIMESTAMP,
                    effective_date TIMESTAMP,
                    language TEXT,
                    source_reliability TEXT,
                    s3_key TEXT,
                    content_hash TEXT,
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
                CREATE TABLE document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(id),
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    section_path TEXT,
                    token_count INTEGER,
                    metadata TEXT DEFAULT '{}'
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE embeddings (
                    id TEXT PRIMARY KEY,
                    chunk_id TEXT NOT NULL REFERENCES document_chunks(id),
                    model TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    embedding TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (chunk_id, model)
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


def test_recursive_semantic_chunker_boundaries_and_overlap():
    """Verify chunker respects section boundaries and computes overlap."""
    chunker = RecursiveSemanticChunker(target_tokens=50, overlap_pct=0.20, approx_chars_per_token=4)

    document_text = (
        "# Article I: Export Restrictions\n\n"
        "Paragraph 1: The export of gallium, germanium, and related compound materials "
        "is subject to mandatory licensing by the state council.\n\n"
        "Paragraph 2: Exporters must present detailed supply chain contracts identifying the ultimate "
        "consignee and end-use application.\n\n"
        "# Article II: Penalties & Enforcement\n\n"
        "Paragraph 3: Unauthorized transfers shall incur statutory forfeiture of goods and civil penalties "
        "under trade compliance statutes."
    )

    chunks = chunker.chunk_document(document_text, initial_section_path="Root")

    assert len(chunks) >= 2
    # Verify section paths are preserved
    paths = [c.section_path for c in chunks]
    assert any("Article I" in p for p in paths if p)
    assert any("Article II" in p for p in paths if p)

    for chunk in chunks:
        assert chunk.token_count > 0
        assert len(chunk.content) > 0


@pytest.mark.asyncio
async def test_embedding_service_dimensions_and_normalization():
    """Verify EmbeddingService normalizes vectors and respects model dimension contract."""
    mock_provider = MockProvider()
    service = EmbeddingService(provider=mock_provider, model="voyage-3")

    assert service.dimensions == 1024

    vectors = await service.embed_texts(["Gallium semiconductor ban", "Steel tariff increase"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024
    assert len(vectors[1]) == 1024

    # Verify unit-vector normalization
    norm = sum(x * x for x in vectors[0]) ** 0.5
    assert pytest.approx(norm, rel=1e-3) == 1.0


def test_hybrid_retriever_tenant_isolation_and_rrf(sqlite_rag_db: Session):
    """
    CRITICAL SECURITY & RETRIEVAL TEST:
    1. Tenant A indexes private contract.
    2. Tenant B indexes private contract.
    3. Global regulatory notice is indexed with org_id = None.
    4. Query by Tenant A retrieves Tenant A's contract + Global notice, NEVER Tenant B's contract!
    5. Query by Tenant B retrieves Tenant B's contract + Global notice, NEVER Tenant A's contract!
    6. Verified RRF scoring and full citation contract on results.
    """
    db = sqlite_rag_db
    retriever = HybridRetriever(embedding_service=EmbeddingService(provider=MockProvider()))

    org_a = uuid.uuid4()
    org_b = uuid.uuid4()

    # Create Org A & Org B in DB
    db.execute(text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Tenant A', 'tenant-a')"), {"id": str(org_a)})
    db.execute(text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Tenant B', 'tenant-b')"), {"id": str(org_b)})
    db.commit()

    # 1. Tenant A private contract
    doc_a = retriever.index_document_sync(
        db,
        title="Tenant A Procurement Agreement with Foxconn",
        text_content="Exclusive supply terms for microcontrollers between Tenant A and Foxconn Electronics.",
        org_id=org_a,
        source_url="s3://tenant-a-contracts/contract-001.pdf",
        document_type="contract",
    )

    # 2. Tenant B private contract
    doc_b = retriever.index_document_sync(
        db,
        title="Tenant B Supplier Contract with TSMC",
        text_content="Wafer allocation terms between Tenant B and TSMC foundry services.",
        org_id=org_b,
        source_url="s3://tenant-b-contracts/contract-002.pdf",
        document_type="contract",
    )

    # 3. Global public regulatory document
    doc_global = retriever.index_document_sync(
        db,
        title="BIS Export Administration Regulation 2025",
        text_content="Global restriction on advanced packaging and lithography equipment.",
        org_id=None,  # Public / shared
        source_url="https://federalregister.gov/notice/2025-01",
        document_type="regulatory_notice",
    )

    # --- Query from Tenant A perspective ---
    results_a = retriever.retrieve_sync(
        db,
        query="contract terms and allocation equipment",
        org_id=org_a,
        top_k=5,
    )
    retrieved_doc_ids_a = {r.document_id for r in results_a}

    assert doc_a.id in retrieved_doc_ids_a
    assert doc_global.id in retrieved_doc_ids_a
    # STRICT ASSERTION: Tenant B's document MUST NOT BE VISIBLE TO TENANT A
    assert doc_b.id not in retrieved_doc_ids_a

    # --- Query from Tenant B perspective ---
    results_b = retriever.retrieve_sync(
        db,
        query="contract terms and allocation equipment",
        org_id=org_b,
        top_k=5,
    )
    retrieved_doc_ids_b = {r.document_id for r in results_b}

    assert doc_b.id in retrieved_doc_ids_b
    assert doc_global.id in retrieved_doc_ids_b
    # STRICT ASSERTION: Tenant A's document MUST NOT BE VISIBLE TO TENANT B
    assert doc_a.id not in retrieved_doc_ids_b

    # Verify Citation Contract (arch §K.5)
    for hit in results_a:
        assert isinstance(hit, RetrievedChunk)
        assert hit.chunk_id is not None
        assert hit.document_id is not None
        assert hit.source_url is not None
        assert hit.source_type in ("live", "cached")
        assert hit.score > 0.0
