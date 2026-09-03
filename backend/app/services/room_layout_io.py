"""Export / import a room layout — group types (allocation categories) plus
their units — as a portable JSON document.

GDPR-safe: only configuration is ever included, never participants, allocations,
or mark assignments. Mark restrictions (on units, and in the engine's
mark_priorities setting) are carried by mark NAME rather than id, so a layout is
portable across events and even across Moimio instances. On import a name is
linked to a mark of the same name in the target event, or quietly dropped if no
such mark exists (matching the rule: a room's mark restriction only applies when
that mark is present).
"""
import copy
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allocation_category import AllocationCategory
from app.models.allocation_unit import AllocationUnit
from app.models.mark import MarkDefinition

EXPORT_KIND = "moimio.room_layout"
EXPORT_VERSION = 1


def _settings_ids_to_names(settings, id_to_name):
    """Rewrite engine.mark_priorities entries from {id, behaviour} to
    {name, behaviour} for portability. Drops ids that no longer resolve."""
    if not isinstance(settings, dict):
        return settings
    s = copy.deepcopy(settings)
    eng = s.get("engine")
    if isinstance(eng, dict) and isinstance(eng.get("mark_priorities"), list):
        out = []
        for mp in eng["mark_priorities"]:
            if isinstance(mp, dict) and mp.get("id") is not None:
                nm = id_to_name.get(str(mp["id"]))
                if nm is not None:
                    out.append({"name": nm, "behaviour": mp.get("behaviour")})
        eng["mark_priorities"] = out
    return s


def _settings_names_to_ids(settings, name_to_id):
    """Inverse of the above, resolving names against the target event's marks."""
    if not isinstance(settings, dict):
        return settings
    s = copy.deepcopy(settings)
    eng = s.get("engine")
    if isinstance(eng, dict) and isinstance(eng.get("mark_priorities"), list):
        out = []
        for mp in eng["mark_priorities"]:
            if isinstance(mp, dict) and mp.get("name"):
                mid = name_to_id.get(mp["name"])
                if mid is not None:
                    out.append({"id": str(mid), "behaviour": mp.get("behaviour")})
        eng["mark_priorities"] = out
    return s


async def export_room_layout(db: AsyncSession, event_id: uuid.UUID) -> dict:
    marks = (await db.execute(
        select(MarkDefinition).where(MarkDefinition.event_id == event_id)
    )).scalars().all()
    id_to_name = {str(m.id): m.name for m in marks}

    cats = (await db.execute(
        select(AllocationCategory)
        .where(AllocationCategory.event_id == event_id)
        .order_by(AllocationCategory.sort_order)
    )).scalars().all()

    group_types = []
    for cat in cats:
        units = (await db.execute(
            select(AllocationUnit)
            .where(AllocationUnit.category_id == cat.id)
            .order_by(AllocationUnit.sort_order)
        )).scalars().all()
        group_types.append({
            "name": cat.name,
            "item_label": cat.item_label,
            "description": cat.description,
            "rule_type": cat.rule_type,
            # Both ignored from v1.0.3; still written so a file exported here
            # can be read by an older instance without hiding its fields.
            "has_capacity": True,
            "has_gender_restriction": True,
            # v1.0.3 fix: this was omitted, so importing a layout silently
            # reverted "group codes claim units exclusively" to off.
            "exclusive_group_codes": cat.exclusive_group_codes,
            # v1.0.4: carry the translation markers so an exported layout
            # lands in the reader's language rather than freezing English.
            "name_key": cat.name_key,
            "item_label_key": cat.item_label_key,
            "settings": _settings_ids_to_names(cat.settings, id_to_name),
            "units": [{
                "name": u.name,
                "capacity": u.capacity,
                "gender_restriction": u.gender_restriction,
                "is_kept": getattr(u, "is_kept", False),
                "sort_order": u.sort_order,
                "mark_restriction_name": (
                    id_to_name.get(str(u.mark_restriction)) if u.mark_restriction else None
                ),
            } for u in units],
        })

    return {"kind": EXPORT_KIND, "version": EXPORT_VERSION, "group_types": group_types}


async def import_room_layout(db: AsyncSession, event_id: uuid.UUID, payload: dict) -> dict:
    if not isinstance(payload, dict) or payload.get("kind") != EXPORT_KIND:
        raise ValueError("not_a_room_layout")

    marks = (await db.execute(
        select(MarkDefinition).where(MarkDefinition.event_id == event_id)
    )).scalars().all()
    name_to_id = {m.name: m.id for m in marks}

    existing = (await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == event_id)
    )).scalars().all()
    next_sort = max([c.sort_order for c in existing], default=-1) + 1

    created_cats = 0
    created_units = 0
    for gt in payload.get("group_types", []):
        cat = AllocationCategory(
            event_id=event_id,
            name=gt.get("name") or "Untitled",
            item_label=gt.get("item_label"),
            description=gt.get("description"),
            rule_type=gt.get("rule_type"),
            has_capacity=True,  # v1.0.3: ignored; always on
            has_gender_restriction=True,  # v1.0.3: ignored; always on
            exclusive_group_codes=gt.get("exclusive_group_codes", False),
            name_key=gt.get("name_key"),
            item_label_key=gt.get("item_label_key"),
            sort_order=next_sort,
            is_default=False,
            confirmed=False,
            settings=_settings_names_to_ids(gt.get("settings"), name_to_id),
        )
        db.add(cat)
        await db.flush()  # populate cat.id
        created_cats += 1
        next_sort += 1
        for u in gt.get("units", []):
            mr_name = u.get("mark_restriction_name")
            db.add(AllocationUnit(
                category_id=cat.id,
                name=u.get("name") or "Unit",
                capacity=u.get("capacity"),
                gender_restriction=u.get("gender_restriction"),
                mark_restriction=(name_to_id.get(mr_name) if mr_name else None),
                is_kept=u.get("is_kept", False),
                sort_order=u.get("sort_order", 0),
            ))
            created_units += 1

    await db.flush()
    return {"group_types": created_cats, "units": created_units}
