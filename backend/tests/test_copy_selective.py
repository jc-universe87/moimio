import pytest
from sqlalchemy import select
from app.services.event_service import duplicate_event_config
from app.schemas.event import CopyOptions
from app.models.mark import MarkDefinition
from app.models.allocation_unit import AllocationUnit
from app.models.allocation_category import AllocationCategory
from tests.conftest import make_event, make_category, make_unit, make_mark

async def _seed(db):
    src = await make_event(db)
    mark = await make_mark(db, src.id, name="Fleischesser")
    cat = await make_category(db, src.id, has_capacity=True)
    unit = await make_unit(db, cat.id, "MeatRoom", capacity=8)
    unit.mark_restriction = mark.id
    await db.flush()
    return src

async def _counts(db, ev_id):
    marks = (await db.execute(select(MarkDefinition).where(MarkDefinition.event_id == ev_id))).scalars().all()
    cats = (await db.execute(select(AllocationCategory).where(AllocationCategory.event_id == ev_id))).scalars().all()
    units = (await db.execute(select(AllocationUnit).where(AllocationUnit.category_id.in_([c.id for c in cats])))).scalars().all() if cats else []
    return marks, cats, units

@pytest.mark.asyncio
async def test_group_types_without_marks_clears_restriction(db):
    src = await _seed(db)
    dest = await make_event(db)
    await duplicate_event_config(db, source_event_id=src.id, dest_event_id=dest.id,
                                 options=CopyOptions(marks=False, group_types=True, registration_form=False, custom_fields=False, staff=False))
    await db.flush()
    marks, cats, units = await _counts(db, dest.id)
    assert len(marks) == 0, "marks should NOT be copied"
    assert len(units) == 1, "unit should be copied"
    assert units[0].mark_restriction is None, "restriction to an absent mark must be cleared"
    print("  group_types w/o marks: unit copied, restriction cleared, no marks")

@pytest.mark.asyncio
async def test_group_types_with_marks_rewires(db):
    src = await _seed(db)
    dest = await make_event(db)
    await duplicate_event_config(db, source_event_id=src.id, dest_event_id=dest.id,
                                 options=CopyOptions(marks=True, group_types=True, registration_form=False, custom_fields=False, staff=False))
    await db.flush()
    marks, cats, units = await _counts(db, dest.id)
    assert len(marks) == 1 and units[0].mark_restriction == marks[0].id, "restriction rewired to copied mark"
    print("  group_types w/ marks: restriction rewired to the copied mark")

@pytest.mark.asyncio
async def test_marks_only(db):
    src = await _seed(db)
    dest = await make_event(db)
    await duplicate_event_config(db, source_event_id=src.id, dest_event_id=dest.id,
                                 options=CopyOptions(marks=True, group_types=False, registration_form=False, custom_fields=False, staff=False))
    await db.flush()
    marks, cats, units = await _counts(db, dest.id)
    assert len(marks) == 1 and len(cats) == 0, "only marks copied, no group types"
    print("  marks only: 1 mark, 0 group types")

@pytest.mark.asyncio
async def test_default_copies_all(db):
    src = await _seed(db)
    dest = await make_event(db)
    await duplicate_event_config(db, source_event_id=src.id, dest_event_id=dest.id)  # options=None
    await db.flush()
    marks, cats, units = await _counts(db, dest.id)
    assert len(marks) == 1 and len(cats) == 1 and len(units) == 1, "None = copy all (back-compat)"
    print("  default (None): all copied")
