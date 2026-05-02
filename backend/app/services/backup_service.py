"""Backup service — event export and restore (data portability).

Export: builds a ZIP in memory containing JSON/CSV files for every
        entity belonging to an event.

Restore: parses a ZIP, previews counts, then creates a new event with
         all entities re-keyed to fresh UUIDs.
"""

import csv
import io
import json
import uuid
import zipfile
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MoimioAppError
from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_unit import AllocationUnit
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event import Event
from app.models.event_field_config import EventFieldConfig
from app.models.mark import MarkDefinition, MarkAssignment
from app.models.note import Note
from app.models.participant import Participant
from app.models.preference_request import ParticipantPreferenceRequest

BACKUP_VERSION = "1"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _str(v) -> str | None:
    """Coerce UUIDs, dates, datetimes to strings; pass through None."""
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _row(obj, *fields) -> dict:
    """Build a dict from an ORM object, serialising UUIDs/dates."""
    return {f: _str(getattr(obj, f, None)) for f in fields}


# ── Export ────────────────────────────────────────────────────────────────────

async def export_event_zip(
    event_id: uuid.UUID,
    db: AsyncSession,
    mode: str = "full",
) -> bytes:
    """
    Build a backup ZIP for one event and return the raw bytes.

    Args:
        event_id — event to back up
        db — async DB session
        mode — "full" (default, everything) or "structure" (v0.50r, GDPR-safe:
               event settings, categories, units, custom field definitions,
               mark definitions, field configs, event-level notes; NO
               participant PII, custom-field values, allocations, mark
               assignments, or preferences tied to a participant)

    ZIP contents (always present — restore path expects them all):
        manifest.json          — version, event_id, exported_at, row counts,
                                 backup_mode
        event.json             — event metadata + settings
        participants.csv       — participant rows (EMPTY header-only in structure mode)
        custom_fields.json     — { definitions, values: {} in structure mode }
        allocation_categories.json
        allocation_units.json
        allocations.json       — participant↔unit assignments ([] in structure mode)
        marks.json             — { definitions, assignments: [] in structure mode }
        preferences.json       — [] in structure mode
        notes.json             — event-level team notes (kept in both modes —
                                 they're organisational, not personal)
        field_configs.json

    Why "structure mode" keeps empty versions of participant-linked files:
    the restore path expects all files present (see _parse_zip). Empty
    lists iterate as no-ops, so the existing restore logic handles
    structure backups without changes — a restored structure-backup
    produces an event with zero participants but the full template of
    groups, marks, and form config ready for fresh registrations.

    GDPR note: in structure mode the backup deliberately contains NO
    personal data. Safe to share with another organisation as an event
    template, version-control, email between staff, etc.
    """
    if mode not in ("full", "structure"):
        raise MoimioAppError("errors.export.unknown_backup_mode", params={"mode": str(mode), "allowed": "full, structure"}, status_code=400)
    structure_only = mode == "structure"

    # ── Load event ──
    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise MoimioAppError("errors.event.not_found", status_code=404)

    # ── Load participants (skipped entirely in structure mode) ──
    if structure_only:
        participants = []
    else:
        p_result = await db.execute(
            select(Participant).where(
                Participant.event_id == event_id,
                Participant.deleted_at.is_(None),
            ).order_by(Participant.participant_number)
        )
        participants = list(p_result.scalars().all())
    participant_ids = [p.id for p in participants]

    # ── Load custom fields ──
    cf_result = await db.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
        .order_by(CustomFieldDefinition.sort_order)
    )
    cf_defs = list(cf_result.scalars().all())

    cfv_data: dict[str, list] = {}
    if participant_ids:
        cfv_result = await db.execute(
            select(CustomFieldValue).where(
                CustomFieldValue.participant_id.in_(participant_ids)
            )
        )
        for cfv in cfv_result.scalars().all():
            cfv_data.setdefault(str(cfv.participant_id), []).append({
                "field_id": str(cfv.field_id),
                "value": cfv.value,
            })

    # ── Load allocation structure ──
    cat_result = await db.execute(
        select(AllocationCategory)
        .where(AllocationCategory.event_id == event_id)
        .order_by(AllocationCategory.sort_order)
    )
    categories = list(cat_result.scalars().all())
    category_ids = [c.id for c in categories]

    units: list[AllocationUnit] = []
    if category_ids:
        unit_result = await db.execute(
            select(AllocationUnit)
            .where(AllocationUnit.category_id.in_(category_ids))
            .order_by(AllocationUnit.sort_order)
        )
        units = list(unit_result.scalars().all())

    unit_ids = [u.id for u in units]
    allocations: list[Allocation] = []
    # v0.50r: in structure mode we keep units (the template) but skip
    # the allocations (which link participant→unit).
    if unit_ids and not structure_only:
        alloc_result = await db.execute(
            select(Allocation).where(Allocation.unit_id.in_(unit_ids))
        )
        allocations = list(alloc_result.scalars().all())

    # ── Load marks ──
    mark_result = await db.execute(
        select(MarkDefinition).where(MarkDefinition.event_id == event_id)
    )
    mark_defs = list(mark_result.scalars().all())

    mark_assignments: list[MarkAssignment] = []
    if participant_ids:
        ma_result = await db.execute(
            select(MarkAssignment).where(MarkAssignment.event_id == event_id)
        )
        mark_assignments = list(ma_result.scalars().all())

    # ── Load preferences ──
    # v0.50r: preferences link participant→preferred_participant. Skipped
    # entirely in structure mode.
    preferences: list[ParticipantPreferenceRequest] = []
    if not structure_only:
        pref_result = await db.execute(
            select(ParticipantPreferenceRequest)
            .where(ParticipantPreferenceRequest.event_id == event_id)
        )
        preferences = list(pref_result.scalars().all())

    # ── Load field configs (registration form visibility) ──
    fc_result = await db.execute(
        select(EventFieldConfig).where(EventFieldConfig.event_id == event_id)
    )
    field_configs = list(fc_result.scalars().all())

    # ── Load published notes ──
    note_result = await db.execute(
        select(Note).where(
            Note.notable_id == event_id,
            Note.is_published.is_(True),
        )
    )
    notes = list(note_result.scalars().all())

    # ── Build participants CSV ──
    csv_buf = io.StringIO()
    csv_cols = [
        "id", "first_name", "last_name", "email", "gender", "date_of_birth",
        "phone", "address", "country", "church_organisation", "message",
        "group_code", "group_code_categories", "participant_number",
        "registration_status", "gdpr_consent", "checked_in", "preferred_language",
        "created_at",
    ]
    writer = csv.DictWriter(csv_buf, fieldnames=csv_cols, lineterminator="\r\n")
    writer.writeheader()
    for p in participants:
        row = {f: _str(getattr(p, f, None)) for f in csv_cols}
        # group_code_categories is a list — serialise as JSON string
        if p.group_code_categories is not None:
            row["group_code_categories"] = json.dumps(p.group_code_categories)
        writer.writerow(row)

    # ── Assemble JSON payloads ──
    event_data = _row(
        event, "id", "name", "description", "location",
        "start_date", "end_date", "status", "created_at", "updated_at",
    )
    event_data["settings"] = event.settings or {}
    event_data["status"] = event.status.value if hasattr(event.status, "value") else str(event.status)

    custom_fields_data = {
        "definitions": [
            _row(cf, "id", "event_id", "label", "field_type", "is_required", "sort_order", "created_at")
            | {"options": cf.options}
            for cf in cf_defs
        ],
        "values": cfv_data,
    }

    categories_data = [
        _row(cat, "id", "event_id", "name", "item_label", "description",
             "rule_type", "has_capacity", "has_gender_restriction",
             "sort_order", "is_default", "created_at")
        | {"settings": cat.settings or {}}
        for cat in categories
    ]

    units_data = [
        _row(u, "id", "category_id", "name", "description",
             "capacity", "gender_restriction", "sort_order", "created_at")
        for u in units
    ]

    allocations_data = [
        _row(a, "id", "event_id", "participant_id", "unit_id", "created_at")
        for a in allocations
    ]

    marks_data = {
        "definitions": [
            _row(m, "id", "event_id", "name", "colour", "created_at")
            | {"visible_in": m.visible_in}
            for m in mark_defs
        ],
        "assignments": [
            _row(ma, "id", "mark_id", "participant_id", "event_id", "created_at")
            for ma in mark_assignments
        ],
    }

    field_configs_data = [
        _row(fc, "id", "event_id", "field_name", "is_enabled", "is_required", "created_at")
        for fc in field_configs
    ]

    preferences_data = [
        _row(pr, "id", "event_id", "participant_id",
             "preferred_participant_number", "preferred_name",
             "preferred_details", "resolved", "created_at")
        | {"category_scope": pr.category_scope}
        for pr in preferences
    ]

    notes_data = [
        _row(n, "id", "notable_type", "notable_id",
             "content", "is_published", "author_id", "created_at")
        for n in notes
    ]

    manifest = {
        "backup_version": BACKUP_VERSION,
        # v0.50r: mode indicates whether this is a full backup (all data,
        # including PII) or a GDPR-safe structure-only template (no
        # participants, allocations, mark assignments, preferences, or
        # custom field values). Restore logic handles both transparently
        # — structure-mode ZIPs have empty lists for participant-linked
        # files which iterate to no-ops.
        "backup_mode": mode,
        "event_id": str(event_id),
        "event_name": event.name,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "counts": {
            "participants": len(participants),
            "custom_field_definitions": len(cf_defs),
            "allocation_categories": len(categories),
            "allocation_units": len(units),
            "allocations": len(allocations),
            "mark_definitions": len(mark_defs),
            "mark_assignments": len(mark_assignments),
            "preferences": len(preferences),
            "field_configs": len(field_configs),
            "notes": len(notes),
        },
    }

    # ── Write ZIP in memory ──
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        zf.writestr("event.json", json.dumps(event_data, indent=2, ensure_ascii=False))
        zf.writestr("participants.csv", "\ufeff" + csv_buf.getvalue())  # BOM for Excel
        zf.writestr("custom_fields.json", json.dumps(custom_fields_data, indent=2, ensure_ascii=False))
        zf.writestr("allocation_categories.json", json.dumps(categories_data, indent=2, ensure_ascii=False))
        zf.writestr("allocation_units.json", json.dumps(units_data, indent=2, ensure_ascii=False))
        zf.writestr("allocations.json", json.dumps(allocations_data, indent=2, ensure_ascii=False))
        zf.writestr("marks.json", json.dumps(marks_data, indent=2, ensure_ascii=False))
        zf.writestr("field_configs.json", json.dumps(field_configs_data, indent=2, ensure_ascii=False))
        zf.writestr("preferences.json", json.dumps(preferences_data, indent=2, ensure_ascii=False))
        zf.writestr("notes.json", json.dumps(notes_data, indent=2, ensure_ascii=False))

    return buf.getvalue()


