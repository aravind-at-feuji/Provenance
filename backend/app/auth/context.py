"""
Tenant context management via contextvars.

Maintains request-scoped tenant ID and user context.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.auth.verifier import CurrentUser

_current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar("current_tenant_id", default=None)
_current_user: ContextVar[CurrentUser | None] = ContextVar("current_user", default=None)


def get_current_tenant_id() -> uuid.UUID | None:
    return _current_tenant_id.get()


def set_current_tenant_id(org_id: uuid.UUID | None) -> None:
    _current_tenant_id.set(org_id)


def get_current_user_context() -> CurrentUser | None:
    return _current_user.get()


def set_current_user_context(user: CurrentUser | None) -> None:
    _current_user.set(user)
