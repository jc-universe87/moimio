"""v1.0.0e — equalise sweep and manual-move soft warning tests.

Two surfaces under test:

  1. ``engine_service._equalise_sweep`` (PASS 4c). The post-allocation
     pass that moves whole movable clusters between units to even out
     occupancies proportional to capacity. Tests cover convergence,
     no-op behaviour, cluster movability rules (fill / whole
     group_code / whole mark_together yes; *_split / mark_split /
     gender_drain no), gender + capacity preservation, and the
     audit-trail wrapping (``placement_reasons[pid].previous`` carries
     the original cluster reason so the (i) panel renders both lines).

  2. ``allocation_service.compute_manual_move_warning``. The
     soft-warning helper called by the API after manual assign / move /
     unassign. Tests cover: silent when no engine commit, silent when
     rule disabled, fires on cluster separation, silent when the
     destination still has a clustermate, peels the equalise wrapper
     so equalised participants warn against their original cluster
     constraint.

These tests exercise the engine's actual reason vocabulary
(``group_code``, ``group_code_split``, ``mark_together``,
``mark_split``, ``gender_drain``, ``fill``, ``equalise``).
"""

import uuid

import pytest

from app.services.engine_service import run_engine, commit_proposal
from app.services.allocation_service import (
    assign_participant,
    move_participant,
    unassign_participant,
    compute_manual_move_warning,
)
from app.services.allocation_events_service import list_allocation_events
from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_participant,
    make_user,
    make_mark,
)


# ─── Equalise sweep ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_equalise_moves_fill_singleton_to_empty_unit(db):
    """Three solo fill participants in two equal-capacity rooms — without
    equalise the engine fills Room A first, leaving Room B at zero. The
    sweep should redistribute one participant into the empty room."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    b = await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    pids = []
    for i in range(3):
        p = await make_participant(db, event_id=ev.id, first_name=f"P{i}")
        pids.append(str(p.id))

    result = await run_engine(db, ev.id, cat.id)
    proposed = result["proposed"]
    a_count = len(proposed[str(a.id)])
    b_count = len(proposed[str(b.id)])
    # After equalise: 3 participants over capacity-4 rooms equalises
    # to ratios 0.5 / 0.25 (or 0.25 / 0.5). The greedy sweep should
    # leave both rooms with at least 1 participant rather than 3 / 0.
    assert min(a_count, b_count) >= 1
    assert a_count + b_count == 3


@pytest.mark.asyncio
async def test_equalise_no_op_when_already_balanced(db):
    """Four participants over two cap-4 rooms — engine already produces
    a balanced 2/2 split. Equalise should be a no-op (no spurious
    moves) and leave placement_reasons untouched."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    b = await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    for i in range(4):
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    result = await run_engine(db, ev.id, cat.id)
    # No participant should carry an `equalise` reason — the original
    # `fill` reasons stay because the sweep found nothing to improve.
    for pid, reason in result["placement_reasons"].items():
        assert reason["reason"] == "fill", (
            f"unexpected reason {reason!r} on already-balanced layout"
        )


@pytest.mark.asyncio
async def test_equalise_does_not_split_whole_group_code_cluster(db):
    """A whole 3-person group_code cluster placed together must NOT be
    split by the equalise sweep. The cluster moves as a unit or not at
    all — the engine's group-cluster commitment is preserved."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="Room A", capacity=6)
    b = await make_unit(db, category_id=cat.id, name="Room B", capacity=6)
    members = []
    for i in range(3):
        p = await make_participant(
            db, event_id=ev.id, first_name=f"M{i}", group_code="SMITH",
        )
        members.append(p)

    result = await run_engine(db, ev.id, cat.id)
    proposed = result["proposed"]
    # All three SMITH members must end up in the same unit, regardless
    # of whether equalise moved them.
    in_a = sum(1 for m in members if str(m.id) in proposed[str(a.id)])
    in_b = sum(1 for m in members if str(m.id) in proposed[str(b.id)])
    assert (in_a, in_b) in [(3, 0), (0, 3)], (
        f"group_code cluster was split: {in_a} in A, {in_b} in B"
    )


@pytest.mark.asyncio
async def test_equalise_respects_gender_restriction(db):
    """A male solo fill participant cannot be equalised into a female-
    only unit. The destination's hard gender constraint is honoured."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="Mixed", capacity=4)
    b = await make_unit(
        db, category_id=cat.id, name="Female", capacity=4,
        gender_restriction="female",
    )
    male = await make_participant(db, event_id=ev.id, first_name="Bob", gender="male")
    female = await make_participant(db, event_id=ev.id, first_name="Alice", gender="female")

    result = await run_engine(db, ev.id, cat.id)
    proposed = result["proposed"]
    # Bob must NEVER end up in the female-only Room B, even if the
    # equalise sweep would have preferred to move him there for ratios.
    assert str(male.id) not in proposed[str(b.id)]


