"""Outbound webhook service (v1.0.0g).

Responsibilities:
- Generate strong random secrets server-side at endpoint creation
- Sign outbound payloads with HMAC-SHA256, header format symmetric with
  inbound Paddle pattern: `Moimio-Signature: ts=<unix>;h1=<hex_hmac>`
- Queue events for delivery (one `OutboundWebhookDelivery` row per
  endpoint × event)
- Attempt delivery via httpx, classify the outcome, schedule retry on
  the agreed schedule (30s / 2min / 10min / 1h / 6h), then exhaust
- Update endpoint state on consecutive-failure thresholds (5 → degraded,
  20 → disabled)
- Prune deliveries older than retention window

Secret storage: plaintext at-rest. CE is the sender; it must produce a
fresh HMAC per delivery and therefore needs recoverable secrets. The
"shown once via UI" UX is enforced at the API layer, not at the
storage layer.
"""

import hashlib
import hmac
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import and_, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)


log = get_logger(__name__)

# Retry schedule in seconds. Index N gives the delay applied AFTER
# attempt N fails, before attempt N+1. Total attempts = 1 (initial) +
# len(schedule) = 6.
RETRY_SCHEDULE_SECONDS: list[int] = [30, 120, 600, 3600, 21600]

# Endpoint state thresholds (consecutive failures across all deliveries).
DEGRADED_AFTER_FAILURES = 5
DISABLED_AFTER_FAILURES = 20

# httpx timeout for a single delivery attempt.
DELIVERY_TIMEOUT_SECONDS = 15.0

# Acceptable response codes (any 2xx).
SUCCESS_CODES = range(200, 300)


# ── Secret generation ──

def generate_secret() -> str:
    """Generate a fresh URL-safe random secret.

    32 bytes of randomness → 43-char base64url string. Indistinguishable
    from GitHub PATs / Stripe restricted keys in terms of entropy.
    """
    return secrets.token_urlsafe(32)


# ── Signing ──

def sign_payload(*, raw_body: bytes, secret: str, ts: int | None = None) -> str:
    """Produce a Moimio-Signature header value for the given body.

    Format mirrors Paddle's inbound convention so the receiver-side code
    can be symmetric. `ts=<unix>;h1=<hex_hmac_sha256_of(ts:body)>`.
    """
    ts = ts if ts is not None else int(time.time())
    mac_payload = f"{ts}:".encode() + raw_body
    h1 = hmac.new(secret.encode(), mac_payload, hashlib.sha256).hexdigest()
    return f"ts={ts};h1={h1}"


def secrets_match(provided: str, expected: str) -> bool:
    """Constant-time equality for two secret strings."""
    return hmac.compare_digest(provided, expected)


# ── Subscription matching ──

def endpoint_subscribes_to(
    endpoint: OutboundWebhookEndpoint, event_type: str
) -> bool:
    """Does this endpoint want events of this type?"""
    types = endpoint.event_types or []
    return "*" in types or event_type in types


# ── Event queuing ──

async def queue_event(
    db: AsyncSession,
    *,
    event_type: str,
    data: dict[str, Any],
    event_id: uuid.UUID | None = None,
) -> list[OutboundWebhookDelivery]:
    """Queue an event for delivery to all subscribed, active endpoints.

    Returns one OutboundWebhookDelivery row per endpoint that subscribes
    to this event type. Disabled or paused endpoints are skipped silently.

    Caller is responsible for committing the session. The scheduled
    worker job will pick up these PENDING rows on its next tick.
    """
    if event_id is None:
        event_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(OutboundWebhookEndpoint).where(
            and_(
                OutboundWebhookEndpoint.is_active.is_(True),
                OutboundWebhookEndpoint.state != WebhookEndpointState.DISABLED,
            )
        )
    )
    endpoints = list(result.scalars())

    deliveries: list[OutboundWebhookDelivery] = []
    payload = _envelope(event_id, event_type, data, now)

    for ep in endpoints:
        if not endpoint_subscribes_to(ep, event_type):
            continue
        d = OutboundWebhookDelivery(
            endpoint_id=ep.id,
            event_id=event_id,
            event_type=event_type,
            payload=payload,
            attempt=0,
            status=WebhookDeliveryStatus.PENDING,
            next_attempt_at=now,
        )
        db.add(d)
        deliveries.append(d)

    log.info(
        "outbound_webhook.event_queued",
        event_id=str(event_id),
        event_type=event_type,
        n_endpoints=len(deliveries),
    )
    return deliveries


