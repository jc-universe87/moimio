"""
POST /api/admin/workspace/request-deletion — the customer-triggered end
of the self-service lifecycle (the Danger Zone).

This endpoint records the customer's intent and emits a
`workspace.delete_requested` event through CE's outbound-webhooks
subsystem. The actual deletion happens on the SaaS control plane: when
it receives the event, it generates the data export, stamps the 30/44-day
clocks (export window + erasure date), stops the tenant container, and
emails the customer the download link.

CE itself does NOT delete its own data here. The container going down is
what cuts off live access; full erasure is the SaaS's day-44 job. This
keeps CE billing-/tenancy-agnostic.

Self-hosters: no outbound endpoints are configured, so `queue_event` is
a no-op and the request is recorded in logs only. The endpoint still
returns 202 (the customer's intent is what we acknowledge).

Auth: super-admin only. UX guard: the caller must include
`confirmation: "DELETE"` in the body. The frontend (next ship) gates
this behind a typed confirmation modal — locale-appropriate framing,
canonical English token over the wire.
"""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.webhook_service import queue_event

router = APIRouter(prefix="/api/admin/workspace", tags=["danger_zone"])

# The fixed confirmation token the API expects. Locale-specific UI framing
# is the frontend's job; the wire contract is English-canonical.
CONFIRMATION_TOKEN = "DELETE"


class WorkspaceDeleteRequest(BaseModel):
    confirmation: str


class WorkspaceDeleteResponse(BaseModel):
    status: str
    requested_at: str
    event_id: str


@router.post(
    "/request-deletion",
    response_model=WorkspaceDeleteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_workspace_deletion(
    body: WorkspaceDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceDeleteResponse:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"key": "errors.danger_zone.super_admin_only"},
        )

    if body.confirmation != CONFIRMATION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.danger_zone.confirmation_mismatch"},
        )

    now = datetime.now(UTC)
    event_id = uuid.uuid4()

    await queue_event(
        db,
        event_id=event_id,
        event_type="workspace.delete_requested",
        data={
            "confirmed_by_user_id": str(current_user.id),
            "confirmed_by_email": current_user.email,
            "confirmed_at": now.isoformat(),
        },
    )
    await db.commit()

    return WorkspaceDeleteResponse(
        status="accepted",
        requested_at=now.isoformat(),
        event_id=str(event_id),
    )
