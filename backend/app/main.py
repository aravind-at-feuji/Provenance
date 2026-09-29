"""
main.py — FastAPI application factory.

Import and call `create_app()` to get the configured ASGI application.
`app` at module level is what uvicorn/gunicorn targets.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.webhooks import router as webhooks_router
from app.auth.dependencies import get_token_verifier
from app.auth.middleware import TenantContextMiddleware
from app.config import get_settings
from app.core.logging import configure_logging
from app.modules.organizations.router import router as organizations_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info(
        "provenance_api_starting",
        environment=settings.environment,
        version=application.version,
    )
    yield
    logger.info("provenance_api_stopping")


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Provenance API",
        description="Supply-chain risk intelligence platform.",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Tenant Context & Auth Middleware (§L.3, Phase 3) ───────────────────
    application.add_middleware(
        TenantContextMiddleware,
        verifier=get_token_verifier(),
    )

    # ── Routers ─────────────────────────────────────────────────────────────
    # Top-level health
    application.include_router(health_router)

    # Core Phase 3 routes (mounted at /api/v1 and top-level)
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(organizations_router, prefix="/api/v1")
    application.include_router(webhooks_router, prefix="/api/v1")

    # Convenience aliases for root paths
    application.include_router(auth_router)
    application.include_router(organizations_router)

    return application


app = create_app()
