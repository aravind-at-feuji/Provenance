"""
Unit and integration tests for Phase 3 Authentication and Authorization.

Acceptance criteria (§Phase 3):
1. Expired / invalid / wrong-audience tokens are rejected.
2. Each role's permission matrix passes.
3. Tenant isolation: valid token for Org A cannot read Org B on any endpoint.
4. /auth/me returns current user identity, org, role, and permissions.
5. Webhook Svix signature validation.
"""

from __future__ import annotations

import time
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.auth.providers.clerk import ClerkVerifier
from app.auth.verifier import (
    CurrentUser,
    ExpiredTokenError,
    InvalidTokenError,
    MissingTenantError,
    get_permissions_for_role,
)
from app.config import Settings
from app.main import app


# ── Helpers to create test JWTs ───────────────────────────────────────────────

SECRET = "test-secret-key-12345"


def create_test_token(
    user_id: str = "user_test_123",
    org_id: str | uuid.UUID | None = None,
    role: str = "org_user",
    persona: str | None = None,
    exp_delta: int = 3600,
    issuer: str = "https://clerk.test",
    audience: str = "provenance-api",
    secret: str = SECRET,
    alg: str = "HS256",
) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "exp": now + exp_delta,
        "iat": now,
        "iss": issuer,
        "aud": audience,
        "role": role,
    }
    if org_id is not None:
        payload["org_id"] = str(org_id)
    if persona is not None:
        payload["persona"] = persona

    return jwt.encode(payload, secret, algorithm=alg)


@pytest.fixture
def auth_settings() -> Settings:
    return Settings(
        secret_key=SECRET,
        auth_issuer="https://clerk.test",
        auth_audience="provenance-api",
    )


@pytest.fixture
def verifier(auth_settings: Settings) -> ClerkVerifier:
    return ClerkVerifier(settings=auth_settings)


@pytest.fixture(autouse=True)
def override_db():
    """Mock get_db in unit tests so tests can run without live PostgreSQL."""
    from unittest.mock import AsyncMock
    from app.db.session import get_db

    async def _dummy_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _dummy_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


# ── 1. TokenVerifier Claim & Error Tests ──────────────────────────────────────


@pytest.mark.asyncio
async def test_valid_token_verified(verifier: ClerkVerifier) -> None:
    test_org_id = uuid.uuid4()
    token = create_test_token(
        user_id="user_valid_1",
        org_id=test_org_id,
        role="analyst",
        persona="risk_manager",
    )

    user: CurrentUser = await verifier.verify_token(token)
    assert user.user_id == "user_valid_1"
    assert user.org_id == test_org_id
    assert user.role == "analyst"
    assert user.persona == "risk_manager"
    assert "alerts:write" in user.permissions
    assert "suppliers:write" in user.permissions


@pytest.mark.asyncio
async def test_expired_token_rejected(verifier: ClerkVerifier) -> None:
    token = create_test_token(org_id=uuid.uuid4(), exp_delta=-60)
    with pytest.raises(ExpiredTokenError):
        await verifier.verify_token(token)


@pytest.mark.asyncio
async def test_invalid_signature_rejected(verifier: ClerkVerifier) -> None:
    token = create_test_token(org_id=uuid.uuid4(), secret="wrong-secret")
    with pytest.raises(InvalidTokenError):
        await verifier.verify_token(token)


@pytest.mark.asyncio
async def test_wrong_audience_rejected(verifier: ClerkVerifier) -> None:
    token = create_test_token(org_id=uuid.uuid4(), audience="wrong-aud")
    with pytest.raises(InvalidTokenError):
        await verifier.verify_token(token)


@pytest.mark.asyncio
async def test_wrong_issuer_rejected(verifier: ClerkVerifier) -> None:
    token = create_test_token(org_id=uuid.uuid4(), issuer="https://evil.issuer")
    with pytest.raises(InvalidTokenError):
        await verifier.verify_token(token)


@pytest.mark.asyncio
async def test_missing_tenant_rejected(verifier: ClerkVerifier) -> None:
    token = create_test_token(org_id=None)
    with pytest.raises(MissingTenantError):
        await verifier.verify_token(token)


@pytest.mark.asyncio
async def test_clerk_string_org_id_maps_to_uuid(verifier: ClerkVerifier) -> None:
    token = create_test_token(org_id="org_2bXYZ123456")
    user = await verifier.verify_token(token)
    assert isinstance(user.org_id, uuid.UUID)


# ── 2. RBAC Role Matrix Verification (§L.2) ──────────────────────────────────