# ── Restore ───────────────────────────────────────────────────────────────────

def _parse_zip(content: bytes) -> dict:
    """
    Parse a backup ZIP and return a dict of all file contents.
    Raises ValueError if the ZIP is invalid or missing required files.
    """
    required = {"manifest.json", "event.json", "participants.csv",
                "custom_fields.json", "field_configs.json",
                "allocation_categories.json",
                "allocation_units.json", "allocations.json",
                "marks.json", "preferences.json", "notes.json"}

    try:
        buf = io.BytesIO(content)
        zf = zipfile.ZipFile(buf, "r")
    except zipfile.BadZipFile:
        raise MoimioAppError("errors.export.invalid_zip", status_code=422)

    names = set(zf.namelist())
    missing = required - names
    if missing:
        raise MoimioAppError("errors.export.zip_missing_files", params={"files": ", ".join(sorted(missing))}, status_code=422)

    data = {}
    for name in required:
        raw = zf.read(name)
        if name.endswith(".json"):
            data[name] = json.loads(raw.decode("utf-8"))
        else:
            # CSV — decode stripping BOM
            data[name] = raw.decode("utf-8-sig")
    zf.close()
    return data


def preview_restore(content: bytes) -> dict:
    """
    Parse a backup ZIP and return a summary without writing anything to the DB.

    Returns:
        {
            event_name: str,
            exported_at: str,
            backup_version: str,
            backup_mode: "full" | "structure" (v0.50r — structure backups
                        contain no PII; older backups without this field
                        are implicitly "full"),
            counts: { participants, allocation_categories, ... }
        }
    """
    data = _parse_zip(content)
    manifest = data["manifest.json"]
    return {
        "event_name": manifest.get("event_name", "Unknown"),
        "exported_at": manifest.get("exported_at"),
        "backup_version": manifest.get("backup_version"),
        "backup_mode": manifest.get("backup_mode", "full"),
        "counts": manifest.get("counts", {}),
    }


