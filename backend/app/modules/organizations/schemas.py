"""
Organization schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clerk_org_id: str
    name: str
    slug: str
    company_id: uuid.UUID | None = None
    industry: str | None = None
    country: str | None = None
    subscription_tier: str
    settings: dict[str, Any] = Field(default_factory=dict)
    monthly_token_budget: int
    onboarding_completed_at: datetime | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    country: str | None = None
    settings: dict[str, Any] | None = None


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    user_id: str
    role: str
    persona: str | None = None
    assigned_categories: list[str] = Field(default_factory=list)
    joined_at: datetime | None = None


class MemberCreate(BaseModel):
    user_id: str
    role: str = "org_user"
    persona: str | None = None
    assigned_categories: list[str] = Field(default_factory=list)
