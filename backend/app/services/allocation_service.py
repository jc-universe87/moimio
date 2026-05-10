"""Allocation service — core logic for participant assignment.

v0.60a: assign/move/unassign now emit append-only `AllocationEvent`
rows via `allocation_events_service.record_allocation_event`. The three
write surfaces below thread `actor_user_id` through to the event row;
callers at the API layer pass `current_user.id`. `None` is accepted to
keep backward-compat signatures for any internal callers that have no
user context (tests, migrations).
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MoimioAppError
from app.core.logging import get_logger
from app.models.allocation_category import AllocationCategory
from app.models.allocation_unit import AllocationUnit
from app.models.allocation import Allocation
from app.models.allocation_event import AllocationEventSource, AllocationEventType
from app.models.participant import Participant
from app.services.allocation_events_service import record_allocation_event

logger = get_logger(__name__)


# ─── Categories ───

async def create_category(db: AsyncSession, event_id: uuid.UUID, **kwargs) -> AllocationCategory:
    cat = AllocationCategory(event_id=event_id, **kwargs)
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return cat


async def list_categories(db: AsyncSession, event_id: uuid.UUID) -> list[dict]:
    """List categories with unit counts, capacity sums, and allocation counts.

    Performance: flat query count regardless of category count.
        1. Fetch categories.
        2. One aggregate for unit stats (unit_count, total_capacity).
        3. One aggregate for allocation counts.

    Why the two aggregates are kept SEPARATE (and not folded into a single
    join): joining AllocationUnit to Allocation would multiply each unit
    row by its occupant count, causing ``SUM(capacity)`` to be counted
    once per allocation rather than once per unit. Keeping the
    capacity-bearing aggregate off the allocation side avoids that trap
    entirely. (Alternatives — ``SUM(DISTINCT capacity)`` or a subquery —
    are fragile or more complex than just running two queries.)
    """
    result = await db.execute(
        select(AllocationCategory)
        .where(AllocationCategory.event_id == event_id)
        .order_by(AllocationCategory.sort_order, AllocationCategory.created_at)
    )
    cats = list(result.scalars().all())
    if not cats:
        return []
    cat_ids = [c.id for c in cats]

    # Aggregate 1: unit stats grouped by category — NO join to Allocation
    # (see docstring for why).
    units_stats_q = await db.execute(
        select(
            AllocationUnit.category_id,
            func.count(AllocationUnit.id).label("unit_count"),
            func.sum(AllocationUnit.capacity).label("total_capacity"),
        )
        .where(AllocationUnit.category_id.in_(cat_ids))
        .group_by(AllocationUnit.category_id)
    )
    units_stats = {row.category_id: row for row in units_stats_q.all()}

    # Aggregate 2: allocation counts grouped by category (via join to units).
    allocs_q = await db.execute(
        select(
            AllocationUnit.category_id,
            func.count(Allocation.id).label("allocated_count"),
        )
        .select_from(Allocation)
        .join(AllocationUnit, Allocation.unit_id == AllocationUnit.id)
        .where(AllocationUnit.category_id.in_(cat_ids))
        .group_by(AllocationUnit.category_id)
    )
    alloc_counts = {row.category_id: row.allocated_count for row in allocs_q.all()}

    out = []
    for cat in cats:
        us = units_stats.get(cat.id)
        unit_count = us.unit_count if us else 0
        total_capacity = (us.total_capacity or 0) if us else 0
        allocated = alloc_counts.get(cat.id, 0)

        out.append({
            "id": cat.id, "event_id": cat.event_id, "name": cat.name,
            "item_label": cat.item_label,
            "description": cat.description, "rule_type": cat.rule_type,
            "has_capacity": cat.has_capacity, "has_gender_restriction": cat.has_gender_restriction,
            "sort_order": cat.sort_order, "is_default": cat.is_default,
            "confirmed": cat.confirmed,
            "unit_count": unit_count, "allocated_count": allocated,
            "total_capacity": total_capacity if cat.has_capacity else None,
            "settings": cat.settings,
        })
    return out


async def get_category(db: AsyncSession, category_id: uuid.UUID) -> AllocationCategory | None:
    result = await db.execute(select(AllocationCategory).where(AllocationCategory.id == category_id))
    return result.scalar_one_or_none()


async def update_category(db: AsyncSession, category_id: uuid.UUID, **kwargs) -> AllocationCategory:
    cat = await get_category(db, category_id)
    if not cat:
        raise MoimioAppError("errors.allocation.group_type_not_found", status_code=404)
    # v0.74: pre-v0.74 Bug 3 guard ("reject has_capacity=true→false
    # when units have capacity set") is obsolete. Capacity is now
    # required on every unit (NOT NULL); the toggle controls whether
    # the engine honours the values. Toggling off no longer leaves
    # dead data.
    for k, v in kwargs.items():
        if v is not None and hasattr(cat, k):
            setattr(cat, k, v)
    await db.flush()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, category_id: uuid.UUID) -> bool:
    cat = await get_category(db, category_id)
    if not cat:
        return False
    await db.delete(cat)
    await db.flush()
    return True


# ─── v50c-3: allocation lifecycle helpers ───

async def _unconfirm_category_if_confirmed(db: AsyncSession, category_id: uuid.UUID) -> None:
    """Silently flip a category's `confirmed` flag to False if it's True.

    Called by every mutation that changes allocations or units within the
    category. Per §12.3 re-open rule: any edit → In Progress.
    """
    cat = await get_category(db, category_id)
    if cat and cat.confirmed:
        cat.confirmed = False
        await db.flush()


async def _unconfirm_category_for_unit(db: AsyncSession, unit_id: uuid.UUID) -> None:
    """Same as above but given a unit_id (looks up the category)."""
    unit = await get_unit(db, unit_id)
    if unit:
        await _unconfirm_category_if_confirmed(db, unit.category_id)


async def confirm_category(db: AsyncSession, category_id: uuid.UUID) -> AllocationCategory:
    """Mark a category's allocation as confirmed (organiser is done with it)."""
    cat = await get_category(db, category_id)
    if not cat:
        raise MoimioAppError("errors.allocation.group_type_not_found", status_code=404)
    cat.confirmed = True
    await db.flush()
    await db.refresh(cat)
    return cat


