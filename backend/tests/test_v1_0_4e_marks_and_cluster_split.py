"""v1.0.4e — mark packing, mark priority order, and cluster split capacity.

Four defects fixed in this release, one test each plus two guards that
the group_code path is unchanged.

1. A mark with cluster_behaviour='together' was even-split across as
   many units as it took, leaving free capacity in every unit it
   touched; PASS 4b then filled every one of those holes with
   non-holders. Result: several mixed units where one was correct.

2. PASS 2 and PASS 3 were two consecutive loops — every 'together'
   mark, then every 'split' mark — so pass order overrode the
   organiser's mark_priorities order.

3. _place_cluster clamped each share to the unit's remaining capacity
   and discarded the remainder instead of passing it to the next unit
   in the combo, dropping members out of a cluster that had room.

4. unplaced_reasons kept stale entries for participants that a later
   pass placed.
"""

import pytest

from app.services.engine_service import run_engine

from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_participant,
    make_mark,
    assign_mark,
)


def _counts(result, units, member_ids):
    """(members, others) per unit, in the order `units` was given."""
    out = []
    for u in units:
        pids = result["proposed"][str(u.id)]
        n = sum(1 for p in pids if p in member_ids)
        out.append((n, len(pids) - n))
    return out


# ─── 1. keep-together saturates instead of spreading ───────────────────


@pytest.mark.anyio
async def test_v104e_mark_together_saturates_one_unit_at_a_time(db):
    """15 mark holders, 30 people, three rooms of 10.

    Before: 8 / 7 / 0 holders, so TWO rooms came out mixed.
    After:  10 / 5 / 0, so exactly ONE room is mixed and the first is
    entirely holders.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    rooms = [await make_unit(db, cat.id, n, capacity=10) for n in ("A", "B", "C")]

    mark = await make_mark(db, event.id, name="Choir", cluster_behaviour="together")
    cat.settings = {
        "engine": {
            "use_group_codes": False,
            "group_remaining_by_gender": False,
            "split_oversized_groups": False,
            "include_pending_in_allocation": False,
            "equalise_after_allocation": False,
            "mark_priorities": [str(mark.id)],
        }
    }
    await db.flush()

    holders = set()
    for i in range(30):
        p = await make_participant(db, event.id, first_name=f"P{i:02d}")
        if i < 15:
            await assign_mark(db, event.id, mark.id, p.id)
            holders.add(str(p.id))
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")

    assert _counts(res, rooms, holders) == [(10, 0), (5, 5), (0, 10)]
    assert res["stats"]["unplaced"] == 0
    # Exactly one room mixes holders with non-holders.
    mixed = sum(1 for m, o in _counts(res, rooms, holders) if m and o)
    assert mixed == 1


@pytest.mark.anyio
async def test_v104e_mark_together_fills_two_units_before_the_third(db):
    """25 holders over three rooms of 10 → 10 / 10 / 5, not 9 / 8 / 8."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    rooms = [await make_unit(db, cat.id, n, capacity=10) for n in ("A", "B", "C")]

    mark = await make_mark(db, event.id, name="Youth", cluster_behaviour="together")
    cat.settings = {"engine": {
        "use_group_codes": False,
        "equalise_after_allocation": False,
        "mark_priorities": [str(mark.id)],
    }}
    await db.flush()

    holders = set()
    for i in range(30):
        p = await make_participant(db, event.id, first_name=f"P{i:02d}")
        if i < 25:
            await assign_mark(db, event.id, mark.id, p.id)
            holders.add(str(p.id))
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")
    assert _counts(res, rooms, holders) == [(10, 0), (10, 0), (5, 5)]


# ─── 2. mark priority order beats pass order ───────────────────────────


