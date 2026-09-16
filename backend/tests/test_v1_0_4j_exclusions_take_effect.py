"""v1.0.4j — exclusions take effect: engine pre-filter, vacate on exclude,
placement clears the exclusion, stats, action_id grouping.

Governing principle: exclusion overrides every other allocation rule.
The other rules decide WHERE a person goes; exclusion decides WHETHER
they are allocated in that group type at all, and that settles first.
Each test asks: can an excluded participant hold an allocation in that
category by this route?

Covers:
  1. Participant in three units of one overlapping category, excluded →
     holds none of them, still holds their allocation in another
     category (the unassign_all_for_participant trap).
  2. Excluding from a confirmed category re-opens it once, for a
     participant holding three units.
  3. Excluding out of a keep-as-is unit removes them; is_kept unchanged.
  4. Engine does not place an excluded participant: replace mode, top_up
     mode with the person already allocated, and the kept-unit seeding
     loop (exclusion row written directly so the allocation is still in
     the table, exercising the belt-and-braces guards).
  5. commit_proposal placing an excluded participant clears the exclusion.
  6. assign_participant placing an excluded participant clears the
     exclusion and returns the fact that it did; move_participant too.
  7. Un-excluding does not restore a previous placement.
  8. Stats: excluded out of total, counted separately, figures reconcile,
     on all three build sites.
  9. Every row from one exclude action shares one action_id; rows from
     two separate actions do not; single-row actions get one too.

Service-layer only, like the v1.0.4i file.
"""

import pytest
from sqlalchemy import select

from app.models.allocation import Allocation
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_event import (
    AllocationEvent,
    AllocationEventSource,
    AllocationEventType,
)
from app.services import allocation_service
from app.services.allocation_service import (
    add_exclusion,
    remove_exclusion,
    list_excluded_participant_ids,
    assign_participant,
    move_participant,
    unassign_participant,
)
from app.services.engine_service import run_engine, commit_proposal

from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_participant,
)


pytestmark = pytest.mark.asyncio


# ─── helpers ───

async def _held_unit_ids(db, participant_id, category_id=None) -> set:
    """Unit ids the participant currently holds, optionally within one category."""
    from app.models.allocation_unit import AllocationUnit
    q = (
        select(Allocation.unit_id)
        .join(AllocationUnit, Allocation.unit_id == AllocationUnit.id)
        .where(Allocation.participant_id == participant_id)
    )
    if category_id is not None:
        q = q.where(AllocationUnit.category_id == category_id)
    result = await db.execute(q)
    return set(result.scalars().all())


async def _events(db, event_id) -> list[AllocationEvent]:
    result = await db.execute(
        select(AllocationEvent)
        .where(AllocationEvent.event_id == event_id)
        .order_by(AllocationEvent.occurred_at, AllocationEvent.id)
    )
    return list(result.scalars().all())


async def _place_directly(db, ev, unit, participant):
    """Write an Allocation row without any service call or audit row."""
    db.add(Allocation(event_id=ev.id, unit_id=unit.id, participant_id=participant.id))
    await db.flush()


async def _exclude_directly(db, cat, participant):
    """Write an exclusion row without add_exclusion, so any allocation the
    participant holds stays in the table. Exercises the engine's own
    guards rather than relying on add_exclusion having vacated first."""
    db.add(AllocationCategoryExclusion(allocation_category_id=cat.id, participant_id=participant.id))
    await db.flush()


def _proposed_pids(result) -> set:
    return {pid for pids in result["proposed"].values() for pid in pids}


async def _three_unit_overlapping(db, ev, name="Teams"):
    cat = await make_category(db, ev.id, name=name, has_capacity=True)
    cat.rule_type = "overlapping"
    await db.flush()
    units = [await make_unit(db, cat.id, f"{name} {i}", capacity=10) for i in range(3)]
    return cat, units


# ─── 1. vacate every unit in that category, and only that category ───

async def test_exclusion_vacates_every_unit_in_category_but_not_other_categories(db):
    ev = await make_event(db)
    teams, team_units = await _three_unit_overlapping(db, ev)
    rooms = await make_category(db, ev.id, name="Rooms", has_capacity=True)
    room = await make_unit(db, rooms.id, "Room 1", capacity=4)
    p = await make_participant(db, ev.id, first_name="Alice")
    for u in team_units:
        await _place_directly(db, ev, u, p)
    await _place_directly(db, ev, room, p)
    assert len(await _held_unit_ids(db, p.id, teams.id)) == 3

    await add_exclusion(db, teams.id, p.id)

    assert await _held_unit_ids(db, p.id, teams.id) == set()
    # The trap: unassign_all_for_participant would have taken the room too.
    assert await _held_unit_ids(db, p.id, rooms.id) == {room.id}

    evs = await _events(db, ev.id)
    assert [e.event_type for e in evs] == (
        [AllocationEventType.EXCLUDE] + [AllocationEventType.UNASSIGN] * 3
    )
    unassigns = [e for e in evs if e.event_type == AllocationEventType.UNASSIGN]
    assert {e.source for e in unassigns} == {AllocationEventSource.PARTICIPANT_EXCLUDED}
    assert {e.unit_id for e in unassigns} == {u.id for u in team_units}
    assert {e.unit_name_snapshot for e in unassigns} == {u.name for u in team_units}
    assert all(e.category_id == teams.id for e in evs)