async def unconfirm_category(db: AsyncSession, category_id: uuid.UUID) -> AllocationCategory:
    """Explicitly flip confirmed → False. Used for the 'edit' CTA on a
    confirmed category (user clicks to re-open for editing)."""
    cat = await get_category(db, category_id)
    if not cat:
        raise MoimioAppError("errors.allocation.group_type_not_found", status_code=404)
    cat.confirmed = False
    await db.flush()
    await db.refresh(cat)
    return cat


async def create_default_categories(db: AsyncSession, event_id: uuid.UUID):
    """Create Rooms + Small Groups for a new event."""
    await create_category(
        db, event_id, name="Rooms", item_label="Room", rule_type="exclusive",
        has_capacity=True, has_gender_restriction=True, sort_order=0, is_default=True,
    )
    await create_category(
        db, event_id, name="Small Groups", item_label="Group", rule_type="exclusive",
        has_capacity=False, has_gender_restriction=False, sort_order=1, is_default=True,
    )


# ─── Units ───

async def create_unit(db: AsyncSession, category_id: uuid.UUID, **kwargs) -> AllocationUnit:
    # v0.74: capacity is now required on every unit (NOT NULL in DB).
    # Pre-v0.74 Bug 3 guard ("reject capacity when has_capacity=false")
    # is obsolete — capacity is always required, has_capacity toggle now
    # only controls whether the engine HONOURS the cap value (vs
    # treating the unit as effectively unlimited).
    await _unconfirm_category_if_confirmed(db, category_id)
    unit = AllocationUnit(category_id=category_id, **kwargs)
    db.add(unit)
    await db.flush()
    await db.refresh(unit)
    return unit


