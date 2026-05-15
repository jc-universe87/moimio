"""Tests for v1.0.0h event.created emission — payload shape, envelope-
level tenant_id stamping, atomicity with event creation.

These tests exercise the full service path (event_service.create_event)
rather than queue_event directly, so we cover the whole "create event +
queue webhook in same transaction" flow.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.event import Event
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.schemas.event import EventCreate
from app.services import event_service
from tests.conftest import make_user


pytestmark = pytest.mark.asyncio


async def _make_subscribed_endpoint(db) -> OutboundWebhookEndpoint:
    """Active endpoint subscribed to all event types so deliveries persist."""
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


# ─── Payload shape ──────────────────────────────────────────────────────


async def test_create_event_queues_one_delivery(db, monkeypatch):
    """Successful event creation queues exactly one event.created delivery
    when a subscribed endpoint exists.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")

    await event_service.create_event(
        db,
        EventCreate(name="Spring Retreat 2026"),
        created_by=user.id,
    )

    result = await db.execute(select(OutboundWebhookDelivery))
    deliveries = result.scalars().all()
    assert len(deliveries) == 1
    assert deliveries[0].event_type == "event.created"
    assert deliveries[0].status == WebhookDeliveryStatus.PENDING


async def test_event_created_payload_is_minimal(db, monkeypatch):
    """event.created data block has exactly {event_id, created_at}.

    No event name, no admin email, no created_by — receivers can
    resolve those from their own records using event_id. Locked
    GDPR-minimal decision; this test pins it.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")

    event = await event_service.create_event(
        db,
        EventCreate(name="A Sensitive Name That Must Not Leak"),
        created_by=user.id,
    )

    delivery = (await db.execute(select(OutboundWebhookDelivery))).scalar_one()
    body = delivery.payload

    assert set(body["data"].keys()) == {"event_id", "created_at"}
    assert body["data"]["event_id"] == str(event.id)
    # Confirm the timestamp is ISO-8601 parseable
    datetime.fromisoformat(body["data"]["created_at"])
    # And the name is not in data (paranoid check, since the lock matters)
    assert "A Sensitive Name" not in str(body["data"])


# ─── Envelope-level tenant_id stamping ──────────────────────────────────


async def test_event_created_envelope_omits_tenant_id_when_env_unset(db, monkeypatch):
    """No MOIMIO_TENANT_ID → no tenant_id key on the envelope."""
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")

    await event_service.create_event(
        db,
        EventCreate(name="Self-host install"),
        created_by=user.id,
    )

    delivery = (await db.execute(select(OutboundWebhookDelivery))).scalar_one()
    assert "tenant_id" not in delivery.payload


async def test_event_created_envelope_stamps_tenant_id_when_env_set(db, monkeypatch):
    """MOIMIO_TENANT_ID=cmi-germany → envelope has tenant_id top-level."""
    monkeypatch.setenv("MOIMIO_TENANT_ID", "cmi-germany")
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    user = await make_user(db, email="creator@test.local")

    await event_service.create_event(
        db,
        EventCreate(name="SaaS install"),
        created_by=user.id,
    )

    delivery = (await db.execute(select(OutboundWebhookDelivery))).scalar_one()
    body = delivery.payload
    assert body["tenant_id"] == "cmi-germany"
    # Tenant ID lives on the envelope, NOT in data (routing metadata,
    # not resource metadata).
    assert "tenant_id" not in body["data"]


# ─── No subscriber → no delivery, but creation still succeeds ───────────


async def test_create_event_no_endpoints_succeeds_silently(db, monkeypatch):
    """Self-hoster with no webhook endpoints: event creation works,
    no delivery row queued, no error raised.

    This is the typical self-hoster path — queue_event finds nothing
    subscribed and returns gracefully.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    user = await make_user(db, email="self-hoster@test.local")

    event = await event_service.create_event(
        db,
        EventCreate(name="Local-only event"),
        created_by=user.id,
    )

    # Event was created
    assert event.id is not None
    survivor = await db.execute(select(Event).where(Event.id == event.id))
    assert survivor.scalar_one_or_none() is not None
    # No delivery queued
    result = await db.execute(select(OutboundWebhookDelivery))
    assert result.scalars().all() == []
