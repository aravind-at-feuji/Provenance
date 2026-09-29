"""
TokenVerifier protocol and CurrentUser domain model.

Architecture reference: §C.3, §L.1, §L.2
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol


class AuthError(Exception):
    """Base exception for authentication errors."""


class InvalidTokenError(AuthError):
    """Raised when token signature, issuer, or audience is invalid."""


class ExpiredTokenError(AuthError):
    """Raised when token expiration time is in the past."""


class MissingTenantError(AuthError):
    """Raised when token lacks an org_id context."""


# ── RBAC Matrix (§L.2) ────────────────────────────────────────────────────────
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "platform_admin": {
        "admin:all",
        "org:read",
        "org:write",
        "org:admin",
        "members:read",
        "members:write",
        "suppliers:read",
        "suppliers:write",
        "graph:read",
        "events:read",
        "alerts:read",
        "alerts:write",
        "alerts:acknowledge",
        "documents:read",
        "documents:upload",
        "spend:read",
        "investigations:run",
        "data_sources:read",
        "data_sources:write",
    },
    "org_admin": {
        "org:read",
        "org:write",
        "org:admin",
        "members:read",
        "members:write",
        "suppliers:read",
        "suppliers:write",
        "graph:read",
        "events:read",
        "alerts:read",
        "alerts:write",
        "alerts:acknowledge",
        "documents:read",
        "documents:upload",
        "spend:read",
        "investigations:run",
        "data_sources:read",
    },
    "analyst": {
        "org:read",
        "members:read",
        "suppliers:read",
        "suppliers:write",
        "graph:read",
        "events:read",
        "alerts:read",
        "alerts:write",
        "alerts:acknowledge",
        "documents:read",
        "documents:upload",
        "spend:read",
        "investigations:run",
    },
    "org_user": {
        "org:read",
        "members:read",
        "suppliers:read",
        "graph:read",
        "events:read",
        "alerts:read",
        "alerts:acknowledge",
        "documents:read",
        "spend:read",
    },
    "read_only": {
        "org:read",
        "members:read",
        "suppliers:read",
        "graph:read",
        "events:read",
        "alerts:read",
        "documents:read",
        "spend:read",
    },
}


def get_permissions_for_role(role: str) -> set[str]:
    """Return permissions set for a given role, or empty set if unrecognized."""
    return set(ROLE_PERMISSIONS.get(role, set()))


@dataclass(frozen=True)
class CurrentUser:
    """
    Authenticated user context consumed by application code.
    All claims are verified before this object is constructed.
    """

    user_id: str
    org_id: uuid.UUID
    role: str
    permissions: set[str] = field(default_factory=set)
    persona: str | None = None

    def has_permission(self, permission: str) -> bool:
        return "admin:all" in self.permissions or permission in self.permissions


class TokenVerifier(Protocol):
    """
    Pluggable token verification protocol.
    Implementations: ClerkVerifier (MVP), KeycloakVerifier (Phase 3 enterprise).
    """

    async def verify_token(self, token: str) -> CurrentUser:
        """
        Verify raw JWT string and return authenticated CurrentUser.
        Raises InvalidTokenError, ExpiredTokenError, or MissingTenantError on failure.
        """
        ...
