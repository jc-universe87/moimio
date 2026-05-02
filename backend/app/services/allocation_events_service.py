"""Append-only writer for `allocation_events`.

v0.60a adds audit-trail rows at every point where an `Allocation` is
created or deleted. This module centralises the write so instrumentation
call sites stay one-liners.

v0.60b adds the single read path used by the History section in
InsightPanel. The read returns already-serialised dicts (with
participant/actor display names resolved via OUTER JOIN) so the API
layer stays a thin auth+return wrapper.

Design notes:
  - This module only WRITES and READS — no UPDATEs or DELETEs against
    `allocation_events`. The table is append-only.
  - Callers of `record_allocation_event` are responsible for flushing.
    The helper calls `db.add(...)` but does NOT flush — that's the
    caller's decision so multiple events can be recorded in a single
    flush.
  - All snapshot resolution (fetching unit_name, category_name) is
    done by callers, because callers usually already have the objects
    loaded. The helper just takes the final strings.
  - No commit here. The service layer commits/rolls back as a unit;
    audit events participate in the same transaction as the allocation
    write itself, so a rollback clears both. That's the correct
    transactional story — we never record phantom events for actions
    that didn't succeed.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation_event import (
    AllocationEvent,
    AllocationEventSource,
    AllocationEventType,
)
from app.models.participant import Participant
from app.models.user import User


async def record_allocation_event(
    db: AsyncSession,
    *,
    event_id: uuid.UUID,
    participant_id: uuid.UUID,
    unit_id: uuid.UUID,
    category_id: uuid.UUID,
    unit_name_snapshot: str,
    category_name_snapshot: str,
    event_type: str,
    source: str,
    actor_user_id: uuid.UUID | None = None,
    meta: dict | None = None,
) -> AllocationEvent:
    """Write a single audit row. Does NOT flush.

    `event_type` must be one of AllocationEventType.ALL.
    `source` must be one of AllocationEventSource.ALL.
    Invalid values raise ValueError — callers should never construct
    arbitrary labels.
    """
    if event_type not in AllocationEventType.ALL:
        raise ValueError(
            f"Unknown allocation event_type {event_type!r}; "
            f"expected one of {sorted(AllocationEventType.ALL)}"
        )
    if source not in AllocationEventSource.ALL:
        raise ValueError(
            f"Unknown allocation event source {source!r}; "
            f"expected one of {sorted(AllocationEventSource.ALL)}"
        )

    ev = AllocationEvent(
        event_id=event_id,
        participant_id=participant_id,
        unit_id=unit_id,
        category_id=category_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        source=source,
        unit_name_snapshot=unit_name_snapshot,
        category_name_snapshot=category_name_snapshot,
        meta=meta,
    )
    db.add(ev)
    return ev


async def list_allocation_events(
    db: AsyncSession,
    *,
    event_id: uuid.UUID,
    participant_id: uuid.UUID | None = None,
    limit: int = 500,
) -> list[dict]:
    """Return serialised audit events for an event, newest first.

    v0.60b primary caller: the InsightPanel "History" section, which
    always passes ``participant_id``. Unfiltered reads (event-wide
    timeline) are supported for future UI surfaces but not wired in
    v0.60b.

    Display names for participants and actors are eagerly resolved
    via OUTER JOIN so the response is self-contained. When an FK is
    NULL (GDPR erasure cascade), the corresponding ``_name`` field
    comes back as ``None`` and the UI renders a "[removed X]" label
    at display time.

    ``limit`` is clamped to ``[1, 2000]``. The default of 500 is
    generous enough for any realistic participant timeline (a
    participant with 500 allocation events would be pathological).
    """
    safe_limit = max(1, min(limit, 2000))

    stmt = (
        select(AllocationEvent, Participant, User)
        .outerjoin(
            Participant,
            AllocationEvent.participant_id == Participant.id,
        )
        .outerjoin(
            User,
            AllocationEvent.actor_user_id == User.id,
        )
        .where(AllocationEvent.event_id == event_id)
    )
    if participant_id is not None:
        stmt = stmt.where(AllocationEvent.participant_id == participant_id)
    stmt = stmt.order_by(
        AllocationEvent.occurred_at.desc(),
        AllocationEvent.id.desc(),
    ).limit(safe_limit)

    result = await db.execute(stmt)
    rows = result.all()

    return [_serialise_event(ev, p, u) for ev, p, u in rows]


def _serialise_event(ev: AllocationEvent, p: Participant | None, u: User | None) -> dict:
    """Shape an AllocationEvent + its joined participant/user into the
    JSON-friendly dict the frontend consumes.

    Split out for direct unit testing of serialisation and for reuse
    if future endpoints want to produce the same shape from a
    different query.
    """
    return {
        "id": str(ev.id),
        "event_type": ev.event_type,
        "source": ev.source,
        "participant_id": str(ev.participant_id) if ev.participant_id else None,
        "participant_name": (
            f"{p.first_name} {p.last_name}".strip() if p else None
        ),
        "unit_id": str(ev.unit_id) if ev.unit_id else None,
        "unit_name": ev.unit_name_snapshot,
        "category_id": str(ev.category_id) if ev.category_id else None,
        "category_name": ev.category_name_snapshot,
        "actor_user_id": str(ev.actor_user_id) if ev.actor_user_id else None,
        "actor_display_name": u.full_name if u else None,
        "occurred_at": ev.occurred_at.isoformat() if ev.occurred_at else None,
        "meta": ev.meta,
    }
