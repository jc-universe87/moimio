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
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MoimioAppError
from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_unit import AllocationUnit
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event import Event
from app.models.event_field_config import EventFieldConfig
from app.models.mark import MarkDefinition, MarkAssignment
from app.models.note import Note
from app.models.participant import Participant
from app.models.preference_request import ParticipantPreferenceRequest

BACKUP_VERSION = "1"


# ── The backup register ───────────────────────────────────────────────────────

BACKUP_REGISTER_DOC = """What a backup carries, declared rather than implied.

Every gap the v1.0.4m and backup-completeness investigations found had one
root cause: what a backup contains was decided by hand-written field lists
inside export_event_zip, and nothing checked them. A column added to a model
years later was simply absent from a list nobody re-read, and the loss was
silent in both directions.

So the lists live here instead, as a register. For every event-scoped table,
and for every column of every table the backup carries, the register records
three facts: whether export writes the column, what restore does with it, and
why, whenever the answer is not "carried faithfully".

`export_event_zip` takes its column lists FROM this register, so the register
cannot drift from the export. `tests/test_v1_0_4n_backup_guard.py` fails when
the register disagrees with the schema, or with what the export writes. Adding
a column to a backed-up model, or adding an event-scoped table, therefore
fails a test until somebody records a decision about backups.

RESTORE VERBS — what confirm_restore does with the column:

  copied       the file's value is restored
  remapped     an id, translated through one of the restore's id maps
  parent       set to the restored event
  defaulted    not restored, so the model default applies
  placeholder  restore writes a stand-in value
  ignored      exported, but restore does not use the file's value

  `copied` and `remapped` require the column to be exported.

REASON TAGS — why a column is not carried faithfully:

  secret                    never leaves the instance
  derived                   recoverable from something else the backup holds
  new_id                    restore mints a fresh id, and nothing refers to
                            the old one
  reset_on_restore          a restored event is deliberately a fresh draft
  not_meaningful_elsewhere  the value names something that does not exist on
                            the receiving instance
  instance_state            true of the sending instance, not of the event
  known_gap:BACKUP-n        a real gap, filed under that backlog id

  A reason is required unless the column is exported and `copied` or
  `remapped`, or is `parent`. A `known_gap` tag is allowed on any entry,
  because a copied column can still be wrong: JSON holding stale ids is
  copied faithfully and still restores a rule that no longer works.

**v1.0.5 ships only when no `known_gap` remains.** Each release between now
and then removes its own tags; the register shrinking to zero is the
definition of done, not a judgement call.
"""

RESTORE_VERBS = frozenset({
    "copied", "remapped", "parent", "defaulted", "placeholder", "ignored",
})

REASON_TAGS = frozenset({
    "secret", "derived", "new_id", "reset_on_restore",
    "not_meaningful_elsewhere", "instance_state",
})

KNOWN_GAP_PREFIX = "known_gap:"


class Col(NamedTuple):
    """One column's three facts, plus how export writes it.

    `raw` marks a column export writes by hand rather than through `_row`:
    the JSON columns appended after the `_row` dict, and the custom field
    values, which are keyed by participant instead of listed as rows. They
    are declared so the guard can see them; how they are written is
    unchanged.
    """
    exported: bool
    restore: str
    reason: str | None = None
    raw: bool = False


class Table(NamedTuple):
    """One carried table: its ZIP member, and its key inside that member
    when one member holds two tables (marks.json, custom_fields.json)."""
    member: str
    key: str | None
    columns: dict[str, Col]


# Column order matters: export derives its field lists from this register, so
# the exported columns of each table are declared in exactly the order they
# are written today, `raw` ones last. Columns export does not write follow.

