"""
Tenant context middleware.

Architecture reference: §L.3, Phase 3
Extracts tenant context from request and ensures clean contextvar lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.auth.context import (
    get_current_tenant_id,
    set_current_tenant_id,
    set_current_user_context,
)

if TYPE_CHECKING:
    from app.auth.verifier import TokenVerifier

logger = structlog.get_logger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Ensures per-request isolation of tenant context.
    Optionally extracts early Bearer token to populate tenant contextvar.
    """

    def __init__(self, app: Any, verifier: TokenVerifier | None = None) -> None:
        super().__init__(app)
        self.verifier = verifier

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Clear/initialize request-scoped context
        set_current_tenant_id(None)
        set_current_user_context(None)

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer ") and self.verifier:
            token = auth_header[7:].strip()
            try:
                user = await self.verifier.verify_token(token)
                set_current_tenant_id(user.org_id)
                set_current_user_context(user)
                request.state.current_user = user
                request.state.current_org_id = user.org_id
            except Exception as exc:
                # Endpoint dependencies will handle 401/403 with exact error detail
                logger.debug("tenant_middleware_token_deferred", error=str(exc))

        try:
            response = await call_next(request)
            # Add X-Tenant-Id header if tenant context was established
            tenant_id = get_current_tenant_id()
            if tenant_id:
                response.headers["X-Tenant-Id"] = str(tenant_id)
            return response
        finally:
            set_current_tenant_id(None)
            set_current_user_context(None)
