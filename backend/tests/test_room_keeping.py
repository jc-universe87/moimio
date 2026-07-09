"""v1.0.1e — room-keeping ("keep as-is") engine + commit behaviour.

A unit flagged is_kept is frozen on re-allocate: its occupants stay, it
receives no new placements, and commit leaves its rows untouched (no
clear, no rewrite — so no audit churn and no duplication). These tests
prove:

  1. replace mode keeps a kept unit's occupants and fills only the rest;
  2. a kept unit never absorbs overflow, even with spare capacity;
  3. commit_proposal leaves a kept unit's allocation rows literally
     unchanged (same row ids), while writing the rest.

All need the Postgres test DB (shared db_engine fixture); they skip when
it is unreachable.
"""

import pytest
from sqlalchemy import select

from app.models.allocation import Allocation
from app.services.engine_service import run_engine, commit_proposal
from tests.conftest import make_event, make_category, make_unit, make_participant


def _placement_map(result):
    placed = {}
    for uid, pids in result["proposed"].items():
        for pid in pids:
            placed[pid] = uid
    return placed


async def _seed_kept(db, ev, cat):
    """A kept room with 2 pre-existing occupants + a general room."""
    kept = await make_unit(db, cat.id, "Kept room", capacity=10)
    kept.is_kept = True
    general = await make_unit(db, cat.id, "General", capacity=10)
    await db.flush()
    orig = [await make_participant(db, ev.id, first_name=f"Orig{i}", gender="male")
            for i in range(2)]
    allocs = []
    for p in orig:
        a = Allocation(event_id=ev.id, unit_id=kept.id, participant_id=p.id)
        db.add(a)
        allocs.append(a)
    await db.flush()
    return kept, general, orig, allocs


@pytest.mark.asyncio
async def test_kept_unit_frozen_on_replace(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    kept, general, orig, _ = await _seed_kept(db, ev, cat)
    new = [await make_participant(db, ev.id, first_name=f"New{i}", gender="male")
           for i in range(3)]
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    placed = _placement_map(result)
    kr = str(kept.id)
    orig_ids = [str(p.id) for p in orig]
    new_ids = [str(p.id) for p in new]

    # Kept room keeps exactly its original occupants...
    assert set(result["proposed"][kr]) == set(orig_ids)
    # ...the originals are not re-placed anywhere else (no duplication)...
    assert all(placed[o] == kr for o in orig_ids)
    # ...and the new people fill the general room instead.
    assert all(placed[n] == str(general.id) for n in new_ids)


@pytest.mark.asyncio
async def test_kept_unit_never_receives_overflow(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    kept = await make_unit(db, cat.id, "Kept room", capacity=10)  # plenty of space
    kept.is_kept = True
    general = await make_unit(db, cat.id, "General", capacity=2)  # deliberately tiny
    await db.flush()
    orig = await make_participant(db, ev.id, first_name="Orig", gender="male")
    db.add(Allocation(event_id=ev.id, unit_id=kept.id, participant_id=orig.id))
    new = [await make_participant(db, ev.id, first_name=f"New{i}", gender="male")
           for i in range(4)]  # 4 new, general holds only 2
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    kr = str(kept.id)

    # Kept room still holds only its one original — no overflow despite the
    # spare beds and a full general room.
    assert set(result["proposed"][kr]) == {str(orig.id)}
    assert len(result["proposed"][str(general.id)]) == 2
    # The other two spill to unplaced, NOT into the frozen room.
    assert len(result["unplaced"]) == 2


@pytest.mark.asyncio
async def test_commit_leaves_kept_unit_rows_untouched(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    kept, general, orig, orig_allocs = await _seed_kept(db, ev, cat)
    orig_alloc_ids = {str(a.id) for a in orig_allocs}
    new = [await make_participant(db, ev.id, first_name=f"New{i}", gender="male")
           for i in range(3)]
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    await commit_proposal(
        db, ev.id, cat.id, result["proposed"],
        placement_reasons=result["placement_reasons"],
        engine_run_id=result["run_id"],
    )
    await db.flush()

    # The kept room's allocation ROWS are the same ones — not cleared and
    # recreated (which would change their ids). This is what "untouched"
    # means, and it's why the audit trail stays clean.
    kept_allocs = (await db.execute(
        select(Allocation).where(Allocation.unit_id == kept.id))).scalars().all()
    assert {str(a.id) for a in kept_allocs} == orig_alloc_ids
    assert {str(a.participant_id) for a in kept_allocs} == {str(p.id) for p in orig}

    # The rest were written normally: the 3 new people are in general.
    gen_allocs = (await db.execute(
        select(Allocation).where(Allocation.unit_id == general.id))).scalars().all()
    assert {str(a.participant_id) for a in gen_allocs} == {str(p.id) for p in new}
