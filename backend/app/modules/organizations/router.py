"""
Organizations module router.

Architecture reference: §N.2, Phase 3
Endpoints:
- GET   /organizations/{id}
- PATCH /organizations/{id}
- GET   /organizations/{id}/members
- POST  /organizations/{id}/members
- DELETE /organizations/{id}/members/{user_id}
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_permission
from app.auth.verifier import CurrentUser
from app.db.session import get_db
from app.modules.organizations.models import Organization, OrganizationMember
from app.modules.organizations.schemas import (
    MemberCreate,
    MemberRead,
    OrganizationRead,
    OrganizationUpdate,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def verify_org_permission(permission: str) -> Callable[..., Any]:
    """Enforce both permission and tenant ownership before DB access."""

    async def _guard(
        org_id: uuid.UUID,
        user: CurrentUser = Depends(require_permission(permission)),
    ) -> CurrentUser:
        if user.role != "platform_admin" and user.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to organization denied",
            )
        return user

    return _guard


async def verify_org_access(
    org_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Ensure user belongs to the target organization or is platform_admin."""
    if user.role != "platform_admin" and user.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to organization denied",
        )
    return user


@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization(
    org_id: uuid.UUID,
    user: CurrentUser = Depends(verify_org_access),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve organization details."""
    res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return org


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
    user: CurrentUser = Depends(verify_org_permission("org:write")),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update organization settings and profile."""
    res = await db.execute(select(Organization).where(Organization.id == org_id))
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if payload.name is not None:
        org.name = payload.name
    if payload.industry is not None:
        org.industry = payload.industry
    if payload.country is not None:
        org.country = payload.country
    if payload.settings is not None:
        org.settings = {**org.settings, **payload.settings}

    await db.commit()
    await db.refresh(org)
    return org


@router.get("/{org_id}/members", response_model=list[MemberRead])
async def list_members(
    org_id: uuid.UUID,
    user: CurrentUser = Depends(verify_org_permission("members:read")),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List members of an organization."""
    res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.org_id == org_id)
        .order_by(OrganizationMember.created_at.asc())
    )
    return res.scalars().all()


@router.post(
    "/{org_id}/members",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    org_id: uuid.UUID,
    payload: MemberCreate,
    user: CurrentUser = Depends(verify_org_permission("members:write")),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Add or invite a member to an organization."""
    # Check if already a member
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == payload.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    member = OrganizationMember(
        org_id=org_id,
        user_id=payload.user_id,
        role=payload.role,
        persona=payload.persona,
        assigned_categories=payload.assigned_categories,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_member(
    org_id: uuid.UUID,
    user_id: str,
    user: CurrentUser = Depends(verify_org_permission("members:write")),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Remove a member from an organization."""
    res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user_id,
        )
    )
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    await db.delete(member)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