async def list_units(db: AsyncSession, category_id: uuid.UUID) -> list[dict]:
    """List units with occupant counts.

    Performance: flat query count regardless of unit count.
        1. Fetch units.
        2. One aggregate ``GROUP BY unit_id`` for occupant counts.
    """
    result = await db.execute(
        select(AllocationUnit)
        .where(AllocationUnit.category_id == category_id)
        .order_by(AllocationUnit.sort_order, AllocationUnit.created_at)
    )
    units = list(result.scalars().all())
    if not units:
        return []
    unit_ids = [u.id for u in units]

    occ_q = await db.execute(
        select(
            Allocation.unit_id,
            func.count(Allocation.id).label("occupant_count"),
        )
        .where(Allocation.unit_id.in_(unit_ids))
        .group_by(Allocation.unit_id)
    )
    occupant_counts = {row.unit_id: row.occupant_count for row in occ_q.all()}

    out = []
    for unit in units:
        out.append({
            "id": unit.id, "category_id": unit.category_id, "name": unit.name,
            "description": unit.description, "capacity": unit.capacity,
            "gender_restriction": unit.gender_restriction, "sort_order": unit.sort_order,
            "occupant_count": occupant_counts.get(unit.id, 0),
        })
    return out


async def get_unit(db: AsyncSession, unit_id: uuid.UUID) -> AllocationUnit | None:
    result = await db.execute(select(AllocationUnit).where(AllocationUnit.id == unit_id))
    return result.scalar_one_or_none()


async def delete_unit(db: AsyncSession, unit_id: uuid.UUID) -> bool:
    unit = await get_unit(db, unit_id)
    if not unit:
        return False
    await _unconfirm_category_if_confirmed(db, unit.category_id)
    await db.delete(unit)
    await db.flush()
    return True


async def update_unit(db: AsyncSession, unit_id: uuid.UUID, **kwargs) -> AllocationUnit:
    unit = await get_unit(db, unit_id)
    if not unit:
        raise MoimioAppError("errors.allocation.unit_not_found", status_code=404)
    # v0.74: capacity required-everywhere; pre-v0.74 Bug 3 guard is
    # obsolete (see create_unit comment).
    await _unconfirm_category_if_confirmed(db, unit.category_id)
    for k, v in kwargs.items():
        if hasattr(unit, k):
            setattr(unit, k, v)
    await db.flush()
    await db.refresh(unit)
    return unit


# ─── Allocations (core logic) ───

