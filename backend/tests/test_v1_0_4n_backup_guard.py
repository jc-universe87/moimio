"""v1.0.4n — the backup register guard.

Every backup gap the completeness investigation found had one root cause:
what a backup contains was decided by hand-written field lists that nothing
checked. A column added to a model years later was simply absent from a list
nobody re-read.

These four tests make that impossible. Adding a column to a backed-up model,
or adding an event-scoped table, fails here until somebody records a decision
about backups in `BACKUP_REGISTER`.

  1. Classification — every event-scoped table is either carried or listed as
     not carried, and nothing else is classified.
  2. Columns — the register's columns for a carried table are exactly the
     model's columns.
  3. Declarations — every verb and reason tag is legal, and present where the
     rules require one.
  4. Export agrees — the keys a real export writes are exactly the register's
     exported columns, in the register's order.

Which tables belong to an event is COMPUTED, by walking the foreign keys to
`events`, not hand-listed. References with no foreign key for the walk to
follow are declared in `EVENT_SCOPE_OVERRIDES`; `notes.notable_id` is the only
one today.

v1.0.5 ships only when no `known_gap` tag remains. Test 3 deliberately does
NOT fail on a `known_gap`: the register goes in green and shrinks release by
release. The last backup release adds the test that forbids them.
"""

import io
import json
import zipfile

import pytest
from sqlalchemy import select

from app.core.database import Base
import app.models  # noqa: F401  — populate Base.metadata, as conftest does
from app.models.checkin_field import CheckInField
from app.models.checkin_value import CheckInValue
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event_field_config import EventFieldConfig
from app.models.mark import MarkAssignment, MarkDefinition
from app.models.note import Note
from app.models.preference_request import ParticipantPreferenceRequest
from app.models.user import User
from app.services.backup_service import (
    BACKUP_REGISTER,
    BACKUP_REGISTER_DOC,
    EVENT_SCOPE_OVERRIDES,
    KNOWN_GAP_PREFIX,
    NOT_CARRIED,
    REASON_TAGS,
    RESTORE_VERBS,
    exported_columns,
    export_event_zip,
)

# The v1.0.4m event builder, imported rather than copied. That file is the
# only coverage the restore path has and must not be edited.
from tests.test_v1_0_4m_backup_exclusions import _build_event

pytestmark = pytest.mark.asyncio

FIX = (
    "Add it to BACKUP_REGISTER in backup_service.py: whether export writes "
    "it, what restore does with it, and why."
)


# ─── Which tables belong to an event ──────────────────────────────────

def _event_scoped_tables() -> set[str]:
    """Every table with a path of foreign keys to `events`, plus the
    overrides for references that have no foreign key to follow."""
    tables = Base.metadata.tables
    refs = {
        name: {fk.column.table.name for fk in tbl.foreign_keys}
        for name, tbl in tables.items()
    }

    scoped = set()
    for start in tables:
        seen: set[str] = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur == "events":
                scoped.add(start)
                break
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(refs.get(cur, ()))

    return scoped | set(EVENT_SCOPE_OVERRIDES)


# ─── 1. Classification ────────────────────────────────────────────────

async def test_1_every_event_scoped_table_is_classified():
    scoped = _event_scoped_tables()
    carried = set(BACKUP_REGISTER)
    not_carried = set(NOT_CARRIED)

    overlap = carried & not_carried
    assert not overlap, (
        f"{', '.join(sorted(overlap))}: listed as both carried and not "
        f"carried. Decide which."
    )

    unclassified = scoped - carried - not_carried
    assert not unclassified, (
        "These tables belong to an event and the backup does not know about "
        f"them: {', '.join(sorted(unclassified))}. {FIX} Or add the table to "
        "NOT_CARRIED with a reason."
    )

    unknown = (carried | not_carried) - scoped
    assert not unknown, (
        f"These tables are classified but are not event-scoped tables: "
        f"{', '.join(sorted(unknown))}. Either the table no longer exists, "
        f"or it does not belong to an event and should not be in the register."
    )

    missing_override = set(EVENT_SCOPE_OVERRIDES) - set(Base.metadata.tables)
    assert not missing_override, (
        f"EVENT_SCOPE_OVERRIDES names tables that do not exist: "
        f"{', '.join(sorted(missing_override))}."
    )


