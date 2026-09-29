"""
Authentication endpoints.

Architecture reference: §N.2, Phase 3
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.verifier import CurrentUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AuthMeResponse(BaseModel):
    user_id: str
    org_id: uuid.UUID
    role: str
    persona: str | None
    permissions: list[str]


@router.get("/me", response_model=AuthMeResponse)
async def get_me(user: CurrentUser = Depends(get_current_user)) -> Any:
    """
    Return identity, tenant, role, persona, and permissions of current user.
    """
    return AuthMeResponse(
        user_id=user.user_id,
        org_id=user.org_id,
        role=user.role,
        persona=user.persona,
        permissions=sorted(user.permissions),
    )