async def assign_participant(
    db: AsyncSession,
    event_id: uuid.UUID,
    unit_id: uuid.UUID,
    participant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
) -> Allocation:
    """Assign a participant to a unit, respecting rules.

    v0.60a: emits an `assign` AllocationEvent on success. For exclusive
    categories, any existing allocation in sibling units is cascaded
    away and emits an `unassign` event with source=manual_cascade —
    so a "move" within an exclusive category produces a paired
    unassign + assign in the audit log.

    ``actor_user_id`` is threaded into the audit row. Pass ``None``
    only from callers without user context (tests, batch jobs).
    """
    unit = await get_unit(db, unit_id)
    if not unit:
        raise MoimioAppError("errors.allocation.unit_not_found", status_code=404)

    cat = await get_category(db, unit.category_id)
    if not cat:
        raise MoimioAppError("errors.allocation.group_type_not_found", status_code=404)

    # v50c-3: assigning a participant is an edit — if this category was
    # confirmed, silently revert to In Progress (§12.3 re-open rule).
    if cat.confirmed:
        cat.confirmed = False
        await db.flush()

    participant = await db.execute(select(Participant).where(Participant.id == participant_id))
    participant = participant.scalar_one_or_none()
    if not participant:
        raise MoimioAppError("errors.participant.not_found", status_code=404)

    # Rule: exclusive category → remove from other units in same category.
    # v0.60a: for each cascaded deletion, emit an unassign audit event
    # with source=manual_cascade so a "move" reads as a paired
    # unassign+assign in the timeline. We select the unit alongside
    # the allocation to get its name for the snapshot without an
    # extra per-row fetch.
    if cat.rule_type == "exclusive":
        existing = await db.execute(
            select(Allocation, AllocationUnit)
            .join(AllocationUnit, Allocation.unit_id == AllocationUnit.id)
            .where(
                Allocation.participant_id == participant_id,
                AllocationUnit.category_id == cat.id,
            )
        )
        for old_alloc, old_unit in existing.all():
            await record_allocation_event(
                db,
                event_id=event_id,
                participant_id=participant_id,
                unit_id=old_unit.id,
                category_id=cat.id,
                unit_name_snapshot=old_unit.name,
                category_name_snapshot=cat.name,
                event_type=AllocationEventType.UNASSIGN,
                source=AllocationEventSource.MANUAL_CASCADE,
                actor_user_id=actor_user_id,
            )
            await db.delete(old_alloc)
        await db.flush()

    # v0.54: capacity is a SOFT constraint on the manual-assignment path.
    # Organisers may overbook a unit (e.g. "2 small children sleeping in 1
    # bed, family stays together") — the frontend renders a burgundy
    # "over capacity" signal so it's a visible, conscious decision. The
    # engine path continues to respect capacity as a HARD constraint
    # (see engine_service.remaining_cap) so auto-allocation never overbooks.
    # Gender restriction remains HARD on both paths.

    # Rule: check gender restriction (v0.73e Finding 4 — strict on
    # manual placement, symmetric to v0.73a Bug 4 in the engine).
    # Pre-v0.73e the participant.gender check short-circuited when
    # gender was None, silently allowing genderless participants
    # into restricted rooms — inconsistent with the engine's strict
    # behaviour. Post-fix: two distinct error paths so the
    # organiser sees a different message depending on cause.
    #   - Wrong gender → find a different room
    #   - No gender on record → update the participant, then re-try
    if cat.has_gender_restriction and unit.gender_restriction:
        if not participant.gender:
            raise MoimioAppError(
                "errors.allocation.unit_gender_unknown_blocked",
                params={
                    "unit_name": unit.name,
                    "restriction": unit.gender_restriction,
                    "participant_name": f"{participant.first_name} {participant.last_name}",
                },
                status_code=409,
            )
        if participant.gender.lower() != unit.gender_restriction.lower():
            raise MoimioAppError(
                "errors.allocation.unit_gender_restricted",
                params={
                    "unit_name": unit.name,
                    "restriction": unit.gender_restriction,
                },
                status_code=409,
            )

    # Check not already in this exact unit
    dup = await db.execute(
        select(Allocation).where(
            Allocation.participant_id == participant_id,
            Allocation.unit_id == unit_id,
        )
    )
    if dup.scalar_one_or_none():
        raise MoimioAppError("errors.allocation.already_assigned", status_code=409)

    alloc = Allocation(event_id=event_id, participant_id=participant_id, unit_id=unit_id)
    db.add(alloc)
    # v0.60a: audit-log the assignment. Recorded in the same transaction
    # as the allocation insert — a rollback clears both cleanly.
    await record_allocation_event(
        db,
        event_id=event_id,
        participant_id=participant_id,
        unit_id=unit.id,
        category_id=cat.id,
        unit_name_snapshot=unit.name,
        category_name_snapshot=cat.name,
        event_type=AllocationEventType.ASSIGN,
        source=AllocationEventSource.MANUAL,
        actor_user_id=actor_user_id,
    )
    await db.flush()
    await db.refresh(alloc)
    return alloc


async def move_participant(
    db: AsyncSession,
    event_id: uuid.UUID,
    to_unit_id: uuid.UUID,
    participant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
) -> Allocation:
    """Move participant to a different unit (handles exclusive removal automatically)."""
    return await assign_participant(db, event_id, to_unit_id, participant_id, actor_user_id)


