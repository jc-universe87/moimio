"""Tests for v1.0.0y event.over_cap emission.

CE watches an event's active roster (confirmed + pending, excluding
removed) and, the first time it crosses the configured participant cap
(MOIMIO_PARTICIPANT_CAP), emits ONE event.over_cap webhook with an
approximate band — never the exact count — and the cap. It fires once,
never blocks, and is a complete no-op when no cap is configured
(self-hosters).

These exercise the maybe_signal_over_cap helper directly with a small
cap, so we don't have to create 300+ rows. The band function is unit-
tested separately on realistic values.
"""

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.event import Event
from app.models.participant import RegistrationStatus
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.services.participant_service import (
    maybe_signal_over_cap,
    _round_up_to_band,
    soft_delete_participant,
)
from tests.conftest import make_user, make_event, make_participant


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """Settings are cached; clear around each test so an env cap set here
    is read freshly and never leaks into other test files."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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


async def _deliveries(db):
    return (await db.execute(select(OutboundWebhookDelivery))).scalars().all()


# ─── band (pure function, realistic values) ─────────────────────────────


def test_band_rounds_up_to_next_50():
    assert _round_up_to_band(300) == 300
    assert _round_up_to_band(301) == 350
    assert _round_up_to_band(312) == 350
    assert _round_up_to_band(350) == 350
    assert _round_up_to_band(351) == 400
    assert _round_up_to_band(1) == 50


# ─── crossing the cap: one signal, right band + id, flag set ────────────


async def test_crossing_cap_emits_one_over_cap(db, monkeypatch):
    monkeypatch.setenv("MOIMIO_PARTICIPANT_CAP", "3")
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    await make_user(db, email="o@test.local")
    ev = await make_event(db, name="Big Camp")
    for i in range(4):  # 4 active > cap of 3
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    assert await maybe_signal_over_cap(db, ev.id) is True

    ds = await _deliveries(db)
    assert len(ds) == 1
    d = ds[0]
    assert d.event_type == "event.over_cap"
    assert d.status == WebhookDeliveryStatus.PENDING
    assert d.payload["data"]["event_id"] == str(ev.id)
    assert d.payload["data"]["cap"] == 3
    # An approximate band, not the exact count. 4 rounds up to the 50-band.
    assert d.payload["data"]["participant_estimate"] == 50
    # The exact count (4) never appears in the payload.
    assert "4" not in str(d.payload["data"]["participant_estimate"])

    refreshed = await db.get(Event, ev.id)
    assert refreshed.over_cap_signalled is True


# ─── fires once, even as more register ──────────────────────────────────


async def test_over_cap_fires_only_once(db, monkeypatch):
    monkeypatch.setenv("MOIMIO_PARTICIPANT_CAP", "3")
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    await make_user(db, email="o@test.local")
    ev = await make_event(db, name="Big Camp")
    for i in range(4):
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    assert await maybe_signal_over_cap(db, ev.id) is True
    # more registrations after the first crossing
    await make_participant(db, event_id=ev.id, first_name="late")
    assert await maybe_signal_over_cap(db, ev.id) is False

    assert len(await _deliveries(db)) == 1  # still just the one


# ─── at/under cap: silent ───────────────────────────────────────────────


async def test_at_or_under_cap_no_signal(db, monkeypatch):
    monkeypatch.setenv("MOIMIO_PARTICIPANT_CAP", "3")
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    await make_user(db, email="o@test.local")
    ev = await make_event(db, name="Small Camp")
    for i in range(3):  # exactly at cap, not over
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    assert await maybe_signal_over_cap(db, ev.id) is False
    assert await _deliveries(db) == []
    refreshed = await db.get(Event, ev.id)
    assert refreshed.over_cap_signalled is False


# ─── no cap configured: silent (self-hoster path) ───────────────────────


async def test_unset_cap_is_silent(db, monkeypatch):
    monkeypatch.delenv("MOIMIO_PARTICIPANT_CAP", raising=False)
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    await make_user(db, email="o@test.local")
    ev = await make_event(db, name="Self-host Camp")
    for i in range(10):  # well over any cap, but none is configured
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    assert await maybe_signal_over_cap(db, ev.id) is False
    assert await _deliveries(db) == []


# ─── cancelled + removed do NOT count toward the cap ────────────────────


async def test_cancelled_and_removed_excluded_from_count(db, monkeypatch):
    monkeypatch.setenv("MOIMIO_PARTICIPANT_CAP", "3")
    get_settings.cache_clear()

    await _make_subscribed_endpoint(db)
    await make_user(db, email="o@test.local")
    ev = await make_event(db, name="Mixed Camp")
    # 3 active (confirmed) — at cap, not over.
    for i in range(3):
        await make_participant(db, event_id=ev.id, first_name=f"A{i}")
    # Noise that must NOT count: 5 cancelled + 5 removed (soft-deleted).
    for i in range(5):
        await make_participant(
            db, event_id=ev.id, first_name=f"C{i}",
            status=RegistrationStatus.CANCELLED,
        )
    for i in range(5):
        p = await make_participant(db, event_id=ev.id, first_name=f"D{i}")
        await soft_delete_participant(db, p)

    # Active = 3 ≤ cap 3 → silent. If cancelled/removed were counted,
    # 13 > 3 would fire — so a silent result proves the exclusion.
    assert await maybe_signal_over_cap(db, ev.id) is False
    assert await _deliveries(db) == []