async def test_exclusion_with_no_allocations_writes_only_the_exclude_row(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id)
    await make_unit(db, cat.id, "Room 1")
    p = await make_participant(db, ev.id)

    await add_exclusion(db, cat.id, p.id)

    evs = await _events(db, ev.id)
    assert [e.event_type for e in evs] == [AllocationEventType.EXCLUDE]


# ─── 2. confirmed category re-opens once ───

async def test_excluding_from_confirmed_category_reopens_it_once(db, monkeypatch):
    ev = await make_event(db)
    cat, units = await _three_unit_overlapping(db, ev)
    p = await make_participant(db, ev.id)
    for u in units:
        await _place_directly(db, ev, u, p)
    cat.confirmed = True
    await db.flush()

    # Count how many times the flag actually flips. The helper is looked
    # up by name at call time, so wrapping the module attribute is enough.
    real = allocation_service._unconfirm_category_if_confirmed
    flips = []

    async def counting(db_, category_id):
        before = (await allocation_service.get_category(db_, category_id)).confirmed
        await real(db_, category_id)
        after = (await allocation_service.get_category(db_, category_id)).confirmed
        if before and not after:
            flips.append(category_id)

    monkeypatch.setattr(allocation_service, "_unconfirm_category_if_confirmed", counting)

    await add_exclusion(db, cat.id, p.id)
    await db.refresh(cat)

    assert cat.confirmed is False
    assert flips == [cat.id]  # three removals, one flip
    assert await _held_unit_ids(db, p.id, cat.id) == set()


# ─── 3. keep-as-is lock is overridden, lock stays on ───