async def unassign_participant(
    db: AsyncSession,
    unit_id: uuid.UUID,
    participant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
) -> bool:
    """Remove a participant from a specific unit.

    v0.60a: emits an `unassign` AllocationEvent with source=manual on
    successful deletion. Returns False (and emits no event) when the
    allocation didn't exist in the first place — a failed unassign is
    a no-op, not an audit-worthy action.
    """
    result = await db.execute(
        select(Allocation).where(
            Allocation.unit_id == unit_id,
            Allocation.participant_id == participant_id,
        )
    )
    alloc = result.scalar_one_or_none()
    if not alloc:
        return False

    # Fetch the unit + category for snapshot fields. The unit is in scope
    # by id only; we need its name and its category's name.
    unit = await get_unit(db, unit_id)
    cat = await get_category(db, unit.category_id) if unit else None
    # If unit or cat has disappeared mid-request, fall back to "unknown"
    # labels rather than raising — the deletion should still succeed.
    unit_name = unit.name if unit else "[deleted unit]"
    category_id = unit.category_id if unit else None
    category_name = cat.name if cat else "[deleted category]"

    # v50c-3: unassigning is an edit → revert confirmed if applicable.
    await _unconfirm_category_for_unit(db, unit_id)

    await record_allocation_event(
        db,
        event_id=alloc.event_id,
        participant_id=participant_id,
        unit_id=unit_id,
        category_id=category_id,
        unit_name_snapshot=unit_name,
        category_name_snapshot=category_name,
        event_type=AllocationEventType.UNASSIGN,
        source=AllocationEventSource.MANUAL,
        actor_user_id=actor_user_id,
    )
    await db.delete(alloc)
    await db.flush()
    return True


async def unassign_all_for_participant(
    db: AsyncSession,
    participant_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
    source: str = AllocationEventSource.PARTICIPANT_CANCELLED,
) -> int:
    """Remove ALL of a participant's allocations across every category.

    v0.70d-2a-2: primary caller is the participant-cancellation path
    (`PATCH /api/participants/{id}` with `registration_status='cancelled'`).
    When a participant withdraws, they shouldn't continue to occupy
    spots in allocation units — other people or the allocation engine
    may want those slots. Their PeopleTable record and audit history
    remain; only the live unit memberships are removed.

    Unlike the raw `delete(Allocation).where(...)` that this replaces,
    every deallocation here goes through the canonical per-allocation
    path so that:

      - Each removal emits an `unassign` AllocationEvent with the
        `participant_cancelled` source, so the audit trail
        distinguishes withdrawal-driven cleanups from organiser-
        initiated unassigns.
      - Each affected category's `confirmed` flag is reverted to
        unconfirmed via `_unconfirm_category_for_unit`, so the
        organiser re-reviews categories whose membership just
        changed (mirrors the manual-unassign path).
      - Unit / category name snapshots are captured at the moment
        of unassign, preserving accurate history even if names are
        later renamed.

    Returns the number of allocations removed. Zero if the participant
    had no live allocations, which is a no-op.

    Performance: O(N) per-allocation cycles where N = participant's
    allocation count. For a typical event, N is small (one per
    category — rooms, small group, team, etc.); a participant with
    5 categories produces 5 event rows. Cancellations are cold-path,
    so the overhead is acceptable vs. the correctness + auditability
    gain.
    """
    # Fetch the participant's live allocations. Do one query to the
    # Allocation table; snapshot data for each (unit name, category
    # name) is then fetched inside the loop like unassign_participant
    # does — this keeps the canonical pattern identical and avoids a
    # separate code path for "bulk" cleanup.
    result = await db.execute(
        select(Allocation).where(Allocation.participant_id == participant_id)
    )
    allocations = list(result.scalars().all())
    if not allocations:
        return 0

    removed = 0
    for alloc in allocations:
        unit = await get_unit(db, alloc.unit_id)
        cat = await get_category(db, unit.category_id) if unit else None
        unit_name = unit.name if unit else "[deleted unit]"
        category_id = unit.category_id if unit else None
        category_name = cat.name if cat else "[deleted category]"

        # v50c-3 / v0.70d-2a-2: mirror the manual unassign path —
        # removing a member from a category invalidates the
        # organiser's prior "confirmed" sign-off on that category,
        # even when the trigger was the participant cancelling
        # rather than a direct organiser action.
        await _unconfirm_category_for_unit(db, alloc.unit_id)

        await record_allocation_event(
            db,
            event_id=alloc.event_id,
            participant_id=participant_id,
            unit_id=alloc.unit_id,
            category_id=category_id,
            unit_name_snapshot=unit_name,
            category_name_snapshot=category_name,
            event_type=AllocationEventType.UNASSIGN,
            source=source,
            actor_user_id=actor_user_id,
        )
        await db.delete(alloc)
        removed += 1

    await db.flush()
    return removed


