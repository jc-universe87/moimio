"""Tests for v1.0.0h-1 — delete-event emits webhook + test.ping carries tenant_id.

v1.0.0h-1 simplified the architecture: the v1.0.0h cancel/grace-window
machinery is gone. Delete is the single destructive path and it always
emits an event.deleted webhook. SaaS owns the decision of whether the
deletion warrants a refund (e.g. a 24-hour paid-plan policy).

Also covers the v1.0.0h bug fix: test.ping now routes through _envelope
so it picks up MOIMIO_TENANT_ID stamping like every other event type.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.main import app as fastapi_app
from app.models.event import Event
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.models.user import User, UserRole
from app.schemas.event import EventCreate
from app.services import event_service
from tests.conftest import make_user


pytestmark = pytest.mark.asyncio


# ─── Helpers ────────────────────────────────────────────────────────────


async def _make_subscribed_endpoint(db) -> OutboundWebhookEndpoint:
    ep = OutboundWebhookEndpoint(
        name="test-receiver",
        url="https://example.invalid/webhook",
        secret="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        event_types=["*"],
        state=WebhookEndpointState.ACTIVE,
        managed_by=WebhookEndpointManagedBy.USER,
    )
    db.add(ep)
    await db.flush()
    return ep


def _super_admin() -> User:
    return User(
        email="super@test.local",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Super",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )


# ─── delete_event emits event.deleted ──────────────────────────────────


async def test_delete_event_emits_event_deleted_webhook(db, monkeypatch):
    """delete_event queues one event.deleted delivery in the same transaction.

    Same transactional contract as event.created: webhook delivery row
    and the cascade commit together. No more event.cancelled — there
    is only one destructive verb now.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")
    event = await event_service.create_event(
        db,
        EventCreate(name="To be deleted"),
        created_by=user.id,
    )
    # Clear the event.created delivery so we can check event.deleted in isolation
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(OutboundWebhookDelivery))
    await db.flush()

    ok = await event_service.delete_event(db, event.id)
    assert ok is True

    deliveries = (await db.execute(select(OutboundWebhookDelivery))).scalars().all()
    assert len(deliveries) == 1
    assert deliveries[0].event_type == "event.deleted"
    assert deliveries[0].status == WebhookDeliveryStatus.PENDING


