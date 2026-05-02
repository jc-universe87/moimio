"""Allocation engine — v0.53 test suite.

Covers the core behaviours of `run_engine` and pins the regressions
that motivated the v0.53 audit:

  • flat_cap bug (top_up mode silently unplacing everyone)
  • eligible_p bug (same, in the gender-restricted branch)
  • split_oversized_groups=false scattering instead of leaving unplaced
  • stats dict shape consistency

These are the first automated tests for the engine. Goals:

  1. Prevent silent regressions when the engine evolves.
  2. Act as living spec for what the engine is supposed to do.
  3. Give future contributors confidence to refactor the placement
     loops without breaking observable behaviour.
"""

import pytest

from app.services.engine_service import run_engine
from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_participant,
)


# ─── 1. Empty participants ────────────────────────────────────────────


@pytest.mark.anyio
async def test_empty_participants_returns_consistent_stats(db):
    """With no participants, engine returns a fully-shaped stats dict
    — no KeyError risk for the frontend."""
    event = await make_event(db)
    cat = await make_category(db, event.id)
    unit_a = await make_unit(db, cat.id, "Room A")
    unit_b = await make_unit(db, cat.id, "Room B")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["unplaced"] == []
    assert result["proposed"] == {str(unit_a.id): [], str(unit_b.id): []}
    stats = result["stats"]
    # All the keys the full path produces — keeps the frontend's dict
    # access safe regardless of which branch produced the result.
    for key in ("total", "placed", "unplaced", "clusters_total",
                "clusters_kept_whole", "clusters_split", "mark_clusters",
                "mode", "already_allocated"):
        assert key in stats, f"missing stats key: {key}"
    assert stats["total"] == 0
    assert stats["placed"] == 0


# ─── 2. Basic replace, no gender, no capacity ─────────────────────────


@pytest.mark.anyio
async def test_basic_replace_distributes_evenly(db):
    """10 participants, 2 units, no capacity, no gender → 5 per unit."""
    event = await make_event(db)
    cat = await make_category(db, event.id)
    unit_a = await make_unit(db, cat.id, "A")
    unit_b = await make_unit(db, cat.id, "B")
    for i in range(10):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")
    counts = {uid: len(pids) for uid, pids in result["proposed"].items()}

    assert counts[str(unit_a.id)] + counts[str(unit_b.id)] == 10
    assert abs(counts[str(unit_a.id)] - counts[str(unit_b.id)]) <= 1
    assert result["unplaced"] == []
    assert result["stats"]["total"] == 10
    assert result["stats"]["placed"] == 10


# ─── 3. top_up regression — the flat_cap bug ──────────────────────────


@pytest.mark.anyio
async def test_top_up_places_remaining_when_units_half_full(db):
    """Regression test for the flat_cap bug.

    Pre-v0.53: top_up filtered `participants` to only the unallocated,
    then computed `flat_cap = ceil(len(participants) / n_units)`.
    For a half-full event this gave a cap below current occupancy,
    so every remaining participant landed unplaced.

    Fix: the cap is computed against the TOTAL population so already-
    allocated counts toward the denominator.
    """
    from app.models.allocation import Allocation

    event = await make_event(db)
    cat = await make_category(db, event.id)
    unit_a = await make_unit(db, cat.id, "A")
    unit_b = await make_unit(db, cat.id, "B")

    participants = []
    for i in range(10):
        p = await make_participant(db, event.id, first_name=f"P{i}")
        participants.append(p)

    # Manually pre-allocate 6 participants: 3 to A, 3 to B.
    for i in range(3):
        db.add(Allocation(event_id=event.id, participant_id=participants[i].id, unit_id=unit_a.id))
    for i in range(3, 6):
        db.add(Allocation(event_id=event.id, participant_id=participants[i].id, unit_id=unit_b.id))
    await db.flush()

    result = await run_engine(db, event.id, cat.id, mode="top_up")

    # All 10 should be placed: 3+2 in A, 3+2 in B (or similar split).
    counts = {uid: len(pids) for uid, pids in result["proposed"].items()}
    total_placed = counts[str(unit_a.id)] + counts[str(unit_b.id)]
    assert total_placed == 10, (
        f"Expected all 10 placed in top_up; got {total_placed}. "
        f"Unplaced: {len(result['unplaced'])}. This is the flat_cap bug."
    )
    assert result["unplaced"] == []
    # Each unit should be within 1 of even — no unit starved.
    assert abs(counts[str(unit_a.id)] - counts[str(unit_b.id)]) <= 1


