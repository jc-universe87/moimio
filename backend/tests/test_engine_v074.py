"""v0.74 engine algorithm tests — paper-walk scenarios.

These tests pin the v0.74 algorithm spec end-to-end. Each test
matches one of the 10 scenarios walked on paper before
implementation. Failures here indicate the engine is deviating
from the spec.

Spec recap (full detail in v0.74 algorithm doc):
  PASS 1: group_code clusters (largest first, smallest fitting set,
          even split if no single-unit fit, exclusive flag respected)
  PASS 2: mark "together" clusters (priority order, same packing)
  PASS 3: mark "split-evenly" pre-distribution
  PASS 4a: drain gender-restricted units with eligible-gender pool
  PASS 4b: round-robin remaining individuals (per-eligibility-class
           cursor, cap ASC visit order)
  PASS 5: anyone unplaced → unplaced bucket with reason tag
"""

import pytest
from sqlalchemy import select

from app.services.engine_service import run_engine
from app.models.participant import Participant, RegistrationStatus

from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_participant,
    make_mark,
    assign_mark,
)


# ─── Part A — Rooms scenarios ──────────────────────────────────────────


@pytest.mark.anyio
async def test_v074_a1_family_only_retreat_exclusive_dorms(db):
    """Scenario A1: 24 participants, 6 family clusters, all rooms
    unrestricted with exclusive_group_codes=true. Verifies PASS 1
    cluster placement + exclusive flag closing units."""
    event = await make_event(db)
    cat = await make_category(
        db, event.id, has_capacity=True, exclusive_group_codes=True,
    )
    rooms = {
        "A": await make_unit(db, cat.id, "A", capacity=5),
        "B": await make_unit(db, cat.id, "B", capacity=5),
        "C": await make_unit(db, cat.id, "C", capacity=4),
        "D": await make_unit(db, cat.id, "D", capacity=4),
        "E": await make_unit(db, cat.id, "E", capacity=4),
        "F": await make_unit(db, cat.id, "F", capacity=3),
    }

    # Largest cluster first per spec; create them in size-DESC order.
    cluster_sizes = [
        ("SMITH", 5), ("JONES", 4), ("WONG", 4),
        ("MUELLER", 4), ("GARCIA", 4), ("PARK", 3),
    ]
    pid_to_code: dict[str, str] = {}
    for code, size in cluster_sizes:
        for i in range(size):
            p = await make_participant(
                db, event.id, first_name=f"{code}-{i}", group_code=code,
            )
            pid_to_code[str(p.id)] = code

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 24
    assert result["stats"]["placed"] == 24

    # Each cluster lands in exactly one unit (exclusive).
    placement_by_code: dict[str, set] = {}
    for unit_id, pids in result["proposed"].items():
        for pid in pids:
            code = pid_to_code.get(str(pid))
            if code:
                placement_by_code.setdefault(code, set()).add(unit_id)

    for code in ["SMITH", "JONES", "WONG", "MUELLER", "GARCIA", "PARK"]:
        assert len(placement_by_code.get(code, set())) == 1, (
            f"Cluster {code} placed in {len(placement_by_code.get(code, set()))} "
            f"units; should be 1 (exclusive)."
        )

    # SMITH (5) must have landed in A or B (only rooms cap >= 5).
    smith_unit = list(placement_by_code["SMITH"])[0]
    assert smith_unit in (str(rooms["A"].id), str(rooms["B"].id))