async def confirm_restore(content: bytes, db: AsyncSession) -> dict:
    """
    Parse a backup ZIP and create a new event with fresh UUIDs.

    All relationships are re-keyed so the restored event is completely
    independent of the original. Returns the new event id and counts.
    """
    from app.models.allocation import Allocation
    from app.models.allocation_category import AllocationCategory
    from app.models.allocation_unit import AllocationUnit
    from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
    from app.models.event import Event, EventStatus
    from app.models.mark import MarkDefinition, MarkAssignment
    from app.models.note import Note
    from app.models.participant import Participant, RegistrationStatus
    from app.models.event_field_config import EventFieldConfig
    from app.models.preference_request import ParticipantPreferenceRequest

    data = _parse_zip(content)
    event_src = data["event.json"]

    # ── ID remap tables ──
    participant_map: dict[str, uuid.UUID] = {}  # old_id → new_id
    category_map: dict[str, uuid.UUID] = {}
    unit_map: dict[str, uuid.UUID] = {}
    mark_map: dict[str, uuid.UUID] = {}
    cf_map: dict[str, uuid.UUID] = {}           # custom field definition old → new

    counts = {"participants": 0, "allocations": 0, "marks_assigned": 0,
              "categories": 0, "units": 0}

    # ── Create event ──
    new_event_id = uuid.uuid4()
    # Append "(Restored)" to name to make it distinguishable
    new_name = event_src.get("name", "Restored Event") + " (Restored)"
    # Restore as DRAFT regardless of original status
    event = Event(
        id=new_event_id,
        name=new_name,
        description=event_src.get("description"),
        location=event_src.get("location"),
        start_date=_parse_date(event_src.get("start_date")),
        end_date=_parse_date(event_src.get("end_date")),
        status=EventStatus.DRAFT,
        settings=event_src.get("settings") or {},
        created_by=new_event_id,  # placeholder — no original user in new install
    )
    db.add(event)
    await db.flush()

    # ── Custom field definitions ──
    cf_data = data["custom_fields.json"]
    for cf_src in cf_data.get("definitions", []):
        new_cf_id = uuid.uuid4()
        cf_map[cf_src["id"]] = new_cf_id
        cf = CustomFieldDefinition(
            id=new_cf_id,
            event_id=new_event_id,
            label=cf_src["label"],
            field_type=cf_src["field_type"],
            options=cf_src.get("options"),
            is_required=cf_src.get("is_required", False),
            sort_order=cf_src.get("sort_order", 0),
        )
        db.add(cf)
    await db.flush()

    # ── Field configs (registration form settings) ──
    for fc_src in data["field_configs.json"]:
        fc = EventFieldConfig(
            event_id=new_event_id,
            field_name=fc_src["field_name"],
            is_enabled=fc_src.get("is_enabled", False),
            is_required=fc_src.get("is_required", False),
        )
        db.add(fc)
    await db.flush()

    # ── Participants ──
    cf_values_src = cf_data.get("values", {})  # old_participant_id → [{field_id, value}]
    reader = csv.DictReader(io.StringIO(data["participants.csv"]))
    for row in reader:
        new_p_id = uuid.uuid4()
        participant_map[row["id"]] = new_p_id

        reg_status = _safe_enum(RegistrationStatus, row.get("registration_status"), RegistrationStatus.CONFIRMED)
        p = Participant(
            id=new_p_id,
            event_id=new_event_id,
            first_name=row.get("first_name") or "",
            last_name=row.get("last_name") or "",
            email=row.get("email") or "",
            gender=row.get("gender") or None,
            date_of_birth=_parse_date(row.get("date_of_birth")),
            phone=row.get("phone") or None,
            address=row.get("address") or None,
            country=row.get("country") or None,
            church_organisation=row.get("church_organisation") or None,
            message=row.get("message") or None,
            group_code=row.get("group_code") or None,
            group_code_categories=_parse_json_field(row.get("group_code_categories")),
            participant_number=_parse_int(row.get("participant_number")),
            registration_status=reg_status,
            gdpr_consent=row.get("gdpr_consent", "").lower() in ("true", "1"),
            checked_in=row.get("checked_in", "").lower() in ("true", "1"),
            preferred_language=row.get("preferred_language") or "en",
        )
        db.add(p)
        counts["participants"] += 1

        # Custom field values for this participant
        for cfv_src in cf_values_src.get(row["id"], []):
            old_field_id = cfv_src.get("field_id")
            new_field_id = cf_map.get(old_field_id)
            if new_field_id:
                cfv = CustomFieldValue(
                    participant_id=new_p_id,
                    field_id=new_field_id,
                    value=cfv_src.get("value"),
                )
                db.add(cfv)

    await db.flush()

    # ── Allocation categories + units ──
    for cat_src in data["allocation_categories.json"]:
        new_cat_id = uuid.uuid4()
        category_map[cat_src["id"]] = new_cat_id
        cat = AllocationCategory(
            id=new_cat_id,
            event_id=new_event_id,
            name=cat_src["name"],
            item_label=cat_src.get("item_label"),
            description=cat_src.get("description"),
            rule_type=cat_src.get("rule_type", "none"),
            has_capacity=cat_src.get("has_capacity", False),
            has_gender_restriction=cat_src.get("has_gender_restriction", False),
            sort_order=cat_src.get("sort_order", 0),
            is_default=cat_src.get("is_default", False),
            settings=cat_src.get("settings") or {},
        )
        db.add(cat)
        counts["categories"] += 1

    await db.flush()

    for unit_src in data["allocation_units.json"]:
        new_unit_id = uuid.uuid4()
        unit_map[unit_src["id"]] = new_unit_id
        new_cat_id = category_map.get(unit_src["category_id"])
        if not new_cat_id:
            continue
        unit = AllocationUnit(
            id=new_unit_id,
            category_id=new_cat_id,
            name=unit_src["name"],
            description=unit_src.get("description"),
            capacity=unit_src.get("capacity"),
            gender_restriction=unit_src.get("gender_restriction"),
            sort_order=unit_src.get("sort_order", 0),
        )
        db.add(unit)
        counts["units"] += 1

    await db.flush()

    # ── Allocations ──
    for alloc_src in data["allocations.json"]:
        new_p_id = participant_map.get(alloc_src["participant_id"])
        new_unit_id = unit_map.get(alloc_src["unit_id"])
        if not new_p_id or not new_unit_id:
            continue
        alloc = Allocation(
            event_id=new_event_id,
            participant_id=new_p_id,
            unit_id=new_unit_id,
        )
        db.add(alloc)
        counts["allocations"] += 1

    await db.flush()

    # ── Marks ──
    marks_src = data["marks.json"]
    for mark_src in marks_src.get("definitions", []):
        new_mark_id = uuid.uuid4()
        mark_map[mark_src["id"]] = new_mark_id
        mark = MarkDefinition(
            id=new_mark_id,
            event_id=new_event_id,
            name=mark_src["name"],
            colour=mark_src.get("colour", "#4682B4"),
            visible_in=mark_src.get("visible_in") or [],
        )
        db.add(mark)

    await db.flush()

    for ma_src in marks_src.get("assignments", []):
        new_p_id = participant_map.get(ma_src["participant_id"])
        new_mark_id = mark_map.get(ma_src["mark_id"])
        if not new_p_id or not new_mark_id:
            continue
        ma = MarkAssignment(
            mark_id=new_mark_id,
            participant_id=new_p_id,
            event_id=new_event_id,
        )
        db.add(ma)
        counts["marks_assigned"] += 1

    await db.flush()

    # ── Preferences ──
    for pref_src in data["preferences.json"]:
        new_p_id = participant_map.get(pref_src.get("participant_id", ""))
        if not new_p_id:
            continue
        pref = ParticipantPreferenceRequest(
            event_id=new_event_id,
            participant_id=new_p_id,
            preferred_participant_number=pref_src.get("preferred_participant_number"),
            preferred_name=pref_src.get("preferred_name"),
            preferred_details=pref_src.get("preferred_details"),
            category_scope=pref_src.get("category_scope"),
            resolved=pref_src.get("resolved", False),
        )
        db.add(pref)

    # ── Notes (published only, attached to new event id) ──
    for note_src in data["notes.json"]:
        note = Note(
            notable_type=note_src.get("notable_type", "event"),
            notable_id=new_event_id,
            content=note_src.get("content", ""),
            is_published=True,
            author_id=new_event_id,  # placeholder — original author not in new install
        )
        db.add(note)

    await db.commit()

    return {
        "new_event_id": str(new_event_id),
        "new_event_name": new_name,
        "counts": counts,
    }


# ── Small helpers ─────────────────────────────────────────────────────────────

def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def _parse_int(value) -> int | None:
    try:
        return int(value) if value not in (None, "", "None") else None
    except (ValueError, TypeError):
        return None


def _parse_json_field(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return None


def _safe_enum(enum_cls, value: str | None, default):
    if not value:
        return default
    try:
        return enum_cls(value)
    except ValueError:
        return default

