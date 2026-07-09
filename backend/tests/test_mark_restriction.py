"""v1.0.1e — mark-restriction engine behaviour.

A unit may carry a single mark restriction. When set, only participants
holding that mark may be placed in the unit, enforced strictly (the mark
twin of gender_restriction). These tests prove the behaviour we agreed:

  1. drain + strict — mark-holders are pulled INTO the restricted room
     rather than scattering, and non-holders never enter it (empty beds
     are left rather than backfilled);
  2. overflow — surplus holders spill to unrestricted rooms;
  3. gender AND mark stack (a "male + Leaders" room takes only male leaders);
  4. families are all-or-nothing (a group-coded family with only some
     holders skips the restricted room and stays together elsewhere);
  5. composition — a group-coded family who all hold a "family" mark, with
     exclusive group codes on, lands in the family-restricted room to itself.

All need the Postgres test DB (shared db_engine fixture); they skip when
it is unreachable.
"""

import pytest

from app.services.engine_service import run_engine
from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_mark,
    make_participant,
    assign_mark,
)


def _placement_map(result):
    """pid -> unit_id string, from the engine proposal."""
    placed = {}
    for uid, pids in result["proposed"].items():
        for pid in pids:
            placed[pid] = uid
    return placed


async def _restrict(db, unit, mark):
    unit.mark_restriction = mark.id
    await db.flush()


@pytest.mark.asyncio
async def test_holders_drained_in_and_non_holders_kept_out(db):
    """The core case: leaders are pulled into the Leaders room (not left in
    the roomy general room), and no non-leader is admitted even though beds
    are free."""
    ev = await make_event(db)
    cat = await make_category(db, ev.id, name="Rooms", has_capacity=True)
    leaders = await make_mark(db, ev.id, name="Leaders")

    leaders_room = await make_unit(db, cat.id, "Leaders room", capacity=4)
    await _restrict(db, leaders_room, leaders)
    general = await make_unit(db, cat.id, "General", capacity=20)

    holder_ids = []
    for i in range(2):
        p = await make_participant(db, ev.id, first_name=f"Lead{i}", gender="male")
        await assign_mark(db, ev.id, leaders.id, p.id)
        holder_ids.append(str(p.id))
    other_ids = [str((await make_participant(db, ev.id, first_name=f"Gen{i}", gender="male")).id)
                 for i in range(5)]
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    placed = _placement_map(result)

    lr = str(leaders_room.id)
    # Both leaders drained into the Leaders room...
    assert all(placed[h] == lr for h in holder_ids)
    # ...exactly them, nobody else (strict: 2 in a 4-cap room, beds left empty).
    assert set(result["proposed"][lr]) == set(holder_ids)
    # Every non-leader is in general, never in the restricted room.
    assert all(placed[o] == str(general.id) for o in other_ids)


@pytest.mark.asyncio
async def test_surplus_holders_overflow_to_unrestricted(db):
    """More holders than the restricted room holds → the room fills with
    holders and the rest spill to general; non-holders still never enter."""
    ev = await make_event(db)
    cat = await make_category(db, ev.id, name="Rooms", has_capacity=True)
    leaders = await make_mark(db, ev.id, name="Leaders")

    leaders_room = await make_unit(db, cat.id, "Leaders room", capacity=2)
    await _restrict(db, leaders_room, leaders)
    general = await make_unit(db, cat.id, "General", capacity=20)

    holder_ids = []
    for i in range(4):
        p = await make_participant(db, ev.id, first_name=f"Lead{i}", gender="female")
        await assign_mark(db, ev.id, leaders.id, p.id)
        holder_ids.append(str(p.id))
    other_ids = [str((await make_participant(db, ev.id, first_name=f"Gen{i}", gender="female")).id)
                 for i in range(3)]
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    placed = _placement_map(result)
    lr = str(leaders_room.id)

    assert len(result["proposed"][lr]) == 2                     # room full
    assert set(result["proposed"][lr]).issubset(set(holder_ids))  # only holders inside
    assert all(placed[o] == str(general.id) for o in other_ids)   # non-holders in general
    # The two surplus leaders went to general, not nowhere.
    assert sum(1 for h in holder_ids if placed[h] == str(general.id)) == 2