async def get_allocations_by_category(db: AsyncSession, category_id: uuid.UUID) -> dict:
    """Get all allocations grouped by unit for a category. Returns {unit_id: [members]}.

    Performance: ``list_units`` (2 queries) + 1 joined query pulling every
    allocation+participant for the category at once. Grouping is done in
    Python. Flat query count regardless of unit or allocation count.
    """
    units = await list_units(db, category_id)
    result = {str(u["id"]): [] for u in units}
    if not units:
        return result
    unit_ids = [u["id"] for u in units]

    alloc_q = await db.execute(
        select(Allocation, Participant)
        .join(Participant, Allocation.participant_id == Participant.id)
        .where(Allocation.unit_id.in_(unit_ids))
    )
    for alloc, p in alloc_q.all():
        result[str(alloc.unit_id)].append({
            "allocation_id": str(alloc.id),
            "participant_id": str(p.id),
            "participant_name": f"{p.first_name} {p.last_name}",
        })
    return result


async def get_all_allocations(db: AsyncSession, event_id: uuid.UUID) -> dict:
    """Get every allocation for an event. Returns {category_id: {unit_id: [members]}}.

    Performance (v0.57b): flat query count regardless of scale.
        1. Fetch categories.
        2. Fetch all units for those categories.
        3. Fetch all allocations+participants for those units.
    Grouping is done in Python. Old code issued 3 queries per category via
    get_allocations_by_category, so O(3 * categories) queries.
    """
    cats_q = await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == event_id)
    )
    cats = list(cats_q.scalars().all())
    out: dict = {str(c.id): {} for c in cats}
    if not cats:
        return out

    cat_ids = [c.id for c in cats]
    units_q = await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id.in_(cat_ids))
    )
    units = list(units_q.scalars().all())
    # Initialise every unit with an empty member list so callers can rely
    # on the dict shape even for unoccupied units (preserves the shape
    # that get_allocations_by_category returns).
    for u in units:
        out[str(u.category_id)][str(u.id)] = []
    if not units:
        return out

    unit_to_cat = {u.id: u.category_id for u in units}
    unit_ids = [u.id for u in units]

    alloc_q = await db.execute(
        select(Allocation, Participant)
        .join(Participant, Allocation.participant_id == Participant.id)
        .where(Allocation.unit_id.in_(unit_ids))
    )
    for alloc, p in alloc_q.all():
        cat_id = unit_to_cat.get(alloc.unit_id)
        if cat_id is None:
            continue
        out[str(cat_id)][str(alloc.unit_id)].append({
            "allocation_id": str(alloc.id),
            "participant_id": str(p.id),
            "participant_name": f"{p.first_name} {p.last_name}",
        })
    return out


# ── v1.0.0e: soft-warning computation for manual moves ─────────────────


# Reasons that bind a participant's placement to an engine-honoured
# rule. When the latest engine commit for this participant carries
# one of these reasons (peeled past any `equalise` wrapper), a
# manual move that would override the rule produces a soft warning.
# Other reasons (`fill`, `mark_split`) do not produce warnings —
# `fill` carries no constraint, and `mark_split` participants were
# placed AWAY from peers on purpose, so a manual move further away
# isn't an override.
_BINDING_REASONS = frozenset({
    "group_code",
    "group_code_split",
    "mark_together",
    "mark_together_split",
    "gender_drain",
})


def _peel_equalise(placement: dict | None) -> dict | None:
    """Return the binding placement, peeling off any equalise wrapper.

    The equalise pass wraps the original cluster reason under
    `previous`. The cluster constraint that the engine actually
    honoured lives there; equalise itself imposes no participant-
    level rule. For warning purposes we look at the binding payload.
    """
    if not placement:
        return None
    if placement.get("reason") == "equalise":
        return placement.get("previous") or None
    return placement