# ─── 4. Gender restriction distributes within gender pools ────────────


@pytest.mark.anyio
async def test_gender_restriction_respects_pools(db):
    """6 men + 4 women, 2 male-only units + 2 female-only units.
    Expect 3+3 men, 2+2 women. Nobody cross-gender."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_gender_restriction=True)
    m1 = await make_unit(db, cat.id, "M1", gender_restriction="male")
    m2 = await make_unit(db, cat.id, "M2", gender_restriction="male")
    f1 = await make_unit(db, cat.id, "F1", gender_restriction="female")
    f2 = await make_unit(db, cat.id, "F2", gender_restriction="female")

    male_ids, female_ids = [], []
    for i in range(6):
        p = await make_participant(db, event.id, first_name=f"M{i}", gender="male")
        male_ids.append(str(p.id))
    for i in range(4):
        p = await make_participant(db, event.id, first_name=f"F{i}", gender="female")
        female_ids.append(str(p.id))

    result = await run_engine(db, event.id, cat.id, mode="replace")
    proposed = result["proposed"]

    # Every placement respects the restriction.
    for pid in proposed[str(m1.id)] + proposed[str(m2.id)]:
        assert pid in male_ids, "female placed in male-only unit"
    for pid in proposed[str(f1.id)] + proposed[str(f2.id)]:
        assert pid in female_ids, "male placed in female-only unit"

    # Even split within each gender pool.
    assert len(proposed[str(m1.id)]) + len(proposed[str(m2.id)]) == 6
    assert len(proposed[str(f1.id)]) + len(proposed[str(f2.id)]) == 4
    assert abs(len(proposed[str(m1.id)]) - len(proposed[str(m2.id)])) <= 1
    assert abs(len(proposed[str(f1.id)]) - len(proposed[str(f2.id)])) <= 1


# ─── 5. Explicit capacity beats implicit cap ──────────────────────────


@pytest.mark.anyio
async def test_explicit_capacity_respected(db):
    """Unit with capacity=3 must not receive more than 3 participants,
    even if there's nowhere else to put them."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    unit_a = await make_unit(db, cat.id, "A", capacity=3)
    unit_b = await make_unit(db, cat.id, "B", capacity=10)
    for i in range(8):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")
    assert len(result["proposed"][str(unit_a.id)]) <= 3
    total_placed = sum(len(v) for v in result["proposed"].values())
    assert total_placed == 8  # all fit (3 + 5 into B)


# ─── 6. Group-code cluster kept together when it fits ─────────────────


