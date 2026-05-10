"""v0.60a — allocation_events audit trail tests.

Covers the four write surfaces, actor threading, name snapshots, and
the GDPR-compatible FK SET NULL behaviour.

Surfaces under test:
  1. allocation_service.assign_participant — emits `assign`
  2. allocation_service.assign_participant (exclusive cascade) — emits
     `unassign` (source=manual_cascade) + `assign` (source=manual)
  3. allocation_service.unassign_participant — emits `unassign`
  4. engine_service.commit_proposal — emits `unassign` × cleared +
     `assign` × created (source=engine_commit on both)
  5. engine_service.clear_category_allocations (direct call) — emits
     `unassign` (source=clear_category by default)

v0.60b adds a second test section covering the read path —
list_allocation_events — including participant filtering, ordering,
OUTER JOIN behaviour for display names, and FK-null handling.
"""

import uuid

import pytest
from sqlalchemy import select

from app.models.allocation import Allocation
from app.models.allocation_event import (
    AllocationEvent,
    AllocationEventSource,
    AllocationEventType,
)
from app.services.allocation_service import (
    assign_participant,
    unassign_participant,
)
from app.services.allocation_events_service import list_allocation_events
from app.services.engine_service import (
    clear_category_allocations,
    commit_proposal,
)

from tests.conftest import (
    make_user,
    make_event,
    make_category,
    make_unit,
    make_participant,
)


pytestmark = pytest.mark.asyncio


# ─── Helpers ───

async def _fetch_events(db, event_id, **filter_kwargs):
    """Return all allocation_events for an event, ordered by occurred_at."""
    q = select(AllocationEvent).where(AllocationEvent.event_id == event_id)
    for k, v in filter_kwargs.items():
        q = q.where(getattr(AllocationEvent, k) == v)
    q = q.order_by(AllocationEvent.occurred_at, AllocationEvent.id)
    result = await db.execute(q)
    return list(result.scalars().all())


# ─── Surface 1: manual assign ───

async def test_manual_assign_emits_single_assign_event(db):
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id, first_name="Alice")

    await assign_participant(
        db, ev.id, unit.id, p.id, actor_user_id=user.id
    )

    events = await _fetch_events(db, ev.id)
    assert len(events) == 1
    e = events[0]
    assert e.event_type == AllocationEventType.ASSIGN
    assert e.source == AllocationEventSource.MANUAL
    assert e.participant_id == p.id
    assert e.unit_id == unit.id
    assert e.category_id == cat.id
    assert e.actor_user_id == user.id
    assert e.unit_name_snapshot == "Room A"
    assert e.category_name_snapshot == "Rooms"
    assert e.meta is None


# ─── Surface 2: manual unassign ───

async def test_manual_unassign_emits_single_unassign_event(db):
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)
    # Two events at this point: one assign (above). Unassigning adds a third.
    await unassign_participant(db, unit.id, p.id, actor_user_id=user.id)

    events = await _fetch_events(db, ev.id)
    assert len(events) == 2
    assert events[0].event_type == AllocationEventType.ASSIGN
    assert events[1].event_type == AllocationEventType.UNASSIGN
    assert events[1].source == AllocationEventSource.MANUAL
    assert events[1].unit_name_snapshot == "Room A"
    assert events[1].category_name_snapshot == "Rooms"
    assert events[1].actor_user_id == user.id


