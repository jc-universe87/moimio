"""Reproduce the reported bug: a room marked with a restriction gets filled
with participants who do NOT hold that mark after re-allocation."""
import pytest
from sqlalchemy import select
from app.models.allocation import Allocation
from app.services.engine_service import run_engine
from tests.conftest import make_event, make_category, make_unit, make_participant, make_mark, assign_mark

def _placed(result):
    return {pid: uid for uid, pids in result["proposed"].items() for pid in pids}

@pytest.mark.asyncio
async def test_restricted_room_excludes_non_holders_with_many_participants(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    r1 = await make_unit(db, cat.id, "1", capacity=8)      # will be mark-restricted
    r2 = await make_unit(db, cat.id, "2", capacity=8)
    r3 = await make_unit(db, cat.id, "3", capacity=8)
    mark = await make_mark(db, ev.id, name="Fleischesser")
    r1.mark_restriction = mark.id
    await db.flush()

    # 20 participants, only 2 hold the mark
    ps = [await make_participant(db, ev.id, first_name=f"P{i}", gender="male") for i in range(20)]
    await assign_mark(db, ev.id, mark.id, ps[0].id)
    await assign_mark(db, ev.id, mark.id, ps[1].id)
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="replace")
    r1_pids = set(result["proposed"].get(str(r1.id), []))
    holders = {str(ps[0].id), str(ps[1].id)}
    non_holders = {str(p.id) for p in ps[2:]}

    print(f"room 1 has {len(r1_pids)} people; holders in room1: {r1_pids & holders}; NON-holders in room1: {r1_pids & non_holders}")
    assert r1_pids <= holders, f"BUG: non-holders placed in restricted room 1: {r1_pids & non_holders}"
