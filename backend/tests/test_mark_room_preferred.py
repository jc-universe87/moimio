import pytest
from app.services.engine_service import run_engine
from tests.conftest import make_event, make_category, make_unit, make_participant, make_mark, assign_mark

@pytest.mark.asyncio
async def test_holder_cluster_prefers_mark_room_over_tight_fit(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True, settings={"engine": {"use_group_codes": True, "split_oversized_groups": True}})
    r1 = await make_unit(db, cat.id, "1", capacity=8)   # mark room
    r2 = await make_unit(db, cat.id, "2", capacity=8)
    mark = await make_mark(db, ev.id, name="Fleischesser")
    r1.mark_restriction = mark.id
    await db.flush()
    # a family of 6 (unique code) fills r2 to leave exactly 2 seats — a tight fit for the pair
    for i in range(6):
        await make_participant(db, ev.id, first_name=f"Fam_{i}", gender="male", group_code="FAM6")
    # the purple pair, same code, both hold the mark
    pa = await make_participant(db, ev.id, first_name="PA", gender="male", group_code="PP")
    pb = await make_participant(db, ev.id, first_name="PB", gender="male", group_code="PP")
    await assign_mark(db, ev.id, mark.id, pa.id); await assign_mark(db, ev.id, mark.id, pb.id)
    await db.flush()
    result = await run_engine(db, ev.id, cat.id, mode="replace")
    r1_pids = set(result["proposed"].get(str(r1.id), []))
    assert {str(pa.id), str(pb.id)} <= r1_pids, f"holder pair should be in the mark room, got {r1_pids}"
    print("  holder pair correctly placed in the mark room despite a tight-fit alternative")
