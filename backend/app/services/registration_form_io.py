"""Export / import the registration form — the standard field toggles
(EventFieldConfig) plus the custom field definitions — as a portable JSON
document. GDPR-safe: configuration only, never participants or their answers.

Import is idempotent-ish: standard field toggles are upserted by field name
(the standard fields already exist in every event), and custom fields are added,
skipping any whose label already exists so re-importing doesn't duplicate them.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_field_config import EventFieldConfig
from app.models.custom_field import CustomFieldDefinition

EXPORT_KIND = "moimio.registration_form"
EXPORT_VERSION = 1


async def export_registration_form(db: AsyncSession, event_id: uuid.UUID) -> dict:
    fcs = (await db.execute(
        select(EventFieldConfig).where(EventFieldConfig.event_id == event_id)
    )).scalars().all()
    cfs = (await db.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
        .order_by(CustomFieldDefinition.sort_order)
    )).scalars().all()
    return {
        "kind": EXPORT_KIND,
        "version": EXPORT_VERSION,
        "field_configs": [
            {"field_name": f.field_name, "is_enabled": f.is_enabled, "is_required": f.is_required}
            for f in fcs
        ],
        "custom_fields": [
            {
                "label": c.label,
                "field_type": c.field_type,
                "options": c.options,
                "is_required": c.is_required,
                "show_in_form": getattr(c, "show_in_form", True),
                "sort_order": c.sort_order,
            }
            for c in cfs
        ],
    }


async def import_registration_form(db: AsyncSession, event_id: uuid.UUID, payload: dict) -> dict:
    if not isinstance(payload, dict) or payload.get("kind") != EXPORT_KIND:
        raise ValueError("not_a_registration_form")

    # Standard field toggles: upsert by field_name.
    existing_fcs = {
        f.field_name: f
        for f in (await db.execute(
            select(EventFieldConfig).where(EventFieldConfig.event_id == event_id)
        )).scalars().all()
    }
    updated_fields = 0
    for fc in payload.get("field_configs", []):
        name = fc.get("field_name")
        if not name:
            continue
        row = existing_fcs.get(name)
        if row is not None:
            row.is_enabled = bool(fc.get("is_enabled", False))
            row.is_required = bool(fc.get("is_required", False))
        else:
            db.add(EventFieldConfig(
                event_id=event_id,
                field_name=name,
                is_enabled=bool(fc.get("is_enabled", False)),
                is_required=bool(fc.get("is_required", False)),
            ))
        updated_fields += 1

    # Custom fields: add, skipping labels that already exist.
    existing_labels = {
        c.label
        for c in (await db.execute(
            select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == event_id)
        )).scalars().all()
    }
    created_customs = 0
    for cf in payload.get("custom_fields", []):
        label = cf.get("label")
        if not label or label in existing_labels:
            continue
        db.add(CustomFieldDefinition(
            event_id=event_id,
            label=label,
            field_type=cf.get("field_type", "text"),
            options=cf.get("options"),
            is_required=bool(cf.get("is_required", False)),
            show_in_form=bool(cf.get("show_in_form", True)),
            sort_order=cf.get("sort_order", 0),
        ))
        existing_labels.add(label)
        created_customs += 1

    await db.flush()
    return {"fields": updated_fields, "custom_fields": created_customs}
