"""
agents/schemas/event_extraction.py — Structured output schema for Event Extraction Agent (Agent 1).

Architecture reference: §J.2 Agent 1, §F.1, §Q.7.
This schema enforces:
  - Closed event_type enum (no free text)
  - ISO-3166-1 alpha-2 jurisdiction codes
  - Exact evidence spans with character offsets for verification
  - Role-tagged entity mentions
  - Character-limited summary in our own paraphrase
  - Discrete severity signal and bounded confidence
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class EventTypeEnum(str, Enum):
    """Closed enum of supported supply-chain & regulatory event types (arch §8.4 / §9.1)."""

    SANCTION_DESIGNATION = "sanction_designation"
    EXPORT_PROHIBITION = "export_prohibition"
    EXPORT_RESTRICTION = "export_restriction"
    QUOTA_IMPOSITION = "quota_imposition"
    INSOLVENCY_FILING = "insolvency_filing"
    CREDIT_DOWNGRADE = "credit_downgrade"
    TARIFF_CHANGE = "tariff_change"
    FACILITY_DISRUPTION = "facility_disruption"
    REGULATORY_PROPOSAL = "regulatory_proposal"
    GOING_CONCERN_DISCLOSURE = "going_concern_disclosure"
    MATERIAL_ADVERSE_EVENT = "material_adverse_event"
    TRADE_RESTRICTION = "trade_restriction"
    FORCE_MAJEURE = "force_majeure"


class TextSpan(BaseModel):
    """
    Character span in source text providing direct factual evidence.
    Offsets MUST resolve to verbatim source text (arch §J.2, §Q.7).
    """

    start: int = Field(ge=0, description="Start character offset in source text")
    end: int = Field(gt=0, description="End character offset in source text")
    text: str = Field(description="Exact verbatim substring from source text")


class EntityMention(BaseModel):
    """Company or entity mentioned in source text with its structural role."""

    name: str = Field(description="Name of the mentioned company or organization")
    role: Literal["subject", "affected", "issuer"] = Field(
        default="affected",
        description="Role in event: subject of sanction/distress, affected party, or regulatory issuer",
    )
    text_span: TextSpan = Field(description="Exact character span in source text")


class EventExtraction(BaseModel):
    """
    Extracted structured event schema.
    Tool-less extraction strictly constrained to structured schema.
    """

    is_relevant: bool = Field(
        default=True,
        description="True if record describes a real supply-chain, regulatory, trade, sanctions, or material disruption event",
    )
    event_type: EventTypeEnum = Field(
        default=EventTypeEnum.REGULATORY_PROPOSAL,
        description="Closed enum classification of event type",
    )
    jurisdictions: list[str] = Field(
        default_factory=list,
        description="ISO-3166-1 alpha-2 country codes affected by or issuing the event (e.g. ['US', 'IN', 'CN'])",
    )
    affected_entities: list[EntityMention] = Field(
        default_factory=list,
        description="Companies or entities directly mentioned in the event",
    )
    affected_materials: list[str] = Field(
        default_factory=list,
        description="Commodities, raw materials, chemicals, minerals, or parts impacted",
    )
    affected_hs_codes: list[str] = Field(
        default_factory=list,
        description="Harmonized System (HS) tariff codes if mentioned",
    )
    effective_date: date | None = Field(
        default=None,
        description="Date when restriction, sanction, or disruption takes effect",
    )
    expiry_date: date | None = Field(
        default=None,
        description="Date when restriction expires if specified",
    )
    severity_signal: Literal["low", "moderate", "high", "severe"] = Field(
        default="moderate",
        description="Preliminary qualitative severity signal",
    )
    summary: str = Field(
        max_length=500,
        description="Neutral factual paraphrase of the event in our own words (never verbatim source text copy-paste)",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score between 0.0 and 1.0",
    )
    evidence_spans: list[TextSpan] = Field(
        default_factory=list,
        description="Character spans in source text providing direct factual evidence",
    )


class EventExtractionResult(BaseModel):
    """Result wrapper including status, review flags, and validation error messages."""

    extraction: EventExtraction | None = None
    status: Literal["success", "needs_review", "extraction_failed"] = "success"
    validation_errors: list[str] = Field(default_factory=list)
    raw_prompt: str | None = None
    model_used: str | None = None
    prompt_version: str = "v1"