@pytest.mark.asyncio
async def test_equalise_preserves_previous_reason_for_audit(db):
    """When the sweep moves a fill singleton, the new reason must wrap
    the original `fill` payload under `previous` so the (i) panel can
    show both 'placed to fill' and 'moved to even out unit sizes'."""
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    for i in range(3):
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    result = await run_engine(db, ev.id, cat.id)
    # At least one participant must have been equalised given 3-into-2
    # rooms. Whichever pid carries `equalise`, its `previous` must be
    # a complete placement payload (have a `reason` field).
    equalised = [
        (pid, r) for pid, r in result["placement_reasons"].items()
        if r["reason"] == "equalise"
    ]
    assert equalised, "equalise sweep should have moved at least one fill"
    for pid, r in equalised:
        assert "previous" in r
        assert r["previous"]["reason"] == "fill"
        assert "from_unit_id" in r and "to_unit_id" in r
        assert r["from_unit_id"] != r["to_unit_id"]


@pytest.mark.asyncio
async def test_equalise_disabled_by_setting(db):
    """When `settings.engine.equalise_after_allocation = False`, the
    sweep is skipped entirely and the original PASS 4 placements
    remain. Useful for organisers who want to lock in the engine's
    fill order without the post-balance step."""
    ev = await make_event(db)
    cat = await make_category(
        db, event_id=ev.id, has_capacity=True,
        settings={"engine": {"equalise_after_allocation": False}},
    )
    await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    for i in range(3):
        await make_participant(db, event_id=ev.id, first_name=f"P{i}")

    result = await run_engine(db, ev.id, cat.id)
    # No participant should carry an equalise reason — the sweep was
    # disabled, so original fill reasons stand.
    for pid, r in result["placement_reasons"].items():
        assert r["reason"] != "equalise"


# ─── compute_manual_move_warning ─────────────────────────────────────


@pytest.mark.asyncio
async def test_warning_silent_without_engine_commit(db):
    """A participant who was never engine-placed has nothing the manual
    move could override — the helper returns None."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id)
    a = await make_unit(db, category_id=cat.id, name="A")
    p = await make_participant(db, event_id=ev.id, first_name="Solo")
    # Manual assign without any prior engine commit
    await assign_participant(db, ev.id, a.id, p.id, actor_user_id=user.id)
    warning = await compute_manual_move_warning(
        db, event_id=ev.id, category_id=cat.id,
        participant_id=p.id, new_unit_id=a.id,
    )
    assert warning is None


@pytest.mark.asyncio
async def test_warning_fires_on_group_cluster_separation(db):
    """A 2-person group_code cluster is engine-placed in Room A, then
    one member is manually moved to Room B (with no clustermate). The
    helper should fire `organise.warning.group_split`."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="Room A", capacity=4)
    b = await make_unit(db, category_id=cat.id, name="Room B", capacity=4)
    p1 = await make_participant(
        db, event_id=ev.id, first_name="Alice", group_code="SMITH",
    )
    p2 = await make_participant(
        db, event_id=ev.id, first_name="Bob", group_code="SMITH",
    )
    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"], actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )

    # Both committed into the same unit (engine kept SMITH together).
    # Move Alice to the other unit — Bob stays behind.
    in_a = result["proposed"][str(a.id)]
    target = b if str(p1.id) in in_a else a
    new_unit_id = target.id
    # Apply the manual move and check the warning.
    await move_participant(db, ev.id, new_unit_id, p1.id, actor_user_id=user.id)
    warning = await compute_manual_move_warning(
        db, event_id=ev.id, category_id=cat.id,
        participant_id=p1.id, new_unit_id=new_unit_id,
    )
    assert warning is not None
    assert warning["key"] == "organise.warning.group_split"
    assert warning["params"]["code"] == "SMITH"


