"""Marks routes — colour-coded badges for participants.

v0.50f-1 permission model
─────────────────────────
Marks are metadata ON participants. If you can see the participant, you
can see their marks. Hence "read" is not a separate permission — it's
implicit with event access. Only WRITE is explicitly granted.

- List (GET) / List assignments (GET): any authenticated user.
  Frontend renders the MarkAssignModal in view-only mode for users
  without marks:write so they can see what each mark means.
- Create (POST): admin OR staff with `marks: write`.
- Update (PATCH) / Delete (DELETE): admin OR (staff with `marks: write`
  AND mark.created_by_user_id == current_user.id). Creator-based.
- Import (POST /import): admin only. Bulk admin operation.
- Assign (POST) / Unassign (DELETE): admin OR staff with `marks: write`.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.mark import MarkDefinition, MarkAssignment
from app.api.deps import get_current_user, ensure_event_writable, require_event_admin_dep
from app.services.permissions import get_event_permissions, has_write

router = APIRouter(tags=["marks"])


class MarkDefCreate(BaseModel):
    name: str
    colour: str = "#4682B4"
    visible_in: List[str] = ["allocation", "people", "checkin"]
    # v0.74: 'together' | 'split' | 'none' (default). Drives engine
    # PASS 2 (cluster) / PASS 3 (split-evenly) / no-op respectively.
    cluster_behaviour: str = "none"


class MarkDefUpdate(BaseModel):
    name: Optional[str] = None
    colour: Optional[str] = None
    visible_in: Optional[List[str]] = None
    cluster_behaviour: Optional[str] = None  # v0.74


class MarkAssignRequest(BaseModel):
    participant_id: uuid.UUID


class MarkImportRequest(BaseModel):
    source_event_id: uuid.UUID


def _def_out(d, creator_name=None):
    """Serialise a MarkDefinition. If `creator_name` is provided, include
    it on the response — the frontend uses this for the "Created by …"
    audit line without needing to call /api/users/ (which non-admins
    can't access).
    """
    return {
        "id": str(d.id),
        "event_id": str(d.event_id),
        "name": d.name,
        "colour": d.colour,
        "visible_in": d.visible_in or [],
        # v0.74
        "cluster_behaviour": getattr(d, "cluster_behaviour", "none") or "none",
        "created_by_user_id": str(d.created_by_user_id) if d.created_by_user_id else None,
        "created_by_name": creator_name,
    }


def _asgn_out(a, assigner_name=None):
    """Serialise a MarkAssignment.

    v0.50f-2: includes `assigned_by_user_id`, `assigned_by_name` and
    `assigned_at` (ISO 8601) for the audit trail shown in the modal.
    `assigned_by_name` is joined server-side so non-admin staff can see
    attribution without needing /api/users/.
    """
    return {
        "id": str(a.id),
        "mark_id": str(a.mark_id),
        "participant_id": str(a.participant_id),
        "event_id": str(a.event_id),
        "assigned_by_user_id": str(a.assigned_by_user_id) if a.assigned_by_user_id else None,
        "assigned_by_name": assigner_name,
        "assigned_at": a.created_at.isoformat() if a.created_at else None,
    }


# ─── Permission helpers ───

def _is_admin(user: User) -> bool:
    return user.role == UserRole.SUPER_ADMIN


async def _require_marks_write(db: AsyncSession, user: User, event_id: uuid.UUID):
    """Admin OR staff with `marks: write`. Raises 403 otherwise.

    Used for mark *definitions* (create / update / delete) where you
    need explicit marks:write to create or edit the schema.
    """
    if _is_admin(user):
        return
    perms = await get_event_permissions(db, user, event_id)
    if perms is None or not has_write(perms, "marks"):
        raise HTTPException(status_code=403, detail={"key": "errors.marks.write_required"})


async def _require_mark_assign(db: AsyncSession, user: User, event_id: uuid.UUID):
    """Admin OR staff with `marks: write` OR staff with `people: write`.
    Raises 403 otherwise.

    v0.70d-3c-9: assigning an existing mark to a participant accepts
    people:write too. Operators with edit access to participants
    legitimately need to label them; gating assignment behind
    marks:write was overly strict. Mark *creation* still requires
    marks:write — separate helper above.
    """
    if _is_admin(user):
        return
    perms = await get_event_permissions(db, user, event_id)
    if perms is None or (not has_write(perms, "marks") and not has_write(perms, "people")):
        raise HTTPException(status_code=403, detail={"key": "errors.marks.assign_forbidden"})


async def _require_can_modify_mark(
    db: AsyncSession, user: User, event_id: uuid.UUID, mark: MarkDefinition
):
    """Admin can modify any mark; staff can only modify marks they created.

    Creator-based ownership (v0.50f): staff with `marks: write` can create
    new marks but can only edit/delete marks whose created_by_user_id
    matches their own. This keeps admin-created "system" marks safe from
    accidental staff changes while letting staff manage their own additions.
    """
    if _is_admin(user):
        return
    # Must have marks:write at minimum
    perms = await get_event_permissions(db, user, event_id)
    if perms is None or not has_write(perms, "marks"):
        raise HTTPException(status_code=403, detail={"key": "errors.marks.write_required"})
    # And must be the creator
    if mark.created_by_user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail={"key": "errors.marks.creator_only"},
        )


# ─── Definitions ───

@router.get("/api/events/{event_id}/marks/")
async def list_marks(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all marks for an event.

    v0.50f-1: response includes `created_by_name` via a LEFT JOIN on users
    so the audit trail ("Created by Alice") works for any authenticated
    user — previously the frontend called /api/users/ for names, which
    non-admins can't access.
    """
    result = await db.execute(
        select(MarkDefinition, User.full_name, User.email)
        .join(User, MarkDefinition.created_by_user_id == User.id, isouter=True)
        .where(MarkDefinition.event_id == event_id)
        .order_by(MarkDefinition.created_at)
    )
    rows = result.all()
    out = []
    for d, full_name, email in rows:
        creator_name = None
        if d.created_by_user_id:
            # Prefer full_name, fall back to email, then to None (user deleted).
            creator_name = full_name or email
        out.append(_def_out(d, creator_name=creator_name))
    return out


@router.post("/api/events/{event_id}/marks/", status_code=201)
async def create_mark(
    event_id: uuid.UUID,
    data: MarkDefCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    await _require_marks_write(db, current_user, event_id)
    d = MarkDefinition(
        event_id=event_id,
        name=data.name,
        colour=data.colour,
        visible_in=data.visible_in,
        cluster_behaviour=data.cluster_behaviour,  # v0.74
        created_by_user_id=current_user.id,
    )
    db.add(d)
    await db.flush()
    await db.refresh(d)
    return _def_out(d, creator_name=(current_user.full_name or current_user.email))


@router.patch("/api/events/{event_id}/marks/{mark_id}")
async def update_mark(
    event_id: uuid.UUID,
    mark_id: uuid.UUID,
    data: MarkDefUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MarkDefinition).where(
            MarkDefinition.id == mark_id, MarkDefinition.event_id == event_id
        )
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail={"key": "errors.marks.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    await _require_can_modify_mark(db, current_user, event_id, d)
    if data.name is not None:
        d.name = data.name
    if data.colour is not None:
        d.colour = data.colour
    if data.visible_in is not None:
        d.visible_in = data.visible_in
    if data.cluster_behaviour is not None:  # v0.74
        d.cluster_behaviour = data.cluster_behaviour
    await db.flush()
    await db.refresh(d)
    # Look up creator name for the response
    creator_name = None
    if d.created_by_user_id:
        cr = await db.execute(select(User).where(User.id == d.created_by_user_id))
        cu = cr.scalar_one_or_none()
        if cu:
            creator_name = cu.full_name or cu.email
    return _def_out(d, creator_name=creator_name)


@router.delete("/api/events/{event_id}/marks/{mark_id}", status_code=204)
async def delete_mark(
    event_id: uuid.UUID,
    mark_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MarkDefinition).where(
            MarkDefinition.id == mark_id, MarkDefinition.event_id == event_id
        )
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail={"key": "errors.marks.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    await _require_can_modify_mark(db, current_user, event_id, d)
    await db.execute(delete(MarkAssignment).where(MarkAssignment.mark_id == mark_id))
    await db.delete(d)
    await db.flush()


# ─── Import from another event ───

@router.post("/api/events/{event_id}/marks/import", status_code=201)
async def import_marks(
    event_id: uuid.UUID,
    data: MarkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(
        select(MarkDefinition).where(MarkDefinition.event_id == data.source_event_id)
    )
    source_defs = result.scalars().all()
    creator_name = current_user.full_name or current_user.email
    created = []
    for s in source_defs:
        d = MarkDefinition(
            event_id=event_id,
            name=s.name,
            colour=s.colour,
            visible_in=s.visible_in or [],
            # v0.74: preserve cluster_behaviour when copying marks across events.
            cluster_behaviour=getattr(s, "cluster_behaviour", "none") or "none",
            created_by_user_id=current_user.id,  # imported marks attributed to importer
        )
        db.add(d)
        await db.flush()
        await db.refresh(d)
        created.append(_def_out(d, creator_name=creator_name))
    return created


# ─── Assignments ───

@router.get("/api/events/{event_id}/marks/assignments")
async def list_assignments(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # v0.50f-2: LEFT JOIN on users so the audit trail renders without
    # requiring the caller to hit /api/users/ (which non-admins can't).
    result = await db.execute(
        select(MarkAssignment, User.full_name, User.email)
        .join(User, MarkAssignment.assigned_by_user_id == User.id, isouter=True)
        .where(MarkAssignment.event_id == event_id)
    )
    rows = result.all()
    out = []
    for a, full_name, email in rows:
        assigner_name = None
        if a.assigned_by_user_id:
            assigner_name = full_name or email
        out.append(_asgn_out(a, assigner_name=assigner_name))
    return out


@router.post("/api/events/{event_id}/marks/{mark_id}/assign", status_code=201)
async def assign_mark(
    event_id: uuid.UUID,
    mark_id: uuid.UUID,
    data: MarkAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # v0.70d-3c-9: assignment accepts marks:write OR people:write.
    # Operators with people-write legitimately need to label participants.
    # Mark *definition* CRUD still requires marks:write (separate helper).
    await ensure_event_writable(db, event_id, current_user)
    await _require_mark_assign(db, current_user, event_id)
    # Idempotent — if already assigned, return existing.
    result = await db.execute(
        select(MarkAssignment).where(
            MarkAssignment.mark_id == mark_id,
            MarkAssignment.participant_id == data.participant_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        # Even though assignment is idempotent, the caller probably wants
        # the existing attribution. Look up assigner name for response.
        assigner_name = None
        if existing.assigned_by_user_id:
            cr = await db.execute(select(User).where(User.id == existing.assigned_by_user_id))
            cu = cr.scalar_one_or_none()
            if cu:
                assigner_name = cu.full_name or cu.email
        return _asgn_out(existing, assigner_name=assigner_name)
    # v0.50f-2: stamp assigner on new assignments.
    a = MarkAssignment(
        mark_id=mark_id,
        participant_id=data.participant_id,
        event_id=event_id,
        assigned_by_user_id=current_user.id,
    )
    db.add(a)
    await db.flush()
    await db.refresh(a)
    return _asgn_out(a, assigner_name=(current_user.full_name or current_user.email))


@router.delete(
    "/api/events/{event_id}/marks/{mark_id}/assign/{participant_id}", status_code=204
)
async def unassign_mark(
    event_id: uuid.UUID,
    mark_id: uuid.UUID,
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # v0.70d-3c-9: unassignment same as assignment — marks:write OR people:write.
    await ensure_event_writable(db, event_id, current_user)
    await _require_mark_assign(db, current_user, event_id)
    await db.execute(
        delete(MarkAssignment).where(
            MarkAssignment.mark_id == mark_id,
            MarkAssignment.participant_id == participant_id,
        )
    )
    await db.flush()
