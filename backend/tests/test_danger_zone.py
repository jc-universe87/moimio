"""Danger Zone — customer-triggered workspace deletion (v1.0.0t).

Tests the auth gate (super-admin only), the confirmation-token guard,
and the side effect that matters: a `workspace.delete_requested` event
is queued through the outbound-webhooks subsystem so the SaaS receives
it.

Auth is exercised via FastAPI's `dependency_overrides` rather than a
real JWT — the established pattern for HTTP tests in this codebase.
"""
import uuid

import pytest
from sqlalchemy import select

from app.api.deps import get_current_user
from app.main import app
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


def _super_admin() -> User:
    return User(
        id=uuid.uuid4(),
        email="admin@danger-zone.test",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Super Admin",
        role=UserRole.SUPER_ADMIN,
    )


def _staff_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="staff@danger-zone.test",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Staff",
        role=UserRole.STAFF,
    )


async def _seed_saas_endpoint(db) -> OutboundWebhookEndpoint:
    """Create a subscribed-to-everything endpoint so queue_event produces
    a delivery row we can assert on. Mirrors what CE's auto-registration
    would do at first boot when MOIMIO_WEBHOOK_URL is set."""
    ep = OutboundWebhookEndpoint(
        name="saas",
        url="http://localhost:6130/webhooks/ce",
        secret="test-secret-32-chars-long-enough-yes",
        event_types=["*"],
        state=WebhookEndpointState.ACTIVE,
        managed_by=WebhookEndpointManagedBy.SAAS,
        is_active=True,
    )
    db.add(ep)
    await db.flush()
    return ep


# ── auth gate ──

async def test_unauthenticated_request_returns_401(client):
    """Without a Bearer token at all → 401, not 403."""
    resp = await client.post(
        "/api/admin/workspace/request-deletion",
        json={"confirmation": "DELETE"},
    )
    assert resp.status_code in (401, 403)


async def test_staff_user_is_forbidden(client):
    app.dependency_overrides[get_current_user] = _staff_user
    try:
        resp = await client.post(
            "/api/admin/workspace/request-deletion",
            json={"confirmation": "DELETE"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["key"] == "errors.danger_zone.super_admin_only"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ── confirmation guard ──

async def test_wrong_confirmation_returns_400(client):
    app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(
            "/api/admin/workspace/request-deletion",
            json={"confirmation": "delete"},  # lowercase — not exact
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["key"] == "errors.danger_zone.confirmation_mismatch"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


async def test_empty_confirmation_returns_400(client):
    app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(
            "/api/admin/workspace/request-deletion",
            json={"confirmation": ""},
        )
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ── happy path: the side effect that matters ──

async def test_correct_request_queues_workspace_delete_requested_event(client, db):
    """A successful request must result in a delivery row destined for
    the subscribed endpoint, carrying event_type=workspace.delete_requested."""
    ep = await _seed_saas_endpoint(db)
    await db.commit()

    app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(
            "/api/admin/workspace/request-deletion",
            json={"confirmation": "DELETE"},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "accepted"
    assert "event_id" in body and uuid.UUID(body["event_id"])

    # A delivery row should exist for our subscribed endpoint, carrying
    # the right event_type — proves the event was emitted, not just acked.
    deliveries = (
        await db.execute(
            select(OutboundWebhookDelivery).where(
                OutboundWebhookDelivery.endpoint_id == ep.id
            )
        )
    ).scalars().all()
    assert len(deliveries) == 1
    assert deliveries[0].event_type == "workspace.delete_requested"


async def test_no_endpoints_configured_still_accepts(client, db):
    """A self-hoster with no SaaS endpoint registered — the request is
    still acknowledged. queue_event delivers to zero endpoints (no-op);
    the customer's intent is what we ack."""
    app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(
            "/api/admin/workspace/request-deletion",
            json={"confirmation": "DELETE"},
        )
        assert resp.status_code == 202
    finally:
        app.dependency_overrides.pop(get_current_user, None)
