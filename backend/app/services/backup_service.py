"""Backup service — event export and restore (data portability).

Export: builds a ZIP in memory containing JSON/CSV files for every
        entity belonging to an event.

Restore: parses a ZIP, previews counts, then creates a new event with
         all entities re-keyed to fresh UUIDs.
"""

import copy
import csv
import io
import json
import uuid
import zipfile
from datetime import datetime, date
from typing import NamedTuple

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.default_type_names import ITEM_LABEL_KEYS, NAME_KEYS
from app.core.exceptions import MoimioAppError
from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_event import (
    AllocationEvent,
    AllocationEventSource,
    AllocationEventType,
)
from app.models.allocation_unit import AllocationUnit
from app.models.checkin_field import CheckInField
from app.models.checkin_value import CheckInValue
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
        "created_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
        # v1.0.4q: new exported columns sit after the existing non-raw ones
        # and before the raw ones, because a raw column is appended to the
        # dict by hand after `_row` has run. That keeps every existing key
        # where it was and keeps the guard's export check true.
        "timezone": Col(True, "copied"),
        "is_archived": Col(True, "copied"),
        # v1.0.4s: a structure backup leaves email_from_name and
        # email_reply_to out of this dict, and a full backup keeps both
        # (BACKUP-11). The register records one decision per column and
        # cannot express a key inside a JSON column, let alone one that
        # depends on the mode, so it is written here instead.
        "settings": Col(True, "copied", raw=True),
        # Not exported.
        # The organiser re-ticks both Setup cards before reopening
        # registration, and every ordinary edit already clears them.
        "details_confirmed": Col(False, "defaulted", "reset_on_restore"),
        "registration_confirmed": Col(False, "defaulted", "reset_on_restore"),
        # The sending instance's plan-enforcement state, not the event's.
        "over_cap_signalled": Col(False, "defaulted", "instance_state"),
        # v1.0.4q: the restoring user when there is one. The original user
        # has no account here, so their id would name nobody.
        "created_by": Col(False, "placeholder", "not_meaningful_elsewhere"),
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
        # v1.0.4p: the group type ids inside are translated in place.
        # Retired in v1.0.4r; carried until the column is dropped, so that a
        # backup, the GDPR export and the database agree on what is stored.
        "group_code_categories": Col(True, "remapped"),
        "participant_number": Col(True, "copied"),
        "registration_status": Col(True, "copied"),
        "gdpr_consent": Col(True, "copied"),
        "checked_in": Col(True, "copied"),
        "preferred_language": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        # v1.0.4q. These three are the last columns of participants.csv, so
        # no existing cell moves. None of them can contain a comma, which
        # matters: test_v1_0_4o_damaged_files.py edits the first data row
        # with a plain split on ",".
        "override_group_room": Col(True, "copied"),
        "checked_in_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
        "event_id": Col(False, "parent"),
        "confirmation_token": Col(False, "defaulted", "secret"),
        "deleted_at": Col(False, "defaulted", "derived"),
    }),
    "custom_field_definitions": Table("custom_fields.json", "definitions", {
        "id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "label": Col(True, "copied"),
        "field_type": Col(True, "copied"),
        "is_required": Col(True, "copied"),
        "sort_order": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        # v1.0.4q: False marks a field admin-only, so losing it put
        # CSV-import fields back on the public registration form.
        "show_in_form": Col(True, "copied"),
        "options": Col(True, "copied", raw=True),
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
        "created_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
    }),
    # v1.0.4s: check-in. Two tables in one member, like marks.json. The
    # fields are the columns an organiser added to the check-in desk; the
    # values are one tick per person per column. Restore writes the fields
    # straight after the field configs, and the values straight after the
    # participants, which is where each one's references exist.
    "checkin_fields": Table("checkin.json", "fields", {
        "id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "field_name": Col(True, "copied"),
        "sort_order": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
    }),
    "checkin_values": Table("checkin.json", "values", {
        # Nothing refers to a value row, so its id is minted fresh.
        "id": Col(True, "ignored", "new_id"),
        "event_id": Col(True, "parent"),
        "participant_id": Col(True, "remapped"),
        "field_id": Col(True, "remapped"),
        "checked": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
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
        # So a restore could lose a False an older version would read. The
        # code keeps these retired flags true for rollback safety, so restore
        # goes on forcing True rather than fighting it.
        "has_capacity": Col(True, "ignored", "reset_on_restore"),
        "has_gender_restriction": Col(True, "ignored", "reset_on_restore"),
        "sort_order": Col(True, "copied"),
        "is_default": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        # v1.0.4q. Only a key the app knows is restored; anything else
        # becomes NULL, which is how the stored name shows through.
        "name_key": Col(True, "copied"),
        "item_label_key": Col(True, "copied"),
        "exclusive_group_codes": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
        # v1.0.4p: engine.mark_priorities entries key on a bare mark id, and
        # those ids are translated in place; every other key passes through.
        "settings": Col(True, "remapped", raw=True),
        # A restored event is a fresh draft, and every edit clears this
        # anyway, so the organiser signs each group type off again.
        "confirmed": Col(False, "defaulted", "reset_on_restore"),
    }),
    "allocation_units": Table("allocation_units.json", None, {
        "id": Col(True, "remapped"),
        "category_id": Col(True, "remapped"),
        "name": Col(True, "copied"),
        "description": Col(True, "copied"),
        "capacity": Col(True, "copied"),
        "gender_restriction": Col(True, "copied"),
        "sort_order": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        # v1.0.4q: a real foreign key to mark_definitions, so a dead id
        # cannot be written. v1.0.4p put marks before units, which is what
        # makes `mark_map` available here.
        "mark_restriction": Col(True, "remapped"),
        "is_kept": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
    }),
    "allocations": Table("allocations.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "event_id": Col(True, "parent"),
        "participant_id": Col(True, "remapped"),
        "unit_id": Col(True, "remapped"),
        "created_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
    }),
    "allocation_category_exclusions": Table("allocation_exclusions.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "allocation_category_id": Col(True, "remapped"),
        "participant_id": Col(True, "remapped"),
        "created_at": Col(True, "copied"),
        # v1.0.4m: NULL on purpose. Nobody on the receiving instance made
        # this decision, and allocation_events is the audit surface anyway.
        "created_by": Col(False, "defaulted", "not_meaningful_elsewhere"),
    }),
    "mark_definitions": Table("marks.json", "definitions", {
        "id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "name": Col(True, "copied"),
        "colour": Col(True, "copied"),
        "created_at": Col(True, "copied"),
        # v1.0.4q: only one of the app's own three values is restored.
        "cluster_behaviour": Col(True, "copied"),
        "visible_in": Col(True, "copied", raw=True),
        # NULL is already the modelled "system mark", and the screen renders
        # it. The original user has no account on this instance.
        "created_by_user_id": Col(False, "defaulted", "not_meaningful_elsewhere"),
    }),
    "mark_assignments": Table("marks.json", "assignments", {
        "id": Col(True, "ignored", "new_id"),
        "mark_id": Col(True, "remapped"),
        "participant_id": Col(True, "remapped"),
        "event_id": Col(True, "parent"),
        "created_at": Col(True, "copied"),
        "assigned_by_user_id": Col(False, "defaulted", "not_meaningful_elsewhere"),
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
        "created_at": Col(True, "copied"),
        # v1.0.4q: `resolved` without its note said a request was settled
        # and gave no reason.
        "resolved_note": Col(True, "copied"),
        # v1.0.4p: "all" passes through; a list of group type ids is
        # translated in place.
        # Retired in v1.0.4r; carried until the column is dropped, so that a
        # backup, the GDPR export and the database agree on what is stored.
        "category_scope": Col(True, "remapped", raw=True),
    }),
    "notes": Table("notes.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "notable_type": Col(True, "copied"),
        # v1.0.4s: translated by its type, through the participant, group
        # type and unit maps, and set to the restored event for an
        # event-level note. A note whose type is not one of those four, or
        # whose target the file does not carry, is skipped and counted.
        "notable_id": Col(True, "remapped"),
        "content": Col(True, "copied"),
        # v1.0.4s: carried as it is. It was forced True on restore, so a
        # private note came back published, which is the opposite of what
        # its author chose. Which private notes are exported at all is the
        # caller's choice: see `private_notes` on export_event_zip.
        "is_published": Col(True, "copied"),
        # v1.0.4o: the restoring user. The original author has no account
        # on this instance, and the column is a real foreign key.
        "author_id": Col(True, "placeholder", "not_meaningful_elsewhere"),
        "created_at": Col(True, "copied"),
        "updated_at": Col(True, "copied"),
    }),
    # v1.0.4t: the history. Written last on restore, because a row can name
    # a participant, a unit, a group type and — inside `meta` — a mark.
    "allocation_events": Table("allocation_events.json", None, {
        "id": Col(True, "ignored", "new_id"),
        "event_id": Col(True, "parent"),
        # A row whose participant does not resolve is skipped: history is
        # about somebody, and export only carries rows about exported
        # people in the first place.
        "participant_id": Col(True, "remapped"),
        # A unit or group type that does not resolve becomes NULL, which is
        # what the database itself does when the row is deleted
        # (ON DELETE SET NULL). The name snapshots keep the line readable.
        "unit_id": Col(True, "remapped"),
        "category_id": Col(True, "remapped"),
        "event_type": Col(True, "copied"),
        "source": Col(True, "copied"),
        "unit_name_snapshot": Col(True, "copied"),
        "category_name_snapshot": Col(True, "copied"),
        "action_id": Col(True, "copied"),
        "occurred_at": Col(True, "copied"),
        # v1.0.4t: the ids inside `meta` are translated by the v1.0.4p
        # rule. Written by hand because export also drops the names of
        # people this backup does not carry (§4.5).
        "meta": Col(True, "remapped", raw=True),
        # The only true answer: that account does not exist here. The
        # column is nullable by design and the history screen already
        # renders a missing actor as a removed user.
        "actor_user_id": Col(False, "defaulted", "not_meaningful_elsewhere"),
    }),
}

