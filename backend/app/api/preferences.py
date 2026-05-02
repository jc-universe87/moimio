"""Preference request routes — group preferences for allocation."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.participant import Participant
from app.models.preference_request import ParticipantPreferenceRequest
from app.api.deps import ensure_event_writable, require_event_admin_dep

router = APIRouter(tags=["preferences"])


def _fmt(pr: ParticipantPreferenceRequest, p: Participant) -> dict:
    return {
        "id": str(pr.id),
        "participant_id": str(pr.participant_id),
        "participant_name": f"{p.first_name} {p.last_name}" if p else "Unknown",
        "participant_number": p.participant_number if p else None,
        "preferred_participant_number": pr.preferred_participant_number,
        "preferred_name": pr.preferred_name,
        "preferred_details": pr.preferred_details,
        "category_scope": pr.category_scope,
        "resolved": pr.resolved,
        "resolved_note": pr.resolved_note,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
    }


@router.get("/api/events/{event_id}/preference-requests/")
async def list_preference_requests(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """List all preference requests for an event."""
    result = await db.execute(
        select(ParticipantPreferenceRequest, Participant)
        .join(Participant, Participant.id == ParticipantPreferenceRequest.participant_id)
        .where(ParticipantPreferenceRequest.event_id == event_id)
        .order_by(ParticipantPreferenceRequest.created_at.asc())
    )
    rows = result.all()
    return [_fmt(pr, p) for pr, p in rows]


class ResolvePayload(BaseModel):
    resolved: bool = True
    resolved_note: str | None = None


@router.patch("/api/events/{event_id}/preference-requests/{req_id}/resolve")
async def resolve_preference_request(
    event_id: uuid.UUID,
    req_id: uuid.UUID,
    data: ResolvePayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Mark a preference request as resolved or unresolved."""
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(
        select(ParticipantPreferenceRequest).where(
            ParticipantPreferenceRequest.id == req_id,
            ParticipantPreferenceRequest.event_id == event_id,
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail={"key": "errors.prefs.request_not_found"})
    pr.resolved = data.resolved
    pr.resolved_note = data.resolved_note
    db.add(pr)
    await db.flush()
    # Return updated
    p_result = await db.execute(select(Participant).where(Participant.id == pr.participant_id))
    p = p_result.scalar_one_or_none()
    return _fmt(pr, p)
