"""
Clerk token verifier implementation.

Architecture reference: §C.3, §L.1
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import httpx
import structlog
from jose import ExpiredSignatureError, JWTError, jwt

from app.auth.verifier import (
    CurrentUser,
    ExpiredTokenError,
    InvalidTokenError,
    MissingTenantError,
    get_permissions_for_role,
)
from app.config import Settings, get_settings

logger = structlog.get_logger(__name__)


# Normalize Clerk role strings to internal role names (§L.2)
ROLE_MAP: dict[str, str] = {
    "org:admin": "org_admin",
    "admin": "org_admin",
    "org_admin": "org_admin",
    "org:member": "org_user",
    "member": "org_user",
    "org_user": "org_user",
    "analyst": "analyst",
    "read_only": "read_only",
    "platform_admin": "platform_admin",
}


class ClerkVerifier:
    """
    Verifies Clerk-issued JWTs against Clerk's JWKS or configured signing keys.
    Caches JWKS for 1 hour (§L.1).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0.0
        self._jwks_ttl_seconds: float = 3600.0  # 1 hour cache per §L.1

    async def _get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JWKS from Clerk with 1-hour TTL."""
        now = time.time()
        if self._jwks_cache and (now - self._jwks_fetched_at) < self._jwks_ttl_seconds:
            return self._jwks_cache

        url = self.settings.clerk_jwks_url
        if not url:
            return {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                self._jwks_cache = data if isinstance(data, dict) else {}
                self._jwks_fetched_at = now
                return self._jwks_cache
        except Exception as exc:
            logger.warning("clerk_jwks_fetch_failed", error=str(exc))
            return self._jwks_cache if self._jwks_cache is not None else {}

    async def verify_token(self, token: str) -> CurrentUser:
        """
        Verify raw JWT and construct CurrentUser.
        """
        if not token:
            raise InvalidTokenError("Missing token")

        # 1. Determine key and algorithms
        algorithms = ["RS256"]
        secret_or_key: str | dict[str, Any] | None = None

        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError as exc:
            raise InvalidTokenError(f"Malformed token header: {exc}") from exc

        alg = unverified_header.get("alg", "RS256")

        if alg == "HS256":
            # Supported for testing and local dev secret verification
            secret_or_key = self.settings.secret_key
            algorithms = ["HS256"]
        else:
            # Check JWKS for matching key ID (kid)
            jwks = await self._get_jwks()
            kid = unverified_header.get("kid")
            if jwks and "keys" in jwks:
                for key in jwks["keys"]:
                    if key.get("kid") == kid:
                        secret_or_key = key
                        break
            if not secret_or_key and self.settings.clerk_secret_key:
                # Fallback to configured key if provided
                secret_or_key = self.settings.clerk_secret_key

        if not secret_or_key:
            raise InvalidTokenError("Unable to find suitable signing key for token verification")

        # 2. Decode & verify claims
        options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": bool(self.settings.auth_issuer),
            "verify_aud": bool(self.settings.auth_audience),
        }

        try:
            claims = jwt.decode(
                token,
                secret_or_key,
                algorithms=algorithms,
                issuer=self.settings.auth_issuer or None,
                audience=self.settings.auth_audience or None,
                options=options,
            )
        except ExpiredSignatureError as exc:
            raise ExpiredTokenError("Token has expired") from exc
        except JWTError as exc:
            raise InvalidTokenError(f"Token verification failed: {exc}") from exc

        # 3. Extract required claims (§L.1)
        sub = claims.get("sub")
        if not sub:
            raise InvalidTokenError("Token missing 'sub' subject claim")

        raw_org_id = claims.get("org_id")
        if not raw_org_id:
            raise MissingTenantError("Token missing required 'org_id' tenant claim")

        # Convert org_id to uuid.UUID
        try:
            org_id = uuid.UUID(str(raw_org_id))
        except ValueError:
            # If Clerk org id is a string slug like 'org_12345', generate a deterministic UUIDv5
            # ponytail: maps non-UUID clerk org string to UUID namespace deterministically
            org_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_org_id))

        raw_role = claims.get("org_role") or claims.get("role") or "org_user"
        normalized_role = ROLE_MAP.get(str(raw_role).lower(), "org_user")

        persona = claims.get("persona")

        permissions = get_permissions_for_role(normalized_role)

        return CurrentUser(
            user_id=str(sub),
            org_id=org_id,
            role=normalized_role,
            permissions=permissions,
            persona=str(persona) if persona else None,
        )