# Event-scoped tables the backup does not carry at all.
NOT_CARRIED: dict[str, str] = {
    # v1.0.4s: a permission must never come from a file. Who may see or
    # change an event is decided on the receiving instance, by inviting the
    # team again; the restore screen says so (STRINGS-1).
    #
    # v1.0.4u: the whole-workspace export carries the team as a reference
    # list (`team.json`), per-event roles included, so a customer leaving
    # can see who had what. It is a list to read, not a list to apply:
    # restore never reads it, and this entry is unchanged by it.
    "event_user_assignments": "not_meaningful_elsewhere",
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


# ── Reading a damaged line (v1.0.4o) ─────────────────────────────────────────
#
# A backup is a plain unsigned ZIP, so a hand-edited or truncated file is
# expected input. One damaged line costs that line and whatever depends on
# it, never the whole file.
#
# The rules, in one place:
#
#   - A missing key and an explicit null are the same thing. In the
#     participants CSV a blank cell means the same again.
#   - A damaged value falls back to the column's own default, read from the
#     model so it cannot drift. Restore never invents a value the model does
#     not define.
#   - A NOT NULL column with no model default means the line is skipped.
#   - Over-long text is shortened to the column's declared length.
#   - An empty or missing old id is never a map key: the row is still
#     created, but nothing can refer to it.

_SKIP = object()


def _column(table: str, name: str):
    return Base.metadata.tables[table].columns[name]


def _column_default(table: str, name: str):
    """(has_default, value) for a column's own Python-side default."""
    col = _column(table, name)
    if col.default is None:
        return False, None
    arg = col.default.arg
    if callable(arg):
        try:
            return True, arg(None)
        except TypeError:
            return True, arg()
    return True, arg


def _field(src, key: str, table: str, column: str, *, blank_is_null: bool = False):
    """One field of one line. Returns the value to write, or `_SKIP` when
    the line cannot be written at all. See the rules above."""
    raw = src.get(key) if isinstance(src, dict) else None
    if raw == "" and blank_is_null:
        raw = None
    if raw is None:
        has_default, default = _column_default(table, column)
        if has_default:
            return default
        return None if _column(table, column).nullable else _SKIP
    return raw


# v1.0.4q: the values the app itself accepts for two restored columns.
#
# `cluster_behaviour` is declared as "'together' | 'split' | 'none' (default)"
# at the write schema (api/marks.py) and enforced verbatim for the identical
# value in the per-group-type override path (engine_service, where anything
# else "is silently skipped"). The mark write path does NOT enforce it, so
# restore is very slightly stricter than the API here; an out-of-set value is
# inert either way, because the engine dispatches on equality.
CLUSTER_BEHAVIOURS: frozenset[str] = frozenset({"together", "split", "none"})

# `name_key` and `item_label_key` take only the app's own keys, and the two
# fields have separate sets on purpose: "a default typed into one must never
# attach the other's key" (core/default_type_names.py).
ACCEPTED_KEYS: dict[str, frozenset[str]] = {
    "name_key": frozenset(NAME_KEYS),
    "item_label_key": frozenset(ITEM_LABEL_KEYS),
}


def _parse_datetime(value):
    """A timestamp out of a backup file, or None when it cannot be used.

    v1.0.4q. Separate from `_parse_date`, which serves the date columns and
    deliberately truncates to ten characters.

    Only a timezone-aware value is accepted. Every timestamp column in the
    schema is `DateTime(timezone=True)`, and export writes `isoformat()`, so
    an app-made file always carries the offset. A naive value would be
    written as though it were UTC, which is a guess, so it counts as damage
    and the model default applies instead.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip())
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        return None
    return parsed


def _old_id(src, key: str) -> str | None:
    """The old id a line carries, or None when it is missing or blank.
    None is never used as a map key (rule 4 above)."""
    raw = src.get(key) if isinstance(src, dict) else None
    if raw is None:
        return None
    raw = str(raw).strip()
    return raw or None


# ── Ids that live inside a JSON column (v1.0.4p) ─────────────────────────────
#
# Three columns hold ids inside JSON rather than in a column of their own, so
# restore's id maps cannot reach them by the ordinary route:
#
#   participants.group_code_categories              group type ids, or null
#   participant_preference_requests.category_scope  group type ids, or "all"
#   allocation_categories.settings                  mark ids, under
#                                                   engine.mark_priorities
#
# THE RULE: translate every id the maps know. Leave every other value exactly
# as the file has it, in place. Order and length never change, and nothing is
# added or dropped.
#
# "Every other value" means null, "all", ids the maps do not know, and
# elements of an unexpected type.
#
# Why not drop what cannot be translated: to the engine a list of ids that
# resolve to nothing means "applies nowhere", while an EMPTY list means
# "applies everywhere" — `if scope and cat_id_str not in ...` in
# engine_service is a falsy check, and its own comment reads "default = all
# categories". Emptying such a list would therefore invert the rule instead
# of losing it. Leaving the untranslatable in place keeps every reader's
# behaviour identical to what it was before the backup, whatever the list
# holds.
#
# In a file the app produced every id resolves, because export carries every
# group type and every mark. An id that does not resolve was already dead
# before the backup was taken, which is a live-data question and not a
# backup gap.


def _translate_id(value, id_map: dict[str, uuid.UUID]):
    """One id string, translated if the map knows it, otherwise untouched."""
    if not isinstance(value, str):
        return value
    new = id_map.get(value.strip())
    return str(new) if new is not None else value


def _translate_id_list(value, id_map: dict[str, uuid.UUID]):
    """A JSON column holding a list of ids. Anything that is not a list —
    null, "all" — comes back exactly as it went in."""
    if not isinstance(value, list):
        return value
    return [_translate_id(v, id_map) for v in value]


def _translate_mark_priorities(settings, mark_map: dict[str, uuid.UUID]):
    """The mark ids inside a group type's `settings.engine.mark_priorities`.

    Only an entry's id is ever translated. Every other key in an entry,
    every entry whose mark the map does not know, and every other settings
    key are left exactly as they are.

    Both on-disk entry shapes the engine accepts are handled: a bare id
    string (legacy) and `{"id": ..., "behaviour": ...}`. The shape is
    preserved either way.

    Ids here are bare. The `mark:` prefix belongs to history `meta` and is
    never added or stripped.
    """
    if not isinstance(settings, dict):
        return settings
    engine = settings.get("engine")
    if not isinstance(engine, dict):
        return settings
    entries = engine.get("mark_priorities")
    if not isinstance(entries, list):
        return settings

    translated = []
    for entry in entries:
        if isinstance(entry, str):
            translated.append(_translate_id(entry, mark_map))
        elif isinstance(entry, dict) and isinstance(entry.get("id"), str):
            # Keeps every other key, and `id` in its original position.
            translated.append({**entry, "id": _translate_id(entry["id"], mark_map)})
        else:
            translated.append(entry)

    out = copy.deepcopy(settings)
    out["engine"]["mark_priorities"] = translated
    return out


# ── Ids inside a history row's `meta` (v1.0.4t) ──────────────────────────────
#
# One writer fills `meta`: `commit_proposal` in engine_service, as
# `{"run_id": <engine run>, "placement": <that person's placement reason>}`,
# either key optional. The placement reason is whatever the engine recorded,
# and these are the parts of it that hold an id:
#
#   unit_id, from_unit_id, to_unit_id     a unit
#   mark_id, mark_restriction             a mark, bare, with no prefix
#   cluster_members[].id                  a participant; the `name` beside
#                                         it is a snapshot, left as it is
#   previous                              any of the above again, nested
#                                         (the equalising sweep wraps the
#                                         original reason in it)
#   run_id                                an engine run, not a row: left
#
# `cluster_id` needs the reason to decide, and it is the trap in this
# column:
#
#   reason mark_together / mark_together_split  the value is
#                                               "mark:<mark id>", so the id
#                                               is translated and the
#                                               prefix kept exactly
#   reason group_code / group_code_split        the value IS the group code,
#                                               free organiser text that may
#                                               legitimately begin with
#                                               "mark:". Never translated,
#                                               and nothing stripped from it
#   any other reason                            left alone
#
# The v1.0.4p rule applies throughout: translate every id the maps know, and
# leave every other value exactly as the file has it.

_META_UNIT_KEYS = ("unit_id", "from_unit_id", "to_unit_id")
_META_MARK_KEYS = ("mark_id", "mark_restriction")
_MARK_CLUSTER_REASONS = frozenset({"mark_together", "mark_together_split"})
_MARK_CLUSTER_PREFIX = "mark:"


def _translate_placement(
    placement,
    *,
    participant_map: dict[str, uuid.UUID],
    unit_map: dict[str, uuid.UUID],
    mark_map: dict[str, uuid.UUID],
):
    """One placement reason, with every id the maps know translated."""
    if not isinstance(placement, dict):
        return placement
    out = dict(placement)

    for key in _META_UNIT_KEYS:
        if key in out:
            out[key] = _translate_id(out[key], unit_map)
    for key in _META_MARK_KEYS:
        if key in out:
            out[key] = _translate_id(out[key], mark_map)

    members = out.get("cluster_members")
    if isinstance(members, list):
        out["cluster_members"] = [
            {**m, "id": _translate_id(m["id"], participant_map)}
            if isinstance(m, dict) and isinstance(m.get("id"), str) else m
            for m in members
        ]

    cluster_id = out.get("cluster_id")
    if (
        out.get("reason") in _MARK_CLUSTER_REASONS
        and isinstance(cluster_id, str)
        and cluster_id.startswith(_MARK_CLUSTER_PREFIX)
    ):
        bare = cluster_id[len(_MARK_CLUSTER_PREFIX):]
        out["cluster_id"] = _MARK_CLUSTER_PREFIX + _translate_id(bare, mark_map)

    if "previous" in out:
        out["previous"] = _translate_placement(
            out["previous"], participant_map=participant_map,
            unit_map=unit_map, mark_map=mark_map,
        )
    return out


def _translate_history_meta(
    meta,
    *,
    participant_map: dict[str, uuid.UUID],
    unit_map: dict[str, uuid.UUID],
    mark_map: dict[str, uuid.UUID],
):
    """A history row's `meta`, with the ids inside it translated."""
    if not isinstance(meta, dict) or "placement" not in meta:
        return meta
    return {
        **meta,
        "placement": _translate_placement(
            meta["placement"], participant_map=participant_map,
            unit_map=unit_map, mark_map=mark_map,
        ),
    }


def _scrub_placement(placement, exported: set[str]):
    """Drop cluster members this export does not carry.

    `cluster_members` names everyone who was placed together, and some of
    them may not be in this backup: removed people, or a structure-mode
    export. Personal data travels with its person, so their names come out.

    The counts beside the list — `cluster_size`, `cluster_placed_here` —
    are left exactly as they are. They describe what happened. A line may
    therefore say five and name three, which is truthful; changing the
    numbers would not be.
    """
    if not isinstance(placement, dict):
        return placement
    out = dict(placement)
    members = out.get("cluster_members")
    if isinstance(members, list):
        out["cluster_members"] = [
            m for m in members
            # An entry with no id names nobody, so there is nobody to drop.
            if not (isinstance(m, dict) and isinstance(m.get("id"), str))
            or m["id"] in exported
        ]
    if "previous" in out:
        out["previous"] = _scrub_placement(out["previous"], exported)
    return out


def _scrub_history_meta(meta, exported: set[str]):
    """A history row's `meta` as the file may carry it."""
    if not isinstance(meta, dict) or "placement" not in meta:
        return meta
    return {**meta, "placement": _scrub_placement(meta["placement"], exported)}


# ── Export ────────────────────────────────────────────────────────────────────

# v1.0.4s: who may see a private note decides what a backup may carry.
#
# A private note is visible in the app only to its author: not to a
# colleague, and not to a Super Admin. Any event admin can download an event
# backup. So the caller has to say whose private notes belong in the file,
# and the default says nobody, which means a caller that makes no choice
# cannot leak one.
#
#   private_notes=None                  published notes only (the default)
#   private_notes=<user id>             that user's private notes as well
#   private_notes=ALL_PRIVATE_NOTES     every private note
#
# The last one belongs to the leaving export, which is the organisation's
# own copy of its data and is produced from a shell that already has full
# database access.


class _EveryPrivateNote:
    """The type of `ALL_PRIVATE_NOTES`.

    A sentinel object rather than a string, so that no stray value can be
    mistaken for the choice to carry every private note.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "ALL_PRIVATE_NOTES"


ALL_PRIVATE_NOTES = _EveryPrivateNote()


async def export_event_zip(
    event_id: uuid.UUID,
    db: AsyncSession,
    mode: str = "full",
    private_notes: "uuid.UUID | _EveryPrivateNote | None" = None,
) -> bytes:
    """
    Build a backup ZIP for one event and return the raw bytes.

    Args:
        event_id — event to back up
        db — async DB session
        mode — "full" (default, everything) or "structure" (v0.50r, GDPR-safe:
               event settings, categories, units, custom field definitions,
               mark definitions, field configs, check-in columns; NO
               participant PII, custom-field values, allocations, mark
               assignments, preferences tied to a participant, check-in
               ticks, or notes of any kind)
        private_notes — whose private notes the file may carry. None (the
               default) carries none, a user id carries that user's own, and
               ALL_PRIVATE_NOTES carries every one. Published notes are
               carried whatever this says. See the note above the sentinel.

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
        notes.json             — v1.0.4s: notes on the event, on exported
                                 participants, on group types and on units.
                                 [] in structure mode, and which private
                                 notes it holds is the caller's choice
                                 (`private_notes`).
        allocation_events.json — v1.0.4t: the history, for exported
                                 participants only. [] in structure mode.
                                 Optional on read, so pre-v1.0.4t files
                                 still restore.
        checkin.json           — v1.0.4s: { fields, values }. The fields go
                                 in both modes, the values in full mode
                                 only, and only for exported participants.
                                 Optional on read, so pre-v1.0.4s files
                                 still restore.
        field_configs.json

    v1.0.4s: structure mode also leaves `email_from_name` and
    `email_reply_to` out of the event's settings. They are the organiser's
    own address, not part of the event's shape, and a template is made to be
    shared (BACKUP-11).

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

    # ── Load check-in columns and ticks (v1.0.4s) ──
    # The columns are part of the event's shape, so they go in both modes.
    # The ticks are personal, so they follow the participants: the
    # `participant_ids` test is the same one the exclusions use, and it
    # covers structure mode (no participants) and removed people (already
    # filtered out of `participants`) without a filter of its own.
    ci_result = await db.execute(
        select(CheckInField)
        .where(CheckInField.event_id == event_id)
        .order_by(CheckInField.sort_order, CheckInField.id)
    )
    checkin_fields = list(ci_result.scalars().all())

    checkin_values: list[CheckInValue] = []
    if participant_ids:
        cv_result = await db.execute(
            select(CheckInValue)
            .where(
                CheckInValue.event_id == event_id,
                CheckInValue.participant_id.in_(participant_ids),
            )
            .order_by(CheckInValue.created_at, CheckInValue.id)
        )
        checkin_values = list(cv_result.scalars().all())

    # ── Load history (v1.0.4t) ──
    # A history row is about a person, so it travels with that person: only
    # rows whose participant is in this export go in. `participant_id.in_()`
    # also excludes a row whose participant_id is already NULL from an
    # erasure, because NULL is never IN anything. Structure mode and removed
    # people fall out of the same test, as they do for the exclusions.
    #
    # Ordered by when it happened, then by id, so two backups of the same
    # event are comparable and the restored timeline reads in order.
    allocation_events: list[AllocationEvent] = []
    if participant_ids:
        ae_result = await db.execute(
            select(AllocationEvent)
            .where(
                AllocationEvent.event_id == event_id,
                AllocationEvent.participant_id.in_(participant_ids),
            )
            .order_by(AllocationEvent.occurred_at, AllocationEvent.id)
        )
        allocation_events = list(ae_result.scalars().all())

    # ── Load notes (v1.0.4s) ──
    # A note travels with what it is about. Every note whose target is in
    # this export goes in: the event itself, an exported participant (so a
    # removed person's notes stay out, as their exclusions do), a group
    # type, or a unit. A note about anything else, or about a participant
    # this file does not carry, is not in the export at all.
    #
    # A structure backup carries no notes. They are what people wrote about
    # each other and about the event, never part of its shape, and a
    # template is made to be shared (BACKUP-11).
    #
    # Which private notes go in is the caller's choice; see `private_notes`.
    notes: list[Note] = []
    if not structure_only:
        reachable = [
            and_(Note.notable_type == notable_type, Note.notable_id.in_(ids))
            for notable_type, ids in (
                ("event", [event_id]),
                ("participant", participant_ids),
                ("category", category_ids),
                ("unit", unit_ids),
            )
            if ids
        ]
        note_stmt = select(Note).where(or_(*reachable))
        if private_notes is not ALL_PRIVATE_NOTES:
            allowed = Note.is_published.is_(True)
            if private_notes is not None:
                allowed = or_(allowed, Note.author_id == private_notes)
            note_stmt = note_stmt.where(allowed)
        # A stable order, as the exclusions have, so two backups of the same
        # event are comparable.
        note_result = await db.execute(
            note_stmt.order_by(Note.created_at, Note.id))
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
    # v1.0.4s (BACKUP-11): a structure backup is made to be shared, and the
    # organiser's own sender name and reply-to address are their contact
    # details, not part of the event's shape. A full backup keeps both: it
    # is the same organisation restoring its own event. Copied first, so the
    # event row in the session is never touched.
    settings = dict(event.settings or {})
    if structure_only:
        for personal_key in ("email_from_name", "email_reply_to"):
            settings.pop(personal_key, None)
    event_data["settings"] = settings
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

    exported_participant_ids = {str(p.id) for p in participants}
    allocation_events_data = [
        _row(ae, *_row_fields("allocation_events"))
        | {"meta": _scrub_history_meta(ae.meta, exported_participant_ids)}
        for ae in allocation_events
    ]

    checkin_data = {
        "fields": [
            _row(f, *_row_fields("checkin_fields"))
            for f in checkin_fields
        ],
        "values": [
            _row(v, *_row_fields("checkin_values"))
            for v in checkin_values
        ],
    }

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
            "checkin_fields": len(checkin_fields),
            "checkin_values": len(checkin_values),
            "allocation_events": len(allocation_events),
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
        zf.writestr("checkin.json", json.dumps(checkin_data, indent=2, ensure_ascii=False))
        zf.writestr("allocation_events.json", json.dumps(allocation_events_data, indent=2, ensure_ascii=False))

    return buf.getvalue()


# ── Restore ───────────────────────────────────────────────────────────────────

# v1.0.4m: members that may be absent, with the value to use when they are.
# An older file simply has no exclusions in it, which restores as "nobody
# excluded"; see _parse_zip.
# v1.0.4s: checkin.json joins them, with a default that is a dict of two
# lists. That is the case the v1.0.4o deep copy was written for: without it
# a restore could mutate the module constant.
_OPTIONAL_MEMBERS: dict[str, object] = {
    "allocation_exclusions.json": [],
    "checkin.json": {"fields": [], "values": []},
    "allocation_events.json": [],
}

# v1.0.4o: the top-level shape every member must have. A member that cannot
# be read at all is refused before anything is written (there is no sensible
# per-line recovery from "this member is not a list"), which is what
# _require_shape below does. `object` means a JSON object, `array` a list.
_MEMBER_SHAPES: dict[str, str] = {
    "manifest.json": "object",
    "event.json": "object",
    "custom_fields.json": "object",
    "field_configs.json": "array",
    "allocation_categories.json": "array",
    "allocation_units.json": "array",
    "allocations.json": "array",
    "allocation_exclusions.json": "array",
    "marks.json": "object",
    "preferences.json": "array",
    "notes.json": "array",
    "checkin.json": "object",
    "allocation_events.json": "array",
}

# Members that hold two tables: the keys inside them, and their shapes.
_MEMBER_INNER: dict[str, tuple[tuple[str, str], ...]] = {
    "custom_fields.json": (("definitions", "array"), ("values", "object")),
    "marks.json": (("definitions", "array"), ("assignments", "array")),
    "checkin.json": (("fields", "array"), ("values", "array")),
}


def _unreadable(*members: str):
    """Refuse the file, naming the members at fault.

    `zip_missing_files` is the closest existing key: it is about the backup
    ZIP rather than a generic failure, it names the member through its
    `files` parameter, and it already surfaces as a 422 at both preview and
    confirm. It says "missing" where the truth is "present but unreadable",
    which is why STRINGS-1 carries a specific message for this case.
    """
    return MoimioAppError(
        "errors.export.zip_missing_files",
        params={"files": ", ".join(sorted(members))},
        status_code=422,
    )


def _require_shape(name: str, payload) -> None:
    """Check one member's top-level shape, and its inner keys where it
    holds two tables. Raises rather than repairing: a member of the wrong
    shape is not a damaged line, it is a file that cannot be read."""
    want = _MEMBER_SHAPES.get(name)
    if want == "array" and not isinstance(payload, list):
        raise _unreadable(name)
    if want == "object" and not isinstance(payload, dict):
        raise _unreadable(name)
    for key, inner in _MEMBER_INNER.get(name, ()):
        value = payload.get(key)
        if value is None:
            continue  # absent is fine; the readers default it
        if inner == "array" and not isinstance(value, list):
            raise _unreadable(f"{name}:{key}")
        if inner == "object" and not isinstance(value, dict):
            raise _unreadable(f"{name}:{key}")


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
            # v1.0.4o: invalid JSON used to reach the caller as a 500. A
            # member that will not parse is a file that cannot be read.
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                raise _unreadable(name)
            _require_shape(name, payload)
            data[name] = payload
        else:
            # CSV — decode stripping BOM
            try:
                data[name] = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                raise _unreadable(name)

    # v1.0.4m: optional members, read when present and defaulted when not.
    # Deliberately NOT in `required`: a member added there would reject
    # every backup file made before that member existed. A present member
    # that will not parse raises exactly as a required one does — nothing
    # here catches json.loads, so the caller turns it into the same error.
    for name, default in _OPTIONAL_MEMBERS.items():
        if name in names:
            try:
                payload = json.loads(zf.read(name).decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                raise _unreadable(name)
            _require_shape(name, payload)
            data[name] = payload
        else:
            # v1.0.4o: deep copy, so a default that is a dict or holds one
            # cannot be mutated on the module constant, and does not come
            # back as a list of its own keys the way list() gave.
            data[name] = copy.deepcopy(default)

    # v1.0.4o: without an `id` column nothing in the file can refer to a
    # participant, and every read of it would raise. Refuse the file.
    header = (data["participants.csv"].splitlines() or [""])[0]
    if "id" not in [c.strip() for c in header.split(",")]:
        raise _unreadable("participants.csv:id")

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


async def confirm_restore(
    content: bytes,
    db: AsyncSession,
    actor_user_id: uuid.UUID | None = None,
    *,
    suffix_name: bool = True,
) -> dict:
    """
    Parse a backup ZIP and create a new event with fresh UUIDs.

    All relationships are re-keyed so the restored event is completely
    independent of the original. Returns the new event id and counts.

    v1.0.4u: `suffix_name` decides whether the restored event's name gets
    " (Restored)". It defaults to True, which is what the Backup page has
    always done and what every existing caller expects. The whole-workspace
    restore (`app.cli.import_all`) passes False when the receiving instance
    has no events of its own: there is nothing to tell the restored events
    apart from, so a customer moving to their own server gets their own
    names back.
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
    # v1.0.4s: check-in field old → new, so a tick can name its column.
    checkin_field_map: dict[str, uuid.UUID] = {}
    # v1.0.4m: new unit id → new group type id. An allocation names a unit,
    # an exclusion names a group type, so deciding whether a placement is
    # excluded needs the step between them.
    unit_category_map: dict[uuid.UUID, uuid.UUID] = {}

    counts = {"participants": 0, "allocations": 0, "marks_assigned": 0,
              "categories": 0, "units": 0, "allocation_exclusions": 0,
              "allocation_events": 0}

    # v1.0.4o: a damaged or hand-edited line costs that line and whatever
    # depends on it, never the whole file. Every such loss is counted here,
    # reported in the return value, and summarised in one log line at the
    # end. Keyed by ZIP member so the organiser can be told where the
    # damage was, never by participant.
    skipped: dict[str, int] = {}
    shortened: dict[str, int] = {}
    # v1.0.4q: a value the file carried but restore could not use, so the
    # column's own model default applies. Keyed by table.column, like
    # `shortened`, because that is what a reader needs to know.
    defaulted: dict[str, int] = {}

    # v1.0.4q: only a structure backup is a template. A missing or unknown
    # mode means a full backup, because files older than the distinction
    # carry no mode at all.
    manifest = data["manifest.json"]
    backup_mode = manifest.get("backup_mode", "full") if isinstance(manifest, dict) else "full"
    restore_timestamps = backup_mode != "structure"

    def skip(member: str) -> None:
        skipped[member] = skipped.get(member, 0) + 1

    def fell_back(table: str, column: str) -> None:
        label = f"{table}.{column}"
        defaulted[label] = defaulted.get(label, 0) + 1

    def ts(src, key: str, table: str, column: str) -> dict:
        """A timestamp kwarg, or nothing at all so the model default applies.

        Full backups keep every original timestamp. A structure backup is a
        new event built from somebody's setup, so its rows are dated when
        they are restored. A value the file does not have is not damage; a
        value it has and restore cannot parse is.
        """
        if not restore_timestamps:
            return {}
        raw = src.get(key) if isinstance(src, dict) else None
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return {}
        parsed = _parse_datetime(raw)
        if parsed is None:
            fell_back(table, column)
            return {}
        return {column: parsed}

    def server_side(src, key: str, table: str, column: str) -> dict:
        """A kwarg for a NOT NULL column whose only default is the database's.

        `_field` cannot serve these: it knows Python-side defaults, and where
        there is none it reports the line unwritable, which is wrong for a
        column the database will fill itself. `events.timezone`,
        `events.is_archived` and `allocation_units.is_kept` are the three.
        An absent or wrong-typed value means omit the column.
        """
        raw = src.get(key) if isinstance(src, dict) else None
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return {}
        if not isinstance(raw, _column(table, column).type.python_type):
            fell_back(table, column)
            return {}
        return {column: fit(raw, table, column)}

    def accepted(src, key: str, table: str, column: str):
        """A value the app itself would accept, or the model default.

        Used for the columns whose values the app looks up or validates
        (see ACCEPTED_KEYS and CLUSTER_BEHAVIOURS).
        """
        value = _field(src, key, table, column)
        if value is _SKIP or value is None:
            return value
        allowed = ACCEPTED_KEYS.get(column) or (
            CLUSTER_BEHAVIOURS if column == "cluster_behaviour" else None
        )
        if allowed is not None and value not in allowed:
            fell_back(table, column)
            _, default = _column_default(table, column)
            return default
        return value

    def fit(value, table: str, column: str):
        """Shorten over-long text to the column's declared length, counted
        by characters. The length is read from the model, so it cannot
        drift from the schema."""
        length = getattr(_column(table, column).type, "length", None)
        if isinstance(value, str) and length and len(value) > length:
            label = f"{table}.{column}"
            shortened[label] = shortened.get(label, 0) + 1
            return value[:length]
        return value


    # THE WRITE ORDER. Each block is written where everything it names
    # already exists, so no row is ever inserted pointing at an id that has
    # not been minted yet:
    #
    #   1. the event
    #   2. mark definitions          — a group type's mark priorities and a
    #                                  unit's mark_restriction name a mark
    #   3. custom field definitions
    #   4. field configs
    #   5. check-in columns          — v1.0.4s; a tick names one
    #   6. group types, then units   — a participant's group code scope
    #                                  names a group type
    #   7. participants, with their custom field values
    #   8. check-in ticks            — v1.0.4s; names a participant and a
    #                                  check-in column
    #   9. exclusions resolved       — before the placements, because an
    #                                  exclusion outranks a placement
    #  10. allocations
    #  11. the exclusion rows themselves
    #  12. mark assignments
    #  13. preferences
    #  14. notes                     — v1.0.4s; a note names a participant,
    #                                  a group type, a unit or the event
    #  15. history                   — v1.0.4t; LAST, because one row can
    #                                  name a participant, a unit, a group
    #                                  type and, inside `meta`, a mark

    # ── Create event ──
    new_event_id = uuid.uuid4()
    # Append "(Restored)" to name to make it distinguishable
    # The event is the one row that cannot be skipped, so it keeps its
    # pre-existing fallback name. The suffix is added first and the result
    # shortened, or a name already at the column limit would overflow it.
    # v1.0.4u: unless the caller asked for the name to be kept as it is.
    base_name = event_src.get('name') or 'Restored Event'
    new_name = f"{base_name} (Restored)" if suffix_name else base_name
    # Restore as DRAFT regardless of original status
    event = Event(
        id=new_event_id,
        name=fit(new_name, "events", "name"),
        description=event_src.get("description"),
        location=fit(event_src.get("location"), "events", "location"),
        start_date=_parse_date(event_src.get("start_date")),
        end_date=_parse_date(event_src.get("end_date")),
        status=EventStatus.DRAFT,
        settings=event_src.get("settings") or {},
        # v1.0.4q: the restoring user, who genuinely created this row.
        #
        # v1.0.4zd: with no actor this is now None, not the new event's own
        # id. That stand-in was only ever safe because `events.created_by`
        # had no foreign key; USER-1 gave it one, and an event id is not a
        # user id, so it would now be a violation. None is the truthful
        # answer in any case — nobody on this instance created that event —
        # and the column is nullable for exactly that reason.
        created_by=actor_user_id,
        # The app neither validates nor resolves a timezone anywhere: there
        # is no VALID_TIMEZONES beside VALID_DATE_FORMATS, and nothing
        # imports zoneinfo. So it is carried as it is.
        **server_side(event_src, "timezone", "events", "timezone"),
        **server_side(event_src, "is_archived", "events", "is_archived"),
        **ts(event_src, "created_at", "events", "created_at"),
        **ts(event_src, "updated_at", "events", "updated_at"),
    )
    db.add(event)
    await db.flush()

    # ── Marks ──
    # v1.0.4p: written before group types and units, so `mark_map` exists
    # by the time anything needs to translate a mark id: the priorities
    # inside a group type's settings now, and a unit's mark_restriction
    # from v1.0.4q.
    marks_src = data["marks.json"]
    seen_mark_ids: set[str] = set()
    for mark_src in marks_src.get("definitions", []):
        if not isinstance(mark_src, dict):
            skip("marks.json")
            continue
        old_id = _old_id(mark_src, "id")
        if old_id is not None and old_id in seen_mark_ids:
            skip("marks.json")  # duplicate old id
            continue
        name = _field(mark_src, "name", "mark_definitions", "name")
        if name is _SKIP:
            skip("marks.json")
            continue
        new_mark_id = uuid.uuid4()
        if old_id is not None:
            mark_map[old_id] = new_mark_id
            seen_mark_ids.add(old_id)
        mark = MarkDefinition(
            id=new_mark_id,
            event_id=new_event_id,
            name=fit(name, "mark_definitions", "name"),
            colour=fit(
                _field(mark_src, "colour", "mark_definitions", "colour"),
                "mark_definitions", "colour",
            ),
            visible_in=mark_src.get("visible_in") or [],
            # v1.0.4q: one of the app's own three values, or the default.
            cluster_behaviour=accepted(
                mark_src, "cluster_behaviour",
                "mark_definitions", "cluster_behaviour"),
            **ts(mark_src, "created_at", "mark_definitions", "created_at"),
        )
        db.add(mark)

    await db.flush()

    # ── Custom field definitions ──
    cf_data = data["custom_fields.json"]
    seen_cf_ids: set[str] = set()
    for cf_src in cf_data.get("definitions", []):
        if not isinstance(cf_src, dict):
            skip("custom_fields.json")
            continue
        old_id = _old_id(cf_src, "id")
        if old_id is not None and old_id in seen_cf_ids:
            skip("custom_fields.json")  # duplicate old id: the first wins
            continue
        label = _field(cf_src, "label", "custom_field_definitions", "label")
        field_type = _field(cf_src, "field_type", "custom_field_definitions", "field_type")
        if label is _SKIP or field_type is _SKIP:
            skip("custom_fields.json")
            continue
        new_cf_id = uuid.uuid4()
        if old_id is not None:
            cf_map[old_id] = new_cf_id
            seen_cf_ids.add(old_id)
        cf = CustomFieldDefinition(
            id=new_cf_id,
            event_id=new_event_id,
            label=fit(label, "custom_field_definitions", "label"),
            field_type=fit(field_type, "custom_field_definitions", "field_type"),
            options=cf_src.get("options"),
            is_required=_field(cf_src, "is_required", "custom_field_definitions", "is_required"),
            sort_order=_field(cf_src, "sort_order", "custom_field_definitions", "sort_order"),
            # v1.0.4q: False means admin-only. Absent, as in a pre-v1.0.4q
            # file, means the model default, which is visible.
            show_in_form=_field(cf_src, "show_in_form", "custom_field_definitions", "show_in_form"),
            **ts(cf_src, "created_at", "custom_field_definitions", "created_at"),
        )
        db.add(cf)
    await db.flush()

    # ── Field configs (registration form settings) ──
    for fc_src in data["field_configs.json"]:
        if not isinstance(fc_src, dict):
            skip("field_configs.json")
            continue
        field_name = _field(fc_src, "field_name", "event_field_configs", "field_name")
        if field_name is _SKIP:
            skip("field_configs.json")
            continue
        fc = EventFieldConfig(
            event_id=new_event_id,
            field_name=fit(field_name, "event_field_configs", "field_name"),
            is_enabled=_field(fc_src, "is_enabled", "event_field_configs", "is_enabled"),
            is_required=_field(fc_src, "is_required", "event_field_configs", "is_required"),
            **ts(fc_src, "created_at", "event_field_configs", "created_at"),
            **ts(fc_src, "updated_at", "event_field_configs", "updated_at"),
        )
        db.add(fc)
    await db.flush()

    # ── Check-in columns (v1.0.4s) ──
    # Straight after the field configs: a check-in column names nothing but
    # its event, and the ticks written after the participants need the map
    # this block fills.
    checkin_src = data["checkin.json"]
    seen_ci_ids: set[str] = set()
    for ci_src in checkin_src.get("fields", []):
        if not isinstance(ci_src, dict):
            skip("checkin.json:fields")
            continue
        old_id = _old_id(ci_src, "id")
        if old_id is not None and old_id in seen_ci_ids:
            skip("checkin.json:fields")  # duplicate old id: the first wins
            continue
        field_name = _field(ci_src, "field_name", "checkin_fields", "field_name")
        if field_name is _SKIP:
            skip("checkin.json:fields")
            continue
        new_ci_id = uuid.uuid4()
        if old_id is not None:
            checkin_field_map[old_id] = new_ci_id
            seen_ci_ids.add(old_id)
        db.add(CheckInField(
            id=new_ci_id,
            event_id=new_event_id,
            field_name=fit(field_name, "checkin_fields", "field_name"),
            sort_order=_field(
                ci_src, "sort_order", "checkin_fields", "sort_order"),
            **ts(ci_src, "created_at", "checkin_fields", "created_at"),
            **ts(ci_src, "updated_at", "checkin_fields", "updated_at"),
        ))
    await db.flush()

    # ── Allocation categories + units ──
    seen_cat_ids: set[str] = set()
    for cat_src in data["allocation_categories.json"]:
        if not isinstance(cat_src, dict):
            skip("allocation_categories.json")
            continue
        old_id = _old_id(cat_src, "id")
        if old_id is not None and old_id in seen_cat_ids:
            skip("allocation_categories.json")  # duplicate old id
            continue
        name = _field(cat_src, "name", "allocation_categories", "name")
        if name is _SKIP:
            skip("allocation_categories.json")
            continue
        new_cat_id = uuid.uuid4()
        if old_id is not None:
            category_map[old_id] = new_cat_id
            seen_cat_ids.add(old_id)
        cat = AllocationCategory(
            id=new_cat_id,
            event_id=new_event_id,
            name=fit(name, "allocation_categories", "name"),
            item_label=fit(cat_src.get("item_label"), "allocation_categories", "item_label"),
            description=fit(cat_src.get("description"), "allocation_categories", "description"),
            # v1.0.4o: the column's own default, "exclusive". The "none"
            # this line used to fall back to is not a value the model
            # defines, and nothing reads it as one.
            rule_type=fit(
                _field(cat_src, "rule_type", "allocation_categories", "rule_type"),
                "allocation_categories", "rule_type",
            ),
            # v1.0.4q: only a key the app knows. Anything else becomes
            # NULL, which is exactly how the stored name shows through.
            name_key=accepted(cat_src, "name_key", "allocation_categories", "name_key"),
            item_label_key=accepted(
                cat_src, "item_label_key", "allocation_categories", "item_label_key"),
            exclusive_group_codes=_field(
                cat_src, "exclusive_group_codes",
                "allocation_categories", "exclusive_group_codes"),
            has_capacity=True,  # v1.0.3: ignored; always on
            has_gender_restriction=True,  # v1.0.3: ignored; always on
            sort_order=_field(cat_src, "sort_order", "allocation_categories", "sort_order"),
            is_default=_field(cat_src, "is_default", "allocation_categories", "is_default"),
            # v1.0.4p: the mark ids inside engine.mark_priorities are
            # translated; every other settings key passes through.
            settings=_translate_mark_priorities(
                cat_src.get("settings"), mark_map,
            ) or {},
            **ts(cat_src, "created_at", "allocation_categories", "created_at"),
            **ts(cat_src, "updated_at", "allocation_categories", "updated_at"),
        )
        db.add(cat)
        counts["categories"] += 1

    await db.flush()

    seen_unit_ids: set[str] = set()
    for unit_src in data["allocation_units.json"]:
        if not isinstance(unit_src, dict):
            skip("allocation_units.json")
            continue
        old_id = _old_id(unit_src, "id")
        if old_id is not None and old_id in seen_unit_ids:
            skip("allocation_units.json")  # duplicate old id
            continue
        new_cat_id = category_map.get(_old_id(unit_src, "category_id"))
        name = _field(unit_src, "name", "allocation_units", "name")
        capacity = _field(unit_src, "capacity", "allocation_units", "capacity")
        if not new_cat_id or name is _SKIP or capacity is _SKIP:
            skip("allocation_units.json")
            continue
        # v1.0.4o (BACKUP-7): the map entry is written only once the row is
        # certain to be created. Written above this guard, a unit whose
        # group type was missing still landed in unit_map although no row
        # existed, and an allocation naming it then failed the foreign key
        # and rolled the whole restore back.
        new_unit_id = uuid.uuid4()
        if old_id is not None:
            unit_map[old_id] = new_unit_id
            seen_unit_ids.add(old_id)
        unit_category_map[new_unit_id] = new_cat_id
        # v1.0.4q: mark_restriction is a real foreign key, so a dead id
        # cannot be written. An id `mark_map` does not know becomes NULL —
        # the model default, and what the database itself does when the
        # mark is deleted. v1.0.4p put marks before units so this map
        # exists here at all.
        old_mark_id = _old_id(unit_src, "mark_restriction")
        new_mark_restriction = mark_map.get(old_mark_id) if old_mark_id else None
        if old_mark_id and not new_mark_restriction:
            fell_back("allocation_units", "mark_restriction")
        unit = AllocationUnit(
            id=new_unit_id,
            category_id=new_cat_id,
            name=fit(name, "allocation_units", "name"),
            description=fit(unit_src.get("description"), "allocation_units", "description"),
            capacity=capacity,
            gender_restriction=fit(
                unit_src.get("gender_restriction"),
                "allocation_units", "gender_restriction",
            ),
            sort_order=_field(unit_src, "sort_order", "allocation_units", "sort_order"),
            mark_restriction=new_mark_restriction,
            **server_side(unit_src, "is_kept", "allocation_units", "is_kept"),
            **ts(unit_src, "created_at", "allocation_units", "created_at"),
            **ts(unit_src, "updated_at", "allocation_units", "updated_at"),
        )
        db.add(unit)
        counts["units"] += 1

    await db.flush()

    # ── Participants ──
    # v1.0.4p: written after group types, so `category_map` exists by the
    # time the ids inside group_code_categories need translating.
    cf_values_src = cf_data.get("values", {})  # old_participant_id → [{field_id, value}]
    reader = csv.DictReader(io.StringIO(data["participants.csv"]))
    seen_p_ids: set[str] = set()
    seen_cfv_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for row in reader:
        old_id = _old_id(row, "id")
        if old_id is not None and old_id in seen_p_ids:
            skip("participants.csv")  # duplicate old id: the first wins
            continue
        # A person with no name and no email is not a person. These three
        # are NOT NULL with no model default, so the line goes, and with it
        # everything that referred to this participant.
        first = _field(row, "first_name", "participants", "first_name", blank_is_null=True)
        last = _field(row, "last_name", "participants", "last_name", blank_is_null=True)
        email = _field(row, "email", "participants", "email", blank_is_null=True)
        if first is _SKIP or last is _SKIP or email is _SKIP:
            skip("participants.csv")
            continue

        new_p_id = uuid.uuid4()
        # A blank id cell is never a map key, but the row is still created:
        # nothing in the file can refer to it.
        if old_id is not None:
            participant_map[old_id] = new_p_id
            seen_p_ids.add(old_id)

        # v1.0.4o: the model's own default, PENDING, not CONFIRMED. A bad
        # value must not quietly promote someone into the active roster.
        reg_status = _safe_enum(
            RegistrationStatus,
            row.get("registration_status"),
            _column_default("participants", "registration_status")[1],
        )
        p = Participant(
            id=new_p_id,
            event_id=new_event_id,
            first_name=fit(first, "participants", "first_name"),
            last_name=fit(last, "participants", "last_name"),
            email=fit(email, "participants", "email"),
            gender=fit(row.get("gender") or None, "participants", "gender"),
            date_of_birth=_parse_date(row.get("date_of_birth")),
            phone=fit(row.get("phone") or None, "participants", "phone"),
            address=row.get("address") or None,
            country=fit(row.get("country") or None, "participants", "country"),
            church_organisation=fit(
                row.get("church_organisation") or None,
                "participants", "church_organisation",
            ),
            message=row.get("message") or None,
            group_code=fit(row.get("group_code") or None, "participants", "group_code"),
            # v1.0.4p: group type ids, translated in place.
            group_code_categories=_translate_id_list(
                _parse_json_field(row.get("group_code_categories")), category_map,
            ),
            participant_number=_parse_int(row.get("participant_number")),
            registration_status=reg_status,
            gdpr_consent=(row.get("gdpr_consent") or "").lower() in ("true", "1"),
            checked_in=(row.get("checked_in") or "").lower() in ("true", "1"),
            # v1.0.4q. A CSV cell is text, so the booleans are read the way
            # the two above are; absent reads as False, the model default.
            override_group_room=(
                row.get("override_group_room") or ""
            ).lower() in ("true", "1"),
            preferred_language=fit(
                _field(row, "preferred_language", "participants",
                       "preferred_language", blank_is_null=True),
                "participants", "preferred_language",
            ),
            **ts(row, "checked_in_at", "participants", "checked_in_at"),
            **ts(row, "created_at", "participants", "created_at"),
            **ts(row, "updated_at", "participants", "updated_at"),
        )
        db.add(p)
        counts["participants"] += 1

        # Custom field values for this participant. Keyed by the old
        # participant id, so a line with no id has none to find.
        for cfv_src in (cf_values_src.get(old_id) or [] if old_id else []):
            if not isinstance(cfv_src, dict):
                skip("custom_fields.json:values")
                continue
            new_field_id = cf_map.get(_old_id(cfv_src, "field_id"))
            if not new_field_id:
                skip("custom_fields.json:values")
                continue
            # v1.0.4p: no unique constraint on (participant, field), but
            # neither writer in the app can produce two rows for one pair:
            # registration iterates a dict keyed by field id, and the update
            # path upserts. So a repeated line is damage. The first wins.
            if (new_p_id, new_field_id) in seen_cfv_pairs:
                skip("custom_fields.json:values")
                continue
            seen_cfv_pairs.add((new_p_id, new_field_id))
            db.add(CustomFieldValue(
                participant_id=new_p_id,
                field_id=new_field_id,
                value=cfv_src.get("value"),
            ))

    await db.flush()

    # ── Check-in ticks (v1.0.4s) ──
    # Straight after the participants, because a tick names a participant
    # and a check-in column, and before the exclusions are resolved, which
    # is where the participant-linked work starts.
    seen_cv_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for cv_src in checkin_src.get("values", []):
        if not isinstance(cv_src, dict):
            skip("checkin.json:values")
            continue
        new_p_id = participant_map.get(_old_id(cv_src, "participant_id"))
        new_field_id = checkin_field_map.get(_old_id(cv_src, "field_id"))
        if not new_p_id or not new_field_id:
            skip("checkin.json:values")
            continue
        # The table is UNIQUE on (participant, field). A duplicate in a
        # hand-edited file is dropped here: letting one reach the constraint
        # would roll the whole restore back over a single bad line.
        if (new_p_id, new_field_id) in seen_cv_pairs:
            skip("checkin.json:values")
            continue
        seen_cv_pairs.add((new_p_id, new_field_id))
        db.add(CheckInValue(
            event_id=new_event_id,
            participant_id=new_p_id,
            field_id=new_field_id,
            checked=_field(cv_src, "checked", "checkin_values", "checked"),
            **ts(cv_src, "created_at", "checkin_values", "created_at"),
            **ts(cv_src, "updated_at", "checkin_values", "updated_at"),
        ))
    await db.flush()

    # ── Allocation category exclusions (v1.0.4m) ──
    # Resolved BEFORE the allocations loop, because an exclusion outranks a
    # placement: when a file says someone is both excluded from a group type
    # and placed in it, the exclusion is restored and the placement is not.
    # The rows themselves are written after the allocations block.
    # v1.0.4q: the third element carries the row's own created_at kwargs,
    # because the resolve pass runs before the rows are written.
    exclusion_rows: list[tuple[uuid.UUID, uuid.UUID, dict]] = []
    excluded_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for excl_src in data["allocation_exclusions.json"]:
        if not isinstance(excl_src, dict):
            skip("allocation_exclusions.json")
            continue
        new_p_id = participant_map.get(_old_id(excl_src, "participant_id"))
        new_cat_id = category_map.get(_old_id(excl_src, "allocation_category_id"))
        if not new_p_id or not new_cat_id:
            skip("allocation_exclusions.json")
            continue
        pair = (new_p_id, new_cat_id)
        # The table is UNIQUE on (group type, participant). A duplicate in a
        # hand-edited file is dropped here: letting one reach the constraint
        # would roll the whole restore back over a single bad line.
        if pair in excluded_pairs:
            skip("allocation_exclusions.json")
            continue
        excluded_pairs.add(pair)
        exclusion_rows.append((
            new_p_id, new_cat_id,
            ts(excl_src, "created_at",
               "allocation_category_exclusions", "created_at"),
        ))

    dropped_placements = 0

    # ── Allocations ──
    seen_alloc_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for alloc_src in data["allocations.json"]:
        if not isinstance(alloc_src, dict):
            skip("allocations.json")
            continue
        new_p_id = participant_map.get(_old_id(alloc_src, "participant_id"))
        new_unit_id = unit_map.get(_old_id(alloc_src, "unit_id"))
        if not new_p_id or not new_unit_id:
            skip("allocations.json")
            continue
        # UNIQUE (participant_id, unit_id): a repeated line would break the
        # constraint and roll the whole restore back, so the first wins.
        if (new_p_id, new_unit_id) in seen_alloc_pairs:
            skip("allocations.json")
            continue
        seen_alloc_pairs.add((new_p_id, new_unit_id))
        # v1.0.4m: the exclusion wins, so drop the placement.
        if (new_p_id, unit_category_map.get(new_unit_id)) in excluded_pairs:
            dropped_placements += 1
            continue
        alloc = Allocation(
            event_id=new_event_id,
            participant_id=new_p_id,
            unit_id=new_unit_id,
            **ts(alloc_src, "created_at", "allocations", "created_at"),
            **ts(alloc_src, "updated_at", "allocations", "updated_at"),
        )
        db.add(alloc)
        counts["allocations"] += 1

    await db.flush()

    # Written directly, never through add_exclusion: that writes history
    # rows, vacates units and re-opens a confirmed group type. created_at
    # is left to the column's server default, as the participant block
    # leaves it; created_by is NULL because nobody on this instance made
    # the decision, and restore carries attribution for nothing else.
    for new_p_id, new_cat_id, created in exclusion_rows:
        db.add(AllocationCategoryExclusion(
            allocation_category_id=new_cat_id,
            participant_id=new_p_id,
            created_by=None,
            **created,
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

    # ── Mark assignments ──
    seen_ma_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for ma_src in marks_src.get("assignments", []):
        if not isinstance(ma_src, dict):
            skip("marks.json:assignments")
            continue
        new_p_id = participant_map.get(_old_id(ma_src, "participant_id"))
        new_mark_id = mark_map.get(_old_id(ma_src, "mark_id"))
        if not new_p_id or not new_mark_id:
            skip("marks.json:assignments")
            continue
        # No unique constraint on this table, so a duplicate would insert
        # silently and show the same mark twice. The first wins.
        if (new_p_id, new_mark_id) in seen_ma_pairs:
            skip("marks.json:assignments")
            continue
        seen_ma_pairs.add((new_p_id, new_mark_id))
        ma = MarkAssignment(
            mark_id=new_mark_id,
            participant_id=new_p_id,
            event_id=new_event_id,
            **ts(ma_src, "created_at", "mark_assignments", "created_at"),
        )
        db.add(ma)
        counts["marks_assigned"] += 1

    await db.flush()

    # ── Preferences ──
    for pref_src in data["preferences.json"]:
        if not isinstance(pref_src, dict):
            skip("preferences.json")
            continue
        new_p_id = participant_map.get(_old_id(pref_src, "participant_id"))
        if not new_p_id:
            skip("preferences.json")
            continue
        pref = ParticipantPreferenceRequest(
            event_id=new_event_id,
            participant_id=new_p_id,
            preferred_participant_number=_parse_int(
                pref_src.get("preferred_participant_number")),
            preferred_name=fit(
                pref_src.get("preferred_name"),
                "participant_preference_requests", "preferred_name",
            ),
            preferred_details=pref_src.get("preferred_details"),
            # v1.0.4p: group type ids, translated in place. "all" and null
            # pass through untouched.
            category_scope=_translate_id_list(
                pref_src.get("category_scope"), category_map,
            ),
            resolved=_field(pref_src, "resolved", "participant_preference_requests", "resolved"),
            # v1.0.4q: `resolved` without its note said a request was
            # settled and gave no reason.
            resolved_note=_field(
                pref_src, "resolved_note",
                "participant_preference_requests", "resolved_note"),
            **ts(pref_src, "created_at",
                 "participant_preference_requests", "created_at"),
        )
        db.add(pref)

    seen_ae_ids: set[str] = set()

    # ── Notes ──
    # v1.0.4o: author_id is a real foreign key to users, so the stand-in id
    # written before that release made any note fail the whole restore. The
    # author is whoever is restoring: true on this instance, and the only
    # non-null option, since the column is NOT NULL. With no actor there is
    # no truthful value, so the line is skipped and counted.
    #
    # v1.0.4s: a note is put back on the thing it is about. `notable_id` is
    # a plain UUID typed by `notable_type`, so which map to translate it
    # through depends on the type, and an event-level note takes the
    # restored event. A note of any other type, or one whose target this
    # file does not carry, cannot be placed: it is skipped and counted,
    # exactly as a note with no content is, and the restore carries on.
    #
    # `is_published` is carried as it is. Forcing it True published what
    # somebody had chosen to keep private.
    note_targets = {
        "participant": participant_map,
        "category": category_map,
        "unit": unit_map,
    }
    for note_src in data["notes.json"]:
        if not isinstance(note_src, dict):
            skip("notes.json")
            continue
        if actor_user_id is None:
            skip("notes.json")
            continue
        notable_type = _field(note_src, "notable_type", "notes", "notable_type")
        content = _field(note_src, "content", "notes", "content")
        if notable_type is _SKIP or content is _SKIP:
            skip("notes.json")
            continue
        if notable_type == "event":
            new_notable_id = new_event_id
        else:
            new_notable_id = note_targets.get(notable_type, {}).get(
                _old_id(note_src, "notable_id"))
        if not new_notable_id:
            skip("notes.json")
            continue
        note = Note(
            notable_type=fit(notable_type, "notes", "notable_type"),
            notable_id=new_notable_id,
            content=content,
            is_published=_field(note_src, "is_published", "notes", "is_published"),
            author_id=actor_user_id,
            **ts(note_src, "created_at", "notes", "created_at"),
            **ts(note_src, "updated_at", "notes", "updated_at"),
        )
        db.add(note)

    await db.flush()

    # ── History (v1.0.4t) ──
    # Last, because a row can name a participant, a unit, a group type and,
    # inside `meta`, a mark, so every map it needs is full by now.
    #
    # The actor is not carried: that account does not exist on this
    # instance, the column is nullable by design, and the history screen
    # already renders a missing actor as a removed user.
    for ae_src in data["allocation_events.json"]:
        if not isinstance(ae_src, dict):
            skip("allocation_events.json")
            continue
        old_id = _old_id(ae_src, "id")
        if old_id is not None and old_id in seen_ae_ids:
            skip("allocation_events.json")  # duplicate old id: the first wins
            continue
        # History is about somebody. A row whose participant does not
        # resolve has nobody to be about, so the line goes.
        new_p_id = participant_map.get(_old_id(ae_src, "participant_id"))
        if not new_p_id:
            skip("allocation_events.json")
            continue
        event_type = _field(
            ae_src, "event_type", "allocation_events", "event_type")
        source = _field(ae_src, "source", "allocation_events", "source")
        unit_name = _field(
            ae_src, "unit_name_snapshot",
            "allocation_events", "unit_name_snapshot")
        category_name = _field(
            ae_src, "category_name_snapshot",
            "allocation_events", "category_name_snapshot")
        if _SKIP in (event_type, source, unit_name, category_name):
            skip("allocation_events.json")
            continue
        # The app's own two sets, enforced by the write path
        # (`record_allocation_event` raises on anything else). A label
        # this instance does not know would be a line the history screen
        # could not render, so it is not written.
        if (event_type not in AllocationEventType.ALL
                or source not in AllocationEventSource.ALL):
            skip("allocation_events.json")
            continue

        # The two optional links. A value the maps do not know becomes
        # NULL, which is what the database itself does when the row it
        # named is deleted (ON DELETE SET NULL), and is counted. A row that
        # never had one — every exclude and include row — is not counted:
        # nothing was lost.
        links: dict[str, uuid.UUID | None] = {}
        for key, id_map in (("unit_id", unit_map),
                            ("category_id", category_map)):
            old_link = _old_id(ae_src, key)
            links[key] = id_map.get(old_link) if old_link is not None else None
            if old_link is not None and links[key] is None:
                fell_back("allocation_events", key)

        # Copied exactly as stored, NULL included. A value that is not a
        # UUID at all cannot go in the column, so it falls back to the
        # column's own default, which is NULL, and is counted.
        action_id = None
        raw_action_id = _old_id(ae_src, "action_id")
        if raw_action_id is not None:
            try:
                action_id = uuid.UUID(raw_action_id)
            except ValueError:
                fell_back("allocation_events", "action_id")

        if old_id is not None:
            seen_ae_ids.add(old_id)
        db.add(AllocationEvent(
            event_id=new_event_id,
            participant_id=new_p_id,
            unit_id=links["unit_id"],
            category_id=links["category_id"],
            actor_user_id=None,
            event_type=fit(event_type, "allocation_events", "event_type"),
            source=fit(source, "allocation_events", "source"),
            unit_name_snapshot=fit(
                unit_name, "allocation_events", "unit_name_snapshot"),
            category_name_snapshot=fit(
                category_name, "allocation_events", "category_name_snapshot"),
            action_id=action_id,
            meta=_translate_history_meta(
                ae_src.get("meta"),
                participant_map=participant_map,
                unit_map=unit_map,
                mark_map=mark_map,
            ),
            **ts(ae_src, "occurred_at", "allocation_events", "occurred_at"),
        ))
        counts["allocation_events"] += 1

    await db.commit()

    # v1.0.4o: one line per restore, and only when something was lost or
    # changed. Counts per member and the new event id, so an organiser can
    # be told where the damage was; no names, emails or participant ids.
    # Separate from the v1.0.4m placement warning, which reports a
    # different thing and stays exactly as it was.
    if skipped or shortened or defaulted:
        print(
            f"[RESTORE WARNING] event {new_event_id}: damaged or unreadable "
            f"lines were skipped, shortened or defaulted. "
            f"skipped={dict(sorted(skipped.items()))} "
            f"shortened={dict(sorted(shortened.items()))} "
            f"defaulted={dict(sorted(defaulted.items()))}",
            flush=True,
        )

    return {
        "new_event_id": str(new_event_id),
        "new_event_name": new_name,
        "counts": counts,
        "skipped": dict(sorted(skipped.items())),
        "shortened": dict(sorted(shortened.items())),
        "defaulted": dict(sorted(defaulted.items())),
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

