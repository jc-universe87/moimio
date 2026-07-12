import pytest
from sqlalchemy import select
from app.services.event_service import duplicate_event_config
from app.models.mark import MarkDefinition
from app.models.allocation_unit import AllocationUnit
from app.models.allocation_category import AllocationCategory
from tests.conftest import make_event, make_category, make_unit, make_mark

@pytest.mark.asyncio
async def test_copy_rewires_unit_mark_restriction(db):
    src = await make_event(db)
    mark = await make_mark(db, src.id, name="Fleischesser")
    cat = await make_category(db, src.id, has_capacity=True)
    unit = await make_unit(db, cat.id, "MeatRoom", capacity=8)
    unit.mark_restriction = mark.id
    await db.flush()
    dest = await make_event(db)
    await duplicate_event_config(db, source_event_id=src.id, dest_event_id=dest.id)
    await db.flush()
    new_marks = (await db.execute(select(MarkDefinition).where(MarkDefinition.event_id == dest.id))).scalars().all()
    assert len(new_marks) == 1 and new_marks[0].id != mark.id
    new_mark_id = new_marks[0].id
    new_cats = (await db.execute(select(AllocationCategory).where(AllocationCategory.event_id == dest.id))).scalars().all()
    new_units = (await db.execute(select(AllocationUnit).where(AllocationUnit.category_id.in_([c.id for c in new_cats])))).scalars().all()
    assert len(new_units) == 1, f"{len(new_units)} units copied"
    assert new_units[0].mark_restriction == new_mark_id, f"expected new mark {new_mark_id}, got {new_units[0].mark_restriction} (source was {mark.id})"
    print("  copied unit mark_restriction correctly rewired to the NEW mark")
