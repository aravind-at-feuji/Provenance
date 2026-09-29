"""
FastAPI authentication and authorization dependencies.

Architecture reference: §C.3, §L.1, §L.2, §L.3
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.context import set_current_tenant_id, set_current_user_context
from app.auth.providers.clerk import ClerkVerifier
from app.auth.verifier import (
    CurrentUser,
    ExpiredTokenError,
    InvalidTokenError,
    MissingTenantError,
    TokenVerifier,
)

bearer_scheme = HTTPBearer(auto_error=False)

_verifier: TokenVerifier | None = None


def get_token_verifier() -> TokenVerifier:
    global _verifier
    if _verifier is None:
        _verifier = ClerkVerifier()
    return _verifier


def set_token_verifier(verifier: TokenVerifier | None) -> None:
    """Allow overriding verifier in tests."""
    global _verifier
    _verifier = verifier


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> CurrentUser:
    """
    FastAPI dependency: extracts, decodes, and verifies Bearer JWT.
    Sets tenant context for the request lifecycle.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await verifier.verify_token(credentials.credentials)
    except ExpiredTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={
                "WWW-Authenticate": 'Bearer error="invalid_token", error_description="expired"'
            },
        ) from exc
    except MissingTenantError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from exc

    set_current_tenant_id(user.org_id)
    set_current_user_context(user)
    return user


def require_permission(permission: str) -> Callable[[CurrentUser], CurrentUser]:
    """
    Route-level RBAC dependency enforcing a specific permission string.
    Example: Depends(require_permission("alerts:write"))
    """

    def _permission_guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required",
            )
        return user

    return _permission_guard


def require_role(roles: list[str]) -> Callable[[CurrentUser], CurrentUser]:
    """
    Route-level RBAC dependency enforcing membership in allowed roles.
    Example: Depends(require_role(["org_admin"]))
    """
    allowed_set = set(roles) | {"platform_admin"}

    def _role_guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role forbidden: requires one of {roles}",
            )
        return user

    return _role_guard