@pytest.mark.asyncio
async def test_gender_and_mark_stack_with_and(db):
    """A room restricted by gender AND mark admits only participants who
    satisfy both."""
    ev = await make_event(db)
    cat = await make_category(db, ev.id, name="Rooms", has_capacity=True,
                              has_gender_restriction=True)
    leaders = await make_mark(db, ev.id, name="Leaders")

    male_leaders = await make_unit(db, cat.id, "Male leaders", capacity=4,
                                   gender_restriction="male")
    await _restrict(db, male_leaders, leaders)
    general = await make_unit(db, cat.id, "General", capacity=20)

    p_ml = await make_participant(db, ev.id, first_name="MaleLead", gender="male")
    p_fl = await make_participant(db, ev.id, first_name="FemLead", gender="female")
    p_mn = await make_participant(db, ev.id, first_name="MaleGen", gender="male")
    p_fn = await make_participant(db, ev.id, first_name="FemGen", gender="female")
    await assign_mark(db, ev.id, leaders.id, p_ml.id)
    await assign_mark(db, ev.id, leaders.id, p_fl.id)  # leader but wrong gender
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    placed = _placement_map(result)
    mlr = str(male_leaders.id)

    assert result["proposed"][mlr] == [str(p_ml.id)]            # only the male leader
    for p in (p_fl, p_mn, p_fn):
        assert placed[str(p.id)] == str(general.id)


@pytest.mark.asyncio
async def test_family_all_or_nothing(db):
    """A group-coded family where only some members hold the mark skips the
    restricted room entirely and stays together in a general room."""
    ev = await make_event(db)
    cat = await make_category(db, ev.id, name="Rooms", has_capacity=True,
                              settings={"engine": {"use_group_codes": True}})
    leaders = await make_mark(db, ev.id, name="Leaders")

    leaders_room = await make_unit(db, cat.id, "Leaders room", capacity=10)
    await _restrict(db, leaders_room, leaders)
    general = await make_unit(db, cat.id, "General", capacity=10)

    kim = []
    for i in range(3):
        p = await make_participant(db, ev.id, first_name=f"Kim{i}", last_name="Kim",
                                   gender="male", group_code="KIM-742")
        kim.append(p)
    # Only two of the three carry the mark.
    await assign_mark(db, ev.id, leaders.id, kim[0].id)
    await assign_mark(db, ev.id, leaders.id, kim[1].id)
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    placed = _placement_map(result)
    kim_ids = [str(p.id) for p in kim]

    # Whole family in one unit, and that unit is NOT the restricted room.
    assert len({placed[k] for k in kim_ids}) == 1
    assert placed[kim_ids[0]] == str(general.id)
    assert all(k not in result["proposed"][str(leaders_room.id)] for k in kim_ids)


@pytest.mark.asyncio
async def test_family_with_family_mark_claims_family_room_exclusively(db):
    """Composition: a group-coded family who all hold the 'family' mark, with
    exclusive group codes on, land together in the family-restricted room to
    themselves; unmarked individuals go to general."""
    ev = await make_event(db)
    cat = await make_category(db, ev.id, name="Rooms", has_capacity=True,
                              exclusive_group_codes=True,
                              settings={"engine": {"use_group_codes": True}})
    family = await make_mark(db, ev.id, name="family")

    family_room = await make_unit(db, cat.id, "Family room", capacity=6)
    await _restrict(db, family_room, family)
    general = await make_unit(db, cat.id, "General", capacity=20)

    kim = []
    for i in range(4):
        p = await make_participant(db, ev.id, first_name=f"Kim{i}", last_name="Kim",
                                   gender="female", group_code="KIM-742")
        await assign_mark(db, ev.id, family.id, p.id)
        kim.append(p)
    indiv = [await make_participant(db, ev.id, first_name=f"Solo{i}", gender="female")
             for i in range(3)]
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    placed = _placement_map(result)
    fr = str(family_room.id)
    kim_ids = [str(p.id) for p in kim]

    # The whole family, together, in the family room, to themselves.
    assert set(result["proposed"][fr]) == set(kim_ids)
    # Individuals are elsewhere (general), never in the exclusive family room.
    for p in indiv:
        assert placed[str(p.id)] == str(general.id)
