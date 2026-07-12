"""v1.0.1e-15: top_up must evict occupants who violate a room restriction that
was added after they were placed (the reported bug), while keeping valid ones
and leaving kept units frozen."""
import pytest
from sqlalchemy import select
from app.models.allocation import Allocation
from app.services.engine_service import run_engine
from tests.conftest import make_event, make_category, make_unit, make_participant, make_mark, assign_mark

@pytest.mark.asyncio
async def test_topup_evicts_non_holder_from_newly_restricted_room(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    r1 = await make_unit(db, cat.id, "1", capacity=8)
    r2 = await make_unit(db, cat.id, "2", capacity=8)
    mark = await make_mark(db, ev.id, name="Fleischesser")
    holder = await make_participant(db, ev.id, first_name="Holder", gender="male")
    non = await make_participant(db, ev.id, first_name="NonHolder", gender="male")
    await assign_mark(db, ev.id, mark.id, holder.id)
    # both already sitting in room 1 (placed BEFORE the restriction)
    db.add(Allocation(event_id=ev.id, unit_id=r1.id, participant_id=holder.id))
    db.add(Allocation(event_id=ev.id, unit_id=r1.id, participant_id=non.id))
    await db.flush()
    # NOW restrict room 1 to the mark, and top_up
    r1.mark_restriction = mark.id
    await db.flush()

    result = await run_engine(db, ev.id, cat.id, mode="top_up")
    r1_pids = set(result["proposed"].get(str(r1.id), []))
    assert str(holder.id) in r1_pids, "holder should stay in room 1"
    assert str(non.id) not in r1_pids, "BUG: non-holder should be evicted from restricted room 1"
    # non-holder is re-placed somewhere valid (room 2) or unplaced, but NOT room 1
    assert str(non.id) in set(result["proposed"].get(str(r2.id), [])) or str(non.id) in result["unplaced"]
