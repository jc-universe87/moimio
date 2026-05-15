"""Outbound webhook subsystem models (v1.0.0g).

Two tables:
- `outbound_webhook_endpoints` — registered receivers (admin-managed or
  auto-registered by SaaS env vars). One row per URL the admin wants
  events fired to.
- `outbound_webhook_deliveries` — append-only log of every delivery
  attempt, kept for `WEBHOOK_DELIVERY_RETENTION_DAYS` days then pruned.

Design notes:

- Secret storage. The endpoint table stores the signing secret in
  plaintext. CE is the sender; it must produce a fresh HMAC on every
  outbound delivery and therefore needs the plaintext at-rest. The
  "shown once" UX is enforced at the API layer (GET responses never
  include the secret) — this prevents shoulder-surfing and accidental
  screenshot disclosure, but does NOT protect against full-DB leaks.
  Standard hosting trust + backup encryption are the protections at
  rest; an encrypted-column upgrade is documented as a future hardening.

  For SaaS-managed endpoints, the secret is supplied via environment at
  container startup; CE stores it in the DB at first boot for sender-
  side signing. SaaS retains its own copy for receiver-side verification.

- `managed_by` flag. Distinguishes "saas" (auto-registered, hidden from
  UI, not user-deletable) from "user" (admin-created via UI, fully
  editable). Pattern borrowed from managed Kubernetes — the platform
  creates infrastructure objects customers can't break.

- `event_types` as JSONB array. `["*"]` for all events. Explicit list
  for selective subscription (e.g. `["event.created", "event.cancelled"]`).
  v1.0.0g ships with only `test.ping` actually emittable; real event
  types arrive in v1.0.0h.

- `state` machine. `active` → `degraded` (5 consecutive failures) →
  `disabled` (20 consecutive failures, no manual re-enable). Admin can
  re-enable manually. `state` is set by the delivery worker, not by the
  admin directly.

- Delivery row per attempt, not per event. One event fired to one
  endpoint with three retries = four delivery rows. This makes "what
  happened to event X" answerable with a single index scan.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WebhookEndpointState(str, enum.Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class WebhookEndpointManagedBy(str, enum.Enum):
    USER = "user"  # admin-created via UI; fully editable
    SAAS = "saas"  # auto-registered via env vars; hidden from UI


class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "pending"        # scheduled, not yet attempted
    SUCCESS = "success"        # 2xx response received
    FAILED = "failed"          # non-2xx or transport error, will retry
    EXHAUSTED = "exhausted"    # all retries used up, given up


class OutboundWebhookEndpoint(Base):
    __tablename__ = "outbound_webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Admin-visible label, e.g. "Slack notifications", "SaaS billing".
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    # Signing secret. Stored in plaintext because CE is the SENDER and
    # must produce a fresh HMAC on every outbound delivery. The "show
    # once via UI" pattern is enforced at the API layer (GET responses
    # omit this column); plaintext-at-rest matches how every sender-side
    # webhook system works (Stripe, GitHub, etc.).
    #
    # Threat model accepted: full DB leak = ability to forge signatures
    # against the receiver. Mitigated by standard backup encryption and
    # hosting trust; an encrypted-at-rest column with a master-key env
    # var is a candidate hardening for a future ship.
    secret: Mapped[str] = mapped_column(String(255), nullable=False)

    # Subscribed event types. `["*"]` for all. JSON list of strings.
    event_types: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    state: Mapped[WebhookEndpointState] = mapped_column(
        SAEnum(
            WebhookEndpointState,
            name="webhook_endpoint_state",
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=WebhookEndpointState.ACTIVE,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    managed_by: Mapped[WebhookEndpointManagedBy] = mapped_column(
        SAEnum(
            WebhookEndpointManagedBy,
            name="webhook_endpoint_managed_by",
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=WebhookEndpointManagedBy.USER,
    )

    # Whether the endpoint is currently accepting deliveries. Separate
    # from `state`: an admin can manually pause an active endpoint
    # without it being failure-disabled.
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    deliveries = relationship(
        "OutboundWebhookDelivery",
        back_populates="endpoint",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<OutboundWebhookEndpoint {self.name} ({self.state.value})>"


class OutboundWebhookDelivery(Base):
    __tablename__ = "outbound_webhook_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("outbound_webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Application-level event id (UUID). Same id used across retries of
    # the same event to the same endpoint, so receivers can dedupe.
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Which retry attempt this row represents (0 = first attempt).
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        SAEnum(
            WebhookDeliveryStatus,
            name="webhook_delivery_status",
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=WebhookDeliveryStatus.PENDING,
        index=True,
    )

    # When this delivery should next be attempted. PENDING rows with
    # `next_attempt_at <= now` are the worker's work queue.
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Set when the attempt completes (success or fail). NULL while PENDING.
    attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Capped at 2000 chars; receivers occasionally return huge HTML pages.
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    endpoint = relationship("OutboundWebhookEndpoint", back_populates="deliveries")

    def __repr__(self) -> str:
        return (
            f"<OutboundWebhookDelivery {self.event_type} "
            f"attempt={self.attempt} status={self.status.value}>"
        )