def _envelope(
    event_id: uuid.UUID,
    event_type: str,
    data: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    """Canonical outbound envelope. v1.0.0g — keep this shape stable.

    v1.0.0h: optional top-level `tenant_id` field stamped when
    MOIMIO_TENANT_ID is set in the environment. Omitted entirely when
    blank — self-hosters who don't set the env var see no change in
    payload shape.
    """
    envelope: dict[str, Any] = {
        "event_id": str(event_id),
        "event_type": event_type,
        "timestamp": now.isoformat(),
        "data": data,
    }
    tenant_id = get_settings().moimio_tenant_id
    if tenant_id:
        envelope["tenant_id"] = tenant_id
    return envelope


# ── Delivery worker ──

async def process_pending_deliveries(
    db: AsyncSession,
    *,
    now: datetime | None = None,
    batch_size: int = 50,
    http_client: httpx.AsyncClient | None = None,
) -> int:
    """Attempt all PENDING deliveries whose `next_attempt_at <= now`.

    Returns the number of deliveries processed. Commits per-delivery so
    a single bad receiver doesn't roll back the batch.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    result = await db.execute(
        select(OutboundWebhookDelivery)
        .where(
            and_(
                OutboundWebhookDelivery.status == WebhookDeliveryStatus.PENDING,
                OutboundWebhookDelivery.next_attempt_at <= now,
            )
        )
        .order_by(OutboundWebhookDelivery.next_attempt_at.asc())
        .limit(batch_size)
    )
    due = list(result.scalars())
    if not due:
        return 0

    owns_client = http_client is None
    if owns_client:
        http_client = httpx.AsyncClient(timeout=DELIVERY_TIMEOUT_SECONDS)

    processed = 0
    try:
        for delivery in due:
            ep = await db.get(OutboundWebhookEndpoint, delivery.endpoint_id)
            if ep is None:
                delivery.status = WebhookDeliveryStatus.EXHAUSTED
                delivery.attempted_at = datetime.now(timezone.utc)
                delivery.error = "endpoint deleted"
                await db.commit()
                processed += 1
                continue

            if not ep.is_active or ep.state == WebhookEndpointState.DISABLED:
                delivery.status = WebhookDeliveryStatus.EXHAUSTED
                delivery.attempted_at = datetime.now(timezone.utc)
                delivery.error = "endpoint not active"
                await db.commit()
                processed += 1
                continue

            await _attempt_delivery(db, http_client, ep, delivery)
            processed += 1
    finally:
        if owns_client and http_client is not None:
            await http_client.aclose()

    return processed


async def _attempt_delivery(
    db: AsyncSession,
    http_client: httpx.AsyncClient,
    endpoint: OutboundWebhookEndpoint,
    delivery: OutboundWebhookDelivery,
) -> None:
    """Send one delivery, classify outcome, update endpoint + delivery."""
    raw_body = _serialize_payload(delivery.payload)
    signature = sign_payload(raw_body=raw_body, secret=endpoint.secret)
    headers = {
        "Content-Type": "application/json",
        "Moimio-Signature": signature,
        "Moimio-Event-Id": str(delivery.event_id),
        "Moimio-Event-Type": delivery.event_type,
        "User-Agent": "Moimio-Webhook/1.0",
    }

    started = time.monotonic()
    delivery.attempted_at = datetime.now(timezone.utc)

    try:
        resp = await http_client.post(
            endpoint.url, content=raw_body, headers=headers
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)
        delivery.response_status = resp.status_code
        delivery.duration_ms = elapsed_ms

        if resp.status_code in SUCCESS_CODES:
            _record_success(delivery, endpoint)
            await db.commit()
            log.info(
                "outbound_webhook.delivered",
                endpoint_id=str(endpoint.id),
                event_id=str(delivery.event_id),
                event_type=delivery.event_type,
                attempt=delivery.attempt,
                response_status=resp.status_code,
                duration_ms=elapsed_ms,
            )
            return

        err = f"http {resp.status_code}"
        _record_failure(
            delivery, endpoint,
            response_status=resp.status_code, error=err,
        )
    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        delivery.duration_ms = elapsed_ms
        _record_failure(
            delivery, endpoint, response_status=None, error="timeout"
        )
    except httpx.HTTPError as exc:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        delivery.duration_ms = elapsed_ms
        _record_failure(
            delivery, endpoint,
            response_status=None, error=str(exc)[:2000],
        )

    await db.commit()
    log.info(
        "outbound_webhook.delivery_failed",
        endpoint_id=str(endpoint.id),
        event_id=str(delivery.event_id),
        event_type=delivery.event_type,
        attempt=delivery.attempt,
        response_status=delivery.response_status,
        error=delivery.error,
    )


def _record_success(
    delivery: OutboundWebhookDelivery, endpoint: OutboundWebhookEndpoint
) -> None:
    now = datetime.now(timezone.utc)
    delivery.status = WebhookDeliveryStatus.SUCCESS
    endpoint.consecutive_failures = 0
    endpoint.last_success_at = now
    if endpoint.state == WebhookEndpointState.DEGRADED:
        endpoint.state = WebhookEndpointState.ACTIVE


def _record_failure(
    delivery: OutboundWebhookDelivery,
    endpoint: OutboundWebhookEndpoint,
    *,
    response_status: int | None,
    error: str,
) -> None:
    now = datetime.now(timezone.utc)
    delivery.error = error[:2000]
    delivery.response_status = response_status
    endpoint.last_failure_at = now
    endpoint.consecutive_failures = (endpoint.consecutive_failures or 0) + 1

    if endpoint.consecutive_failures >= DISABLED_AFTER_FAILURES:
        endpoint.state = WebhookEndpointState.DISABLED
    elif endpoint.consecutive_failures >= DEGRADED_AFTER_FAILURES:
        if endpoint.state == WebhookEndpointState.ACTIVE:
            endpoint.state = WebhookEndpointState.DEGRADED

    if delivery.attempt < len(RETRY_SCHEDULE_SECONDS):
        delay = RETRY_SCHEDULE_SECONDS[delivery.attempt]
        delivery.status = WebhookDeliveryStatus.PENDING
        delivery.next_attempt_at = now + timedelta(seconds=delay)
        delivery.attempt += 1
    else:
        delivery.status = WebhookDeliveryStatus.EXHAUSTED


def _serialize_payload(payload: dict[str, Any]) -> bytes:
    """JSON-serialize with stable key order so signatures are reproducible."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


# ── Maintenance ──

async def prune_old_deliveries(
    db: AsyncSession,
    *,
    retention_days: int,
    now: datetime | None = None,
) -> int:
    """Delete deliveries older than retention. Returns number removed."""
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    result = await db.execute(
        delete(OutboundWebhookDelivery).where(
            OutboundWebhookDelivery.created_at < cutoff
        )
    )
    await db.commit()
    n = result.rowcount or 0
    if n > 0:
        log.info(
            "outbound_webhook.delivery_log_pruned",
            removed=n,
            retention_days=retention_days,
        )
    return n


# ── SaaS auto-registration ──

async def ensure_saas_endpoint(
    db: AsyncSession,
    *,
    url: str,
    secret: str,
) -> OutboundWebhookEndpoint | None:
    """Register the SaaS-managed webhook endpoint if not already present.

    Idempotent: if a SaaS-managed endpoint exists with matching URL and
    secret, nothing changes. If either differs (SaaS rotated the secret
    or moved the endpoint), the existing row is updated to match.

    Returns the endpoint (created or updated), or None if env config is
    incomplete.
    """
    if not url or not secret:
        return None

    result = await db.execute(
        select(OutboundWebhookEndpoint).where(
            OutboundWebhookEndpoint.managed_by == WebhookEndpointManagedBy.SAAS
        )
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        endpoint = OutboundWebhookEndpoint(
            name="Moimio SaaS (managed)",
            url=url,
            secret=secret,
            event_types=["*"],
            state=WebhookEndpointState.ACTIVE,
            consecutive_failures=0,
            managed_by=WebhookEndpointManagedBy.SAAS,
            is_active=True,
        )
        db.add(endpoint)
        await db.commit()
        await db.refresh(endpoint)
        log.info(
            "outbound_webhook.saas_endpoint_created",
            endpoint_id=str(endpoint.id),
        )
        return endpoint

    changed = False
    if existing.url != url:
        existing.url = url
        changed = True
    if existing.secret != secret:
        existing.secret = secret
        changed = True
    if changed:
        await db.commit()
        await db.refresh(existing)
        log.info(
            "outbound_webhook.saas_endpoint_updated",
            endpoint_id=str(existing.id),
        )
    return existing
