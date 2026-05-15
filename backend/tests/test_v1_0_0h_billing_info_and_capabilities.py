"""Tests for v1.0.0h /api/billing-info and the updated /api/capabilities.

billing-info is auth-gated (card last-4 is customer data). capabilities
is public but now exposes the create_event_confirmation flag.
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


# ─── /api/billing-info — auth-gated, returns env values ─────────────────


async def test_billing_info_requires_auth(client):
    """Without a valid JWT, /api/billing-info returns 401 (or 403).

    Card last-4 is customer data; an attacker without an account
    shouldn't be able to fingerprint a tenant's billing setup.
    """
    resp = await client.get("/api/billing-info")
    # Could be 401 (missing auth) or 403 (forbidden), depending on
    # the auth scheme. Either is acceptable as long as it's not 200.
    assert resp.status_code in (401, 403)


async def test_billing_info_returns_env_values_when_authed(client, monkeypatch):
    """All three env values come through as-is for an authenticated caller."""
    monkeypatch.setenv("EVENT_CHARGE_AMOUNT", "120")
    monkeypatch.setenv("EVENT_CHARGE_CURRENCY", "EUR")
    monkeypatch.setenv("BILLING_CARD_LAST4", "4242")
    get_settings.cache_clear()

    app.dependency_overrides[get_current_user] = _fake_user
    try:
        resp = await client.get("/api/billing-info")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "amount": "120",
            "currency": "EUR",
            "card_last4": "4242",
        }
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_billing_info_returns_empty_strings_when_unset(client, monkeypatch):
    """Unconfigured env vars → empty strings, not nulls or 500s.

    Empty-string defaults keep the response shape stable for the
    frontend's i18n template logic — it switches body keys based on
    truthy checks, which empty strings handle correctly.
    """
    monkeypatch.delenv("EVENT_CHARGE_AMOUNT", raising=False)
    monkeypatch.delenv("EVENT_CHARGE_CURRENCY", raising=False)
    monkeypatch.delenv("BILLING_CARD_LAST4", raising=False)
    get_settings.cache_clear()

    app.dependency_overrides[get_current_user] = _fake_user
    try:
        resp = await client.get("/api/billing-info")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"amount": "", "currency": "", "card_last4": ""}
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_billing_info_partial_config_returns_what_is_set(client, monkeypatch):
    """Amount + currency set, last4 missing → last4 empty, others present.

    Common in early days when a tenant exists but hasn't completed
    card setup, or after a card update before SaaS has redeployed.
    Frontend uses the empty last4 to fall back to "your card on file"
    wording — this test confirms backend supplies the data it expects.
    """
    monkeypatch.setenv("EVENT_CHARGE_AMOUNT", "80")
    monkeypatch.setenv("EVENT_CHARGE_CURRENCY", "EUR")
    monkeypatch.delenv("BILLING_CARD_LAST4", raising=False)
    get_settings.cache_clear()

    app.dependency_overrides[get_current_user] = _fake_user
    try:
        resp = await client.get("/api/billing-info")
        body = resp.json()
        assert body["amount"] == "80"
        assert body["currency"] == "EUR"
        assert body["card_last4"] == ""
    finally:
        app.dependency_overrides.pop(get_current_user, None)