async def test_exclusion_removes_from_kept_unit_and_leaves_lock_on(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    kept = await make_unit(db, cat.id, "Kept room", capacity=4)
    kept.is_kept = True
    await db.flush()
    p = await make_participant(db, ev.id)
    await _place_directly(db, ev, kept, p)

    await add_exclusion(db, cat.id, p.id)
    await db.refresh(kept)

    assert await _held_unit_ids(db, p.id, cat.id) == set()
    assert kept.is_kept is True


# ─── 4. engine never places an excluded participant ───

async def test_engine_replace_does_not_place_excluded(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    await make_unit(db, cat.id, "Room 1", capacity=10)
    people = [await make_participant(db, ev.id, first_name=f"P{i}", gender="male") for i in range(4)]
    await add_exclusion(db, cat.id, people[0].id)

    result = await run_engine(db, ev.id, cat.id, mode="replace")

    assert str(people[0].id) not in _proposed_pids(result)
    assert str(people[0].id) not in result["unplaced"]
    assert _proposed_pids(result) == {str(p.id) for p in people[1:]}


async def test_engine_top_up_does_not_seed_excluded_already_allocated(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    room = await make_unit(db, cat.id, "Room 1", capacity=10)
    stays = await make_participant(db, ev.id, first_name="Stays", gender="male")
    goes = await make_participant(db, ev.id, first_name="Goes", gender="male")
    newcomer = await make_participant(db, ev.id, first_name="New", gender="male")
    await _place_directly(db, ev, room, stays)
    await _place_directly(db, ev, room, goes)
    # Direct row: the allocation is still in the table when the engine runs.
    await _exclude_directly(db, cat, goes)

    result = await run_engine(db, ev.id, cat.id, mode="top_up")

    assert str(goes.id) not in _proposed_pids(result)
    assert str(goes.id) not in result["unplaced"]
    assert _proposed_pids(result) == {str(stays.id), str(newcomer.id)}
    assert result["stats"]["already_allocated"] == 1
    assert result["stats"]["excluded"] == 1
    assert result["stats"]["total"] == 2


async def test_engine_kept_unit_seeding_skips_excluded_occupant(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    kept = await make_unit(db, cat.id, "Kept room", capacity=10)
    kept.is_kept = True
    general = await make_unit(db, cat.id, "General", capacity=10)
    await db.flush()
    orig = await make_participant(db, ev.id, first_name="Orig", gender="male")
    excluded = await make_participant(db, ev.id, first_name="Excl", gender="male")
    await _place_directly(db, ev, kept, orig)
    await _place_directly(db, ev, kept, excluded)
    await _exclude_directly(db, cat, excluded)

    result = await run_engine(db, ev.id, cat.id, mode="replace")

    assert result["proposed"][str(kept.id)] == [str(orig.id)]
    assert str(excluded.id) not in _proposed_pids(result)
    assert result["proposed"][str(general.id)] == []


# ─── 5. commit_proposal clears the exclusion for placed pids ───

async def test_commit_proposal_clears_exclusion_for_placed_participant(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    room = await make_unit(db, cat.id, "Room 1", capacity=10)
    kept = await make_unit(db, cat.id, "Kept", capacity=10)
    kept.is_kept = True
    await db.flush()
    placed = await make_participant(db, ev.id, first_name="Placed")
    in_kept = await make_participant(db, ev.id, first_name="InKept")
    untouched = await make_participant(db, ev.id, first_name="Untouched")
    await _place_directly(db, ev, kept, in_kept)
    for p in (placed, in_kept, untouched):
        await _exclude_directly(db, cat, p)

    # An organiser dragged `placed` into the proposal on the review screen.
    # `in_kept` rides along in the kept unit's list, which commit skips.
    await commit_proposal(
        db, ev.id, cat.id,
        {str(room.id): [str(placed.id)], str(kept.id): [str(in_kept.id)]},
    )

    remaining = set(await list_excluded_participant_ids(db, cat.id))
    assert placed.id not in remaining
    assert remaining == {in_kept.id, untouched.id}
    assert await _held_unit_ids(db, placed.id, cat.id) == {room.id}

    evs = await _events(db, ev.id)
    include = [e for e in evs if e.event_type == AllocationEventType.INCLUDE]
    assert len(include) == 1
    assert include[0].participant_id == placed.id
    assert include[0].source == AllocationEventSource.ENGINE_COMMIT
    # The include and the assign are one action.
    assert len({e.action_id for e in evs}) == 1
    assert evs[0].action_id is not None


# ─── 6. assign_participant clears the exclusion and says so ───

async def test_assign_participant_clears_exclusion_and_returns_it(db):
    ev = await make_event(db)
    cat, units = await _three_unit_overlapping(db, ev)
    p = await make_participant(db, ev.id)
    await add_exclusion(db, cat.id, p.id)

    alloc, cleared = await assign_participant(db, ev.id, units[0].id, p.id)

    assert cleared is True
    assert alloc.unit_id == units[0].id
    assert await list_excluded_participant_ids(db, cat.id) == []

    # Nothing left to clear on the next placement in the same category.
    alloc2, cleared2 = await assign_participant(db, ev.id, units[1].id, p.id)
    assert cleared2 is False
    assert alloc2.unit_id == units[1].id

    evs = await _events(db, ev.id)
    types = [e.event_type for e in evs]
    assert types == [
        AllocationEventType.EXCLUDE,
        AllocationEventType.INCLUDE,
        AllocationEventType.ASSIGN,
        AllocationEventType.ASSIGN,
    ]
    include = evs[1]
    assert include.source == AllocationEventSource.MANUAL
    # include + first assign share an action; the exclude and the second
    # assign each have their own.
    assert include.action_id == evs[2].action_id
    assert evs[0].action_id != include.action_id
    assert evs[3].action_id != include.action_id


async def test_move_participant_returns_the_same_shape(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    a = await make_unit(db, cat.id, "A", capacity=4)
    b = await make_unit(db, cat.id, "B", capacity=4)
    p = await make_participant(db, ev.id)
    await _place_directly(db, ev, a, p)
    await _exclude_directly(db, cat, p)

    alloc, cleared = await move_participant(db, ev.id, b.id, p.id)

    assert cleared is True
    assert alloc.unit_id == b.id
    assert await _held_unit_ids(db, p.id, cat.id) == {b.id}
    assert await list_excluded_participant_ids(db, cat.id) == []


# ─── 7. un-excluding restores nothing ───

async def test_remove_exclusion_does_not_restore_previous_placement(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    room = await make_unit(db, cat.id, "Room 1", capacity=4)
    p = await make_participant(db, ev.id)
    await _place_directly(db, ev, room, p)

    await add_exclusion(db, cat.id, p.id)
    assert await _held_unit_ids(db, p.id, cat.id) == set()

    assert await remove_exclusion(db, cat.id, p.id) is True

    assert await _held_unit_ids(db, p.id, cat.id) == set()
    assert await list_excluded_participant_ids(db, cat.id) == []
    # Eligible again: the next engine run places them.
    result = await run_engine(db, ev.id, cat.id, mode="replace")
    assert _proposed_pids(result) == {str(p.id)}


# ─── 8. stats ───

async def test_stats_excluded_out_of_total_and_figures_reconcile(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    await make_unit(db, cat.id, "Room 1", capacity=2)
    people = [await make_participant(db, ev.id, first_name=f"P{i}", gender="male") for i in range(5)]
    await add_exclusion(db, cat.id, people[0].id)
    await add_exclusion(db, cat.id, people[1].id)

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    stats = result["stats"]

    assert stats["excluded"] == 2
    assert stats["total"] == 3
    assert stats["placed"] + stats["unplaced"] == stats["total"]
    assert stats["placed"] == 2 and stats["unplaced"] == 1
    assert stats["total"] + stats["excluded"] == len(people)


async def test_stats_excluded_survives_the_no_participants_exit(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    await make_unit(db, cat.id, "Room 1", capacity=2)
    people = [await make_participant(db, ev.id, first_name=f"P{i}") for i in range(2)]
    for p in people:
        await add_exclusion(db, cat.id, p.id)

    result = await run_engine(db, ev.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 0
    assert result["stats"]["excluded"] == 2
    assert result["unplaced"] == []


async def test_stats_excluded_survives_the_everyone_allocated_exit(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    room = await make_unit(db, cat.id, "Room 1", capacity=4)
    stays = await make_participant(db, ev.id, first_name="Stays", gender="male")
    excluded = await make_participant(db, ev.id, first_name="Excl", gender="male")
    await _place_directly(db, ev, room, stays)
    await add_exclusion(db, cat.id, excluded.id)

    result = await run_engine(db, ev.id, cat.id, mode="top_up")

    assert result["stats"]["total"] == 1
    assert result["stats"]["already_allocated"] == 1
    assert result["stats"]["excluded"] == 1
    assert _proposed_pids(result) == {str(stays.id)}


async def test_stats_excluded_counts_only_eligible_participants(db):
    """A cancelled participant is not in the pool, so excluding them does
    not inflate the figure: total + excluded must equal what was loaded."""
    from app.models.participant import RegistrationStatus
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    await make_unit(db, cat.id, "Room 1", capacity=4)
    active = await make_participant(db, ev.id, first_name="Active")
    cancelled = await make_participant(
        db, ev.id, first_name="Gone", status=RegistrationStatus.CANCELLED
    )
    await add_exclusion(db, cat.id, cancelled.id)

    result = await run_engine(db, ev.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 1
    assert result["stats"]["excluded"] == 0
    assert _proposed_pids(result) == {str(active.id)}


# ─── 9. action_id ───

async def test_rows_from_one_exclude_action_share_an_action_id(db):
    ev = await make_event(db)
    cat, units = await _three_unit_overlapping(db, ev)
    alice = await make_participant(db, ev.id, first_name="Alice")
    bob = await make_participant(db, ev.id, first_name="Bob")
    for u in units:
        await _place_directly(db, ev, u, alice)
        await _place_directly(db, ev, u, bob)

    await add_exclusion(db, cat.id, alice.id)
    await add_exclusion(db, cat.id, bob.id)

    evs = await _events(db, ev.id)
    assert len(evs) == 8
    alice_rows = [e for e in evs if e.participant_id == alice.id]
    bob_rows = [e for e in evs if e.participant_id == bob.id]
    assert len(alice_rows) == 4 and len(bob_rows) == 4
    assert len({e.action_id for e in alice_rows}) == 1
    assert len({e.action_id for e in bob_rows}) == 1
    assert alice_rows[0].action_id is not None
    assert alice_rows[0].action_id != bob_rows[0].action_id
    # And the timestamps really are distinct, so nothing else could group them.
    assert len({e.occurred_at for e in alice_rows}) == 4


async def test_single_row_actions_get_an_action_id_too(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    room = await make_unit(db, cat.id, "Room 1", capacity=4)
    p = await make_participant(db, ev.id)

    await assign_participant(db, ev.id, room.id, p.id)
    await unassign_participant(db, room.id, p.id)
    await add_exclusion(db, cat.id, p.id)
    await remove_exclusion(db, cat.id, p.id)

    evs = await _events(db, ev.id)
    assert [e.event_type for e in evs] == [
        AllocationEventType.ASSIGN,
        AllocationEventType.UNASSIGN,
        AllocationEventType.EXCLUDE,
        AllocationEventType.INCLUDE,
    ]
    ids = [e.action_id for e in evs]
    assert all(i is not None for i in ids)
    assert len(set(ids)) == 4
