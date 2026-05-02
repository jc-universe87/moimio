"""Event assignment routes — assign users to events with inline permissions.

v0.50e-1b: Staff groups removed. Permissions live on the assignment itself.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.models.event_assignment import EventUserAssignment
from app.api.deps import get_current_user, ensure_event_writable, require_event_admin_dep

logger = get_logger(__name__)
router = APIRouter(tags=["event_assignments"])


# ─── Event User Assignments ───

class AssignmentCreate(BaseModel):
    user_id: uuid.UUID
    role: str = "staff"  # "event_admin" | "staff"
    # v0.50e-1d: permissions inline with final shape. Admin optionally supplies:
    #   {
    #     "people": "write",
    #     "organise": "read",
    #     "checkin": {"access": "write", "pre_event": false},  # v1.0-pre #10 α-shape
    #     "reports": "read",
    #     "marks": "write"
    #   }
    # Legacy callers may still pass `"checkin": "write"` — both shapes are
    # accepted; the helpers in services/permissions.py read either form.
    # Ignored for role="event_admin" since event admins have full access.
    permissions: dict = {}


class AssignmentUpdate(BaseModel):
    role: Optional[str] = None
    permissions: Optional[dict] = None


def assignment_out(a: EventUserAssignment, user: User | None = None) -> dict:
    out = {
        "id": str(a.id),
        "event_id": str(a.event_id),
        "user_id": str(a.user_id),
        "role": a.role,
        "permissions": a.permissions or {},
    }
    if user:
        out["user_email"] = user.email
        out["user_full_name"] = user.full_name
        out["user_is_active"] = user.is_active
    return out


@router.get("/api/events/{event_id}/assignments/")
async def list_assignments(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """List all assignments for an event. Includes each user's inline
    permissions so the UI can render "Copy from" and display summaries."""
    result = await db.execute(
        select(EventUserAssignment).where(EventUserAssignment.event_id == event_id)
    )
    assignments = list(result.scalars().all())
    if not assignments:
        return []

    # v0.57b F4 fix: batch-fetch referenced users in a single IN-query
    # instead of one SELECT per assignment.
    user_ids = [a.user_id for a in assignments]
    users_q = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_by_id = {u.id: u for u in users_q.scalars().all()}

    return [assignment_out(a, users_by_id.get(a.user_id)) for a in assignments]


@router.post("/api/events/{event_id}/assignments/", status_code=201)
async def create_assignment(
    event_id: uuid.UUID,
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    existing = await db.execute(
        select(EventUserAssignment).where(
            EventUserAssignment.event_id == event_id,
            EventUserAssignment.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"key": "errors.assignments.already_assigned"})

    # Event admins ignore the permissions map — they have full access regardless.
    perms = {} if data.role == "event_admin" else (data.permissions or {})
    a = EventUserAssignment(
        event_id=event_id,
        user_id=data.user_id,
        role=data.role,
        permissions=perms,
    )
    db.add(a)
    await db.flush()
    await db.refresh(a)
    ur = await db.execute(select(User).where(User.id == data.user_id))
    user = ur.scalar_one_or_none()
    return assignment_out(a, user)


@router.patch("/api/events/{event_id}/assignments/{assignment_id}")
async def update_assignment(
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(
        select(EventUserAssignment).where(
            EventUserAssignment.id == assignment_id,
            EventUserAssignment.event_id == event_id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail={"key": "errors.assignments.not_found"})
    if data.role is not None:
        a.role = data.role
    if data.permissions is not None:
        # If the role is (or becomes) event_admin, permissions are ignored.
        a.permissions = {} if a.role == "event_admin" else (data.permissions or {})
    db.add(a)
    await db.flush()
    await db.refresh(a)
    ur = await db.execute(select(User).where(User.id == a.user_id))
    user = ur.scalar_one_or_none()
    return assignment_out(a, user)


@router.delete("/api/events/{event_id}/assignments/{assignment_id}", status_code=204)
async def delete_assignment(
    event_id: uuid.UUID,
    assignment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(
        select(EventUserAssignment).where(
            EventUserAssignment.id == assignment_id,
            EventUserAssignment.event_id == event_id,
        )
    )
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail={"key": "errors.assignments.not_found"})
    await db.delete(a)
    await db.flush()


# ─── Staff: get my assigned events ───
@router.get("/api/my-events")
async def get_my_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """For authenticated users — returns ALL event assignments.

    v0.50e-1c: previously returned a single assignment, which implicitly
    assumed staff were assigned to exactly one event. Now returns a list
    so callers can look up permissions per event_id.

    Super admins: returns empty list (they see all events unrestricted).
    Event admins / staff: returns one entry per assignment with role and
    per-event permissions. Event admins get a full-access permissions
    sentinel so callers don't need special-case code.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return {"assignments": []}

    result = await db.execute(
        select(EventUserAssignment).where(EventUserAssignment.user_id == current_user.id)
    )
    assignments = result.scalars().all()
    # v0.50f: for event_admin role, synthesise a full-access permissions
    # blob so downstream frontend code can use a single uniform lookup.
    # Keys match the final permission model.
    # v0.84 #12: checkin promoted to α-shape {access, pre_event} so the
    # frontend's pre-event helpers see event_admins as having pre_event
    # access. Without this, an event_admin assigned via the my-events
    # endpoint reads checkin: "write" (legacy string) and the pre-event
    # gate in canAccessSection returns false — even though event_admins
    # should have full access including pre-event.
    FULL = {
        "people": "write",
        "organise": "write",
        "checkin": {"access": "write", "pre_event": True},
        "reports": "read",
        "marks": "write",
    }

    def _normalise_checkin(perms: dict) -> dict:
        """v0.84 #12: belt-and-braces — convert legacy flat-string checkin
        to the α-shape on read, so the frontend always sees the new shape
        regardless of whether the migration touched this row. The migration
        (75a00000) does this on disk; this is a runtime safety net for any
        record that escaped (data migrated out-of-band, manual SQL, etc.)."""
        if not perms:
            return perms
        out = dict(perms)
        c = out.get("checkin")
        if isinstance(c, str):
            out["checkin"] = {"access": c, "pre_event": False}
        return out
    out = []
    for a in assignments:
        out.append({
            "event_id": str(a.event_id),
            "role": a.role,
            "permissions": FULL if a.role == "event_admin" else _normalise_checkin(a.permissions or {}),
        })
    return {"assignments": out}


# ─── Back-compat shim: /api/my-event (singular) ───
# v0.50e-1c: keeps existing deployments from breaking mid-upgrade. Returns
# the FIRST assignment if any, matching the old shape. New frontend code
# should prefer /api/my-events. This shim can be removed in a future ship
# once we're confident nothing calls it.
@router.get("/api/my-event")
async def get_my_event_legacy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.SUPER_ADMIN:
        return {"event_id": None}
    result = await db.execute(
        select(EventUserAssignment).where(EventUserAssignment.user_id == current_user.id)
    )
    assignment = result.scalars().first()
    if not assignment:
        return {"event_id": None, "permissions": {}}
    return {
        "event_id": str(assignment.event_id),
        "role": assignment.role,
        "permissions": assignment.permissions or {},
    }