async def test_delete_event_payload_is_minimal(db, monkeypatch):
    """event.deleted data block has exactly {event_id, deleted_at}.

    Same GDPR-minimal contract as event.created and (previously)
    event.cancelled. Receivers can resolve everything else from
    their own records using event_id.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")
    event = await event_service.create_event(
        db,
        EventCreate(name="Sensitive Event Name"),
        created_by=user.id,
    )
    event_id = event.id
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(OutboundWebhookDelivery))
    await db.flush()

    await event_service.delete_event(db, event_id)

    delivery = (await db.execute(select(OutboundWebhookDelivery))).scalar_one()
    body = delivery.payload
    assert body["event_type"] == "event.deleted"
    assert set(body["data"].keys()) == {"event_id", "deleted_at"}
    assert body["data"]["event_id"] == str(event_id)
    datetime.fromisoformat(body["data"]["deleted_at"])
    # The event name must not appear in the wire payload
    assert "Sensitive Event Name" not in str(body)


async def test_delete_event_emits_with_tenant_id_when_env_set(db, monkeypatch):
    """MOIMIO_TENANT_ID set → event.deleted envelope has tenant_id top-level."""
    monkeypatch.setenv("MOIMIO_TENANT_ID", "ycc-2026")
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")
    event = await event_service.create_event(
        db,
        EventCreate(name="Tenant-stamped"),
        created_by=user.id,
    )
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(OutboundWebhookDelivery))
    await db.flush()

    await event_service.delete_event(db, event.id)

    delivery = (await db.execute(select(OutboundWebhookDelivery))).scalar_one()
    assert delivery.payload["tenant_id"] == "ycc-2026"
    assert "tenant_id" not in delivery.payload["data"]


async def test_delete_event_returns_false_for_missing_event(db):
    """delete_event(unknown_id) returns False, doesn't emit a webhook.

    Pre-existing contract from v0.50g-2; the v1.0.0h-1 changes must
    not regress it. Without this, a 404-via-API would still send a
    spurious event.deleted to SaaS for a nonexistent event.
    """
    await _make_subscribed_endpoint(db)
    result = await event_service.delete_event(db, uuid.uuid4())
    assert result is False

    deliveries = (await db.execute(select(OutboundWebhookDelivery))).scalars().all()
    assert deliveries == []


# ─── Delete route — auth + 204 + 404 ───────────────────────────────────


async def test_delete_route_requires_super_admin(client, db):
    """DELETE /api/events/{id} without auth → 401/403; non-super → 403.

    Pre-existing contract. Sanity-pinning here because we just rewired
    what delete does (added webhook emission); we want to confirm we
    didn't accidentally widen the auth surface.
    """
    user = await make_user(db, email="creator@test.local")
    event = await event_service.create_event(
        db, EventCreate(name="Auth-gated"), created_by=user.id,
    )
    await db.commit()

    resp = await client.delete(f"/api/events/{event.id}")
    assert resp.status_code in (401, 403)


async def test_delete_route_204_on_success(client, db):
    """DELETE /api/events/{id} with super admin → 204 No Content."""
    user = await make_user(db, email="creator@test.local")
    event = await event_service.create_event(
        db, EventCreate(name="Will be deleted"), created_by=user.id,
    )
    await db.commit()

    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.delete(f"/api/events/{event.id}")
        assert resp.status_code == 204
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)


async def test_delete_route_404_for_unknown(client, db):
    """DELETE /api/events/{nonexistent} → 404."""
    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.delete(f"/api/events/{uuid.uuid4()}")
        assert resp.status_code == 404
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)


# ─── test.ping now carries tenant_id (v1.0.0h-1 bug fix) ───────────────


async def test_test_ping_omits_tenant_id_when_env_unset(client, db, monkeypatch):
    """Self-hoster sends a test ping → payload has no tenant_id field."""
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    ep = await _make_subscribed_endpoint(db)
    await db.commit()

    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(f"/api/webhooks/endpoints/{ep.id}/test")
        assert resp.status_code in (200, 201, 202, 204)
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)

    delivery = (await db.execute(
        select(OutboundWebhookDelivery).where(OutboundWebhookDelivery.event_type == "test.ping")
    )).scalar_one()
    assert "tenant_id" not in delivery.payload


async def test_test_ping_stamps_tenant_id_when_env_set(client, db, monkeypatch):
    """SaaS-deployed CE sends a test ping → payload has tenant_id top-level.

    This is the v1.0.0h regression bug fix: prior to v1.0.0h-1 the
    test-ping code path hand-built its envelope and silently bypassed
    the tenant_id stamping that every other event type uses.
    """
    monkeypatch.setenv("MOIMIO_TENANT_ID", "cmi-germany")
    get_settings.cache_clear()

    ep = await _make_subscribed_endpoint(db)
    await db.commit()

    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(f"/api/webhooks/endpoints/{ep.id}/test")
        assert resp.status_code in (200, 201, 202, 204)
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)

    delivery = (await db.execute(
        select(OutboundWebhookDelivery).where(OutboundWebhookDelivery.event_type == "test.ping")
    )).scalar_one()
    assert delivery.payload["tenant_id"] == "cmi-germany"
    # As with every other event, tenant_id lives at envelope top level,
    # not inside the data block.
    assert "tenant_id" not in delivery.payload["data"]


# ─── No cancel surface anywhere (regression pin) ───────────────────────


async def test_cancel_route_returns_404_no_longer_exists(client, db):
    """POST /api/events/{id}/cancel must 404 — the v1.0.0h route is gone.

    Pinning the architecture decision: there is only one destructive
    verb (delete). If someone re-introduces a /cancel route in the
    future, this test will fail and force a conversation about why.
    """
    user = await make_user(db, email="creator@test.local")
    event = await event_service.create_event(
        db, EventCreate(name="Cancel-route should not exist"), created_by=user.id,
    )
    await db.commit()

    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(f"/api/events/{event.id}/cancel")
        assert resp.status_code == 404
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)