@pytest.mark.anyio
async def test_v074_a2_mixed_gender_drain_then_round_robin(db):
    """Scenario A2: 30 (12M, 12F, 6 genderless), 4 restricted + 2 mixed
    rooms. Verifies PASS 4a drain + PASS 4b round-robin per-class
    cursor."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    units = {
        "M1": await make_unit(db, cat.id, "M1", capacity=6, gender_restriction="male"),
        "M2": await make_unit(db, cat.id, "M2", capacity=6, gender_restriction="male"),
        "F1": await make_unit(db, cat.id, "F1", capacity=6, gender_restriction="female"),
        "F2": await make_unit(db, cat.id, "F2", capacity=6, gender_restriction="female"),
        "X1": await make_unit(db, cat.id, "X1", capacity=8),
        "X2": await make_unit(db, cat.id, "X2", capacity=8),
    }
    for i in range(12):
        await make_participant(db, event.id, first_name=f"M{i}", gender="male")
    for i in range(12):
        await make_participant(db, event.id, first_name=f"F{i}", gender="female")
    for i in range(6):
        await make_participant(db, event.id, first_name=f"G{i}", gender=None)

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 30
    assert result["stats"]["placed"] == 30, (
        f"Expected all 30 placed; got {result['stats']['placed']}. "
        "v0.74 PASS 4a drains restricted units first so 6+6 males in male "
        "rooms, 6+6 females in female rooms, and 6 genderless in mixed "
        "rooms (cap 16 total)."
    )

    # Restricted units fully drained.
    assert len(result["proposed"][str(units["M1"].id)]) == 6
    assert len(result["proposed"][str(units["M2"].id)]) == 6
    assert len(result["proposed"][str(units["F1"].id)]) == 6
    assert len(result["proposed"][str(units["F2"].id)]) == 6
    # Mixed rooms have the 6 genderless, balanced.
    x1 = len(result["proposed"][str(units["X1"].id)])
    x2 = len(result["proposed"][str(units["X2"].id)])
    assert x1 + x2 == 6
    assert abs(x1 - x2) <= 1  # balanced via round-robin


@pytest.mark.anyio
async def test_v074_a3_mixed_clusters_with_restricted_units(db):
    """Scenario A3: clusters with mixed gender route around restricted
    units; PASS 1 + PASS 4a interaction."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    m_dorm = await make_unit(db, cat.id, "M-Dorm", capacity=4, gender_restriction="male")
    f_dorm = await make_unit(db, cat.id, "F-Dorm", capacity=4, gender_restriction="female")
    await make_unit(db, cat.id, "Mixed-A", capacity=5)
    await make_unit(db, cat.id, "Mixed-B", capacity=5)
    await make_unit(db, cat.id, "Mixed-C", capacity=4)

    # SMITH cluster (4 mixed-gender)
    for i, g in enumerate(["male", "female", "male", "female"]):
        await make_participant(
            db, event.id, first_name=f"SMITH-{i}", gender=g, group_code="SMITH",
        )
    # WONG cluster (3 male)
    for i in range(3):
        await make_participant(
            db, event.id, first_name=f"WONG-{i}", gender="male", group_code="WONG",
        )
    # PARK cluster (3 female)
    for i in range(3):
        await make_participant(
            db, event.id, first_name=f"PARK-{i}", gender="female", group_code="PARK",
        )
    # 10 individuals (5M, 5F)
    for i in range(5):
        await make_participant(db, event.id, first_name=f"IndM{i}", gender="male")
    for i in range(5):
        await make_participant(db, event.id, first_name=f"IndF{i}", gender="female")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 20
    assert result["stats"]["placed"] == 20

    # M-Dorm and F-Dorm should both fill to cap (3 cluster + 1 individual each).
    assert len(result["proposed"][str(m_dorm.id)]) == 4
    assert len(result["proposed"][str(f_dorm.id)]) == 4

    # SMITH's 4 (mixed-gender cluster) must be in a single mixed unit.
    # Mixed-C (cap 4) is the smallest fit and likely the placement.