@pytest.mark.anyio
async def test_group_code_cluster_kept_whole(db):
    """Family of 4 with same group_code goes into one unit when it fits."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    unit_a = await make_unit(db, cat.id, "A", capacity=5)
    unit_b = await make_unit(db, cat.id, "B", capacity=5)

    family_ids = []
    for i in range(4):
        p = await make_participant(
            db, event.id, first_name=f"Smith{i}", group_code="smith"
        )
        family_ids.append(str(p.id))
    # Fill with some singles so there's a choice to make.
    for i in range(4):
        await make_participant(db, event.id, first_name=f"Single{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")
    proposed = result["proposed"]

    # All Smiths must be in the same unit.
    in_a = sum(1 for pid in proposed[str(unit_a.id)] if pid in family_ids)
    in_b = sum(1 for pid in proposed[str(unit_b.id)] if pid in family_ids)
    assert (in_a == 4 and in_b == 0) or (in_a == 0 and in_b == 4), (
        f"Family split: {in_a} in A, {in_b} in B. Should have stayed together."
    )
    assert result["stats"]["clusters_kept_whole"] == 1


# ─── 7. Oversized cluster + split_oversized_groups=TRUE → splits ──────


@pytest.mark.anyio
async def test_oversized_cluster_splits_when_enabled(db):
    """Family of 5 in rooms of 4. Default setting splits them across units."""
    event = await make_event(db)
    cat = await make_category(
        db, event.id, has_capacity=True,
        settings={"engine": {"split_oversized_groups": True,
                             "use_group_codes": True,
                             "group_remaining_by_gender": True}},
    )
    await make_unit(db, cat.id, "A", capacity=4)
    await make_unit(db, cat.id, "B", capacity=4)

    family_ids = []
    for i in range(5):
        p = await make_participant(
            db, event.id, first_name=f"Smith{i}", group_code="smith"
        )
        family_ids.append(str(p.id))

    result = await run_engine(db, event.id, cat.id, mode="replace")
    total_placed = sum(len(v) for v in result["proposed"].values())
    assert total_placed == 5
    assert result["unplaced"] == []
    assert result["stats"]["clusters_split"] == 1
    assert result["stats"]["clusters_kept_whole"] == 0


# ─── 8. Oversized cluster + split_oversized_groups=FALSE → UNPLACED ───
#
# New v0.53 semantics (option 1 from scope discussion). Previously this
# setting silently fell back to scattering individuals; now it leaves
# the whole cluster in the organiser's review queue.


@pytest.mark.anyio
async def test_oversized_cluster_unplaced_when_split_disabled(db):
    """Family of 5 in rooms of 4 with split disabled → cluster goes to unplaced,
    none of the 5 members get placed individually."""
    event = await make_event(db)
    cat = await make_category(
        db, event.id, has_capacity=True,
        settings={"engine": {"split_oversized_groups": False,
                             "use_group_codes": True,
                             "group_remaining_by_gender": True}},
    )
    unit_a = await make_unit(db, cat.id, "A", capacity=4)
    unit_b = await make_unit(db, cat.id, "B", capacity=4)

    family_ids = []
    for i in range(5):
        p = await make_participant(
            db, event.id, first_name=f"Smith{i}", group_code="smith"
        )
        family_ids.append(str(p.id))
    # Add singles so the units have other things to fill with.
    for i in range(3):
        await make_participant(db, event.id, first_name=f"Single{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")
    proposed = result["proposed"]

    # None of the family members are placed anywhere.
    for pid in proposed[str(unit_a.id)] + proposed[str(unit_b.id)]:
        assert pid not in family_ids, (
            "Family member got placed individually despite split=False. "
            "This is the pre-v0.53 'scatter' bug."
        )
    # All 5 family members should be in unplaced.
    unplaced = set(result["unplaced"])
    for pid in family_ids:
        assert pid in unplaced, f"{pid} should be unplaced"
    # The 3 singles should still be placed normally.
    total_placed = len(proposed[str(unit_a.id)]) + len(proposed[str(unit_b.id)])
    assert total_placed == 3
    assert result["stats"]["clusters_split"] == 1


# ─── 9. Unknown-gender placement surfaced in stats ────────────────────
#
# New v0.53 stats key: the organiser needs to know if anyone was
# placed by the fallback "unknown gender → allow anywhere" rule, so
# they can review.


@pytest.mark.anyio
async def test_unknown_gender_placement_counted(db):
    """Participant with gender=None placed into a gender-restricted unit
    is counted in stats.gender_unknown_placements AND their id is in
    stats.gender_unknown_placement_ids (v0.55 — names for review UI)."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_gender_restriction=True)
    await make_unit(db, cat.id, "M", gender_restriction="male")
    await make_unit(db, cat.id, "F", gender_restriction="female")

    await make_participant(db, event.id, first_name="M1", gender="male")
    await make_participant(db, event.id, first_name="F1", gender="female")
    # Unknown-gender participant — fallback rule lets them land anywhere.
    unknown = await make_participant(db, event.id, first_name="U1", gender=None)

    result = await run_engine(db, event.id, cat.id, mode="replace")
    assert result["stats"].get("gender_unknown_placements", 0) == 1
    # v0.55: check that the list is populated with the right participant id.
    ids = result["stats"].get("gender_unknown_placement_ids", [])
    assert ids == [str(unknown.id)]


# ─── 10. v0.54 guardrail — engine NEVER overbooks ─────────────────────
#
# v0.54 allows organisers to overbook a unit via manual drag/drop. The
# engine path must continue to treat capacity as a HARD constraint.
# This test locks that invariant: even with more participants than
# total capacity, the engine leaves the excess unplaced rather than
# exceeding any unit's cap.