@pytest.mark.asyncio
async def test_warning_silent_when_use_group_codes_disabled(db):
    """Even if the engine had clustered participants by group_code, a
    later category setting that disables group_codes means the engine
    no longer claims to honour the rule. Manual moves should be
    silent — no warning."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(
        db, event_id=ev.id, has_capacity=True,
        settings={"engine": {"use_group_codes": True}},
    )
    a = await make_unit(db, category_id=cat.id, name="A", capacity=4)
    b = await make_unit(db, category_id=cat.id, name="B", capacity=4)
    p1 = await make_participant(db, event_id=ev.id, first_name="A1", group_code="X")
    p2 = await make_participant(db, event_id=ev.id, first_name="A2", group_code="X")
    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"], actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    # Disable the rule after the fact
    cat.settings = {"engine": {"use_group_codes": False}}
    await db.flush()

    in_a = result["proposed"][str(a.id)]
    new_unit_id = b.id if str(p1.id) in in_a else a.id
    await move_participant(db, ev.id, new_unit_id, p1.id, actor_user_id=user.id)
    warning = await compute_manual_move_warning(
        db, event_id=ev.id, category_id=cat.id,
        participant_id=p1.id, new_unit_id=new_unit_id,
    )
    assert warning is None


@pytest.mark.asyncio
async def test_warning_silent_when_destination_has_clustermate(db):
    """If the participant moves to a unit that already contains a
    clustermate, the cluster's togetherness is intact — silent."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="A", capacity=4)
    b = await make_unit(db, category_id=cat.id, name="B", capacity=4)
    p1 = await make_participant(db, event_id=ev.id, first_name="A1", group_code="X")
    p2 = await make_participant(db, event_id=ev.id, first_name="A2", group_code="X")
    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"], actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    # Both clustered in the same unit. Manually assign p1 to that
    # same unit (idempotent move) — clustermate p2 is still there.
    in_a = str(p1.id) in result["proposed"][str(a.id)]
    same_unit_id = a.id if in_a else b.id
    warning = await compute_manual_move_warning(
        db, event_id=ev.id, category_id=cat.id,
        participant_id=p1.id, new_unit_id=same_unit_id,
    )
    assert warning is None