async def test_unassign_nonexistent_emits_nothing(db):
    """A no-op unassign (participant not in that unit) writes no event."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    result = await unassign_participant(
        db, unit.id, p.id, actor_user_id=user.id
    )
    assert result is False

    events = await _fetch_events(db, ev.id)
    assert events == []


# ─── Surface 3: exclusive-category cascade ───

async def test_exclusive_cascade_emits_paired_unassign_and_assign(db):
    """Moving a participant within an exclusive category emits a paired
    unassign (source=manual_cascade) + assign (source=manual)."""
    user = await make_user(db)
    ev = await make_event(db)
    # Exclusive rule means "a participant can only be in one unit of this
    # category" — default for Rooms.
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit_a = await make_unit(db, category_id=cat.id, name="Room A")
    unit_b = await make_unit(db, category_id=cat.id, name="Room B")
    p = await make_participant(db, event_id=ev.id)

    # First assignment: single event (plain assign).
    await assign_participant(db, ev.id, unit_a.id, p.id, actor_user_id=user.id)
    # Second assignment (the "move"): cascade unassign from A + assign to B.
    await assign_participant(db, ev.id, unit_b.id, p.id, actor_user_id=user.id)

    events = await _fetch_events(db, ev.id)
    assert len(events) == 3

    # Event 0: initial assign to Room A
    assert events[0].event_type == AllocationEventType.ASSIGN
    assert events[0].source == AllocationEventSource.MANUAL
    assert events[0].unit_id == unit_a.id

    # Event 1: cascade unassign from Room A (fires BEFORE the new assign)
    assert events[1].event_type == AllocationEventType.UNASSIGN
    assert events[1].source == AllocationEventSource.MANUAL_CASCADE
    assert events[1].unit_id == unit_a.id
    assert events[1].unit_name_snapshot == "Room A"

    # Event 2: assign to Room B
    assert events[2].event_type == AllocationEventType.ASSIGN
    assert events[2].source == AllocationEventSource.MANUAL
    assert events[2].unit_id == unit_b.id
    assert events[2].unit_name_snapshot == "Room B"


# ─── Surface 4: engine commit_proposal ───

async def test_engine_commit_emits_assign_events_with_engine_source(db):
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit_a = await make_unit(db, category_id=cat.id, name="Room A")
    unit_b = await make_unit(db, category_id=cat.id, name="Room B")
    p1 = await make_participant(db, event_id=ev.id, first_name="Alice")
    p2 = await make_participant(db, event_id=ev.id, first_name="Bob")

    await commit_proposal(
        db, ev.id, cat.id,
        proposed={str(unit_a.id): [str(p1.id)], str(unit_b.id): [str(p2.id)]},
        actor_user_id=user.id,
    )

    events = await _fetch_events(db, ev.id)
    # No clearing events — category was empty. Two assign events.
    assert len(events) == 2
    for e in events:
        assert e.event_type == AllocationEventType.ASSIGN
        assert e.source == AllocationEventSource.ENGINE_COMMIT
        assert e.actor_user_id == user.id
        assert e.category_id == cat.id

    # Each participant placed in their assigned unit, with correct snapshots
    by_participant = {e.participant_id: e for e in events}
    assert by_participant[p1.id].unit_id == unit_a.id
    assert by_participant[p1.id].unit_name_snapshot == "Room A"
    assert by_participant[p2.id].unit_id == unit_b.id
    assert by_participant[p2.id].unit_name_snapshot == "Room B"


async def test_engine_commit_clears_existing_with_engine_source(db):
    """commit_proposal's pre-clear phase emits unassign events with
    source=engine_commit (not clear_category), so the engine commit
    reads as one atomic action in the timeline."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit_a = await make_unit(db, category_id=cat.id, name="Room A")
    unit_b = await make_unit(db, category_id=cat.id, name="Room B")
    p1 = await make_participant(db, event_id=ev.id)
    p2 = await make_participant(db, event_id=ev.id)

    # Pre-populate: p1 in A, p2 in B (via direct Allocation inserts to
    # avoid muddying the audit log with events from assign_participant).
    db.add(Allocation(event_id=ev.id, unit_id=unit_a.id, participant_id=p1.id))
    db.add(Allocation(event_id=ev.id, unit_id=unit_b.id, participant_id=p2.id))
    await db.flush()

    # Engine commit: swap them.
    await commit_proposal(
        db, ev.id, cat.id,
        proposed={str(unit_a.id): [str(p2.id)], str(unit_b.id): [str(p1.id)]},
        actor_user_id=user.id,
    )

    events = await _fetch_events(db, ev.id)
    # 2 cleared unassigns + 2 fresh assigns = 4 events, all source=engine_commit
    assert len(events) == 4
    for e in events:
        assert e.source == AllocationEventSource.ENGINE_COMMIT

    unassigns = [e for e in events if e.event_type == AllocationEventType.UNASSIGN]
    assigns = [e for e in events if e.event_type == AllocationEventType.ASSIGN]
    assert len(unassigns) == 2
    assert len(assigns) == 2