async def _latest_engine_placement(
    db: AsyncSession,
    *,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    participant_id: uuid.UUID,
) -> dict | None:
    """Return meta.placement from the most recent engine_commit assign
    event for the given participant in the given category, or None.

    The lookup is bounded by category_id so cross-category history
    doesn't leak. Newest-first by occurred_at — the same ordering the
    audit log uses.
    """
    from app.models.allocation_event import AllocationEvent
    q = await db.execute(
        select(AllocationEvent)
        .where(
            AllocationEvent.event_id == event_id,
            AllocationEvent.category_id == category_id,
            AllocationEvent.participant_id == participant_id,
            AllocationEvent.event_type == AllocationEventType.ASSIGN,
            AllocationEvent.source == AllocationEventSource.ENGINE_COMMIT,
        )
        .order_by(AllocationEvent.occurred_at.desc())
        .limit(1)
    )
    row = q.scalar_one_or_none()
    if not row or not row.meta:
        return None
    return row.meta.get("placement") or None


async def _mark_behaviour_for(
    db: AsyncSession,
    *,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    mark_id: str | None,
) -> str:
    """Return the effective cluster_behaviour for a mark in this
    category — honouring per-category overrides. Returns "none" if
    the mark or its definition has been removed.
    """
    if not mark_id:
        return "none"
    cat = await get_category(db, category_id)
    if not cat:
        return "none"
    cat_settings = (cat.settings or {}).get("engine", {})
    overrides = {}
    for entry in cat_settings.get("mark_priorities", []) or []:
        if isinstance(entry, dict) and entry.get("id") and entry.get("behaviour"):
            overrides[str(entry["id"])] = entry["behaviour"]
    if mark_id in overrides:
        return overrides[mark_id]
    # Fall back to the global definition.
    from app.models.mark import MarkDefinition
    md_q = await db.execute(
        select(MarkDefinition).where(MarkDefinition.id == uuid.UUID(mark_id))
    )
    md = md_q.scalar_one_or_none()
    if not md:
        return "none"
    return getattr(md, "cluster_behaviour", None) or "none"