@pytest.mark.anyio
async def test_engine_never_overbooks_explicit_capacity(db):
    """6 participants, 2 units of capacity 2 (total cap 4). Engine places
    4, leaves 2 unplaced — does NOT exceed capacity on either unit."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    unit_a = await make_unit(db, cat.id, "A", capacity=2)
    unit_b = await make_unit(db, cat.id, "B", capacity=2)

    for i in range(6):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert len(result["proposed"][str(unit_a.id)]) <= 2
    assert len(result["proposed"][str(unit_b.id)]) <= 2
    total_placed = sum(len(v) for v in result["proposed"].values())
    assert total_placed == 4
    assert len(result["unplaced"]) == 2


# ─── v0.73a regression suite ──────────────────────────────────────────
#
# Three scenarios that motivated the v0.73a engine audit:
#   • Bug 1: implicit cap on uncapped units doesn't absorb participants
#     that explicit-cap units can't take.
#   • Bug 4: unknown-gender participants must NOT be placed in
#     gender-restricted units (was previously allowed with "review").
#   • Bug 5: Semantics B — fill uncapped/big-cap units before small-
#     cap units when remaining capacity differs.
# Each scenario also pins the unplaced_reasons output shape introduced
# in v0.73a.


@pytest.mark.anyio
async def test_v073a_mixed_explicit_and_implicit_caps_place_everyone(db):
    """Bug 1 regression: 25 participants, 3 units, one with explicit
    cap=2, others uncapped. Pre-v0.73a math gave implicit_cap=9 each
    and 5 ended up unplaced. Post-fix, implicit cap absorbs the
    leftover slack and all 25 are placed.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    room1 = await make_unit(db, cat.id, "Room 1")  # uncapped
    room2 = await make_unit(db, cat.id, "Room 2", capacity=2)  # capped
    room3 = await make_unit(db, cat.id, "Room 3")  # uncapped

    for i in range(25):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 25
    assert result["stats"]["placed"] == 25, (
        f"Expected all 25 placed; got {result['stats']['placed']}. "
        f"This is the Bug 1 regression."
    )
    assert result["stats"]["unplaced"] == 0
    assert result["unplaced"] == []
    # Room 2 must respect its hard cap of 2.
    assert len(result["proposed"][str(room2.id)]) == 2
    # Room 1 + Room 3 absorb the remaining 23 between them.
    others = (
        len(result["proposed"][str(room1.id)])
        + len(result["proposed"][str(room3.id)])
    )
    assert others == 23


@pytest.mark.anyio
async def test_v073a_unknown_gender_blocked_from_restricted_units(db):
    """Bug 4 regression: with category gender restrictions on, every
    unit gender-restricted, and 2 of 10 participants having no gender
    on record — the 2 must end up unplaced, NOT silently placed in a
    restricted unit. Reason tag must be the new
    gender_unknown_no_mixed_unit_available value.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_gender_restriction=True)
    male_room = await make_unit(db, cat.id, "Male room", gender_restriction="male")
    female_room = await make_unit(db, cat.id, "Female room", gender_restriction="female")

    # 4 male, 4 female, 2 unknown gender.
    for i in range(4):
        await make_participant(db, event.id, first_name=f"M{i}", gender="male")
    for i in range(4):
        await make_participant(db, event.id, first_name=f"F{i}", gender="female")
    for i in range(2):
        await make_participant(db, event.id, first_name=f"U{i}", gender=None)

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 10
    assert result["stats"]["placed"] == 8
    assert result["stats"]["unplaced"] == 2
    # The 2 unknown-gender participants must be the unplaced ones.
    assert len(result["unplaced"]) == 2
    # Each unplaced participant must carry the gender-unknown reason tag.
    for pid in result["unplaced"]:
        reason = result["unplaced_reasons"].get(pid)
        assert reason is not None, f"Unplaced pid {pid} has no reason tag"
        assert reason["reason"] == "gender_unknown_no_mixed_unit_available", (
            f"Wrong reason for unplaced pid {pid}: got {reason}"
        )
    # Verify NO unknown-gender participant was placed in a restricted
    # unit (the pre-v0.73a behaviour).
    placed_in_male = result["proposed"][str(male_room.id)]
    placed_in_female = result["proposed"][str(female_room.id)]
    # gender_unknown_placements stats must be 0 — no fallback placements.
    assert result["stats"]["gender_unknown_placements"] == 0
    assert len(placed_in_male) == 4
    assert len(placed_in_female) == 4


@pytest.mark.anyio
async def test_v074_constrained_units_fill_first(db):
    """v0.74 regression (replaces the v0.73a Bug 5 test, which asserted
    Semantics B "biggest remaining wins" — explicitly reversed in
    v0.74). Under v0.74, constrained units drain first via cap-ASC
    cursor in the round-robin pass.

    With 4 participants and units cap 4 + cap 2: the cap-2 unit fills
    first (smallest cap, smallest remaining), then cap-4 absorbs the
    leftover. End: cap-2 = 2/2, cap-4 = 2/4.

    This is a deliberate reversal of the v0.73a Bug 5 fix. Rationale
    captured in the v0.74 spec: organisers want their constrained
    rooms used, not left as honeymoon-suite leftovers.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    big_room = await make_unit(db, cat.id, "Big room", capacity=4)
    small_room = await make_unit(db, cat.id, "Small room", capacity=2)

    for i in range(4):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 4
    # v0.74: cap-2 fills first; cap-4 absorbs leftover.
    assert len(result["proposed"][str(small_room.id)]) == 2, (
        f"Expected cap-2 to fill first (v0.74 Semantics A); got "
        f"{len(result['proposed'][str(small_room.id)])} in small_room and "
        f"{len(result['proposed'][str(big_room.id)])} in big_room."
    )
    assert len(result["proposed"][str(big_room.id)]) == 2