# ─── Surface 5: manual clear_category_allocations ───

async def test_manual_clear_category_emits_unassign_with_default_source(db):
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p1 = await make_participant(db, event_id=ev.id)
    p2 = await make_participant(db, event_id=ev.id)

    # Seed allocations directly (bypass audit log).
    db.add(Allocation(event_id=ev.id, unit_id=unit.id, participant_id=p1.id))
    db.add(Allocation(event_id=ev.id, unit_id=unit.id, participant_id=p2.id))
    await db.flush()

    count = await clear_category_allocations(
        db, ev.id, cat.id, actor_user_id=user.id
    )
    assert count == 2

    events = await _fetch_events(db, ev.id)
    assert len(events) == 2
    for e in events:
        assert e.event_type == AllocationEventType.UNASSIGN
        assert e.source == AllocationEventSource.CLEAR_CATEGORY
        assert e.actor_user_id == user.id
        assert e.unit_name_snapshot == "Room A"
        assert e.category_name_snapshot == "Rooms"


# ─── Actor threading ───

async def test_actor_user_id_defaults_to_null_when_omitted(db):
    """Callers without user context (tests, batch jobs) can omit
    actor_user_id and get a null attribution in the event row."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    # No actor_user_id passed.
    await assign_participant(db, ev.id, unit.id, p.id)

    events = await _fetch_events(db, ev.id)
    assert len(events) == 1
    assert events[0].actor_user_id is None


# ─── Name snapshots ───

async def test_unit_name_snapshot_survives_rename(db):
    """After a unit is renamed, historical audit events still show
    the name at the time they fired."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)

    # Rename the unit after the event was written.
    unit.name = "Lobby"
    await db.flush()

    events = await _fetch_events(db, ev.id)
    assert events[0].unit_name_snapshot == "Room A"  # unchanged


# ─── GDPR / FK SET NULL ───

async def test_participant_delete_nullifies_audit_row_fk(db):
    """When a participant is hard-deleted, the audit row survives
    with participant_id=NULL. This is the Path 1 (FK nullification)
    GDPR behaviour — no scrub job required."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)
    events_before = await _fetch_events(db, ev.id)
    assert len(events_before) == 1
    assert events_before[0].participant_id == p.id

    # Delete the participant (simulates GDPR erasure).
    await db.delete(p)
    await db.flush()
    # Detach all cached instances so the re-fetch below reads fresh
    # rows from the DB (reflecting the ON DELETE SET NULL cascade).
    # expire_all() would also work but can trigger lazy-load in async
    # contexts; expunge_all() is safer.
    db.expunge_all()

    events_after = await _fetch_events(db, ev.id)
    assert len(events_after) == 1
    assert events_after[0].participant_id is None
    # Snapshots preserved — history still legible after erasure.
    assert events_after[0].unit_name_snapshot == "Room A"


async def test_event_hard_delete_cascades_audit_rows(db):
    """Deleting the parent Event CASCADES the audit rows away.

    Note: the existing schema does NOT cascade from Event → Participant
    (pre-existing design — events are typically archived, not hard-
    deleted). So this test first clears children, then deletes the
    event, to isolate the allocation_events CASCADE behaviour.
    """
    from app.models.event import Event as EventModel
    from app.models.participant import Participant as ParticipantModel

    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)

    # Clear participants first (existing schema: Event→Participant has
    # no CASCADE). Deleting the participant CASCADEs to allocations
    # and SET NULLs the audit row's participant_id.
    await db.delete(p)
    await db.flush()

    # Now delete the event. Its CASCADE on allocation_events.event_id
    # is what this test actually exercises.
    event_obj = (await db.execute(
        select(EventModel).where(EventModel.id == ev.id)
    )).scalar_one()
    await db.delete(event_obj)
    await db.flush()
    db.expunge_all()

    result = await db.execute(
        select(AllocationEvent).where(AllocationEvent.event_id == ev.id)
    )
    assert result.scalars().all() == []


# ─── v0.60b: read path (list_allocation_events) ───

async def test_list_returns_newest_first(db):
    """Events come back in descending occurred_at order."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)
    await unassign_participant(db, unit.id, p.id, actor_user_id=user.id)

    rows = await list_allocation_events(db, event_id=ev.id)
    assert len(rows) == 2
    # Newest first: the unassign (second action) precedes the assign (first).
    assert rows[0]["event_type"] == "unassign"
    assert rows[1]["event_type"] == "assign"


