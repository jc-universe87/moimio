"""Export / import the registration form — the standard field toggles
(EventFieldConfig) plus the custom field definitions — as a portable JSON
document. GDPR-safe: configuration only, never participants or their answers.

Import is idempotent-ish: standard field toggles are upserted by field name
(the standard fields already exist in every event), and custom fields are added,
skipping any whose label already exists so re-importing doesn't duplicate them.

v1.0.7: a field's rule ("show only if") names its source field by LABEL in
the file, because ids mean nothing in another event. Imported fields go to
the end of the form in the file's order. A rule whose source cannot be found
above the field, by label, is dropped and counted rather than guessed at.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_field_config import EventFieldConfig
from app.models.custom_field import CustomFieldDefinition
from app.services.field_conditions import (
    BUILTIN_KINDS, ConditionError, clean_rule, load_defs, ordered, rule_problem,
)

EXPORT_KIND = "moimio.registration_form"
EXPORT_VERSION = 1


async def export_registration_form(db: AsyncSession, event_id: uuid.UUID) -> dict:
    fcs = (await db.execute(
        select(EventFieldConfig).where(EventFieldConfig.event_id == event_id)
    )).scalars().all()
    cfs = ordered(list((await db.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
    )).scalars().all()))
    label_of = {str(c.id): c.label for c in cfs}
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
                "show_if": _rule_out(c.show_if, label_of),
            }
            for c in cfs
        ],
    }


def _rule_out(rule: dict | None, label_of: dict[str, str]) -> dict | None:
    """A rule for the file: custom sources named by label, not id."""
    if not rule:
        return None
    out = []
    for c in rule.get("conditions") or []:
        if c.get("source") in BUILTIN_KINDS:
            out.append(dict(c))
            continue
        label = label_of.get(str(c.get("source")))
        if label is not None:
            out.append({**{k: v for k, v in c.items() if k != "source"}, "source_label": label})
    return {"match": rule.get("match", "all"), "conditions": out} if out else None


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
    existing = await load_defs(db, event_id)
    id_by_label = {c.label: c.id for c in existing}
    next_order = max((c.sort_order or 0 for c in existing), default=-1) + 1
    created_customs = 0
    dropped_rules = 0
    file_fields = sorted(
        (cf for cf in payload.get("custom_fields", []) if isinstance(cf, dict)),
        key=lambda cf: cf.get("sort_order", 0) if isinstance(cf.get("sort_order", 0), int) else 0,
    )
    for cf in file_fields:
        label = cf.get("label")
        if not label or label in id_by_label:
            continue
        # Every field already in the event, and every one imported before
        # this, sits above it, so a source found by label is always above.
        rule = _rule_in(cf.get("show_if"), id_by_label)
        if cf.get("show_if") and rule is None:
            dropped_rules += 1
        new = CustomFieldDefinition(
            id=uuid.uuid4(),
            event_id=event_id,
            label=label,
            field_type=cf.get("field_type", "text"),
            options=cf.get("options"),
            is_required=bool(cf.get("is_required", False)),
            show_in_form=bool(cf.get("show_in_form", True)),
            sort_order=next_order,
            show_if=rule,
        )
        db.add(new)
        id_by_label[label] = new.id
        next_order += 1
        created_customs += 1

    await db.flush()
    # A rule that names the wrong kind of field, or an option its source does
    # not have, would hide its field for good. Drop those too.
    defs = await load_defs(db, event_id)
    for d in defs:
        if d.show_if is not None and rule_problem(defs, d):
            d.show_if = None
            dropped_rules += 1
    await db.flush()
    return {"fields": updated_fields, "custom_fields": created_customs, "dropped_rules": dropped_rules}


def _rule_in(rule, id_by_label: dict[str, uuid.UUID]) -> dict | None:
    """A rule from the file. A condition naming a field that cannot be found
    drops the whole rule, and the import counts it: keeping the rest would
    quietly change what the rule means (fewer conditions to meet under
    "all", more under "any"), and a counted drop is one the organiser hears
    about."""
    if not isinstance(rule, dict) or not isinstance(rule.get("conditions"), list):
        return None
    conditions = []
    for c in rule["conditions"]:
        if not isinstance(c, dict):
            return None
        if c.get("source") in BUILTIN_KINDS:
            conditions.append(c)
            continue
        src = id_by_label.get(c.get("source_label"))
        if src is None:
            return None
        conditions.append({**{k: v for k, v in c.items() if k != "source_label"}, "source": str(src)})
    try:
        return clean_rule({"match": rule.get("match", "all"), "conditions": conditions})
    except ConditionError:
        return None