BACKUP_REGISTER: dict[str, Table] = {
    "events": Table("event.json", None, {
        # Exported, in export order.
        "id": Col(True, "ignored", "new_id"),
        # Restore appends " (Restored)", as the restore screen promises; the
        # file's value is still what the new name is built from.
        "name": Col(True, "copied"),
        "description": Col(True, "copied"),
        "location": Col(True, "copied"),
        "start_date": Col(True, "copied"),
        "end_date": Col(True, "copied"),
        "status": Col(True, "ignored", "reset_on_restore"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "updated_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "settings": Col(True, "copied", raw=True),
        # Not exported.
        "timezone": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "details_confirmed": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "registration_confirmed": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "is_archived": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "over_cap_signalled": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "created_by": Col(False, "placeholder", "known_gap:BACKUP-2"),
    }),
    "participants": Table("participants.csv", None, {
        "id": Col(True, "remapped"),
        "first_name": Col(True, "copied"),
        "last_name": Col(True, "copied"),
        "email": Col(True, "copied"),
        "gender": Col(True, "copied"),
        "date_of_birth": Col(True, "copied"),
        "phone": Col(True, "copied"),
        "address": Col(True, "copied"),
        "country": Col(True, "copied"),
        "church_organisation": Col(True, "copied"),
        "message": Col(True, "copied"),
        "group_code": Col(True, "copied"),
        # Copied verbatim, so the list still names pre-restore group types.
        "group_code_categories": Col(True, "copied", "known_gap:BACKUP-3"),
        "participant_number": Col(True, "copied"),
        "registration_status": Col(True, "copied"),
        "gdpr_consent": Col(True, "copied"),
        "checked_in": Col(True, "copied"),
        "preferred_language": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "event_id": Col(False, "parent"),
        "override_group_room": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "confirmation_token": Col(False, "defaulted", "secret"),
        "checked_in_at": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "deleted_at": Col(False, "defaulted", "derived"),
        "updated_at": Col(False, "defaulted", "known_gap:BACKUP-8"),
    }),
    "custom_field_definitions": Table("custom_fields.json", "definitions", {
        "id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "label": Col(True, "copied"),
        "field_type": Col(True, "copied"),
        "is_required": Col(True, "copied"),
        "sort_order": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "options": Col(True, "copied", raw=True),
        "show_in_form": Col(False, "defaulted", "known_gap:BACKUP-2"),
    }),
    "custom_field_values": Table("custom_fields.json", "values", {
        # Written as {old participant id: [{field_id, value}]}, so the
        # participant id is the map key rather than a column in a row.
        "participant_id": Col(True, "remapped", raw=True),
        "field_id": Col(True, "remapped", raw=True),
        "value": Col(True, "copied", raw=True),
        "id": Col(False, "defaulted", "new_id"),
    }),
    "event_field_configs": Table("field_configs.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "event_id": Col(True, "parent"),
        "field_name": Col(True, "copied"),
        "is_enabled": Col(True, "copied"),
        "is_required": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "updated_at": Col(False, "defaulted", "known_gap:BACKUP-8"),
    }),
    "allocation_categories": Table("allocation_categories.json", None, {
        "id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "name": Col(True, "copied"),
        "item_label": Col(True, "copied"),
        "description": Col(True, "copied"),
        "rule_type": Col(True, "copied"),
        # Exported, then forced True on restore. Deprecated since v1.0.3 in
        # the sense that the engine no longer reads them, but the API still
        # accepts and stores False (api/allocations.py CategoryUpdate ->
        # update_category), and the stated reason for keeping the columns is
        # that rolling a workspace back to 1.0.2c must not hide the fields.
        # So a restore can lose a False an older version would read.
        "has_capacity": Col(True, "ignored", "known_gap:BACKUP-2"),
        "has_gender_restriction": Col(True, "ignored", "known_gap:BACKUP-2"),
        "sort_order": Col(True, "copied"),
        "is_default": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        # engine.mark_priorities entries key on a bare mark id.
        "settings": Col(True, "copied", "known_gap:BACKUP-3", raw=True),
        "name_key": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "item_label_key": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "exclusive_group_codes": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "confirmed": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "updated_at": Col(False, "defaulted", "known_gap:BACKUP-8"),
    }),
    "allocation_units": Table("allocation_units.json", None, {
        "id": Col(True, "remapped"),
        "category_id": Col(True, "remapped"),
        "name": Col(True, "copied"),
        "description": Col(True, "copied"),
        "capacity": Col(True, "copied"),
        "gender_restriction": Col(True, "copied"),
        "sort_order": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "mark_restriction": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "is_kept": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "updated_at": Col(False, "defaulted", "known_gap:BACKUP-8"),
    }),
    "allocations": Table("allocations.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "event_id": Col(True, "parent"),
        "participant_id": Col(True, "remapped"),
        "unit_id": Col(True, "remapped"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "updated_at": Col(False, "defaulted", "known_gap:BACKUP-8"),
    }),
    "allocation_category_exclusions": Table("allocation_exclusions.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "allocation_category_id": Col(True, "remapped"),
        "participant_id": Col(True, "remapped"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        # v1.0.4m: NULL on purpose. Nobody on the receiving instance made
        # this decision, and allocation_events is the audit surface anyway.
        "created_by": Col(False, "defaulted", "not_meaningful_elsewhere"),
    }),
    "mark_definitions": Table("marks.json", "definitions", {
        "id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "name": Col(True, "copied"),
        "colour": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "visible_in": Col(True, "copied", raw=True),
        "cluster_behaviour": Col(False, "defaulted", "known_gap:BACKUP-2"),
        "created_by_user_id": Col(False, "defaulted", "known_gap:BACKUP-2"),
    }),
    "mark_assignments": Table("marks.json", "assignments", {
        "id": Col(True, "ignored", "new_id"),
        "mark_id": Col(True, "remapped"),
        "participant_id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "assigned_by_user_id": Col(False, "defaulted", "known_gap:BACKUP-2"),
    }),
    "participant_preference_requests": Table("preferences.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "event_id": Col(True, "parent"),
        "participant_id": Col(True, "remapped"),
        # Points at a participant by participant_number, not by id, and that
        # column is both exported and restored, so the target survives.
        "preferred_participant_number": Col(True, "copied"),
        "preferred_name": Col(True, "copied"),
        "preferred_details": Col(True, "copied"),
        "resolved": Col(True, "copied"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        # "all", or a list of pre-restore group type ids.
        "category_scope": Col(True, "copied", "known_gap:BACKUP-3", raw=True),
        "resolved_note": Col(False, "defaulted", "known_gap:BACKUP-2"),
    }),
    "notes": Table("notes.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "notable_type": Col(True, "copied"),
        # Overwritten with the restored event id instead of being remapped
        # through the participant, category and unit maps.
        "notable_id": Col(True, "parent", "known_gap:BACKUP-4"),
        "content": Col(True, "copied"),
        # Forced True on restore, so an unpublished note would come back
        # published. Unreachable today: no screen writes an event-level note,
        # so the export filter (notable_id == event_id AND is_published)
        # never matches and this member is always empty.
        "is_published": Col(True, "ignored", "known_gap:BACKUP-4"),
        "author_id": Col(True, "placeholder", "known_gap:BACKUP-2"),
        "created_at": Col(True, "ignored", "known_gap:BACKUP-8"),
        "updated_at": Col(False, "defaulted", "known_gap:BACKUP-8"),
    }),
}