async def test_list_filters_by_participant(db):
    """When participant_id is passed, only that participant's events
    return — useful for the InsightPanel History section."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    alice = await make_participant(db, event_id=ev.id, first_name="Alice")
    bob = await make_participant(db, event_id=ev.id, first_name="Bob")

    await assign_participant(db, ev.id, unit.id, alice.id, actor_user_id=user.id)
    await assign_participant(db, ev.id, unit.id, bob.id, actor_user_id=user.id)

    alice_rows = await list_allocation_events(
        db, event_id=ev.id, participant_id=alice.id
    )
    assert len(alice_rows) == 1
    assert alice_rows[0]["participant_id"] == str(alice.id)
    assert alice_rows[0]["participant_name"] == "Alice Test"

    bob_rows = await list_allocation_events(
        db, event_id=ev.id, participant_id=bob.id
    )
    assert len(bob_rows) == 1
    assert bob_rows[0]["participant_name"] == "Bob Test"


async def test_list_resolves_display_names(db):
    """Serialised rows include the participant's full name and the
    actor's full name via OUTER JOIN, not just FK uuids."""
    user = await make_user(db)
    user.full_name = "Test Admin"
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, name="Rooms")
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id, first_name="Alice", last_name="Wonderland")

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)

    rows = await list_allocation_events(db, event_id=ev.id, participant_id=p.id)
    assert len(rows) == 1
    row = rows[0]
    assert row["participant_name"] == "Alice Wonderland"
    assert row["actor_display_name"] == "Test Admin"
    # Snapshots also come through for unit/category names.
    assert row["unit_name"] == "Room A"
    assert row["category_name"] == "Rooms"


async def test_list_handles_null_fks_after_erasure(db):
    """After a participant is hard-deleted, their audit rows have
    participant_id=NULL. The read path must still return the row
    with participant_name=None (UI renders [removed participant])."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)
    p_id = p.id

    await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)

    # Simulate GDPR erasure.
    await db.delete(p)
    await db.flush()
    db.expunge_all()

    # Can't filter by the now-null FK (filtering by participant_id
    # excludes nulls); read unfiltered and verify the serialisation.
    rows = await list_allocation_events(db, event_id=ev.id)
    assert len(rows) == 1
    assert rows[0]["participant_id"] is None
    assert rows[0]["participant_name"] is None
    # Unit and category snapshots preserved — audit remains legible.
    assert rows[0]["unit_name"] == "Room A"
    # Actor attribution still works — user wasn't deleted.
    assert rows[0]["actor_display_name"] is not None


async def test_list_handles_null_actor(db):
    """Audit rows written without actor_user_id come back with
    actor_display_name=None — used by system-triggered events (today
    only tests/batch paths; future agentic writers)."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    # Omit actor_user_id — defaults to None.
    await assign_participant(db, ev.id, unit.id, p.id)

    rows = await list_allocation_events(db, event_id=ev.id, participant_id=p.id)
    assert len(rows) == 1
    assert rows[0]["actor_user_id"] is None
    assert rows[0]["actor_display_name"] is None


