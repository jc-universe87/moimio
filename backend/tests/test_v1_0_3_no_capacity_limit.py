"""v1.0.3: capacity 0 means "no capacity limit", and gender is enforced on
every group type.

Guards four things:

  1. The bug this release exists for. Before v1.0.3 a group type with its
     capacity switch off hid the capacity box but still wrote a placeholder
     capacity of 1 to every unit, which the engine enforced. Ten groups then
     took ten people and everyone else came back "no space".
  2. All-uncapped group types spread people evenly.
  3. Option A: on a group type where SOME units carry a capacity and others
     are blank, a blank unit is balanced as an average-sized unit and gets a
     fair share, rather than being treated as full and left empty.
  4. Manual placement honours a unit's gender restriction on a group type
     whose (now dead) gender flag was off — the path automatic allocation
     has always enforced but drag-and-drop did not.
"""
import pytest

from app.core.exceptions import MoimioAppError
from app.services.allocation_service import assign_participant
from app.services.engine_service import run_engine
from tests.conftest import (make_event, make_category, make_unit,
                            make_participant)


async def test_uncapped_units_do_not_cap_at_one(db):
    """The v1.0.3 headline bug, in the shape a real organiser met it."""
    event = await make_event(db)
    cat = await make_category(db, event.id, name="Small Groups")
    for i in range(1, 11):
        await make_unit(db, cat.id, f"Group {i}", capacity=0)
    for i in range(100):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["unplaced"] == 0, (
        "Everyone should be placed when no unit carries a capacity limit; "
        f"{result['stats']['unplaced']} were left over"
    )
    assert result["stats"]["placed"] == 100


async def test_uncapped_units_fill_evenly(db):
    event = await make_event(db)
    cat = await make_category(db, event.id, name="Small Groups")
    for i in range(1, 6):
        await make_unit(db, cat.id, f"Group {i}", capacity=0)
    for i in range(50):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")
    sizes = sorted(len(p) for p in result["proposed"].values())

    assert result["stats"]["unplaced"] == 0
    assert sizes[-1] - sizes[0] <= 1, f"Uneven spread across uncapped units: {sizes}"


async def test_blank_capacity_gets_a_fair_share_alongside_capped_units(db):
    """Option A. The unit whose capacity was never filled in must not be
    skipped: pre-v1.0.3 it counted as permanently full and stayed empty."""
    event = await make_event(db)
    cat = await make_category(db, event.id, name="Rooms", settings={"engine": {
        "use_group_codes": True, "group_remaining_by_gender": True,
        "split_oversized_groups": True, "equalise_after_allocation": True,
    }})
    await make_unit(db, cat.id, "Attic", capacity=2)
    await make_unit(db, cat.id, "Dorm A", capacity=10)
    await make_unit(db, cat.id, "Dorm B", capacity=10)
    side = await make_unit(db, cat.id, "Side room", capacity=0)
    for i in range(20):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["unplaced"] == 0
    side_count = len(result["proposed"].get(str(side.id), []))
    # 20 people over units of 2, 10, 10 and one blank balanced as average
    # size (7) gives roughly 1 / 7 / 7 / 5. Pre-v1.0.3 it was 2 / 9 / 9 / 0.
    # Assert a genuine share rather than merely non-zero, so this test can
    # tell the two behaviours apart.
    assert side_count >= 3, (
        f"The unit left without a capacity received only {side_count} of 20. "
        "It is being treated as full again (the pre-v1.0.3 behaviour)."
    )


async def test_capped_units_are_still_hard_limits(db):
    """The hard limit must be untouched by the uncapped work."""
    event = await make_event(db)
    cat = await make_category(db, event.id, name="Rooms")
    small = await make_unit(db, cat.id, "Twin", capacity=2)
    await make_unit(db, cat.id, "Open room", capacity=0)
    for i in range(20):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert len(result["proposed"].get(str(small.id), [])) <= 2, (
        "A unit with a capacity of 2 took more than two people"
    )
    assert result["stats"]["unplaced"] == 0


async def test_manual_placement_respects_gender_on_any_group_type(db):
    """has_gender_restriction is dead: the unit's own setting decides.

    With the flag off, the engine has blocked this since v0.74 but manual
    drag-and-drop did not, so the two paths disagreed on the same room.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, name="Rooms",
                              has_gender_restriction=False)
    womens = await make_unit(db, cat.id, "Women's room", capacity=4,
                             gender_restriction="female")
    man = await make_participant(db, event.id, first_name="Man", gender="male")
    woman = await make_participant(db, event.id, first_name="Woman", gender="female")

    with pytest.raises(MoimioAppError) as excinfo:
        await assign_participant(db, event.id, womens.id, man.id)
    assert "gender" in excinfo.value.key

    ok = await assign_participant(db, event.id, womens.id, woman.id)
    assert ok is not None