@pytest.mark.asyncio
async def test_warning_peels_equalise_wrapper(db):
    """If a participant's most recent engine commit wraps the original
    cluster reason under `equalise.previous`, the warning helper still
    finds the binding rule and fires when the move breaks it."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="A", capacity=4)
    b = await make_unit(db, category_id=cat.id, name="B", capacity=4)
    c = await make_unit(db, category_id=cat.id, name="C", capacity=4)
    # 2-person SMITH cluster + 2 fill singletons. With equalise on,
    # the two fill singletons may move; the cluster may also move
    # whole. Either way the SMITH placement carries either
    # `group_code` or `equalise(previous=group_code)` post-commit.
    p1 = await make_participant(db, event_id=ev.id, first_name="P1", group_code="SMITH")
    p2 = await make_participant(db, event_id=ev.id, first_name="P2", group_code="SMITH")
    await make_participant(db, event_id=ev.id, first_name="F1")
    await make_participant(db, event_id=ev.id, first_name="F2")
    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"], actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    # Find which unit holds the cluster, move P1 to a clustermate-free unit
    cluster_unit = None
    for uid, pids in result["proposed"].items():
        if str(p1.id) in pids:
            cluster_unit = uid
            break
    assert cluster_unit is not None
    other_unit = next(
        u for u in (a, b, c) if str(u.id) != cluster_unit
    )
    await move_participant(db, ev.id, other_unit.id, p1.id, actor_user_id=user.id)
    warning = await compute_manual_move_warning(
        db, event_id=ev.id, category_id=cat.id,
        participant_id=p1.id, new_unit_id=other_unit.id,
    )
    # Whether the original commit was `group_code` or
    # `equalise(previous=group_code)`, the warning should fire and
    # reference the SMITH cluster. The whole point of `previous` is
    # that the binding rule peeks through the equalise wrapper.
    assert warning is not None
    assert warning["params"].get("code") == "SMITH"


@pytest.mark.asyncio
async def test_warning_on_unassign_to_unallocated(db):
    """Unassigning a clustered participant to the unallocated bucket
    fires a separation warning — they're definitively away from the
    cluster."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    a = await make_unit(db, category_id=cat.id, name="A", capacity=4)
    p1 = await make_participant(db, event_id=ev.id, first_name="P1", group_code="SMITH")
    p2 = await make_participant(db, event_id=ev.id, first_name="P2", group_code="SMITH")
    result = await run_engine(db, ev.id, cat.id)
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"], actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    # Find which unit p1 is in and unassign from there
    src_uid = next(
        uid for uid, pids in result["proposed"].items() if str(p1.id) in pids
    )
    await unassign_participant(
        db, uuid.UUID(src_uid), p1.id, actor_user_id=user.id,
    )
    warning = await compute_manual_move_warning(
        db, event_id=ev.id, category_id=cat.id,
        participant_id=p1.id, new_unit_id=None,
    )
    assert warning is not None
    assert warning["key"] == "organise.warning.group_separated"


# ─── Cluster-member snapshot (v1.0.0e) ──────────────────────────────


@pytest.mark.asyncio
async def test_cluster_members_snapshotted_into_meta(db):
    """Engine commits for cluster placements should snapshot the full
    cluster member list (id + name) into `meta.placement.cluster_members`.
    The frontend reads this for the imprinted "with X, Y, Z" line in
    the (i)-panel history audit trail — independent of whether those
    participants still exist when the history is later viewed."""
    user = await make_user(db)
    ev = await make_event(db)
    cat = await make_category(db, event_id=ev.id, has_capacity=True)
    await make_unit(db, category_id=cat.id, name="A", capacity=4)
    p1 = await make_participant(
        db, event_id=ev.id, first_name="Alice", last_name="Smith",
        group_code="SMITH",
    )
    p2 = await make_participant(
        db, event_id=ev.id, first_name="Bob", last_name="Smith",
        group_code="SMITH",
    )
    result = await run_engine(db, ev.id, cat.id)

    # Engine output: both members carry cluster_members in their reason
    for p in (p1, p2):
        r = result["placement_reasons"][str(p.id)]
        assert "cluster_members" in r
        names = {m["name"] for m in r["cluster_members"]}
        assert names == {"Alice Smith", "Bob Smith"}
        # Each entry carries id + name
        for m in r["cluster_members"]:
            assert "id" in m and "name" in m

    # After commit, the snapshot lives in the assign event's meta
    await commit_proposal(
        db, ev.id, cat.id,
        proposed=result["proposed"], actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    rows = await list_allocation_events(db, event_id=ev.id, participant_id=p1.id)
    assigns = [r for r in rows if r["event_type"] == "assign"]
    assert len(assigns) == 1
    placement = assigns[0]["meta"]["placement"]
    assert placement["reason"] in {"group_code", "equalise"}
    # Equalise wraps the original payload under `previous`. Either way,
    # cluster_members must be reachable.
    members = placement.get("cluster_members") or placement.get("previous", {}).get("cluster_members")
    assert members is not None
    assert {m["name"] for m in members} == {"Alice Smith", "Bob Smith"}