async def test_list_respects_limit_and_clamps_upper(db):
    """limit=N returns at most N rows; over-large values clamp to 2000."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    # Fire 5 assign/unassign pairs = 10 events.
    for _ in range(5):
        await assign_participant(db, ev.id, unit.id, p.id, actor_user_id=user.id)
        await unassign_participant(db, unit.id, p.id, actor_user_id=user.id)

    # Limit to 3 — get the 3 newest.
    rows = await list_allocation_events(db, event_id=ev.id, limit=3)
    assert len(rows) == 3

    # Limit=99999 clamps to 2000; here we only have 10 events so we
    # just verify the full set comes back without error.
    rows = await list_allocation_events(db, event_id=ev.id, limit=99999)
    assert len(rows) == 10


async def test_list_empty_when_no_events(db):
    """An event with no allocation activity returns an empty list,
    not an error."""
    ev = await make_event(db)
    rows = await list_allocation_events(db, event_id=ev.id)
    assert rows == []


async def test_list_isolates_by_event_id(db):
    """Events from different parent Events don't leak into each
    other's timelines."""
    user = await make_user(db)
    ev1 = await make_event(db, name="Retreat 1")
    cat1 = await make_category(db, event_id=ev1.id)
    unit1 = await make_unit(db, category_id=cat1.id, name="Room A")
    p1 = await make_participant(db, event_id=ev1.id)
    await assign_participant(db, ev1.id, unit1.id, p1.id, actor_user_id=user.id)

    ev2 = await make_event(db, name="Retreat 2")
    cat2 = await make_category(db, event_id=ev2.id)
    unit2 = await make_unit(db, category_id=cat2.id, name="Room A")
    p2 = await make_participant(db, event_id=ev2.id)
    await assign_participant(db, ev2.id, unit2.id, p2.id, actor_user_id=user.id)

    rows1 = await list_allocation_events(db, event_id=ev1.id)
    rows2 = await list_allocation_events(db, event_id=ev2.id)
    assert len(rows1) == 1
    assert len(rows2) == 1
    assert rows1[0]["participant_id"] == str(p1.id)
    assert rows2[0]["participant_id"] == str(p2.id)


# ─── v0.60c: engine reasoning capture ───

from app.services.engine_service import run_engine


async def test_run_engine_returns_run_id_and_reasons_shape(db):
    """run_engine always returns placement_reasons + run_id, regardless
    of whether anyone got placed."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    p = await make_participant(db, event_id=ev.id)

    result = await run_engine(db, ev.id, cat.id)
    assert "placement_reasons" in result
    assert "run_id" in result
    assert isinstance(result["placement_reasons"], dict)
    # run_id is a uuid string — parses without raising.
    uuid.UUID(result["run_id"])
    # The participant was placed, so their pid should have a reason.
    assert str(p.id) in result["placement_reasons"]


async def test_run_engine_empty_event_returns_empty_reasons(db):
    """The no-participants early-exit path also populates the new
    fields — shape consistency matters for callers that destructure."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    await make_unit(db, category_id=cat.id, name="Room A")

    result = await run_engine(db, ev.id, cat.id)
    assert result["placement_reasons"] == {}
    uuid.UUID(result["run_id"])  # still present, still a uuid


async def test_placement_reason_fill_for_solitary_participant(db):
    """A participant with no group_code and no mark priorities lands
    via the individual fill pass — reason: 'fill'."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    p = await make_participant(db, event_id=ev.id, first_name="Solo")

    result = await run_engine(db, ev.id, cat.id)
    reason = result["placement_reasons"][str(p.id)]
    assert reason == {"reason": "fill"}


async def test_placement_reason_group_code_cluster_whole(db):
    """Two participants sharing a group_code, cluster fits in one unit
    → both get reason=group_code with cluster_size == cluster_placed_here == 2."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    p1 = await make_participant(db, event_id=ev.id, first_name="Alice", group_code="FAMILY1")
    p2 = await make_participant(db, event_id=ev.id, first_name="Bob",   group_code="FAMILY1")
    # Third participant with a different code — ensures FAMILY1 is a
    # distinct cluster not merged with the fill pool.
    p3 = await make_participant(db, event_id=ev.id, first_name="Carol", group_code="FAMILY2")

    result = await run_engine(db, ev.id, cat.id)

    r1 = result["placement_reasons"][str(p1.id)]
    r2 = result["placement_reasons"][str(p2.id)]
    # Both members of FAMILY1 share the same cluster reason.
    # v1.0.0b: vocabulary aligned with engine output. The pre-v1.1
    # tests asserted `group_code_cluster` / `group_code_cluster_split`
    # — names the engine never emitted; these assertions had been
    # silently failing.
    for r in (r1, r2):
        assert r["reason"] == "group_code"
        assert r["cluster_id"] == "FAMILY1"
        assert r["cluster_size"] == 2
        assert r["cluster_placed_here"] == 2

    # Carol is alone with her code → treated as uncoded → reason=fill.
    # (code_to_members drops singletons into `uncoded` at cluster-build time.)
    r3 = result["placement_reasons"][str(p3.id)]
    assert r3["reason"] == "fill"


