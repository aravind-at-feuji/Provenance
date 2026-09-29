"""
Clerk webhook handler.

Syncs organization and membership events to the database.
Architecture reference: Phase 3
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.modules.organizations.models import Organization, OrganizationMember

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_svix_signature(
    payload: bytes,
    secret: str,
    msg_id: str | None,
    msg_timestamp: str | None,
    msg_signature: str | None,
) -> bool:
    """
    Verify Svix HMAC-SHA256 signature using Python standard library.
    Header format: svix-signature contains 'v1,<base64>' signatures.
    """
    if not secret or not msg_id or not msg_timestamp or not msg_signature:
        return False

    # Check timestamp freshness (tolerance: 5 minutes)
    try:
        ts = int(msg_timestamp)
        if abs(time.time() - ts) > 300:
            return False
    except ValueError:
        return False

    # Remove whsec_ prefix if present
    key = secret.removeprefix("whsec_")
    try:
        secret_bytes = base64.b64decode(key)
    except Exception:
        secret_bytes = key.encode()

    to_sign = f"{msg_id}.{msg_timestamp}.".encode() + payload
    expected_mac = hmac.new(secret_bytes, to_sign, hashlib.sha256).digest()
    expected_sig = base64.b64encode(expected_mac).decode("utf-8")

    passed_signatures = [
        s.split(",", 1)[1] if "," in s else s
        for s in msg_signature.split(" ")
        if s.startswith("v1,") or "," not in s
    ]

    for sig in passed_signatures:
        if hmac.compare_digest(expected_sig, sig):
            return True

    return False


@router.post("/clerk", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    svix_id: str | None = Header(None, alias="svix-id"),
    svix_timestamp: str | None = Header(None, alias="svix-timestamp"),
    svix_signature: str | None = Header(None, alias="svix-signature"),
) -> dict[str, Any]:
    """
    Process inbound Clerk webhooks with Svix signature verification.
    """
    settings = get_settings()
    body = await request.body()

    # In production or when CLERK_WEBHOOK_SECRET is set, enforce signature
    if settings.clerk_webhook_secret:
        if not verify_svix_signature(
            body,
            settings.clerk_webhook_secret,
            svix_id,
            svix_timestamp,
            svix_signature,
        ):
            logger.warning("clerk_webhook_invalid_signature", msg_id=svix_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature",
            )

    try:
        event = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from exc

    event_type = event.get("type", "")
    data = event.get("data", {})

    logger.info("clerk_webhook_received", event_type=event_type)

    if event_type == "organization.created":
        clerk_org_id = data.get("id")
        name = data.get("name") or "Unnamed Organization"
        slug = data.get("slug") or f"org-{clerk_org_id}"

        existing = await db.execute(
            select(Organization).where(Organization.clerk_org_id == clerk_org_id)
        )
        if not existing.scalar_one_or_none():
            org = Organization(
                clerk_org_id=clerk_org_id,
                name=name,
                slug=slug,
            )
            db.add(org)
            await db.commit()

    elif event_type == "organization.updated":
        clerk_org_id = data.get("id")
        res = await db.execute(
            select(Organization).where(Organization.clerk_org_id == clerk_org_id)
        )
        updated_org: Organization | None = res.scalar_one_or_none()
        if updated_org:
            name = data.get("name")
            if name:
                updated_org.name = name
            slug = data.get("slug")
            if slug:
                updated_org.slug = slug
            await db.commit()

    elif event_type == "organizationMembership.created":
        clerk_org_id = data.get("organization", {}).get("id")
        user_id = data.get("public_user_data", {}).get("user_id")
        role = data.get("role", "org:member")
        normalized_role = "org_admin" if "admin" in role else "org_user"

        if clerk_org_id and user_id:
            res = await db.execute(
                select(Organization).where(Organization.clerk_org_id == clerk_org_id)
            )
            target_org: Organization | None = res.scalar_one_or_none()
            if target_org:
                existing_member = await db.execute(
                    select(OrganizationMember).where(
                        OrganizationMember.org_id == target_org.id,
                        OrganizationMember.user_id == user_id,
                    )
                )
                if not existing_member.scalar_one_or_none():
                    member = OrganizationMember(
                        org_id=target_org.id,
                        user_id=user_id,
                        role=normalized_role,
                    )
                    db.add(member)
                    await db.commit()

    elif event_type == "organizationMembership.deleted":
        clerk_org_id = data.get("organization", {}).get("id")
        user_id = data.get("public_user_data", {}).get("user_id")
        if clerk_org_id and user_id:
            res = await db.execute(
                select(Organization).where(Organization.clerk_org_id == clerk_org_id)
            )
            del_org: Organization | None = res.scalar_one_or_none()
            if del_org:
                mem_res = await db.execute(
                    select(OrganizationMember).where(
                        OrganizationMember.org_id == del_org.id,
                        OrganizationMember.user_id == user_id,
                    )
                )
                del_member: OrganizationMember | None = mem_res.scalar_one_or_none()
                if del_member:
                    await db.delete(del_member)
                    await db.commit()

    return {"status": "success", "event": event_type}
