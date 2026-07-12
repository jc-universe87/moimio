"""Regression guard for the v1.0.1e-16 engine fixes, on a faithful scenario
(mixed-gender families + singletons + gender rooms + a mark-restricted room):
  1. determinism  -- two runs produce identical placements
  2. no fillable gap -- nobody is left unplaced while eligible capacity remains
  3. mark room -- a group-coded holder pair lands in the mark room
"""
import pytest
from app.services.engine_service import run_engine
from tests.conftest import (make_event, make_category, make_unit,
                            make_participant, make_mark, assign_mark)

async def _build(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True, settings={"engine": {
        "use_group_codes": True, "group_remaining_by_gender": True,
        "split_oversized_groups": True, "equalise_after_allocation": True,
    }})
    rooms = [await make_unit(db, cat.id, str(i), capacity=8) for i in range(1, 9)]
    maenner = await make_unit(db, cat.id, "Maennerzimmer", capacity=18); maenner.gender_restriction = "male"
    frauen = await make_unit(db, cat.id, "Frauenzimmer", capacity=18); frauen.gender_restriction = "female"
    mark = await make_mark(db, ev.id, name="Fleischesser")
    rooms[0].mark_restriction = mark.id
    await db.flush()
    for f in range(6):
        for i in range(8):
            await make_participant(db, ev.id, first_name=f"Fam{f}_{i}",
                                   gender=("male" if i % 2 == 0 else "female"), group_code=f"FAM{f}")
    pa = await make_participant(db, ev.id, first_name="Purple_A", gender="male", group_code="PURPLE")
    pb = await make_participant(db, ev.id, first_name="Purple_B", gender="female", group_code="PURPLE")
    await assign_mark(db, ev.id, mark.id, pa.id); await assign_mark(db, ev.id, mark.id, pb.id)
    for i in range(50):
        await make_participant(db, ev.id, first_name=f"Single{i}", gender=["male", "female", None][i % 3])
    await db.flush()
    return ev, cat, rooms, maenner, frauen, mark, pa, pb

@pytest.mark.asyncio
async def test_determinism(db):
    ev, cat, *_ = await _build(db)
    r1 = await run_engine(db, ev.id, cat.id, mode="replace")
    r2 = await run_engine(db, ev.id, cat.id, mode="replace")
    a = {u: sorted(p) for u, p in r1["proposed"].items()}
    b = {u: sorted(p) for u, p in r2["proposed"].items()}
    assert a == b, "two runs produced different placements (non-determinism)"

@pytest.mark.asyncio
async def test_no_fillable_gap_and_mark_room(db):
    ev, cat, rooms, maenner, frauen, mark, pa, pb = await _build(db)
    # who holds the mark
    holders = {str(pa.id), str(pb.id)}
    result = await run_engine(db, ev.id, cat.id, mode="replace")
    # mark room got the holder pair
    r1 = set(result["proposed"].get(str(rooms[0].id), []))
    assert holders <= r1, f"holder pair missing from mark room: {r1}"
    # no fillable gap: for every unplaced person there is NO unit with spare
    # capacity they're eligible for (gender + mark)
    placed = {pid for pids in result["proposed"].values() for pid in pids}
    units = rooms + [maenner, frauen]
    remaining = {str(u.id): u.capacity - len(result["proposed"].get(str(u.id), [])) for u in units}
    ok_gender = {"male": lambda u: u.gender_restriction in (None, "male"),
                 "female": lambda u: u.gender_restriction in (None, "female"),
                 None: lambda u: u.gender_restriction is None}
    from app.models import Participant
    from sqlalchemy import select
    parts = (await db.execute(select(Participant).where(Participant.event_id == ev.id))).scalars().all()
    for p in parts:
        if str(p.id) in placed:
            continue
        for u in units:
            if remaining[str(u.id)] <= 0:
                continue
            if u.mark_restriction and str(p.id) not in holders:
                continue
            g = (p.gender or None)
            if u.gender_restriction and (g != u.gender_restriction):
                continue
            pytest.fail(f"unplaced {p.first_name} ({g}) could fit unit {u.name} with {remaining[str(u.id)]} free")
    print("  no fillable gap; mark room holds the holder pair")
