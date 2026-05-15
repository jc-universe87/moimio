"""Tests for the outbound webhook subsystem (v1.0.0g).

Pure-function tests run anywhere. DB-dependent tests use the `db` fixture
which gracefully skips if no Postgres is reachable.
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx
import pytest

from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.services import webhook_service


# ─── Pure-function tests (no DB) ────────────────────────────────────────


def test_sign_payload_format():
    """Header format ts=<int>;h1=<64 hex chars>."""
    sig = webhook_service.sign_payload(
        raw_body=b'{"x":1}', secret="s3cret", ts=1234567890
    )
    assert sig.startswith("ts=1234567890;h1=")
    h1 = sig.split("h1=")[1]
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_sign_payload_matches_external_hmac():
    """Sanity check: we produce the same HMAC the receiver would compute."""
    body = b'{"event_id":"abc","data":{"x":1}}'
    secret = "s3cret"
    ts = 1234567890
    sig = webhook_service.sign_payload(raw_body=body, secret=secret, ts=ts)
    h1 = sig.split("h1=")[1]
    expected = hmac.new(
        secret.encode(),
        f"{ts}:".encode() + body,
        hashlib.sha256,
    ).hexdigest()
    assert h1 == expected


def test_sign_payload_uses_current_time_when_not_given(monkeypatch):
    """ts defaults to time.time() when omitted."""
    monkeypatch.setattr(time, "time", lambda: 9999.0)
    sig = webhook_service.sign_payload(raw_body=b"{}", secret="s")
    assert sig.startswith("ts=9999;")


def test_secrets_match_constant_time():
    """Constant-time compare. Smoke test: equal returns True, off-by-one returns False."""
    assert webhook_service.secrets_match("abcd", "abcd") is True
    assert webhook_service.secrets_match("abcd", "abce") is False
    assert webhook_service.secrets_match("abcd", "abc") is False
    assert webhook_service.secrets_match("", "") is True


def test_generate_secret_strong():
    """Generated secrets have enough entropy and are URL-safe."""
    secrets_seen = {webhook_service.generate_secret() for _ in range(100)}
    assert len(secrets_seen) == 100  # no collisions in 100 draws
    for s in secrets_seen:
        # base64url charset only
        assert all(c.isalnum() or c in "-_" for c in s)
        assert len(s) >= 40  # ~43 chars for 32 bytes


def test_endpoint_subscribes_to_wildcard():
    ep = OutboundWebhookEndpoint(
        name="x", url="https://x", secret="s",
        event_types=["*"], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE,
    )
    assert webhook_service.endpoint_subscribes_to(ep, "anything.at.all") is True
    assert webhook_service.endpoint_subscribes_to(ep, "test.ping") is True


def test_endpoint_subscribes_to_explicit_list():
    ep = OutboundWebhookEndpoint(
        name="x", url="https://x", secret="s",
        event_types=["event.created", "event.cancelled"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE,
    )
    assert webhook_service.endpoint_subscribes_to(ep, "event.created") is True
    assert webhook_service.endpoint_subscribes_to(ep, "event.cancelled") is True
    assert webhook_service.endpoint_subscribes_to(ep, "test.ping") is False
    assert webhook_service.endpoint_subscribes_to(ep, "other.event") is False


def test_endpoint_subscribes_to_empty_list_subscribes_to_nothing():
    """Defensive: empty event_types means no subscription. Wildcard `*` is the
    explicit 'all' signal."""
    ep = OutboundWebhookEndpoint(
        name="x", url="https://x", secret="s",
        event_types=[], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE,
    )
    assert webhook_service.endpoint_subscribes_to(ep, "event.created") is False


def test_serialize_payload_stable_key_order():
    """Different insertion order produces identical bytes (signature stability)."""
    a = webhook_service._serialize_payload({"b": 2, "a": 1, "c": 3})
    b = webhook_service._serialize_payload({"c": 3, "a": 1, "b": 2})
    assert a == b
    assert a == b'{"a":1,"b":2,"c":3}'


def test_envelope_shape():
    """Canonical envelope has event_id, event_type, timestamp, data."""
    eid = uuid.uuid4()
    now = datetime(2026, 5, 12, 11, 34, 0, tzinfo=timezone.utc)
    env = webhook_service._envelope(eid, "test.ping", {"hello": "world"}, now)
    assert env == {
        "event_id": str(eid),
        "event_type": "test.ping",
        "timestamp": "2026-05-12T11:34:00+00:00",
        "data": {"hello": "world"},
    }


def test_retry_schedule_matches_spec():
    """Schedule: 30s, 2min, 10min, 1h, 6h."""
    assert webhook_service.RETRY_SCHEDULE_SECONDS == [30, 120, 600, 3600, 21600]


def test_state_thresholds_match_spec():
    assert webhook_service.DEGRADED_AFTER_FAILURES == 5
    assert webhook_service.DISABLED_AFTER_FAILURES == 20


# ─── Internal state-transition tests (no DB; manipulate ORM objects directly) ──


def _make_endpoint(**kw) -> OutboundWebhookEndpoint:
    return OutboundWebhookEndpoint(
        id=uuid.uuid4(),
        name=kw.get("name", "t"),
        url=kw.get("url", "https://example.com/hook"),
        secret=kw.get("secret", "s"),
        event_types=kw.get("event_types", ["*"]),
        state=kw.get("state", WebhookEndpointState.ACTIVE),
        consecutive_failures=kw.get("consecutive_failures", 0),
        managed_by=kw.get("managed_by", WebhookEndpointManagedBy.USER),
        is_active=kw.get("is_active", True),
    )


def _make_delivery(**kw) -> OutboundWebhookDelivery:
    return OutboundWebhookDelivery(
        id=uuid.uuid4(),
        endpoint_id=kw.get("endpoint_id", uuid.uuid4()),
        event_id=kw.get("event_id", uuid.uuid4()),
        event_type=kw.get("event_type", "test.ping"),
        payload=kw.get("payload", {}),
        attempt=kw.get("attempt", 0),
        status=kw.get("status", WebhookDeliveryStatus.PENDING),
        next_attempt_at=kw.get("next_attempt_at", datetime.now(timezone.utc)),
    )


def test_record_success_resets_consecutive_failures():
    ep = _make_endpoint(consecutive_failures=4)
    d = _make_delivery()
    webhook_service._record_success(d, ep)
    assert ep.consecutive_failures == 0
    assert ep.last_success_at is not None
    assert d.status == WebhookDeliveryStatus.SUCCESS


def test_record_success_recovers_from_degraded():
    ep = _make_endpoint(
        state=WebhookEndpointState.DEGRADED, consecutive_failures=7
    )
    d = _make_delivery()
    webhook_service._record_success(d, ep)
    assert ep.state == WebhookEndpointState.ACTIVE


def test_record_success_does_not_unilaterally_recover_from_disabled():
    """DISABLED requires manual re-enable. A miraculous success should not
    silently un-disable (admin needs to investigate first)."""
    ep = _make_endpoint(
        state=WebhookEndpointState.DISABLED, consecutive_failures=20
    )
    d = _make_delivery()
    webhook_service._record_success(d, ep)
    # Failure count is reset (legitimate), but state stays DISABLED.
    assert ep.consecutive_failures == 0
    assert ep.state == WebhookEndpointState.DISABLED


def test_record_failure_schedules_first_retry_after_30s():
    ep = _make_endpoint()
    d = _make_delivery(attempt=0)
    before = datetime.now(timezone.utc)
    webhook_service._record_failure(
        d, ep, response_status=500, error="http 500"
    )
    after = datetime.now(timezone.utc)
    # next_attempt_at should be ~30s from now
    delay = (d.next_attempt_at - before).total_seconds()
    assert 29 <= delay <= 31
    assert d.attempt == 1
    assert d.status == WebhookDeliveryStatus.PENDING
    assert ep.consecutive_failures == 1


def test_record_failure_exhausts_after_all_retries():
    ep = _make_endpoint()
    d = _make_delivery(
        attempt=len(webhook_service.RETRY_SCHEDULE_SECONDS)  # past the last retry
    )
    webhook_service._record_failure(
        d, ep, response_status=500, error="http 500"
    )
    assert d.status == WebhookDeliveryStatus.EXHAUSTED


def test_record_failure_degrades_after_5_consecutive():
    ep = _make_endpoint(consecutive_failures=4)  # one more makes 5
    d = _make_delivery(attempt=0)
    webhook_service._record_failure(
        d, ep, response_status=500, error="http 500"
    )
    assert ep.consecutive_failures == 5
    assert ep.state == WebhookEndpointState.DEGRADED


def test_record_failure_disables_after_20_consecutive():
    ep = _make_endpoint(
        state=WebhookEndpointState.DEGRADED, consecutive_failures=19,
    )
    d = _make_delivery(attempt=0)
    webhook_service._record_failure(
        d, ep, response_status=500, error="http 500"
    )
    assert ep.consecutive_failures == 20
    assert ep.state == WebhookEndpointState.DISABLED


def test_record_failure_truncates_long_error():
    ep = _make_endpoint()
    d = _make_delivery(attempt=0)
    webhook_service._record_failure(
        d, ep, response_status=None, error="x" * 5000,
    )
    assert len(d.error) == 2000


# ─── DB-dependent tests (skip if no Postgres) ──────────────────────────


@pytest.mark.anyio
async def test_queue_event_creates_delivery_per_subscribed_endpoint(db):
    """One event → one delivery per subscribed endpoint."""
    ep1 = OutboundWebhookEndpoint(
        name="ep1", url="https://a.example/h", secret="s1",
        event_types=["*"], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    ep2 = OutboundWebhookEndpoint(
        name="ep2", url="https://b.example/h", secret="s2",
        event_types=["other.event"], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add_all([ep1, ep2])
    await db.flush()

    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={"hello": "world"},
    )
    # ep1 subscribes to *, ep2 doesn't subscribe to test.ping
    assert len(deliveries) == 1
    assert deliveries[0].endpoint_id == ep1.id
    assert deliveries[0].event_type == "test.ping"
    assert deliveries[0].payload["data"] == {"hello": "world"}


@pytest.mark.anyio
async def test_queue_event_skips_disabled_endpoint(db):
    ep = OutboundWebhookEndpoint(
        name="dead", url="https://dead.example/h", secret="s",
        event_types=["*"], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.DISABLED, is_active=True,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={}
    )
    assert deliveries == []


@pytest.mark.anyio
async def test_queue_event_skips_paused_endpoint(db):
    ep = OutboundWebhookEndpoint(
        name="paused", url="https://p.example/h", secret="s",
        event_types=["*"], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=False,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={}
    )
    assert deliveries == []


@pytest.mark.anyio
async def test_ensure_saas_endpoint_creates_on_first_boot(db):
    ep = await webhook_service.ensure_saas_endpoint(
        db, url="https://saas.example/h", secret="s3cret",
    )
    assert ep is not None
    assert ep.managed_by == WebhookEndpointManagedBy.SAAS
    assert ep.event_types == ["*"]
    assert ep.secret == "s3cret"


@pytest.mark.anyio
async def test_ensure_saas_endpoint_idempotent(db):
    ep1 = await webhook_service.ensure_saas_endpoint(
        db, url="https://saas.example/h", secret="s3cret",
    )
    ep2 = await webhook_service.ensure_saas_endpoint(
        db, url="https://saas.example/h", secret="s3cret",
    )
    assert ep1.id == ep2.id


@pytest.mark.anyio
async def test_ensure_saas_endpoint_updates_on_secret_rotation(db):
    ep1 = await webhook_service.ensure_saas_endpoint(
        db, url="https://saas.example/h", secret="old",
    )
    ep2 = await webhook_service.ensure_saas_endpoint(
        db, url="https://saas.example/h", secret="new",
    )
    assert ep1.id == ep2.id
    assert ep2.secret == "new"


@pytest.mark.anyio
async def test_ensure_saas_endpoint_returns_none_when_url_missing(db):
    ep = await webhook_service.ensure_saas_endpoint(db, url="", secret="x")
    assert ep is None


@pytest.mark.anyio
async def test_prune_old_deliveries_removes_old_keeps_new(db):
    ep = OutboundWebhookEndpoint(
        name="x", url="https://x", secret="s", event_types=["*"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.flush()

    now = datetime.now(timezone.utc)
    old = OutboundWebhookDelivery(
        endpoint_id=ep.id, event_id=uuid.uuid4(),
        event_type="test.ping", payload={}, attempt=0,
        status=WebhookDeliveryStatus.SUCCESS,
        next_attempt_at=now - timedelta(days=60),
    )
    db.add(old)
    await db.flush()
    # Manually backdate created_at (server_default would be now)
    from sqlalchemy import update
    await db.execute(
        update(OutboundWebhookDelivery)
        .where(OutboundWebhookDelivery.id == old.id)
        .values(created_at=now - timedelta(days=60))
    )
    await db.commit()

    fresh = OutboundWebhookDelivery(
        endpoint_id=ep.id, event_id=uuid.uuid4(),
        event_type="test.ping", payload={}, attempt=0,
        status=WebhookDeliveryStatus.SUCCESS,
        next_attempt_at=now,
    )
    db.add(fresh)
    await db.commit()

    removed = await webhook_service.prune_old_deliveries(
        db, retention_days=30, now=now,
    )
    assert removed == 1
    # Fresh one survives
    survivor = await db.get(OutboundWebhookDelivery, fresh.id)
    assert survivor is not None
    # Old one is gone
    gone = await db.get(OutboundWebhookDelivery, old.id)
    assert gone is None


@pytest.mark.anyio
async def test_process_pending_deliveries_handles_success(db):
    """When the receiver returns 200, delivery is marked SUCCESS."""
    ep = OutboundWebhookEndpoint(
        name="ok", url="https://ok.example/h", secret="s", event_types=["*"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={"x": 1}
    )
    await db.commit()

    # Mock httpx.AsyncClient to return 200
    transport = httpx.MockTransport(lambda req: httpx.Response(200, text="ok"))
    async with httpx.AsyncClient(transport=transport, timeout=5.0) as client:
        n = await webhook_service.process_pending_deliveries(
            db, http_client=client,
        )
    assert n == 1
    await db.refresh(deliveries[0])
    assert deliveries[0].status == WebhookDeliveryStatus.SUCCESS
    assert deliveries[0].response_status == 200


@pytest.mark.anyio
async def test_process_pending_deliveries_schedules_retry_on_500(db):
    ep = OutboundWebhookEndpoint(
        name="flaky", url="https://flaky.example/h", secret="s",
        event_types=["*"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={"x": 1}
    )
    await db.commit()

    transport = httpx.MockTransport(
        lambda req: httpx.Response(500, text="boom")
    )
    async with httpx.AsyncClient(transport=transport, timeout=5.0) as client:
        await webhook_service.process_pending_deliveries(
            db, http_client=client,
        )
    await db.refresh(deliveries[0])
    assert deliveries[0].status == WebhookDeliveryStatus.PENDING
    assert deliveries[0].attempt == 1
    assert deliveries[0].next_attempt_at > datetime.now(timezone.utc)