# ─── 2. Columns ───────────────────────────────────────────────────────

async def test_2_register_columns_match_the_models():
    problems = []
    for table, rule in BACKUP_REGISTER.items():
        actual = set(Base.metadata.tables[table].columns.keys())
        declared = set(rule.columns)

        for name in sorted(actual - declared):
            problems.append(
                f"{table}.{name} is a new column and the backup register "
                f"does not know about it. {FIX}"
            )
        for name in sorted(declared - actual):
            problems.append(
                f"{table}.{name} is in the backup register but not on the "
                f"model. If the column was renamed or dropped, update the "
                f"register to match."
            )

    assert not problems, "\n".join(problems)


# ─── 3. Declarations ──────────────────────────────────────────────────

async def test_3_every_declaration_is_legal():
    problems = []

    def check_reason(where: str, reason: str) -> None:
        if reason.startswith(KNOWN_GAP_PREFIX):
            gap = reason[len(KNOWN_GAP_PREFIX):]
            if not gap.startswith("BACKUP-") or not gap[len("BACKUP-"):].isdigit():
                problems.append(
                    f"{where}: reason {reason!r} must name a filed backlog "
                    f"id, as in 'known_gap:BACKUP-2'."
                )
        elif reason not in REASON_TAGS:
            problems.append(
                f"{where}: reason {reason!r} is not one of "
                f"{sorted(REASON_TAGS)} and is not a "
                f"'{KNOWN_GAP_PREFIX}BACKUP-n' tag."
            )

    for table, rule in BACKUP_REGISTER.items():
        for name, col in rule.columns.items():
            where = f"{table}.{name}"

            if col.restore not in RESTORE_VERBS:
                problems.append(
                    f"{where}: restore verb {col.restore!r} is not one of "
                    f"{sorted(RESTORE_VERBS)}."
                )

            if col.restore in ("copied", "remapped") and not col.exported:
                problems.append(
                    f"{where}: restore is {col.restore!r}, which needs the "
                    f"column to be exported. Either export it, or say what "
                    f"restore really does with it."
                )

            if col.raw and not col.exported:
                problems.append(
                    f"{where}: marked raw, which only means anything for a "
                    f"column export writes."
                )

            faithful = (col.exported and col.restore in ("copied", "remapped"))
            if col.reason is None:
                if not (faithful or col.restore == "parent"):
                    problems.append(
                        f"{where}: exported={col.exported}, "
                        f"restore={col.restore!r}, so it is not carried "
                        f"faithfully and needs a reason. Use one of "
                        f"{sorted(REASON_TAGS)}, or "
                        f"'{KNOWN_GAP_PREFIX}BACKUP-n' if it is a real gap."
                    )
            else:
                check_reason(where, col.reason)

    for table, reason in NOT_CARRIED.items():
        check_reason(f"NOT_CARRIED[{table}]", reason)

    assert not problems, "\n".join(problems)

    # The register's own explanation has to stay in step with the sets it
    # describes, or it stops being the thing a reader can trust.
    for verb in RESTORE_VERBS:
        assert verb in BACKUP_REGISTER_DOC, (
            f"restore verb {verb!r} is not explained in BACKUP_REGISTER_DOC."
        )
    for tag in REASON_TAGS:
        assert tag in BACKUP_REGISTER_DOC, (
            f"reason tag {tag!r} is not explained in BACKUP_REGISTER_DOC."
        )
    assert KNOWN_GAP_PREFIX in BACKUP_REGISTER_DOC


# ─── 4. Export agrees with the register ───────────────────────────────

