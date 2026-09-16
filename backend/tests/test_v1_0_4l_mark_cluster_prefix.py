"""v1.0.4l — the engine's "mark:" cluster_id prefix and its consumers.

The engine writes a mark cluster's id as ``mark:<uuid>``
(``engine_service._place_cluster`` is called with
``cluster_id=f"mark:{prio_mid}"``). That prefixed string is persisted
in ``allocation_event.meta.placement`` and read back later by
``allocation_service.compute_manual_move_warning``.

Three consumer sites treated it as a bare UUID:

  * the per-category override lookup in ``_mark_behaviour_for`` — keyed
    on the bare id, so the prefixed value never matched and a
    per-category behaviour override was silently ignored;
  * the ``MarkDefinition`` parse in the same function — ``uuid.UUID``
    on ``"mark:<uuid>"`` raises ``ValueError``;
  * the ``MarkAssignment`` parse in ``compute_manual_move_warning``.

The ValueError escaped through a write endpoint: assign, move and
unassign all call ``compute_manual_move_warning`` after a successful
write, so a manual unassign of an engine-placed mark cluster member
returned 500 even though the unassign itself had committed.

The prefix is deliberately left on the write side — it is part of
audit rows already in deployed databases — so each consumer peels it
with ``_mark_id_from_cluster`` at its own use site.
"""

import uuid

import pytest

from app.services.engine_service import run_engine, commit_proposal
from app.services.allocation_service import (
    unassign_participant,
    compute_manual_move_warning,
    _mark_id_from_cluster,
)

from tests.conftest import (
    make_event,
    make_category,
    make_unit,
    make_participant,
    make_user,
    make_mark,
    assign_mark,
)


async def _split_mark_cluster(db, *, global_behaviour, priorities_factory):
    """Engine-place five holders of one keep-together mark across two
    rooms of three, then commit. Returns (user, event, category, rooms,
    holders, engine result).

    Five into 3 + 3 cannot fit in a single unit, so ``_place_cluster``
    takes the multi-unit combo branch and every member is committed
    with reason ``mark_together_split``.
    """
    user = await make_user(db, email=f"a-{uuid.uuid4().hex[:8]}@test.local")
    event = await make_event(db)
    cat = await make_category(db, event.id, has_capacity=True)
    rooms = [await make_unit(db, cat.id, n, capacity=3) for n in ("A", "B")]

    mark = await make_mark(
        db, event.id, name="Choir", cluster_behaviour=global_behaviour,
    )
    cat.settings = {"engine": {
        "use_group_codes": False,
        "equalise_after_allocation": False,
        "mark_priorities": priorities_factory(str(mark.id)),
    }}
    await db.flush()

    holders = []
    for i in range(5):
        p = await make_participant(db, event.id, first_name=f"H{i}")
        await assign_mark(db, event.id, mark.id, p.id)
        holders.append(p)
    await db.flush()

    result = await run_engine(db, event.id, cat.id, mode="replace")
    await commit_proposal(
        db, event.id, cat.id, result["proposed"],
        actor_user_id=user.id,
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    return user, event, cat, mark, rooms, holders, result


def _unit_of(result, rooms, participant):
    for u in rooms:
        if str(participant.id) in result["proposed"][str(u.id)]:
            return u
    return None


# ─── The crash: mark_together_split, then a manual unassign ──────────


@pytest.mark.asyncio
async def test_unassign_after_mark_together_split_warns_instead_of_raising(db):
    """The regression. Before the fix this raised

        ValueError: badly formed hexadecimal UUID string

    out of ``_mark_behaviour_for`` — a 500 from DELETE
    /allocations/unassign after the row had already been deleted.
    """
    user, event, cat, mark, rooms, holders, result = await _split_mark_cluster(
        db, global_behaviour="together", priorities_factory=lambda mid: [mid],
    )

    # The engine really did split the cluster and really did prefix the
    # cluster_id. If either stops being true this test is no longer
    # testing what it claims to.
    victim = holders[0]
    placement = result["placement_reasons"][str(victim.id)]
    assert placement["reason"] == "mark_together_split"
    assert placement["cluster_id"] == f"mark:{mark.id}"

    room = _unit_of(result, rooms, victim)
    assert room is not None
    await unassign_participant(db, room.id, victim.id, actor_user_id=user.id)

    warning = await compute_manual_move_warning(
        db, event_id=event.id, category_id=cat.id,
        participant_id=victim.id, new_unit_id=None,
    )
    assert warning is not None
    assert warning["key"] == "organise.warning.mark_separated"
    assert warning["params"]["name"].startswith("H0")


# ─── The silently ignored per-category behaviour override ───────────


@pytest.mark.asyncio
async def test_category_override_together_is_honoured(db):
    """Global definition says "none"; the category override says
    "together". The override is what the engine clustered on, so the
    warning must fire. Matching on the prefixed id failed, so this
    fell back to the global "none" and stayed silent.
    """
    user, event, cat, mark, rooms, holders, result = await _split_mark_cluster(
        db, global_behaviour="none",
        priorities_factory=lambda mid: [{"id": mid, "behaviour": "together"}],
    )
    victim = holders[0]
    assert result["placement_reasons"][str(victim.id)]["reason"] == "mark_together_split"

    room = _unit_of(result, rooms, victim)
    await unassign_participant(db, room.id, victim.id, actor_user_id=user.id)

    warning = await compute_manual_move_warning(
        db, event_id=event.id, category_id=cat.id,
        participant_id=victim.id, new_unit_id=None,
    )
    assert warning is not None
    assert warning["key"] == "organise.warning.mark_separated"


@pytest.mark.asyncio
async def test_category_override_away_from_together_silences_warning(db):
    """The mirror image: the global definition says "together", but the
    organiser has since overridden this category to "split". The engine
    no longer claims to keep the mark together here, so a manual
    unassign is not overriding anything — silent.
    """
    user, event, cat, mark, rooms, holders, result = await _split_mark_cluster(
        db, global_behaviour="together", priorities_factory=lambda mid: [mid],
    )
    victim = holders[0]
    room = _unit_of(result, rooms, victim)

    cat.settings = {"engine": {
        "use_group_codes": False,
        "equalise_after_allocation": False,
        "mark_priorities": [{"id": str(mark.id), "behaviour": "split"}],
    }}
    await db.flush()

    await unassign_participant(db, room.id, victim.id, actor_user_id=user.id)
    warning = await compute_manual_move_warning(
        db, event_id=event.id, category_id=cat.id,
        participant_id=victim.id, new_unit_id=None,
    )
    assert warning is None


# ─── The peeling helper's own contract ──────────────────────────────


def test_mark_id_from_cluster_contract():
    mid = uuid.uuid4()
    assert _mark_id_from_cluster(f"mark:{mid}") == str(mid)
    assert _mark_id_from_cluster(str(mid)) == str(mid)
    # Canonicalised, so a lookup keyed on the bare id matches.
    assert _mark_id_from_cluster(f"mark:{str(mid).upper()}") == str(mid)
    # A group code is free organiser text and is not a mark cluster id.
    assert _mark_id_from_cluster("SMITH") is None
    assert _mark_id_from_cluster("mark:not-a-uuid") is None
    assert _mark_id_from_cluster("") is None
    assert _mark_id_from_cluster(None) is None
