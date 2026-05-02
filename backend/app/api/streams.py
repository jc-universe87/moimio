"""Server-Sent Event (SSE) endpoints for real-time event streams.

v1.0-pre #8/#9: clients open a long-lived HTTP connection and receive
push notifications when participant check-in state or allocation state
changes. Backed by app.core.pubsub.broker — see that module for the
fan-out semantics.

Why SSE rather than WebSockets?
─────────────────────────────────
- One-way (server → client) is sufficient for our use case. Writes
  still go through normal POST endpoints; SSE is purely for cache
  invalidation.
- SSE works through reverse proxies (Caddy, Nginx) without protocol
  upgrade. WebSocket through Caddy is fine but trickier to debug.
- No new dependency — FastAPI's StreamingResponse is enough.

Topics & permission gating
──────────────────────────
- "checkin:<event_id>"   — gated on has_checkin(perms) for the event.
- "organise:<event_id>"  — gated on has_read(perms, "organise") for the event.

The SSE protocol on the wire
────────────────────────────
Each event is two lines plus a blank:
    event: <type>
    data: <json>

A heartbeat comment is sent every 20s as `:` to keep the connection
warm through proxies and detect dropped connections fast.
"""

import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.pubsub import broker
from app.models.user import User, UserRole
from app.api.deps import get_current_user, get_current_user_query_token
from app.services.event_service import get_event_by_id
from app.services.permissions import (
    get_event_permissions,
    has_checkin,
    has_read,
)


logger = get_logger(__name__)
router = APIRouter(tags=["streams"])


# Heartbeat interval in seconds. SSE comments (lines starting ":") are
# silently ignored by EventSource clients but keep the TCP connection
# warm through any proxy idle timeouts.
_HEARTBEAT_S = 20.0


def _format_sse(event_type: str, data: dict) -> bytes:
    """Format a single SSE message frame."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


async def _stream_events(
    request: Request,
    topic: str,
):
    """Generator that yields SSE-formatted bytes for messages on `topic`,
    sending a heartbeat comment every _HEARTBEAT_S seconds to keep the
    connection alive. Exits when the client disconnects.
    """
    # Initial 'connected' frame so the client knows the stream is live.
    yield _format_sse("connected", {"topic": topic})

    async with broker.subscribe(topic) as queue:
        while True:
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=_HEARTBEAT_S)
                event_type = message.get("type", "message") if isinstance(message, dict) else "message"
                yield _format_sse(event_type, message)
            except asyncio.TimeoutError:
                # No traffic — emit a heartbeat comment.
                yield b": ping\n\n"


@router.get("/api/events/{event_id}/checkin/stream")
async def stream_checkin(
    event_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_query_token),
):
    """Stream check-in events for one event.

    Authentication is via a `?token=...` query parameter rather than the
    usual Authorization header — EventSource (the browser SSE primitive)
    does not support custom request headers. The query-token resolver
    accepts the same JWT as the header form.
    """
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})

    if current_user.role != UserRole.SUPER_ADMIN:
        perms = await get_event_permissions(db, current_user, event_id)
        if perms is None or not has_checkin(perms):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.checkin.permission_required"})

    return StreamingResponse(
        _stream_events(request, f"checkin:{event_id}"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering (nginx-style)
        },
    )


@router.get("/api/events/{event_id}/organise/stream")
async def stream_organise(
    event_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_query_token),
):
    """Stream allocation events for one event.

    Same authentication model as the check-in stream — query-token JWT.
    Gated on read access to the organise surface.
    """
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})

    if current_user.role != UserRole.SUPER_ADMIN:
        perms = await get_event_permissions(db, current_user, event_id)
        if perms is None or not has_read(perms, "organise"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.organise.permission_required"})

    return StreamingResponse(
        _stream_events(request, f"organise:{event_id}"),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