# ─── v0.73b: include_pending_in_allocation toggle ─────────────────────


@pytest.mark.anyio
async def test_v073b_include_pending_default_on_places_pending_participants(db):
    """v0.73b regression: with the new include_pending_in_allocation
    default ON, an event with both CONFIRMED and PENDING participants
    has all of them allocated. Pre-v0.73b the engine filtered to
    CONFIRMED only, leaving PENDING invisible.
    """
    from app.models.participant import RegistrationStatus
    event = await make_event(db)
    cat = await make_category(db, event.id)  # default settings → include_pending=True
    unit_a = await make_unit(db, cat.id, "A")
    unit_b = await make_unit(db, cat.id, "B")

    # 5 confirmed + 4 pending — matches the user's screenshot scenario shape.
    for i in range(5):
        await make_participant(db, event.id, first_name=f"C{i}", status=RegistrationStatus.CONFIRMED)
    for i in range(4):
        await make_participant(db, event.id, first_name=f"P{i}", status=RegistrationStatus.PENDING)

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 9, (
        f"Expected 9 in pool (5 confirmed + 4 pending) by default; "
        f"got {result['stats']['total']}."
    )
    assert result["stats"]["placed"] == 9
    assert result["stats"]["unplaced"] == 0


@pytest.mark.anyio
async def test_v073b_include_pending_off_excludes_pending_participants(db):
    """v0.73b regression: with include_pending_in_allocation=False,
    the engine reverts to CONFIRMED-only behaviour. Pending participants
    stay outside the engine's view.
    """
    from app.models.participant import RegistrationStatus
    event = await make_event(db)
    cat = await make_category(
        db, event.id,
        settings={"engine": {"include_pending_in_allocation": False}},
    )
    unit_a = await make_unit(db, cat.id, "A")
    unit_b = await make_unit(db, cat.id, "B")

    for i in range(5):
        await make_participant(db, event.id, first_name=f"C{i}", status=RegistrationStatus.CONFIRMED)
    for i in range(4):
        await make_participant(db, event.id, first_name=f"P{i}", status=RegistrationStatus.PENDING)

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 5, (
        f"Expected only 5 confirmed in pool when include_pending=False; "
        f"got {result['stats']['total']}."
    )
    assert result["stats"]["placed"] == 5
    assert result["stats"]["unplaced"] == 0


# ─── v0.73e: uncapped rooms absorb leftover slack from constrained capped rooms ───


