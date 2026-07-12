import pytest
from sqlalchemy import select
from app.services.registration_form_io import export_registration_form, import_registration_form
from app.models.event_field_config import EventFieldConfig
from app.models.custom_field import CustomFieldDefinition
from tests.conftest import make_event

@pytest.mark.asyncio
async def test_form_roundtrip_upsert_and_dedup(db):
    src = await make_event(db)
    db.add(EventFieldConfig(event_id=src.id, field_name="phone", is_enabled=True, is_required=True))
    db.add(CustomFieldDefinition(event_id=src.id, label="T-Shirt Size", field_type="text", is_required=False, sort_order=1))
    await db.flush()

    payload = await export_registration_form(db, src.id)
    assert payload["kind"] == "moimio.registration_form"
    assert any(f["field_name"] == "phone" and f["is_required"] for f in payload["field_configs"])
    assert any(c["label"] == "T-Shirt Size" for c in payload["custom_fields"])

    dest = await make_event(db)
    db.add(EventFieldConfig(event_id=dest.id, field_name="phone", is_enabled=False, is_required=False))
    await db.flush()
    await import_registration_form(db, dest.id, payload)
    await db.flush()

    fcs = (await db.execute(select(EventFieldConfig).where(EventFieldConfig.event_id == dest.id))).scalars().all()
    phones = [f for f in fcs if f.field_name == "phone"]
    assert len(phones) == 1 and phones[0].is_enabled and phones[0].is_required, "phone upserted, not duplicated"
    cfs = (await db.execute(select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == dest.id))).scalars().all()
    assert any(c.label == "T-Shirt Size" for c in cfs), "custom field created"

    # re-import must not duplicate the custom field
    await import_registration_form(db, dest.id, payload)
    await db.flush()
    cfs2 = (await db.execute(select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == dest.id))).scalars().all()
    assert len([c for c in cfs2 if c.label == "T-Shirt Size"]) == 1, "no duplicate on re-import"
    print("  form round-trip OK: field upserted, custom field created, dedup on re-import")

@pytest.mark.asyncio
async def test_form_import_rejects_wrong_kind(db):
    dest = await make_event(db)
    with pytest.raises(ValueError):
        await import_registration_form(db, dest.id, {"kind": "moimio.room_layout"})
    print("  wrong-kind payload rejected")