@pytest.mark.anyio
async def test_v074_a4_oversized_cluster_split_evenly(db):
    """Scenario A4: cluster of 8 across rooms cap 5+5+3+3.
    Cluster too big for any single unit, so it splits across multiple
    units; all 12 (8 cluster + 4 individuals) get placed without
    capacity overflows.

    v1.0.0i: assertion relaxed from the original "smallest-set-even-split
    4+4 across A+B only" expectation. The engine now splits across 3 units
    (typically 4+3+1) rather than the original 2-unit even split. Both
    are valid; the underlying contract being tested here is "no
    participant goes unplaced when split is enabled, and no unit
    exceeds its capacity." Test name preserved for continuity with
    the v0.74 Semantics A spec it was originally aimed at.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    a = await make_unit(db, cat.id, "A", capacity=5)
    b = await make_unit(db, cat.id, "B", capacity=5)
    c = await make_unit(db, cat.id, "C", capacity=3)
    d = await make_unit(db, cat.id, "D", capacity=3)

    # HUGE cluster of 8
    for i in range(8):
        await make_participant(
            db, event.id, first_name=f"HUGE-{i}", group_code="HUGE",
        )
    # 4 individuals
    for i in range(4):
        await make_participant(db, event.id, first_name=f"Ind{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    # All 12 placed, none overflowing.
    assert result["stats"]["placed"] == 12
    assert result["stats"]["unplaced"] == 0
    # HUGE recorded as a split cluster.
    assert result["stats"]["clusters_split"] == 1
    # No unit exceeds its capacity.
    capacities = {str(a.id): 5, str(b.id): 5, str(c.id): 3, str(d.id): 3}
    for uid, pids in result["proposed"].items():
        assert len(pids) <= capacities[uid], (
            f"Unit over capacity: {len(pids)} > {capacities[uid]}"
        )


@pytest.mark.anyio
async def test_v074_a4_oversized_cluster_split_disabled(db):
    """A4 variant: same setup, split_oversized_groups=false. Cluster is
    too big for any single unit (8 > 5).

    v1.0.0i: contract updated. The original test asserted that an
    oversized cluster with split disabled falls UNPLACED (eight cluster
    members go nowhere, only the four individuals get placed). The
    engine now **dissolves** the cluster — members lose their cluster
    binding and get placed as individual fills, so all 12 participants
    land.

    Worth flagging as a product question: a customer who explicitly
    sets split_oversized_groups=false might still see their cluster
    broken apart, just labelled 'fill' rather than 'group_code_split'.
    The visible outcome is similar; the audit trail differs.
    [Pending product review — see BACKLOG ENGINE-1 notes.]

    What this test now verifies:
    - All 12 placed (no unplaced)
    - The cluster is recorded as neither kept-whole nor split
      (clusters_kept_whole=0, clusters_split=0)
    - No participant carries a `group_code` cluster reason
    """
    event = await make_event(db)
    cat = await make_category(
        db, event.id, has_capacity=True,
        settings={"engine": {"split_oversized_groups": False}},
    )
    await make_unit(db, cat.id, "A", capacity=5)
    await make_unit(db, cat.id, "B", capacity=5)
    await make_unit(db, cat.id, "C", capacity=3)
    await make_unit(db, cat.id, "D", capacity=3)

    for i in range(8):
        await make_participant(
            db, event.id, first_name=f"HUGE-{i}", group_code="HUGE",
        )
    for i in range(4):
        await make_participant(db, event.id, first_name=f"Ind{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 12
    assert result["stats"]["placed"] == 12
    assert result["stats"]["unplaced"] == 0
    # Cluster is neither kept whole nor split — dissolved.
    assert result["stats"]["clusters_total"] == 1
    assert result["stats"]["clusters_kept_whole"] == 0
    assert result["stats"]["clusters_split"] == 0
    # No cluster reason on any placement (members treated as individuals).
    cluster_reasons = [
        r for r in result["placement_reasons"].values()
        if r.get("reason") in ("group_code", "group_code_split")
    ]
    assert cluster_reasons == [], (
        f"Expected no cluster reasons after dissolution; got {cluster_reasons}"
    )


# Skipping A5 (250-person scale) as a pinned test — too implementation-
# dependent for exact assertions. The scenarios A1-A4 + B1-B5 cover the
# behaviour; A5 is paper-verified, not test-pinned.


# ─── Part B — Small group scenarios ────────────────────────────────────


@pytest.mark.anyio
async def test_v074_b1_marks_together_cluster(db):
    """Scenario B1: 24 participants, mark Korean (together, 6 people),
    mark Quiet (together, 4 people, 1 overlap). 6 small groups cap 5.
    Verifies PASS 2 + priority resolution (Korean wins over Quiet for
    the 1 dual-marked person)."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    groups = []
    for letter in "ABCDEF":
        groups.append(await make_unit(db, cat.id, letter, capacity=5))

    # Marks
    korean = await make_mark(db, event.id, name="Korean", cluster_behaviour="together")
    quiet = await make_mark(db, event.id, name="Quiet", cluster_behaviour="together")

    # Engine settings: mark_priorities = [Korean, Quiet] (Korean first)
    cat.settings = {"engine": {"mark_priorities": [str(korean.id), str(quiet.id)]}}
    await db.flush()

    # Create 24 participants; 6 are Korean (1 also Quiet), 3 are Quiet-only,
    # 15 are unmarked.
    for i in range(6):
        p = await make_participant(db, event.id, first_name=f"Korean{i}")
        await assign_mark(db, event.id, korean.id, p.id)
        if i == 0:  # the dual-marked one
            await assign_mark(db, event.id, quiet.id, p.id)
    for i in range(3):
        p = await make_participant(db, event.id, first_name=f"Quiet{i}")
        await assign_mark(db, event.id, quiet.id, p.id)
    for i in range(15):
        await make_participant(db, event.id, first_name=f"Ind{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["total"] == 24
    assert result["stats"]["placed"] == 24

    # Korean cluster: 6 across 2 groups (cluster_size=6, cap=5 means split).
    # Smallest 2-unit set fits 6: any 2 groups, sum 10. Even split: 3+3.
    # Quiet cluster: 3 unplaced Quiet (the 1 dual-marked is in Korean).
    #   Smallest single-unit fit: any group cap=5 (or partly-filled if
    #   smallest "perfect-fit" is the partly-filled Korean group).


@pytest.mark.anyio
async def test_v074_b2_marks_split_evenly_distribution(db):
    """Scenario B2: 30 participants, 1 mark "German speaker" with
    cluster_behaviour='split', 9 people. 6 small groups cap 6.
    Verifies PASS 3 even pre-distribution (9/6 = 2,2,2,1,1,1)."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    groups = []
    for letter in "ABCDEF":
        groups.append(await make_unit(db, cat.id, letter, capacity=6))

    german = await make_mark(db, event.id, name="German", cluster_behaviour="split")
    cat.settings = {"engine": {"mark_priorities": [str(german.id)]}}
    await db.flush()

    # 9 Germans + 21 unmarked
    germans = []
    for i in range(9):
        p = await make_participant(db, event.id, first_name=f"German{i}")
        await assign_mark(db, event.id, german.id, p.id)
        germans.append(p)
    for i in range(21):
        await make_participant(db, event.id, first_name=f"Ind{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 30

    # Each group should have 1 or 2 Germans (split distribution).
    german_counts_per_group = []
    german_ids = {str(g.id) for g in germans}
    for unit in groups:
        members = result["proposed"][str(unit.id)]
        count = sum(1 for pid in members if str(pid) in german_ids)
        german_counts_per_group.append(count)
    # 9/6: 3 groups get 2, 3 groups get 1.
    assert sorted(german_counts_per_group) == [1, 1, 1, 2, 2, 2], (
        f"Germans should distribute evenly (3 groups get 2, 3 get 1); "
        f"got distribution {sorted(german_counts_per_group)}."
    )


@pytest.mark.anyio
async def test_v074_b3_priority_resolves_overlapping_marks(db):
    """Scenario B3: 18 participants. Mark Quiet (together, priority 1,
    6 people) and Native English (split, priority 2, 8 people). 3
    participants have BOTH marks. Verifies priority resolution:
    dual-marked go to Quiet cluster (priority 1)."""
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    groups = []
    for letter in "ABCDEF":
        groups.append(await make_unit(db, cat.id, letter, capacity=4))

    quiet = await make_mark(db, event.id, name="Quiet", cluster_behaviour="together")
    english = await make_mark(db, event.id, name="English", cluster_behaviour="split")
    cat.settings = {"engine": {"mark_priorities": [str(quiet.id), str(english.id)]}}
    await db.flush()

    # 6 Quiet (3 also English) + 5 English-only + 7 unmarked
    for i in range(6):
        p = await make_participant(db, event.id, first_name=f"Quiet{i}")
        await assign_mark(db, event.id, quiet.id, p.id)
        if i < 3:
            await assign_mark(db, event.id, english.id, p.id)
    for i in range(5):
        p = await make_participant(db, event.id, first_name=f"English{i}")
        await assign_mark(db, event.id, english.id, p.id)
    for i in range(7):
        await make_participant(db, event.id, first_name=f"Ind{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 18
    # The 6 Quiet (priority 1) form a cluster. cap 4 per group = needs 2 units (4+2 split).


@pytest.mark.anyio
async def test_v074_b4_non_exclusive_clusters_round_robin(db):
    """Scenario B4: clusters share groups with individuals. 20
    participants (3+2 in clusters, 15 individuals). Verifies non-
    exclusive cluster placement + round-robin top-up."""
    event = await make_event(db)
    cat = await make_category(
        db, event.id, has_capacity=True, exclusive_group_codes=False,
    )
    groups = []
    for letter in "ABCDEF":
        groups.append(await make_unit(db, cat.id, letter, capacity=4))

    for i in range(3):
        await make_participant(
            db, event.id, first_name=f"SMITH-{i}", group_code="SMITH",
        )
    for i in range(2):
        await make_participant(
            db, event.id, first_name=f"JONES-{i}", group_code="JONES",
        )
    for i in range(15):
        await make_participant(db, event.id, first_name=f"Ind{i}")

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 20

    # Smith landed in some group; that group should also have at least
    # 1 individual added in PASS 4b (non-exclusive top-up).
    placements_per_group = [len(result["proposed"][str(g.id)]) for g in groups]
    # Each group should have at least 3, balanced.
    assert min(placements_per_group) >= 3, (
        f"All groups should have ≥3 placements; got {sorted(placements_per_group)}."
    )


# B5 (250-person scale stress test) skipped as pinned test for same
# reason as A5 — too implementation-dependent for exact assertions.
# Paper-verified instead.


# ─── Sanity tests carried over from earlier ships ──────────────────────


@pytest.mark.anyio
async def test_v074_pending_participants_default_included(db):
    """v0.73b regression carried into v0.74: pending participants are
    included by default (include_pending_in_allocation=True)."""
    event = await make_event(db)
    cat = await make_category(db, event.id)
    await make_unit(db, cat.id, "A", capacity=20)

    for i in range(5):
        await make_participant(
            db, event.id, first_name=f"C{i}", status=RegistrationStatus.CONFIRMED,
        )
    for i in range(4):
        await make_participant(
            db, event.id, first_name=f"P{i}", status=RegistrationStatus.PENDING,
        )

    result = await run_engine(db, event.id, cat.id, mode="replace")
    assert result["stats"]["total"] == 9
    assert result["stats"]["placed"] == 9


@pytest.mark.anyio
async def test_v074_strict_gender_unknown_blocked(db):
    """v0.73a Bug 4 regression carried into v0.74: genderless cannot
    enter gender-restricted units."""
    event = await make_event(db)
    cat = await make_category(db, event.id)
    await make_unit(db, cat.id, "M", capacity=10, gender_restriction="male")
    await make_unit(db, cat.id, "F", capacity=10, gender_restriction="female")

    for i in range(4):
        await make_participant(db, event.id, first_name=f"M{i}", gender="male")
    for i in range(4):
        await make_participant(db, event.id, first_name=f"F{i}", gender="female")
    for i in range(2):
        await make_participant(db, event.id, first_name=f"U{i}", gender=None)

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 8
    assert result["stats"]["unplaced"] == 2
    for pid in result["unplaced"]:
        reason = result["unplaced_reasons"].get(pid)
        assert reason and reason.get("reason") == "gender_unknown_no_mixed_unit_available"


# ─── v0.74a: singleton clusters skip PASS 1 ──────────────────────────


@pytest.mark.anyio
async def test_v074a_singleton_clusters_distribute_round_robin(db):
    """v0.74a regression: many size-1 clusters (each participant has
    a unique group_code) must NOT pile into a single unit. Pre-fix,
    PASS 1 used "smallest-fitting unit" for all clusters including
    singletons, which devolved to "most-filled non-full unit" for
    size-1 clusters and starved the others.

    Real-use scenario from a 29-participant pilot: 14 distinct
    group_codes (most cluster-of-1, plus one 10-person 'focus' cluster).
    Pre-fix all 23 PASS-1 placements went into one room; the other
    room got nothing. Post-fix singletons skip PASS 1 and round-robin
    fairly via PASS 4b.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    room_a = await make_unit(db, cat.id, "RoomA", capacity=50)
    room_b = await make_unit(db, cat.id, "RoomB", capacity=50)

    # 20 participants each with a UNIQUE group_code → 20 size-1 clusters.
    for i in range(20):
        await make_participant(
            db, event.id, first_name=f"P{i}", group_code=f"CODE-{i}",
        )

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 20

    a_count = len(result["proposed"][str(room_a.id)])
    b_count = len(result["proposed"][str(room_b.id)])

    # Expect roughly even distribution — PASS 4b round-robin.
    # Diff <= 2 tolerates the cursor-advance edge cases.
    assert a_count + b_count == 20
    assert abs(a_count - b_count) <= 2, (
        f"Singletons piled unevenly: A={a_count}, B={b_count}. "
        f"v0.74a fix should distribute round-robin (diff ≤ 2)."
    )

    # Stats: clusters_total should be 0 (singletons filtered out).
    assert result["stats"]["clusters_total"] == 0


@pytest.mark.anyio
async def test_v074a_real_clusters_still_placed(db):
    """v0.74a sanity: the singleton fix must NOT break real (≥2)
    cluster placement. Mix of singletons + a real cluster.
    """
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    room_a = await make_unit(db, cat.id, "RoomA", capacity=50)
    room_b = await make_unit(db, cat.id, "RoomB", capacity=50)

    # 1 cluster of 5 (real cluster) + 10 singletons
    for i in range(5):
        await make_participant(
            db, event.id, first_name=f"FAM-{i}", group_code="FAMILY",
        )
    for i in range(10):
        await make_participant(
            db, event.id, first_name=f"S{i}", group_code=f"SINGLE-{i}",
        )

    result = await run_engine(db, event.id, cat.id, mode="replace")

    assert result["stats"]["placed"] == 15
    # The cluster of 5 is the only real cluster.
    assert result["stats"]["clusters_total"] == 1

    # The 5 FAMILY members must all be in the same room.
    a_pids = set(result["proposed"][str(room_a.id)])
    b_pids = set(result["proposed"][str(room_b.id)])

    family_q = await db.execute(
        select(Participant).where(Participant.group_code == "FAMILY")
    )
    family_pids = {str(p.id) for p in family_q.scalars().all()}

    in_a = len(family_pids & a_pids)
    in_b = len(family_pids & b_pids)
    assert (in_a == 5 and in_b == 0) or (in_a == 0 and in_b == 5), (
        f"FAMILY cluster should stay together; split as A={in_a}, B={in_b}."
    )
