"""v1.0.1e-1 — API-shaped round trip for the two new unit fields.

Mirrors exactly what the PATCH endpoint does with a browser payload:
UnitUpdate(...).model_dump(exclude_unset=True) → update_unit(**kwargs)
→ fresh SELECT. Written because v1.0.1e verified the engine but never
the click-to-save path.
"""
import pytest
from sqlalchemy import select
from app.api.allocations import UnitUpdate
from app.services.allocation_service import update_unit, list_units
from app.models.allocation_unit import AllocationUnit
from tests.conftest import make_event, make_category, make_unit, make_mark

@pytest.mark.asyncio
async def test_mark_and_kept_persist_via_api_path(db):
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    unit = await make_unit(db, cat.id, "Room 1", capacity=8)
    mark = await make_mark(db, ev.id, name="family")
    await db.flush()

    payload = UnitUpdate.model_validate({"mark_restriction": str(mark.id), "is_kept": True})
    await update_unit(db, unit.id, **payload.model_dump(exclude_unset=True))
    await db.commit()

    fresh = (await db.execute(select(AllocationUnit).where(AllocationUnit.id == unit.id))).scalar_one()
    assert fresh.mark_restriction == mark.id
    assert fresh.is_kept is True

    # And clearing works too (null over the wire).
    payload2 = UnitUpdate.model_validate({"mark_restriction": None, "is_kept": False})
    await update_unit(db, unit.id, **payload2.model_dump(exclude_unset=True))
    await db.commit()
    fresh2 = (await db.execute(select(AllocationUnit).where(AllocationUnit.id == unit.id))).scalar_one()
    assert fresh2.mark_restriction is None and fresh2.is_kept is False


@pytest.mark.asyncio
async def test_board_read_path_includes_new_fields(db):
    """v1.0.1e-2 regression guard: the units the UI actually renders come
    from list_units' hand-built dicts (the occupant_count serializer), not
    from raw ORM rows. v1.0.1e saved the two new fields but this read path
    stripped them — the padlock/mark appeared to 'not save'. Assert the
    serializer now carries them."""
    ev = await make_event(db)
    cat = await make_category(db, ev.id, has_capacity=True)
    unit = await make_unit(db, cat.id, "Room 1", capacity=8)
    mark = await make_mark(db, ev.id, name="family")
    await db.flush()
    payload = UnitUpdate.model_validate({"mark_restriction": str(mark.id), "is_kept": True})
    await update_unit(db, unit.id, **payload.model_dump(exclude_unset=True))
    await db.commit()

    rows = await list_units(db, cat.id)
    row = next(r for r in rows if r["id"] == unit.id)
    assert row["is_kept"] is True
    assert row["mark_restriction"] == mark.id
