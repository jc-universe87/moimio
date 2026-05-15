"""Pydantic schemas for the outbound webhook admin API (v1.0.0g)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class OutboundWebhookEndpointCreate(BaseModel):
    """Request body for creating a new endpoint.

    Secret is generated server-side; admin sees it once in the response.
    """
    name: str = Field(..., min_length=1, max_length=120)
    url: HttpUrl
    event_types: list[str] = Field(default_factory=lambda: ["*"])


class OutboundWebhookEndpointUpdate(BaseModel):
    """All fields optional. Secret rotation handled by separate endpoint."""
    name: str | None = Field(None, min_length=1, max_length=120)
    url: HttpUrl | None = None
    event_types: list[str] | None = None
    is_active: bool | None = None


class OutboundWebhookEndpointOut(BaseModel):
    """Returned shape — never includes the secret (only hash exists in DB)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    event_types: list[str]
    state: str
    consecutive_failures: int
    managed_by: str
    is_active: bool
    last_success_at: datetime | None
    last_failure_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OutboundWebhookEndpointCreateOut(OutboundWebhookEndpointOut):
    """One-time response on creation: includes the plaintext secret.

    The admin UI is expected to present this in the sticky-modal pattern
    (visible until the admin acknowledges they have saved it). After
    this response, the plaintext secret is unrecoverable.
    """
    secret: str


class OutboundWebhookDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    endpoint_id: uuid.UUID
    event_id: uuid.UUID
    event_type: str
    attempt: int
    status: str
    next_attempt_at: datetime
    attempted_at: datetime | None
    response_status: int | None
    duration_ms: int | None
    error: str | None
    created_at: datetime


class TestSendRequest(BaseModel):
    """Body for the 'send test event' admin action — currently no params."""
    pass


class TestSendOut(BaseModel):
    """Returned shape from the test-send action.

    `delivery_id` lets the admin navigate to the recent-deliveries view
    to inspect what actually happened.
    """
    delivery_id: uuid.UUID
    queued: bool = True