async def _add_the_remaining_rows(db, src) -> None:
    """The v1.0.4m event leaves several members empty, so on its own it
    cannot check them. Add rows here, on top of the imported builder, so
    test 4 covers every member rather than half of them.

    v1.0.4s: check-in joined the register, and a newly carried table has to
    show a row or test 4 cannot check it against the register. Two fields
    and two ticks, which is also what `checkin.json` needs to be a real
    sample of both of its lists.
    """
    author = (await db.execute(select(User).limit(1))).scalars().first()
    ev = src["event"]
    p1 = src["p1"]

    cf = CustomFieldDefinition(
        event_id=ev.id, label="T-shirt size", field_type="text",
        options=None, is_required=False, sort_order=0,
    )
    db.add(cf)
    await db.flush()
    db.add(CustomFieldValue(participant_id=p1.id, field_id=cf.id, value="M"))

    db.add(EventFieldConfig(
        event_id=ev.id, field_name="phone", is_enabled=True, is_required=False,
    ))

    mark = MarkDefinition(
        event_id=ev.id, name="Leader", colour="#4682B4",
        visible_in=["allocation"],
    )
    db.add(mark)
    await db.flush()
    db.add(MarkAssignment(mark_id=mark.id, participant_id=p1.id, event_id=ev.id))

    db.add(ParticipantPreferenceRequest(
        event_id=ev.id, participant_id=p1.id,
        preferred_participant_number=None, preferred_name="Quentin Two",
        preferred_details=None, category_scope="all", resolved=False,
    ))

    # v1.0.4s: two check-in columns and a tick on each, so both of
    # checkin.json's lists carry a row.
    ci_fields = []
    for field_name, order in (("Wristband", 0), ("Key handed over", 1)):
        f = CheckInField(event_id=ev.id, field_name=field_name, sort_order=order)
        db.add(f)
        ci_fields.append(f)
    await db.flush()
    for f in ci_fields:
        db.add(CheckInValue(
            event_id=ev.id, participant_id=p1.id, field_id=f.id, checked=True,
        ))

    # An event-level published note. No screen writes one (BACKUP-4), so
    # this is the only way notes.json is ever non-empty and the only way to
    # check the register against it.
    db.add(Note(
        notable_type="event", notable_id=ev.id, content="Check the minibus.",
        is_published=True, author_id=author.id,
    ))
    await db.flush()


def _members(content: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def _rows_for(table: str, rule, members: dict[str, bytes]) -> list[dict]:
    """The rows a member holds for one table, as dicts of written keys."""
    raw = members[rule.member]

    if rule.member.endswith(".csv"):
        # Header-only when there are no rows; the header IS the key list.
        text = raw.decode("utf-8-sig")
        header = text.splitlines()[0]
        return [dict.fromkeys(header.split(","), None)]

    payload = json.loads(raw.decode("utf-8"))
    if rule.key is not None:
        payload = payload[rule.key]

    if table == "custom_field_values":
        # Adapter: this member is written as {participant id: [{field_id,
        # value}]}, so the participant id is the map key rather than a key
        # in the row. Rebuild it as rows, participant id first, which is
        # the order the register declares.
        return [
            {"participant_id": pid} | entry
            for pid, entries in payload.items()
            for entry in entries
        ]

    if isinstance(payload, dict):      # event.json is one object, not a list
        return [payload]
    return payload


async def test_4_export_writes_exactly_what_the_register_declares(db):
    src = await _build_event(db)
    await _add_the_remaining_rows(db, src)

    members = _members(await export_event_zip(src["event"].id, db, mode="full"))

    problems = []
    checked = []
    for table, rule in BACKUP_REGISTER.items():
        expected = list(exported_columns(table))
        rows = _rows_for(table, rule, members)
        if not rows:
            problems.append(
                f"{table}: no rows in {rule.member}, so the register cannot "
                f"be checked against it. Give the test event a row."
            )
            continue
        checked.append(table)
        for i, row in enumerate(rows):
            if list(row.keys()) != expected:
                problems.append(
                    f"{table} row {i} in {rule.member} writes "
                    f"{list(row.keys())} but the register declares "
                    f"{expected}. Export takes its field list from the "
                    f"register, so a mismatch means a key is written by "
                    f"hand somewhere. {FIX}"
                )

    assert not problems, "\n".join(problems)
    assert len(checked) == len(BACKUP_REGISTER)

    # Structure mode empties the person-linked members, as it does today.
    s = _members(await export_event_zip(src["event"].id, db, mode="structure"))
    assert json.loads(s["allocations.json"]) == []
    assert json.loads(s["allocation_exclusions.json"]) == []
    assert json.loads(s["preferences.json"]) == []
    assert json.loads(s["marks.json"])["assignments"] == []
    assert json.loads(s["custom_fields.json"])["values"] == {}
    csv_text = s["participants.csv"].decode("utf-8-sig")
    assert csv_text.splitlines()[1:] == [], "structure mode must have no participant rows"