async def compute_manual_move_warning(
    db: AsyncSession,
    *,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    participant_id: uuid.UUID,
    new_unit_id: uuid.UUID | None,
) -> dict | None:
    """v1.0.0e: compute a soft warning for a manual move that overrides
    an engine-honoured rule. Returns a dict shaped as

        {"key": "organise.warning.<...>",
         "params": {"name": "...", "code": "...", ...}}

    or None when no warning should fire.

    Trigger conditions, in order:

      1. The participant has a most-recent engine_commit assign event
         in this category. (No engine commit → nothing for the manual
         move to override → no warning.)
      2. The binding reason (peeled past any equalise wrapper) is in
         _BINDING_REASONS. (Reasons like `fill`/`mark_split` impose no
         participant-level rule — see _BINDING_REASONS docstring.)
      3. The rule is still active in the category. group_code rules
         require `settings.engine.use_group_codes` to be true; mark
         rules require the mark's effective behaviour to be `together`.
         If the rule has since been disabled, the engine no longer
         claims to honour it, so a manual move can't "override" it.
      4. The new placement actually breaks the rule. For
         group_code*/mark_together* this means the participant has no
         clustermate at the destination (or is unassigned). For
         gender_drain it means the destination has a different gender
         restriction profile than the original drained unit.

    The function is read-only — it never modifies allocations or events.
    Callers (typically the API layer right after a successful write)
    forward the returned dict to the response payload as the "warning"
    field; the frontend renders it as a gold soft-warning toast.
    """
    placement = await _latest_engine_placement(
        db,
        event_id=event_id,
        category_id=category_id,
        participant_id=participant_id,
    )
    binding = _peel_equalise(placement)
    if not binding:
        return None
    reason = binding.get("reason")
    if reason not in _BINDING_REASONS:
        return None

    cat = await get_category(db, category_id)
    if not cat:
        return None
    cat_settings = (cat.settings or {}).get("engine", {})

    participant_q = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = participant_q.scalar_one_or_none()
    if not participant:
        return None
    name = f"{participant.first_name} {participant.last_name}".strip()

    # ── Group code rules ──
    if reason in ("group_code", "group_code_split"):
        if not cat_settings.get("use_group_codes", True):
            return None
        code = binding.get("cluster_id") or participant.group_code or ""
        if not code:
            return None
        # Find the participant's clustermates in this event with the
        # same group_code (excluding the participant themself).
        clustermates_q = await db.execute(
            select(Participant.id).where(
                Participant.event_id == event_id,
                Participant.group_code == code,
                Participant.id != participant_id,
                Participant.deleted_at.is_(None),
            )
        )
        clustermate_ids = {row[0] for row in clustermates_q.all()}
        if not clustermate_ids:
            return None  # Lone clustermate — nothing to break.

        if new_unit_id is None:
            # Move to unassigned — definitively separated from cluster.
            return {
                "key": "organise.warning.group_separated",
                "params": {"name": name, "code": code},
            }

        # Check whether any clustermate still occupies new_unit_id.
        co_q = await db.execute(
            select(func.count())
            .select_from(Allocation)
            .where(
                Allocation.unit_id == new_unit_id,
                Allocation.participant_id.in_(clustermate_ids),
            )
        )
        co_count = co_q.scalar_one()
        if co_count == 0:
            # Distinguish "whole group lost" from "moved to a different
            # unit but cluster still exists somewhere". Both warrant a
            # warning; the wording differs slightly. For a whole
            # cluster (`group_code`) — the cluster was kept together,
            # now it's split. For a split cluster (`group_code_split`)
            # — the participant is now alone, separated from the rest.
            key = (
                "organise.warning.group_split"
                if reason == "group_code"
                else "organise.warning.group_separated"
            )
            return {"key": key, "params": {"name": name, "code": code}}
        return None

    # ── Mark together rules ──
    if reason in ("mark_together", "mark_together_split"):
        mark_id = binding.get("cluster_id")
        behaviour = await _mark_behaviour_for(
            db, event_id=event_id, category_id=category_id, mark_id=mark_id,
        )
        if behaviour != "together":
            return None  # rule no longer active for this mark
        if not mark_id:
            return None
        # Find clustermates: other participants in this event tagged
        # with the same mark.
        from app.models.mark import MarkAssignment
        mates_q = await db.execute(
            select(MarkAssignment.participant_id).where(
                MarkAssignment.event_id == event_id,
                MarkAssignment.mark_id == uuid.UUID(mark_id),
                MarkAssignment.participant_id != participant_id,
            )
        )
        mate_ids = {row[0] for row in mates_q.all()}
        if not mate_ids:
            return None
        if new_unit_id is None:
            return {
                "key": "organise.warning.mark_separated",
                "params": {"name": name},
            }
        co_q = await db.execute(
            select(func.count())
            .select_from(Allocation)
            .where(
                Allocation.unit_id == new_unit_id,
                Allocation.participant_id.in_(mate_ids),
            )
        )
        co_count = co_q.scalar_one()
        if co_count == 0:
            return {
                "key": "organise.warning.mark_separated",
                "params": {"name": name},
            }
        return None

    # ── Gender drain ──
    if reason == "gender_drain":
        # The original placement was in a gender-restricted unit. A
        # manual move out of that unit doesn't violate a hard rule
        # (the backend would reject hard violations as 409 errors
        # before reaching this function). The warning is purely a
        # heads-up: the engine had filled this restricted unit on
        # purpose, and the move undoes that.
        if new_unit_id is None:
            return {
                "key": "organise.warning.gender_restriction",
                "params": {"name": name},
            }
        # If the destination has a different gender restriction profile
        # from the original (or none), warn. Same restriction → silent.
        new_unit = await get_unit(db, new_unit_id)
        if not new_unit:
            return None
        original_restriction = (binding.get("gender_restriction") or "").lower()
        new_restriction = (new_unit.gender_restriction or "").lower()
        if original_restriction != new_restriction:
            return {
                "key": "organise.warning.gender_restriction",
                "params": {"name": name},
            }
        return None

    return None