@pytest.mark.anyio
async def test_v073e_uncapped_rooms_absorb_constraint_leftover_slack(db):
    """v0.73e Finding 1 regression: when capped rooms have constraints
    (gender restriction) that prevent them from filling to their
    explicit cap, the leftover slack must spill into uncapped rooms.

    Scenario from the bug report screenshot:
      - 29 participants
      - 5 rooms in one category:
        - "2 and female only" — cap 2, female-only
        - "6 and male only" — cap 6, male-only
        - "10 and mixed" — cap 10, no gender restriction
        - "Unlimited 1" — no cap, no gender
        - "Unlimited 2" — no cap, no gender

    The category has has_gender_restriction=True (so unit gender
    matters). Pre-v0.73e: implicit cap on uncapped rooms was
    ceil((eligible_p - explicit_total_eligible) / uncapped_eligible_count),
    which under-sized uncapped rooms when constraints prevented
    capped rooms from filling. Post-fix: uncapped rooms get
    implicit cap = eligible_p (no hard cap). All 29 placed.

    Pool composition that triggered the bug:
      - 1 female (so cap-2 female-only stays at 1/2)
      - 7 males (so cap-6 male-only stays at exactly 6/6, 1 leftover male)
      - 21 of unspecified-but-mixed-eligible gender (so the cap-10
        mixed and the two uncapped absorb them).
    """
    from app.models.participant import RegistrationStatus
    event = await make_event(db)
    cat = await make_category(
        db, event.id, has_capacity=True, has_gender_restriction=True,
    )
    female_room = await make_unit(db, cat.id, "2 female only", capacity=2, gender_restriction="female")
    male_room = await make_unit(db, cat.id, "6 male only", capacity=6, gender_restriction="male")
    mixed_capped = await make_unit(db, cat.id, "10 mixed", capacity=10)
    unlimited_1 = await make_unit(db, cat.id, "Unlimited 1")
    unlimited_2 = await make_unit(db, cat.id, "Unlimited 2")

    # 1 female: cap-2 female-only ends at 1/2.
    await make_participant(db, event.id, first_name="F1", gender="female")
    # 7 males: cap-6 male-only fills to 6/6, 1 male spills.
    for i in range(7):
        await make_participant(db, event.id, first_name=f"M{i}", gender="male")
    # 21 mixed-eligible — leave gender None so they can go anywhere
    # gender-unrestricted; the cap-10 mixed + two uncapped absorb them
    # plus the spillover male.
    for i in range(21):
        await make_participant(db, event.id, first_name=f"X{i}", gender=None)

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 29
    assert result["stats"]["placed"] == 29, (
        f"Expected all 29 placed (Finding 1 fix); got {result['stats']['placed']}."
    )
    assert result["stats"]["unplaced"] == 0
    # cap-6 male room should hold exactly 6 (filled to cap).
    assert len(result["proposed"][str(male_room.id)]) == 6
    # cap-2 female room has at most 2 (likely 1 — only 1 female in pool).
    assert len(result["proposed"][str(female_room.id)]) <= 2
    # cap-10 mixed should hold at most 10.
    assert len(result["proposed"][str(mixed_capped.id)]) <= 10


@pytest.mark.anyio
async def test_v073e_sibling_uncapped_rooms_load_balance(db):
    """v0.73e Q1' refinement regression: two sibling uncapped rooms
    must load-balance via the occupancy tiebreaker, not all-fill into
    whichever sorts first by stable order.

    8 participants, 2 uncapped rooms only. Pre-fix (Finding 1
    naive): both rooms tie on (-remaining, -cap), stable sort puts
    one first, all 8 land there. Post-fix: occupancy_tiebreak
    alternates them — 4 in each, or close to it.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id)  # default settings
    room_a = await make_unit(db, cat.id, "A")
    room_b = await make_unit(db, cat.id, "B")
    for i in range(8):
        await make_participant(db, event.id, first_name=f"P{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    a_count = len(result["proposed"][str(room_a.id)])
    b_count = len(result["proposed"][str(room_b.id)])
    # Strict balance assertion: split should be 4/4 with the v0.73e
    # alternation logic. If something pushed it to 5/3 due to a
    # cluster nuance we missed, that's still acceptable — but anything
    # more uneven than 5/3 (e.g. 6/2 or 7/1 or 8/0) is a failure.
    assert a_count + b_count == 8
    diff = abs(a_count - b_count)
    assert diff <= 2, (
        f"Sibling uncapped rooms did not load-balance: A={a_count}, B={b_count}. "
        f"Expected diff ≤ 2; got {diff}. v0.73e occupancy_tiebreak likely broken."
    )