# Event-scoped tables the backup does not carry at all.
NOT_CARRIED: dict[str, str] = {
    "checkin_fields": "known_gap:BACKUP-4",
    "checkin_values": "known_gap:BACKUP-4",
    "event_user_assignments": "known_gap:BACKUP-4",
    "allocation_events": "known_gap:BACKUP-5",
}

# Which tables belong to an event is computed by walking the foreign keys to
# `events` (see the guard). These are the references that have no foreign key
# for the walk to follow, so each one is declared here with its reason.
EVENT_SCOPE_OVERRIDES: dict[str, str] = {
    # notes.notable_id is a plain UUID typed by notes.notable_type, pointing
    # at a participant, a group type or a unit. The only foreign key on the
    # table is author_id -> users, so the walk would call notes
    # instance-scoped.
    "notes": "notable_id is a polymorphic UUID with no foreign key",
}


def exported_columns(table: str) -> tuple[str, ...]:
    """Every column export writes for this table, in export order."""
    return tuple(
        name for name, col in BACKUP_REGISTER[table].columns.items()
        if col.exported
    )


def _row_fields(table: str) -> tuple[str, ...]:
    """The columns export passes to `_row`: the exported ones it does not
    write by hand. Same order as `exported_columns`, `raw` ones removed."""
    return tuple(
        name for name, col in BACKUP_REGISTER[table].columns.items()
        if col.exported and not col.raw
    )



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

    ZIP contents (all written; only the eleven pre-v1.0.4m members are
    required on read — see _parse_zip):
        manifest.json          — version, event_id, exported_at, row counts,
                                 backup_mode
        event.json             — event metadata + settings
        participants.csv       — participant rows (EMPTY header-only in structure mode)
        custom_fields.json     — { definitions, values: {} in structure mode }
        allocation_categories.json
        allocation_units.json
        allocations.json       — participant↔unit assignments ([] in structure mode)
        allocation_exclusions.json
                               — v1.0.4m: participant↔group-type exclusions
                                 ([] in structure mode). Optional on read, so
                                 pre-v1.0.4m files still restore.
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

    # ── Load allocation category exclusions ──
    # v1.0.4m: an exclusion keeps one participant out of one group type.
    # It travels with its person: only rows whose participant AND whose
    # group type are both in this export go in. The two lists above are
    # the source of truth, so structure mode (participants emptied) and
    # soft-deleted participants (already filtered out of `participants`)
    # both fall out of the `participant_ids` test with no extra filter.
    exclusions: list[AllocationCategoryExclusion] = []
    if category_ids and participant_ids:
        excl_result = await db.execute(
            select(AllocationCategoryExclusion)
            .where(
                AllocationCategoryExclusion.allocation_category_id.in_(category_ids),
                AllocationCategoryExclusion.participant_id.in_(participant_ids),
            )
            .order_by(
                AllocationCategoryExclusion.created_at,
                AllocationCategoryExclusion.id,
            )
        )
        exclusions = list(excl_result.scalars().all())

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
    csv_cols = list(_row_fields("participants"))
    writer = csv.DictWriter(csv_buf, fieldnames=csv_cols, lineterminator="\r\n")
    writer.writeheader()
    for p in participants:
        row = {f: _str(getattr(p, f, None)) for f in csv_cols}
        # group_code_categories is a list — serialise as JSON string
        if p.group_code_categories is not None:
            row["group_code_categories"] = json.dumps(p.group_code_categories)
        writer.writerow(row)

    # ── Assemble JSON payloads ──
    event_data = _row(event, *_row_fields("events"))
    event_data["settings"] = event.settings or {}
    event_data["status"] = event.status.value if hasattr(event.status, "value") else str(event.status)

    custom_fields_data = {
        "definitions": [
            _row(cf, *_row_fields("custom_field_definitions"))
            | {"options": cf.options}
            for cf in cf_defs
        ],
        "values": cfv_data,
    }

    categories_data = [
        _row(cat, *_row_fields("allocation_categories"))
        | {"settings": cat.settings or {}}
        for cat in categories
    ]

    units_data = [
        _row(u, *_row_fields("allocation_units"))
        for u in units
    ]

    allocations_data = [
        _row(a, *_row_fields("allocations"))
        for a in allocations
    ]

    exclusions_data = [
        _row(x, *_row_fields("allocation_category_exclusions"))
        for x in exclusions
    ]

    marks_data = {
        "definitions": [
            _row(m, *_row_fields("mark_definitions"))
            | {"visible_in": m.visible_in}
            for m in mark_defs
        ],
        "assignments": [
            _row(ma, *_row_fields("mark_assignments"))
            for ma in mark_assignments
        ],
    }

    field_configs_data = [
        _row(fc, *_row_fields("event_field_configs"))
        for fc in field_configs
    ]

    preferences_data = [
        _row(pr, *_row_fields("participant_preference_requests"))
        | {"category_scope": pr.category_scope}
        for pr in preferences
    ]

    notes_data = [
        _row(n, *_row_fields("notes"))
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
            "allocation_exclusions": len(exclusions),
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
        zf.writestr("allocation_exclusions.json", json.dumps(exclusions_data, indent=2, ensure_ascii=False))
        zf.writestr("marks.json", json.dumps(marks_data, indent=2, ensure_ascii=False))
        zf.writestr("field_configs.json", json.dumps(field_configs_data, indent=2, ensure_ascii=False))
        zf.writestr("preferences.json", json.dumps(preferences_data, indent=2, ensure_ascii=False))
        zf.writestr("notes.json", json.dumps(notes_data, indent=2, ensure_ascii=False))

    return buf.getvalue()


# ── Restore ───────────────────────────────────────────────────────────────────

# v1.0.4m: members that may be absent, with the value to use when they are.
# An older file simply has no exclusions in it, which restores as "nobody
# excluded"; see _parse_zip.
_OPTIONAL_MEMBERS: dict[str, list] = {"allocation_exclusions.json": []}


def _parse_zip(content: bytes) -> dict:
    """
    Parse a backup ZIP and return a dict of all file contents.
    Raises ValueError if the ZIP is invalid or missing required files.
    Optional members (_OPTIONAL_MEMBERS) are defaulted when absent.
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

    # v1.0.4m: optional members, read when present and defaulted when not.
    # Deliberately NOT in `required`: a member added there would reject
    # every backup file made before that member existed. A present member
    # that will not parse raises exactly as a required one does — nothing
    # here catches json.loads, so the caller turns it into the same error.
    for name, default in _OPTIONAL_MEMBERS.items():
        if name in names:
            data[name] = json.loads(zf.read(name).decode("utf-8"))
        else:
            # Copy: the default lives on a module constant.
            data[name] = list(default)

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
    # v1.0.4m: new unit id → new group type id. An allocation names a unit,
    # an exclusion names a group type, so deciding whether a placement is
    # excluded needs the step between them.
    unit_category_map: dict[uuid.UUID, uuid.UUID] = {}

    counts = {"participants": 0, "allocations": 0, "marks_assigned": 0,
              "categories": 0, "units": 0, "allocation_exclusions": 0}

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
            name_key=cat_src.get("name_key"),            # v1.0.4
            item_label_key=cat_src.get("item_label_key"),  # v1.0.4
            has_capacity=True,  # v1.0.3: ignored; always on
            has_gender_restriction=True,  # v1.0.3: ignored; always on
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
        unit_category_map[new_unit_id] = new_cat_id
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

    # ── Allocation category exclusions (v1.0.4m) ──
    # Resolved BEFORE the allocations loop, because an exclusion outranks a
    # placement: when a file says someone is both excluded from a group type
    # and placed in it, the exclusion is restored and the placement is not.
    # The rows themselves are written after the allocations block.
    exclusion_rows: list[tuple[uuid.UUID, uuid.UUID]] = []
    excluded_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for excl_src in data["allocation_exclusions.json"]:
        new_p_id = participant_map.get(excl_src.get("participant_id", ""))
        new_cat_id = category_map.get(excl_src.get("allocation_category_id", ""))
        if not new_p_id or not new_cat_id:
            continue
        pair = (new_p_id, new_cat_id)
        # The table is UNIQUE on (group type, participant). A duplicate in a
        # hand-edited file is dropped here: letting one reach the constraint
        # would roll the whole restore back over a single bad line.
        if pair in excluded_pairs:
            continue
        excluded_pairs.add(pair)
        exclusion_rows.append(pair)

    dropped_placements = 0

    # ── Allocations ──
    for alloc_src in data["allocations.json"]:
        new_p_id = participant_map.get(alloc_src["participant_id"])
        new_unit_id = unit_map.get(alloc_src["unit_id"])
        if not new_p_id or not new_unit_id:
            continue
        # v1.0.4m: the exclusion wins, so drop the placement.
        if (new_p_id, unit_category_map.get(new_unit_id)) in excluded_pairs:
            dropped_placements += 1
            continue
        alloc = Allocation(
            event_id=new_event_id,
            participant_id=new_p_id,
            unit_id=new_unit_id,
        )
        db.add(alloc)
        counts["allocations"] += 1

    await db.flush()

    # Written directly, never through add_exclusion: that writes history
    # rows, vacates units and re-opens a confirmed group type. created_at
    # is left to the column's server default, as the participant block
    # leaves it; created_by is NULL because nobody on this instance made
    # the decision, and restore carries attribution for nothing else.
    for new_p_id, new_cat_id in exclusion_rows:
        db.add(AllocationCategoryExclusion(
            allocation_category_id=new_cat_id,
            participant_id=new_p_id,
            created_by=None,
        ))
        counts["allocation_exclusions"] += 1

    await db.flush()

    # One line per restore, only when a placement was actually dropped. No
    # names, emails or participant ids: it exists to explain the count, and
    # the board already shows who is excluded.
    if dropped_placements:
        print(
            f"[RESTORE WARNING] event {new_event_id}: {dropped_placements} "
            f"placement(s) not restored because the participant is excluded "
            f"from that group type",
            flush=True,
        )

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

