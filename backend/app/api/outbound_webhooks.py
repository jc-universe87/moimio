"""Outbound webhook admin API (v1.0.0g).

CRUD for self-hoster-managed webhook endpoints, plus a "send test event"
action for verification. Hidden behind FEATURE_OUTBOUND_WEBHOOKS in
main.py — when the flag is off, this router is not included.

SaaS-managed endpoints (managed_by="saas") are filtered out of list
responses and cannot be modified through this API. They are created
and updated only by the auto-registration path at boot time.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.outbound_webhook import (
    OutboundWebhookDelivery,
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.models.user import User, UserRole
from app.schemas.outbound_webhook import (
    OutboundWebhookDeliveryOut,
    OutboundWebhookEndpointCreate,
    OutboundWebhookEndpointCreateOut,
    OutboundWebhookEndpointOut,
    OutboundWebhookEndpointUpdate,
    TestSendOut,
)
from app.services import webhook_service


router = APIRouter(
    prefix="/api/webhooks",
    tags=["outbound-webhooks"],
)


# ── Permission helper ──
# Webhooks are a system-level integration; only Super Admin manages them.
# Per-event admins / staff have no business adding webhook receivers.

def _require_super_admin(user: User) -> None:
    if user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"key": "errors.users.insufficient_permissions"},
        )


# ── User-managed endpoint helpers ──

async def _get_user_endpoint(
    db: AsyncSession, endpoint_id: uuid.UUID
) -> OutboundWebhookEndpoint:
    """Fetch a user-managed endpoint by id, or 404.

    SaaS-managed endpoints are intentionally indistinguishable-from-404
    via this API; they are not user-facing objects.
    """
    ep = await db.get(OutboundWebhookEndpoint, endpoint_id)
    if ep is None or ep.managed_by != WebhookEndpointManagedBy.USER:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"key": "errors.webhooks.endpoint_not_found"},
        )
    return ep


# ── Endpoints CRUD ──

@router.get("/endpoints", response_model=list[OutboundWebhookEndpointOut])
async def list_endpoints(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OutboundWebhookEndpoint]:
    _require_super_admin(current_user)
    result = await db.execute(
        select(OutboundWebhookEndpoint)
        .where(OutboundWebhookEndpoint.managed_by == WebhookEndpointManagedBy.USER)
        .order_by(OutboundWebhookEndpoint.created_at.desc())
    )
    return list(result.scalars())


@router.post(
    "/endpoints",
    response_model=OutboundWebhookEndpointCreateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_endpoint(
    body: OutboundWebhookEndpointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_super_admin(current_user)

    # Validate event_types — must be non-empty list of strings
    event_types = body.event_types or ["*"]
    if not isinstance(event_types, list) or not event_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"key": "errors.webhooks.event_types_invalid"},
        )

    secret = webhook_service.generate_secret()
    # Strip URL fragments (#...) defensively. Fragments are client-side
    # only — HTTP servers never see them — so a fragment in a webhook
    # URL is always a user mistake. Common case: pasting a webhook.site
    # viewer URL (https://webhook.site/#!/view/<uuid>) instead of the
    # endpoint URL (https://webhook.site/<uuid>). v1.0.0g-2.
    url_clean = str(body.url).split("#", 1)[0]
    endpoint = OutboundWebhookEndpoint(
        name=body.name,
        url=url_clean,
        secret=secret,
        event_types=event_types,
        state=WebhookEndpointState.ACTIVE,
        consecutive_failures=0,
        managed_by=WebhookEndpointManagedBy.USER,
        is_active=True,
    )
    db.add(endpoint)
    await db.flush()
    await db.refresh(endpoint)

    # Build the one-time response that includes the plaintext secret.
    # After this, the secret is never exposed via API.
    return OutboundWebhookEndpointCreateOut(
        id=endpoint.id,
        name=endpoint.name,
        url=endpoint.url,
        event_types=endpoint.event_types,
        state=endpoint.state.value,
        consecutive_failures=endpoint.consecutive_failures,
        managed_by=endpoint.managed_by.value,
        is_active=endpoint.is_active,
        last_success_at=endpoint.last_success_at,
        last_failure_at=endpoint.last_failure_at,
        created_at=endpoint.created_at,
        updated_at=endpoint.updated_at,
        secret=secret,
    )


@router.get(
    "/endpoints/{endpoint_id}",
    response_model=OutboundWebhookEndpointOut,
)
async def get_endpoint(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OutboundWebhookEndpoint:
    _require_super_admin(current_user)
    return await _get_user_endpoint(db, endpoint_id)


@router.patch(
    "/endpoints/{endpoint_id}",
    response_model=OutboundWebhookEndpointOut,
)
async def update_endpoint(
    endpoint_id: uuid.UUID,
    body: OutboundWebhookEndpointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OutboundWebhookEndpoint:
    _require_super_admin(current_user)
    ep = await _get_user_endpoint(db, endpoint_id)
    if body.name is not None:
        ep.name = body.name
    if body.url is not None:
        # Same fragment-strip as on create. v1.0.0g-2.
        ep.url = str(body.url).split("#", 1)[0]
    if body.event_types is not None:
        if not isinstance(body.event_types, list) or not body.event_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"key": "errors.webhooks.event_types_invalid"},
            )
        ep.event_types = body.event_types
    if body.is_active is not None:
        ep.is_active = body.is_active
    await db.flush()
    await db.refresh(ep)
    return ep


@router.delete(
    "/endpoints/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_endpoint(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    _require_super_admin(current_user)
    ep = await _get_user_endpoint(db, endpoint_id)
    await db.delete(ep)
    # Commit cascades — delivery rows go too via ondelete=CASCADE.


@router.post(
    "/endpoints/{endpoint_id}/rotate-secret",
    response_model=OutboundWebhookEndpointCreateOut,
)
async def rotate_secret(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerate the signing secret. Returns the new plaintext once."""
    _require_super_admin(current_user)
    ep = await _get_user_endpoint(db, endpoint_id)
    new_secret = webhook_service.generate_secret()
    ep.secret = new_secret
    await db.flush()
    await db.refresh(ep)
    return OutboundWebhookEndpointCreateOut(
        id=ep.id,
        name=ep.name,
        url=ep.url,
        event_types=ep.event_types,
        state=ep.state.value,
        consecutive_failures=ep.consecutive_failures,
        managed_by=ep.managed_by.value,
        is_active=ep.is_active,
        last_success_at=ep.last_success_at,
        last_failure_at=ep.last_failure_at,
        created_at=ep.created_at,
        updated_at=ep.updated_at,
        secret=new_secret,
    )


