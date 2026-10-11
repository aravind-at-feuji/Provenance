"""
app/modules/risk/schemas.py — Pydantic schemas for risk scoring, assessments, and models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FactorBreakdown(BaseModel):
    event_severity: float = Field(ge=0.0, le=1.0)
    dependency_strength: float = Field(ge=0.0, le=1.0)
    evidence_quality: float = Field(ge=0.0, le=1.0)
    urgency_multiplier: float = Field(ge=0.0, le=0.50)
    exposure_multiplier: float = Field(ge=0.80, le=1.50)
    inputs: dict[str, Any] = Field(default_factory=dict)


class RiskAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    event_id: uuid.UUID
    company_id: uuid.UUID
    impact_score: float
    severity_band: str
    confidence: float
    needs_human_judgment: bool = False
    factors: dict[str, Any]
    graph_path: dict[str, Any] | list[Any]
    path_depth: int | None = None
    path_confidence: float | None = None
    completeness: dict[str, Any] = Field(default_factory=dict)
    model_version: str
    computed_at: datetime

    # Joined fields for UI scannability
    company_name: str | None = None
    event_summary: str | None = None
    event_type: str | None = None


class PaginatedRiskAssessments(BaseModel):
    data: list[RiskAssessmentOut]
    total: int
    limit: int
    offset: int


class RiskModelVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: str
    weights: dict[str, Any]
    thresholds: dict[str, Any]
    is_active: bool
    activated_at: datetime | None = None


class RiskModelVersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=30)
    weights: dict[str, Any]
    thresholds: dict[str, Any]
    is_active: bool = False


class RiskSummaryOut(BaseModel):
    total_assessed: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    below_threshold_count: int = 0
    average_impact_score: float = 0.0
    needs_human_judgment_count: int = 0
    top_risks: list[RiskAssessmentOut] = Field(default_factory=list)


class RiskRecomputeRequest(BaseModel):
    event_id: uuid.UUID | None = None
    org_id: uuid.UUID | None = None
    model_version: str | None = None


class RiskRecomputeResponse(BaseModel):
    status: str
    recomputed_count: int
    message: str