@pytest.mark.anyio
async def test_v104e_higher_priority_spread_mark_runs_before_together(db):
    """Spread mark at priority 1, keep-together at priority 2.

    10 groups of 4, 10 spread-holders, 8 together-holders.

    Before: the together mark ran first (pass order), saturated G1 and
    G2, and the spread pass — whose eligible list filters on
    remaining_cap > 0 — then had 8 units for 10 people and doubled two
    of them up, leaving G1 and G2 with no spread-holder at all.

    After: exactly one spread-holder per group.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    groups = [await make_unit(db, cat.id, f"G{i + 1}", capacity=4) for i in range(10)]

    spread = await make_mark(db, event.id, name="Leaders", cluster_behaviour="split")
    together = await make_mark(db, event.id, name="Family", cluster_behaviour="together")
    # Priority order: spread FIRST, together second.
    cat.settings = {"engine": {
        "use_group_codes": False,
        "equalise_after_allocation": False,
        "mark_priorities": [str(spread.id), str(together.id)],
    }}
    await db.flush()

    spread_ids, together_ids = set(), set()
    for i in range(40):
        p = await make_participant(db, event.id, first_name=f"P{i:02d}")
        if i < 10:
            await assign_mark(db, event.id, spread.id, p.id)
            spread_ids.add(str(p.id))
        elif i < 18:
            await assign_mark(db, event.id, together.id, p.id)
            together_ids.add(str(p.id))
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")

    per_group = [n for n, _ in _counts(res, groups, spread_ids)]
    assert per_group == [1] * 10, per_group
    assert res["stats"]["unplaced"] == 0


# ─── 3. cluster split no longer drops members a unit could hold ────────


@pytest.mark.anyio
async def test_v104e_group_code_split_keeps_every_member_in_the_cluster(db):
    """A group code of 5 over rooms of 2 and 4.

    Before: shares were 3 and 2, the 3 was clamped to 2, and the third
    member was discarded with no_capacity_remaining while room B still
    had two free beds. They were then re-placed by PASS 4b as an
    anonymous 'fill'.

    After: all five carry group_code_split.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    room_a = await make_unit(db, cat.id, "A", capacity=2)
    room_b = await make_unit(db, cat.id, "B", capacity=4)

    cat.settings = {"engine": {
        "use_group_codes": True,
        "split_oversized_groups": True,
        "equalise_after_allocation": False,
        "mark_priorities": [],
    }}
    await db.flush()

    family = []
    for i in range(5):
        p = await make_participant(db, event.id, first_name=f"Lim{i}", group_code="LIM")
        family.append(str(p.id))
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")

    reasons = {pid: res["placement_reasons"][pid]["reason"] for pid in family}
    assert set(reasons.values()) == {"group_code_split"}, reasons
    assert _counts(res, [room_a, room_b], set(family)) == [(2, 0), (3, 0)]
    assert res["stats"]["unplaced"] == 0


@pytest.mark.anyio
async def test_v104e_group_code_split_uses_no_more_units_than_needed(db):
    """A group code of 7 over rooms of 5, 5, 3, 3.

    Before: 3 in A and 3 in C, with the seventh stranded ALONE in D.
    After: 4 in A and 3 in C — two rooms, and D stays free.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    rooms = [
        await make_unit(db, cat.id, "A", capacity=5),
        await make_unit(db, cat.id, "B", capacity=5),
        await make_unit(db, cat.id, "C", capacity=3),
        await make_unit(db, cat.id, "D", capacity=3),
    ]
    cat.settings = {"engine": {
        "use_group_codes": True,
        "split_oversized_groups": True,
        "equalise_after_allocation": False,
        "mark_priorities": [],
    }}
    await db.flush()

    family = []
    for i in range(7):
        p = await make_participant(db, event.id, first_name=f"Kim{i}", group_code="KIM")
        family.append(str(p.id))
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")

    rooms_touched = sum(1 for n, _ in _counts(res, rooms, set(family)) if n)
    assert rooms_touched == 2, _counts(res, rooms, set(family))
    assert set(
        res["placement_reasons"][pid]["reason"] for pid in family
    ) == {"group_code_split"}


@pytest.mark.anyio
async def test_v104e_group_code_split_is_still_even_when_capacity_allows(db):
    """Guard: group codes still split EVENLY. Only marks concentrate.

    A group code of 6 over two rooms of 4 stays 3 / 3, not 4 / 2.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    rooms = [
        await make_unit(db, cat.id, "A", capacity=4),
        await make_unit(db, cat.id, "B", capacity=4),
    ]
    cat.settings = {"engine": {
        "use_group_codes": True,
        "split_oversized_groups": True,
        "equalise_after_allocation": False,
        "mark_priorities": [],
    }}
    await db.flush()

    family = []
    for i in range(6):
        p = await make_participant(db, event.id, first_name=f"Park{i}", group_code="PARK")
        family.append(str(p.id))
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")
    assert [n for n, _ in _counts(res, rooms, set(family))] == [3, 3]


# ─── 4. unplaced_reasons describes only genuinely unplaced people ──────


@pytest.mark.anyio
async def test_v104e_unplaced_reasons_carries_no_entry_for_placed_people(db):
    """Every key in unplaced_reasons must appear in unplaced."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    await make_unit(db, cat.id, "A", capacity=2)
    await make_unit(db, cat.id, "B", capacity=4)

    cat.settings = {"engine": {
        "use_group_codes": True,
        "split_oversized_groups": True,
        "equalise_after_allocation": False,
        "mark_priorities": [],
    }}
    await db.flush()

    for i in range(5):
        await make_participant(db, event.id, first_name=f"Lee{i}", group_code="LEE")
    await db.flush()

    res = await run_engine(db, event.id, cat.id, mode="replace")

    unplaced = set(res["unplaced"])
    stale = [pid for pid in res["unplaced_reasons"] if pid not in unplaced]
    assert stale == [], stale