def test_role_matrix_permissions() -> None:
    # platform_admin has administrative superpowers
    p_admin_perms = get_permissions_for_role("platform_admin")
    assert "admin:all" in p_admin_perms
    u_admin = CurrentUser(
        user_id="u",
        org_id=uuid.uuid4(),
        role="platform_admin",
        permissions=p_admin_perms,
    )
    assert u_admin.has_permission("any_random_action")

    # org_admin can manage org & members
    org_admin_perms = get_permissions_for_role("org_admin")
    assert "org:write" in org_admin_perms
    assert "members:write" in org_admin_perms
    assert "alerts:write" in org_admin_perms

    # analyst can write suppliers & alerts, but not org settings
    analyst_perms = get_permissions_for_role("analyst")
    assert "suppliers:write" in analyst_perms
    assert "alerts:write" in analyst_perms
    assert "org:write" not in analyst_perms
    assert "members:write" not in analyst_perms

    # org_user can acknowledge alerts & read, but not mutate graph
    org_user_perms = get_permissions_for_role("org_user")
    assert "alerts:acknowledge" in org_user_perms
    assert "alerts:read" in org_user_perms
    assert "suppliers:write" not in org_user_perms
    assert "alerts:write" not in org_user_perms

    # read_only has strictly read access
    ro_perms = get_permissions_for_role("read_only")
    assert "alerts:read" in ro_perms
    assert "suppliers:read" in ro_perms
    assert "alerts:acknowledge" not in ro_perms
    assert "alerts:write" not in ro_perms


# ── 3. API Endpoints & Tenant Isolation ───────────────────────────────────────


@pytest.mark.asyncio
async def test_auth_me_without_token_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_with_valid_token(monkeypatch) -> None:
    org_id = uuid.uuid4()
    token = create_test_token(
        user_id="user_me_test",
        org_id=org_id,
        role="analyst",
        persona="category_manager",
    )

    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "secret_key", SECRET)
    monkeypatch.setattr(get_settings(), "auth_issuer", "https://clerk.test")
    monkeypatch.setattr(get_settings(), "auth_audience", "provenance-api")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user_me_test"
    assert data["org_id"] == str(org_id)
    assert data["role"] == "analyst"
    assert data["persona"] == "category_manager"
    assert "alerts:write" in data["permissions"]


@pytest.mark.asyncio
async def test_cross_tenant_organization_access_forbidden(monkeypatch) -> None:
    """
    User belonging to Org A attempts to access Org B's details.
    Must be rejected with 403 Forbidden.
    """
    org_a_id = uuid.uuid4()
    org_b_id = uuid.uuid4()

    token_org_a = create_test_token(
        user_id="user_tenant_a",
        org_id=org_a_id,
        role="org_admin",
    )

    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "secret_key", SECRET)
    monkeypatch.setattr(get_settings(), "auth_issuer", "https://clerk.test")
    monkeypatch.setattr(get_settings(), "auth_audience", "provenance-api")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Request Org B with Org A token
        resp = await client.get(
            f"/api/v1/organizations/{org_b_id}",
            headers={"Authorization": f"Bearer {token_org_a}"},
        )

    assert resp.status_code == 403
    assert "Access to organization denied" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_cross_tenant_members_access_forbidden(monkeypatch) -> None:
    """
    User belonging to Org A attempts to list Org B's members.
    Must be rejected with 403 Forbidden.
    """
    org_a_id = uuid.uuid4()
    org_b_id = uuid.uuid4()

    token_org_a = create_test_token(
        user_id="user_tenant_a",
        org_id=org_a_id,
        role="org_admin",
    )

    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "secret_key", SECRET)
    monkeypatch.setattr(get_settings(), "auth_issuer", "https://clerk.test")
    monkeypatch.setattr(get_settings(), "auth_audience", "provenance-api")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            f"/api/v1/organizations/{org_b_id}/members",
            headers={"Authorization": f"Bearer {token_org_a}"},
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_permission_denied_for_insufficient_role(monkeypatch) -> None:
    """
    Analyst attempts to call PATCH /organizations/{id} which requires org:write.
    Must return 403 Forbidden.
    """
    org_id = uuid.uuid4()
    token_analyst = create_test_token(
        user_id="user_analyst",
        org_id=org_id,
        role="analyst",
    )

    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "secret_key", SECRET)
    monkeypatch.setattr(get_settings(), "auth_issuer", "https://clerk.test")
    monkeypatch.setattr(get_settings(), "auth_audience", "provenance-api")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/organizations/{org_id}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token_analyst}"},
        )

    assert resp.status_code == 403
    assert "Permission denied: 'org:write' required" in resp.json()["detail"]


# ── 4. Webhook Signature Validation ──────────────────────────────────────────


def test_verify_svix_signature() -> None:
    from app.api.v1.webhooks import verify_svix_signature

    secret = "whsec_MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE"
    payload = b'{"type":"user.created","data":{"id":"user_123"}}'
    msg_id = "msg_test_001"
    msg_timestamp = str(int(time.time()))

    import base64
    import hashlib
    import hmac

    key_bytes = base64.b64decode(secret.removeprefix("whsec_"))
    to_sign = f"{msg_id}.{msg_timestamp}.".encode() + payload
    sig = base64.b64encode(
        hmac.new(key_bytes, to_sign, hashlib.sha256).digest()
    ).decode()

    valid_header = f"v1,{sig}"
    assert verify_svix_signature(payload, secret, msg_id, msg_timestamp, valid_header)

    # Wrong signature fails
    assert not verify_svix_signature(
        payload, secret, msg_id, msg_timestamp, "v1,bad-signature"
    )

    # Expired timestamp (> 300s) fails
    old_ts = str(int(time.time()) - 600)
    assert not verify_svix_signature(payload, secret, msg_id, old_ts, valid_header)
