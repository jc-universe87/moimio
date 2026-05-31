"""Tests for /api/billing-info and the updated /api/capabilities.

billing-info is auth-gated (the buy-credit link is tenant-specific).
capabilities is public but exposes the create_event_confirmation flag.
Under the prepaid-credit model (v1.0.0w) billing-info returns a single
field, buy_credit_url; before v1.0.0w it returned a charge amount,
currency and card last-four.
"""

import pytest

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.main import app
from app.models.user import User, UserRole


pytestmark = pytest.mark.asyncio


# ─── Helpers ────────────────────────────────────────────────────────────


def _fake_user() -> User:
    """Build a minimally-valid User for dependency override.

    Returning a real User instance (not a dict) keeps endpoint code
    that introspects user.role or user.email working in the override
    path.
    """
    return User(
        email="test-billing@test.local",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Billing User",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )


# ─── /api/capabilities — public, now includes the new flag ──────────────


async def test_capabilities_response_includes_create_event_confirmation(client, monkeypatch):
    """capabilities response schema now has the create_event_confirmation field."""
    monkeypatch.delenv("FEATURE_CREATE_EVENT_CONFIRMATION", raising=False)
    get_settings.cache_clear()

    resp = await client.get("/api/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    assert "create_event_confirmation" in body
    # Default is false — CE self-hosters never opt in to the dialog
    # unless their environment explicitly enables it.
    assert body["create_event_confirmation"] is False


async def test_capabilities_create_event_confirmation_reflects_env(client, monkeypatch):
    """FEATURE_CREATE_EVENT_CONFIRMATION=true → flag is true in the response."""
    monkeypatch.setenv("FEATURE_CREATE_EVENT_CONFIRMATION", "true")
    get_settings.cache_clear()

    resp = await client.get("/api/capabilities")
    assert resp.status_code == 200
    assert resp.json()["create_event_confirmation"] is True


async def test_capabilities_remains_unauthenticated(client, monkeypatch):
    """/api/capabilities is intentionally public. Adding a new flag mustn't
    accidentally introduce an auth requirement.
    """
    monkeypatch.delenv("FEATURE_CREATE_EVENT_CONFIRMATION", raising=False)
    get_settings.cache_clear()

    # No Authorization header
    resp = await client.get("/api/capabilities")
    assert resp.status_code == 200


# ─── /api/billing-info — auth-gated, returns the buy-credit link ─────────


async def test_billing_info_requires_auth(client):
    """Without a valid JWT, /api/billing-info returns 401 (or 403).

    The buy-credit link is tenant-specific; an attacker without an
    account shouldn't be able to read it.
    """
    resp = await client.get("/api/billing-info")
    # 401 (missing auth) or 403 (forbidden); either is fine, just not 200.
    assert resp.status_code in (401, 403)


async def test_billing_info_returns_buy_url_when_authed(client, monkeypatch):
    """The configured buy link comes through as-is for an authed caller."""
    monkeypatch.setenv("BUY_CREDIT_URL", "https://moimio.app/buy?tenant=abc")
    get_settings.cache_clear()

    app.dependency_overrides[get_current_user] = _fake_user
    try:
        resp = await client.get("/api/billing-info")
        assert resp.status_code == 200
        assert resp.json() == {"buy_credit_url": "https://moimio.app/buy?tenant=abc"}
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_billing_info_empty_when_unset(client, monkeypatch):
    """No link configured → empty string, not null or a 500. CE hides the
    buy button when this is empty."""
    monkeypatch.delenv("BUY_CREDIT_URL", raising=False)
    get_settings.cache_clear()

    app.dependency_overrides[get_current_user] = _fake_user
    try:
        resp = await client.get("/api/billing-info")
        assert resp.status_code == 200
        assert resp.json() == {"buy_credit_url": ""}
    finally:
        app.dependency_overrides.pop(get_current_user, None)
