"""Tests for v1.0.0y event.allocated emission.

When the allocation engine commits a run for a category
(engine_service.commit_proposal), CE emits an `event.allocated`
webhook in the SAME transaction as the commit. These tests exercise
the full service path (set up event/category/unit/participant, then
commit a proposal) rather than calling queue_event directly.

The contract pinned here:
  • exactly one event.allocated delivery is queued per commit, when a
    subscribed endpoint exists;
  • the delivery is GDPR-minimal — data is exactly {event_id}, with no
    participant data;
  • the BUSINESS event id rides in data.event_id (the correlation key),
    NOT the envelope event_id (which is a per-message idempotency key);
  • a self-hoster with no endpoint sees no delivery and no error.
"""

import uuid

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.services.engine_service import commit_proposal
from tests.conftest import (
    make_user,
    make_event,
    make_category,
    make_unit,
    make_participant,
)


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


async def _setup_one_placement(db):
    """A minimal committable allocation: one unit, one participant.

    Returns (event, category, unit, participant, proposed) where
    `proposed` maps the unit to the single participant, ready to pass
    to commit_proposal.
    """
    await make_user(db, email="organiser@test.local")
    ev = await make_event(db, name="Sommerfreizeit 2026")
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id, first_name="Alice")
    proposed = {str(unit.id): [str(p.id)]}
    return ev, cat, unit, p, proposed


# ─── Emission + count ──────────────────────────────────────────────────


async def test_commit_proposal_queues_one_event_allocated(db, monkeypatch):
    """A committed engine run queues exactly one event.allocated delivery."""
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    ev, cat, _unit, _p, proposed = await _setup_one_placement(db)

    await commit_proposal(db, ev.id, cat.id, proposed)

    deliveries = (await db.execute(select(OutboundWebhookDelivery))).scalars().all()
    assert len(deliveries) == 1
    assert deliveries[0].event_type == "event.allocated"
    assert deliveries[0].status == WebhookDeliveryStatus.PENDING


# ─── Payload shape + correlation key ────────────────────────────────────


async def test_event_allocated_payload_is_minimal_and_keyed_on_business_id(
    db, monkeypatch
):
    """data is exactly {event_id}, holding the BUSINESS event id.

    The envelope event_id is a per-message idempotency key and must NOT
    be the business id — the receiver correlates on data.event_id. This
    pins both: data carries the event's id, and the envelope id is a
    distinct per-message value (guards against anyone reintroducing the
    'envelope id == business id' bug, which would break self-hosters'
    documented dedupe).
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    ev, cat, _unit, _p, proposed = await _setup_one_placement(db)

    await commit_proposal(db, ev.id, cat.id, proposed)

    body = (await db.execute(select(OutboundWebhookDelivery))).scalar_one().payload

    # data is GDPR-minimal: only the event id, no participant data.
    assert set(body["data"].keys()) == {"event_id"}
    assert body["data"]["event_id"] == str(ev.id)
    assert "Alice" not in str(body["data"])

    # The envelope event_id is a per-message id (a fresh UUID), NOT the
    # business event id.
    assert body["event_id"] != str(ev.id)
    uuid.UUID(body["event_id"])  # parseable UUID


# ─── No subscriber → no delivery, but the commit still succeeds ─────────


async def test_commit_proposal_no_endpoints_succeeds_silently(db, monkeypatch):
    """Self-hoster with no webhook endpoint: the allocation commits, no
    delivery is queued, and nothing raises."""
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    ev, cat, _unit, _p, proposed = await _setup_one_placement(db)

    result = await commit_proposal(db, ev.id, cat.id, proposed)

    # The allocation landed...
    assert result["created"] == 1
    # ...and no delivery was queued.
    deliveries = (await db.execute(select(OutboundWebhookDelivery))).scalars().all()
    assert deliveries == []
