"""Permission helper — resolves effective permissions for a user on a specific event.

v0.50f-1 / v1.0-pre #10 shape
─────────────────────────────
Staff assignment permissions are a flat dict with five recognised keys:

  people:   "read" | "write" | None    # access to participant list
  organise: "read" | "write" | None    # access to allocation board
  checkin:  { access: "write" | None, pre_event: bool }
                                       # access to check-in. v1.0-pre #10:
                                       # promoted from a flat string to an
                                       # object so a sibling `pre_event` flag
                                       # can grant access during Registration
                                       # phase (for setting up check-in
                                       # columns ahead of the event). Legacy
                                       # flat-string values ("write" or None)
                                       # are still accepted by the helpers
                                       # below for backwards compatibility
                                       # with assignments created before the
                                       # migration runs.
  reports:  "read" | None              # access to reports + report export
  marks:    "write" | None             # v0.50f-1 — write access (create/edit
                                       # own/delete own/assign/unassign).
                                       # READ is implicit with event access:
                                       # anyone who can see participants can
                                       # see the marks on them and open the
                                       # MarkAssignModal in view-only mode.

Anything else in the dict is ignored.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.event_assignment import EventUserAssignment


# Admins and event admins short-circuit to full access. The value here is
# used only as a frontend-friendly marker; backend logic checks role first.
FULL_WRITE = {
    "people": "write",
    "organise": "write",
    "checkin": {"access": "write", "pre_event": True},
    "reports": "read",
    "marks": "write",
}


async def get_event_permissions(db: AsyncSession, user: User, event_id: uuid.UUID) -> dict | None:
    """
    Returns effective permissions dict for a user on an event, or None if no access.

    Admins/super admins: full write everywhere.
    Staff: permissions stored directly on their event assignment.
    Returns None if the user has no assignment for this event (staff only).
    """
    if user.role == UserRole.SUPER_ADMIN:
        return FULL_WRITE

    # Staff: look up their event assignment
    result = await db.execute(
        select(EventUserAssignment).where(
            EventUserAssignment.user_id == user.id,
            EventUserAssignment.event_id == event_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        return None

    # Event admin role within assignment
    if assignment.role == "event_admin":
        return FULL_WRITE

    # Staff role — return inline permissions
    return assignment.permissions or {}


def has_write(perms: dict, view: str) -> bool:
    """Check if permissions grant write access to a view."""
    if view == "checkin":
        # checkin is an object {access, pre_event} — fall through to the
        # dedicated helper for clarity. Tolerates legacy flat-string values.
        return has_checkin(perms)
    return perms.get(view) == "write"


def has_read(perms: dict, view: str) -> bool:
    """Check if permissions grant at least read access to a view.

    For checkin: any "access" being write means access; pre_event alone
    does NOT grant read access — pre_event is a phase-gate flag, not a
    capability. Use has_checkin_pre_event() for the pre-event check.
    For reports: "read" is the only meaningful value; has_read is the
    natural check. Kept for semantic clarity across views.
    """
    if view == "checkin":
        return has_checkin(perms)
    return perms.get(view) in ("read", "write")


def has_checkin(perms: dict) -> bool:
    """Single check-in permission — any truthy value means access.

    v1.0-pre #10: tolerates both the new α-shape ({access, pre_event}) and
    the legacy flat-string ("write" or None) shape. Once the migration has
    run, every assignment uses the new shape; until then, this helper
    keeps both readable.

    Prefer this over has_read(perms, "checkin") or has_write(perms, "checkin")
    in new code, to make the intent unambiguous.
    """
    raw = perms.get("checkin")
    if isinstance(raw, dict):
        return bool(raw.get("access"))
    return bool(raw)


def has_checkin_pre_event(perms: dict) -> bool:
    """Whether this user can access check-in during Registration phase.

    Returns True for:
      - Admins / event admins (FULL_WRITE has pre_event=True).
      - Staff with the new α-shape and pre_event=True.

    Returns False for:
      - Staff with α-shape and pre_event=False (or absent).
      - Staff on legacy flat-string "write" (defaults to False — they only
        had Event-phase access historically; the toggle is opt-in).
      - Anyone without checkin access at all.
    """
    raw = perms.get("checkin")
    if isinstance(raw, dict):
        return bool(raw.get("access")) and bool(raw.get("pre_event"))
    return False


def has_reports(perms: dict) -> bool:
    """Single reports permission — any truthy value means access (and export)."""
    return bool(perms.get("reports"))
