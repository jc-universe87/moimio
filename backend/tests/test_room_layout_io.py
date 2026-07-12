import pytest
from sqlalchemy import select
from app.services.room_layout_io import export_room_layout, import_room_layout, EXPORT_KIND
from app.models.allocation_unit import AllocationUnit
from app.models.allocation_category import AllocationCategory
from tests.conftest import make_event, make_category, make_unit, make_mark

@pytest.mark.asyncio
async def test_export_import_roundtrip_resolves_mark_by_name(db):
    # source: mark + category(with mark_priorities settings) + unit restricted to the mark
    src = await make_event(db)
    mark = await make_mark(db, src.id, name="Fleischesser")
    cat = await make_category(db, src.id, has_capacity=True, settings={"engine": {"mark_priorities": [{"id": str(mark.id), "behaviour": "none"}]}})
    unit = await make_unit(db, cat.id, "MeatRoom", capacity=8)
    unit.mark_restriction = mark.id
    await db.flush()

    payload = await export_room_layout(db, src.id)
    assert payload["kind"] == EXPORT_KIND
    gt = payload["group_types"][0]
    assert gt["units"][0]["mark_restriction_name"] == "Fleischesser", "unit restriction exported by name"
    assert gt["settings"]["engine"]["mark_priorities"][0]["name"] == "Fleischesser", "settings mark by name"

    # target: a DIFFERENT event with a mark of the SAME NAME (different id)
    dest = await make_event(db)
    dmark = await make_mark(db, dest.id, name="Fleischesser")
    res = await import_room_layout(db, dest.id, payload)
    await db.flush()
    assert res == {"group_types": 1, "units": 1}
    dcats = (await db.execute(select(AllocationCategory).where(AllocationCategory.event_id == dest.id))).scalars().all()
    dunits = (await db.execute(select(AllocationUnit).where(AllocationUnit.category_id.in_([c.id for c in dcats])))).scalars().all()
    assert dunits[0].mark_restriction == dmark.id, "restriction re-linked to the same-named mark in target"
    assert dcats[0].settings["engine"]["mark_priorities"][0]["id"] == str(dmark.id), "settings mark re-linked"
    print("  round-trip OK; mark restriction + settings re-linked by name")

@pytest.mark.asyncio
async def test_import_drops_absent_mark(db):
    src = await make_event(db)
    mark = await make_mark(db, src.id, name="OnlyHere")
    cat = await make_category(db, src.id, has_capacity=True)
    unit = await make_unit(db, cat.id, "R", capacity=4); unit.mark_restriction = mark.id
    await db.flush()
    payload = await export_room_layout(db, src.id)
    dest = await make_event(db)  # no marks
    await import_room_layout(db, dest.id, payload)
    await db.flush()
    dcats = (await db.execute(select(AllocationCategory).where(AllocationCategory.event_id == dest.id))).scalars().all()
    dunits = (await db.execute(select(AllocationUnit).where(AllocationUnit.category_id.in_([c.id for c in dcats])))).scalars().all()
    assert dunits[0].mark_restriction is None, "absent mark -> restriction dropped"
    print("  absent-mark restriction correctly dropped on import")

@pytest.mark.asyncio
async def test_import_rejects_bad_payload(db):
    dest = await make_event(db)
    with pytest.raises(ValueError):
        await import_room_layout(db, dest.id, {"kind": "something_else"})
    print("  bad payload rejected")