async def test_placement_reason_group_code_cluster_split(db):
    """A 4-person cluster into a category where no unit can hold 4 →
    reason=group_code_split. cluster_placed_here reflects how
    many landed in THIS unit (may differ across the split members)."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    # Two units, each cap 2 — a 4-person cluster cannot fit whole.
    await make_unit(db, category_id=cat.id, name="Room A", capacity=2)
    await make_unit(db, category_id=cat.id, name="Room B", capacity=2)
    members = []
    for i in range(4):
        p = await make_participant(
            db, event_id=ev.id,
            first_name=f"Member{i}", group_code="BIGFAMILY",
        )
        members.append(p)

    result = await run_engine(db, ev.id, cat.id)

    for p in members:
        r = result["placement_reasons"][str(p.id)]
        # v1.0.0b: vocab aligned. Was `group_code_cluster_split`.
        assert r["reason"] == "group_code_split"
        assert r["cluster_id"] == "BIGFAMILY"
        assert r["cluster_size"] == 4
        # All four land — 2 in each unit. cluster_placed_here is the
        # local count per unit, so every member sees 2 in this scenario.
        assert r["cluster_placed_here"] == 2


async def test_commit_proposal_writes_meta_when_reasons_provided(db):
    """End-to-end: run_engine → commit_proposal with reasons →
    AllocationEvent rows carry meta with run_id + placement."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    p = await make_participant(db, event_id=ev.id, first_name="Solo")

    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"],
        actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )

    rows = await list_allocation_events(db, event_id=ev.id, participant_id=p.id)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "assign"
    assert rows[0]["source"] == "engine_commit"
    meta = rows[0]["meta"]
    assert meta is not None
    assert meta["run_id"] == result["run_id"]
    assert meta["placement"] == {"reason": "fill"}


async def test_commit_proposal_writes_null_meta_when_reasons_absent(db):
    """Backward compat: commit_proposal called without placement_reasons
    /engine_run_id writes meta=None, matching pre-v0.60c behaviour."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    unit = await make_unit(db, category_id=cat.id, name="Room A")
    p = await make_participant(db, event_id=ev.id)

    await commit_proposal(
        db, ev.id, cat.id,
        proposed={str(unit.id): [str(p.id)]},
        actor_user_id=user.id,
        # no placement_reasons, no engine_run_id
    )

    rows = await list_allocation_events(db, event_id=ev.id)
    # One assign event — no clear because the category was empty.
    assert len(rows) == 1
    assert rows[0]["meta"] is None


async def test_commit_proposal_run_id_correlates_all_assigns(db):
    """Every assign event from one commit shares the same run_id,
    enabling grouping of placements from a single engine invocation."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    pids = []
    for i in range(4):
        p = await make_participant(db, event_id=ev.id, first_name=f"P{i}")
        pids.append(str(p.id))

    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"],
        actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )

    rows = await list_allocation_events(db, event_id=ev.id)
    assigns = [r for r in rows if r["event_type"] == "assign"]
    assert len(assigns) == 4
    # All four assigns carry the same run_id.
    run_ids = {r["meta"]["run_id"] for r in assigns}
    assert run_ids == {result["run_id"]}