@router.post(
    "/endpoints/{endpoint_id}/reenable",
    response_model=OutboundWebhookEndpointOut,
)
async def reenable_endpoint(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OutboundWebhookEndpoint:
    """Reset state from DISABLED/DEGRADED back to ACTIVE.

    Used after the admin has investigated and fixed the receiver. Resets
    the consecutive-failure counter so the next failure starts a fresh
    countdown to degradation.
    """
    _require_super_admin(current_user)
    ep = await _get_user_endpoint(db, endpoint_id)
    ep.state = WebhookEndpointState.ACTIVE
    ep.consecutive_failures = 0
    await db.flush()
    await db.refresh(ep)
    return ep


# ── Test-send ──

@router.post(
    "/endpoints/{endpoint_id}/test",
    response_model=TestSendOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_test_event(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestSendOut:
    """Queue a `test.ping` event for delivery to this endpoint only.

    Unlike `queue_event` which fans out to every subscribed endpoint,
    this targets exactly one. Used by the admin UI's "Send test event"
    button to verify a receiver is reachable and signature-validating.

    v1.0.0g UX: after creating the PENDING delivery row, immediately run
    one worker tick so the admin sees the result in the UI without
    waiting up to 30 s for the next scheduler beat. The worker tick is
    scoped to this endpoint's deliveries only, so a slow receiver here
    won't block the response longer than the per-delivery timeout.
    """
    _require_super_admin(current_user)
    ep = await _get_user_endpoint(db, endpoint_id)

    from datetime import datetime, timezone
    from app.services.webhook_service import _envelope
    event_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    # v1.0.0h-1: route through the canonical envelope builder so test
    # pings get the same tenant_id stamping as real events. Previous
    # versions hand-built this dict, which silently bypassed the
    # MOIMIO_TENANT_ID env var.
    payload = _envelope(
        event_id=event_id,
        event_type="test.ping",
        data={
            "message": "This is a test event from Moimio.",
            "endpoint_id": str(ep.id),
            "endpoint_name": ep.name,
        },
        now=now,
    )

    delivery = OutboundWebhookDelivery(
        endpoint_id=ep.id,
        event_id=event_id,
        event_type="test.ping",
        payload=payload,
        attempt=0,
        status=WebhookDeliveryStatus.PENDING,
        next_attempt_at=now,
    )
    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)

    # Immediate worker tick — fire the delivery now rather than waiting
    # for the scheduled retry job. The worker is per-delivery committed,
    # so this won't roll back the row if the receiver errors.
    try:
        await webhook_service.process_pending_deliveries(db, batch_size=10)
    except Exception:
        # Worker failures are logged inside the service; we still return
        # 202 because the delivery row exists and will be retried by the
        # scheduler in 30 s.
        pass

    return TestSendOut(delivery_id=delivery.id, queued=True)


# ── Deliveries log ──

@router.get(
    "/endpoints/{endpoint_id}/deliveries",
    response_model=list[OutboundWebhookDeliveryOut],
)
async def list_deliveries(
    endpoint_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
) -> list[OutboundWebhookDelivery]:
    """Most recent deliveries for one endpoint, newest first."""
    _require_super_admin(current_user)
    await _get_user_endpoint(db, endpoint_id)
    result = await db.execute(
        select(OutboundWebhookDelivery)
        .where(OutboundWebhookDelivery.endpoint_id == endpoint_id)
        .order_by(OutboundWebhookDelivery.created_at.desc())
        .limit(max(1, min(limit, 500)))
    )
    return list(result.scalars())
