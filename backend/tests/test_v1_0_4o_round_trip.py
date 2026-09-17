"""v1.0.4o Part A — the round-trip net.

The v1.0.4n register says, column by column, what a backup carries and what
restore does with it. Nothing checked the second half of that claim: a column
the register calls `copied` could quietly not be restored at all, exactly as
`allocation_categories.name_key` was read by restore for a field export never
wrote, for releases, with no test to notice.

This file is that check. It builds an event in which every column the
register calls faithful holds a value restore could not produce by ignoring
the file, backs it up, restores it, and asserts every such value came back.

The net reads the register rather than a list of its own, so a later release
that removes a `known_gap` tag brings that column under the net with no
change here.

  1. test_1_the_fixture_is_not_lazy   — the fixture meets its own rules
  2. test_2_round_trip_is_faithful    — every faithful column round trips

An entry tagged `known_gap` is skipped: it is a filed gap, not a regression.
"""

import copy
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.database import Base
import app.models  # noqa: F401  — populate Base.metadata, as conftest does
from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_unit import AllocationUnit
from app.models.checkin_field import CheckInField
from app.models.checkin_value import CheckInValue
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event import Event
from app.models.event_field_config import EventFieldConfig
from app.models.mark import MarkAssignment, MarkDefinition
from app.models.note import Note
from app.models.participant import Participant, RegistrationStatus
from app.models.preference_request import ParticipantPreferenceRequest
from app.models.user import User, UserRole
from app.services.allocation_service import add_exclusion
from app.services.backup_service import (
    ALL_PRIVATE_NOTES,
    BACKUP_REGISTER,
    confirm_restore,
    export_event_zip,
)

pytestmark = pytest.mark.asyncio

# v1.0.4p: an id no map will ever know. Live data can hold one of these —
# deleting a group type leaves its id behind in group_code_categories — so
# the net carries one and checks it comes back untouched rather than dropped.
DEAD_ID = "00000000-0000-4000-8000-0000000dead0"

# v1.0.4q: fixed timestamps, clearly in the past and distinct from each
# other, so a restored value cannot be mistaken for one the restore minted
# and the ordering of the three participants is checkable. Every timestamp
# column in the schema is timezone-aware, and only an aware value is
# accepted on restore.
TZ = timezone(timedelta(hours=1))
T_EVENT = datetime(2026, 1, 5, 8, 30, tzinfo=TZ)
T_MARK = datetime(2026, 1, 6, 9, 0, tzinfo=TZ)
T_CAT = datetime(2026, 1, 7, 10, 0, tzinfo=TZ)
T_UNIT = datetime(2026, 1, 8, 11, 0, tzinfo=TZ)
T_PEOPLE = {
    "anna@test.local": datetime(2026, 2, 1, 12, 0, tzinfo=TZ),
    "bruno@test.local": datetime(2026, 2, 2, 13, 0, tzinfo=TZ),
    "carla@test.local": datetime(2026, 2, 3, 14, 0, tzinfo=TZ),
}
T_CHECKIN = datetime(2026, 6, 1, 16, 45, tzinfo=TZ)
T_ROW = datetime(2026, 3, 3, 15, 0, tzinfo=TZ)


# ─── The natural key each table is matched by ─────────────────────────
#
# Every id changes on restore, so a restored row is found by something the
# fixture keeps unique. Documented here rather than buried in the checks.

# A key must NOT be derived from a reference the net is testing. Keying a
# mark assignment by (participant email, mark name) looks natural, but then a
# restore that linked every assignment to the wrong mark shows up as a
# missing ROW rather than as a wrong `mark_id`, and the failure cannot name
# the column. So the link tables are keyed by participant alone, which the
# fixture keeps unique — one allocation, one exclusion, one mark assignment
# and one custom field value per person. If that uniqueness ever broke, two
# rows would collapse onto one key and test 1's "at least two rows" check
# would fail.
NATURAL_KEY = {
    "events": "the event itself — one row, found by the restored event id",
    "participants": "email",
    "custom_field_definitions": "label",
    "custom_field_values": "participant email (one value each in the fixture)",
    "event_field_configs": "field_name",
    "checkin_fields": "field_name",
    "checkin_values": "participant email (one tick each in the fixture)",
    "allocation_categories": "name",
    "allocation_units": "name (unique across group types in the fixture)",
    "allocations": "participant email (one allocation each in the fixture)",
    "allocation_category_exclusions":
        "participant email (one exclusion each in the fixture)",
    "mark_definitions": "name",
    "mark_assignments":
        "participant email (one assignment each in the fixture)",
    "participant_preference_requests": "participant email (one row each)",
    "notes": "content",
}

# Deliberate transformations restore applies to a `copied` value. Each one
# needs a reason, and there is exactly one today.
TRANSFORMS = {
    # The restore screen promises a renamed draft
    # (portability.restore_as_new_hint).
    ("events", "name"): lambda v: f"{v} (Restored)",
}


# v1.0.4s: one narrow exemption from the "must differ from the default"
# rule below, and the only one.
#
# `notes.is_published` is a boolean whose two states are both meaningful:
# True is a note the team shares, False is a private one. A private note
# therefore HOLDS the column's default, and the fixture has to carry one,
# because restore forcing every note published is the very fault v1.0.4s
# fixed. So for this column the fixture rule is replaced: it must hold at
# least one row in each state. Test 2 then proves both states round trip,
# which is what the rule was for.
BOTH_STATES_REQUIRED = {("notes", "is_published")}


def _model_default(table: str, column: str):
    """(has_default, value) for a column's Python or server default.

    The fixture rule is that a `copied` value must differ from whatever
    restore would end up with by leaving the column out of its insert.
    """
    col = Base.metadata.tables[table].columns[column]
    if col.default is not None:
        arg = col.default.arg
        if callable(arg):
            try:
                return True, arg(None)
            except TypeError:
                return True, arg()
        return True, arg
    if col.server_default is not None:
        raw = str(getattr(col.server_default.arg, "text", col.server_default.arg)).strip()
        # v1.0.4q: interpret a SIMPLE literal, so the comparison is a real
        # one. Before this, a column whose only default is the database's
        # was compared against the SQL text — `False == "false"` is never
        # true, so the self-check waved through a fixture sitting on its own
        # default. v1.0.4q is the first release to carry three such columns
        # (is_kept, is_archived, timezone).
        #
        # A function default like now() or clock_timestamp() is deliberately
        # left as its text: no timestamp can equal it, which is the right
        # answer, because a timestamp is never "at its default".
        lowered = raw.lower()
        if lowered in ("true", "false"):
            return True, lowered == "true"
        if len(raw) >= 2 and raw[0] == raw[-1] == "'":
            return True, raw[1:-1]
        if "(" not in raw:
            return True, raw
        return True, raw
    return False, None


def _cols(table: str, verb: str, *, gaps: bool = False) -> list[str]:
    """Register columns for one table with this restore verb. Entries
    tagged `known_gap` are left out unless asked for: they are filed gaps,
    and a later release removing the tag pulls them in automatically."""
    return [
        name for name, col in BACKUP_REGISTER[table].columns.items()
        if col.restore == verb and (gaps or not col.reason)
    ]


# ─── The fixture ──────────────────────────────────────────────────────

async def _build(db, extra_notes: bool = False) -> dict:
    """An event with at least two rows of every carried table, every
    faithful column holding a non-default value.

    `extra_notes` adds the notes v1.0.4s made carryable: one on a
    participant, one on a group type, one on a unit, and one private note.
    It is OFF by default on purpose. test_v1_0_4o_damaged_files.py imports
    this builder and its note cases were written against a file holding the
    two published event notes alone, so the net switches the keyword on for
    its own two tests and leaves that file the fixture it was written
    against.
    """
    user = await _make_user(db, "restorer@test.local")
    author = await _make_user(db, "author@test.local")

    ev = Event(
        name="Spring Retreat 2026",
        description="Three days at the lake.",
        location="Lake House, Windermere",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        # Every key differs from the model's default settings dict.
        settings={"require_email_confirmation": True, "default_language": "de"},
        created_by=user.id,
        # v1.0.4q. "UTC" is the server default and false is is_archived's,
        # so both of these differ from what restore would produce by
        # ignoring the file.
        timezone="Europe/London",
        is_archived=True,
        created_at=T_EVENT,
        updated_at=T_EVENT,
    )
    db.add(ev)
    await db.flush()

    # ── Marks ──
    # v1.0.4q: ahead of the units, because a unit's mark_restriction names a
    # mark and has to be set at construction. Setting it afterwards would be
    # an UPDATE, and `onupdate=func.now()` would then overwrite the unit's
    # restored updated_at — the trap this release had to avoid.
    marks = {}
    for name, colour, visible, behaviour in (
        ("Team leader", "#AA3311", ["allocation", "people"], "together"),
        ("First aider", "#22AA55", ["people", "checkin"], "split"),
    ):
        m = MarkDefinition(
            event_id=ev.id, name=name, colour=colour, visible_in=visible,
            cluster_behaviour=behaviour, created_at=T_MARK,
        )
        db.add(m)
        marks[name] = m
    await db.flush()

    # ── Participants: three, so a wrong link cannot pass by accident ──
    people = {}
    spec = [
        ("anna@test.local", "Anna", "Alpha", "female", date(1990, 4, 5),
         "+44 7700 900001", "1 High Street", "Scotland", "St Andrews Kirk",
         "Nut allergy.", "SMITH", 101, RegistrationStatus.CONFIRMED, "de"),
        ("bruno@test.local", "Bruno", "Beta", "male", date(1985, 11, 30),
         "+44 7700 900002", "2 Mill Lane", "Wales", "Bethel Chapel",
         "Arrives late on Friday.", "JONES", 102,
         RegistrationStatus.CANCELLED, "ko"),
        ("carla@test.local", "Carla", "Gamma", "female", date(2001, 1, 17),
         "+44 7700 900003", "3 Kirk Road", "Ireland", "Grace Fellowship",
         "Vegetarian.", "SMITH", 103, RegistrationStatus.CONFIRMED, "fr"),
    ]
    for (email, first, last, gender, dob, phone, address, country, church,
         message, code, number, status, lang) in spec:
        p = Participant(
            event_id=ev.id, first_name=first, last_name=last, email=email,
            gender=gender, date_of_birth=dob, phone=phone, address=address,
            country=country, church_organisation=church, message=message,
            group_code=code, participant_number=number,
            registration_status=status, gdpr_consent=True, checked_in=True,
            preferred_language=lang,
            # v1.0.4q. override_group_room defaults False, and the three
            # created_at values are distinct so their order is checkable.
            override_group_room=True,
            checked_in_at=T_CHECKIN,
            created_at=T_PEOPLE[email],
            updated_at=T_PEOPLE[email],
        )
        db.add(p)
        people[email] = p
    await db.flush()

    # ── Group types and units ──
    cats = {}
    for name, item_label, desc, rule, order, name_key, label_key in (
        ("Bedrooms", "Room", "Sleeping arrangements", "overlapping", 5,
         "rooms", "room"),
        ("Workshops", "Session", "Optional afternoon tracks", "overlapping", 6,
         "small_groups", "group"),
    ):
        c = AllocationCategory(
            event_id=ev.id, name=name, item_label=item_label,
            description=desc, rule_type=rule, sort_order=order,
            is_default=True,
            # v1.0.4q. Both keys are ones the app knows (NAME_KEYS and
            # ITEM_LABEL_KEYS), and each field takes only its own set.
            name_key=name_key, item_label_key=label_key,
            exclusive_group_codes=True,
            created_at=T_CAT, updated_at=T_CAT,
        )
        db.add(c)
        cats[name] = c
    await db.flush()

    units = {}
    for name, cat, desc, cap, gender, order, mark in (
        ("Lakeside", "Bedrooms", "Two bunks, view of the water", 7, "female", 2,
         "Team leader"),
        ("Hillside", "Bedrooms", "Quiet end of the corridor", 13, "male", 3,
         "First aider"),
        ("Pottery", "Workshops", "In the old barn", 9, "female", 4,
         "Team leader"),
    ):
        u = AllocationUnit(
            category_id=cats[cat].id, name=name, description=desc,
            capacity=cap, gender_restriction=gender, sort_order=order,
            # v1.0.4q. mark_restriction is the one newly carried column that
            # is remapped rather than copied; is_kept defaults false.
            mark_restriction=marks[mark].id,
            is_kept=True,
            created_at=T_UNIT, updated_at=T_UNIT,
        )
        db.add(u)
        units[name] = u
    await db.flush()

    db.add(Allocation(event_id=ev.id,
                      participant_id=people["anna@test.local"].id,
                      unit_id=units["Lakeside"].id,
                      created_at=T_ROW, updated_at=T_ROW))
    db.add(Allocation(event_id=ev.id,
                      participant_id=people["bruno@test.local"].id,
                      unit_id=units["Hillside"].id,
                      created_at=T_ROW, updated_at=T_ROW))
    await db.flush()

    # Exclusions through the real write path. Neither participant holds a
    # unit in the group type they are excluded from, so the v1.0.4m rule
    # (the exclusion wins, the placement is dropped) never fires here.
    await add_exclusion(db, cats["Workshops"].id, people["anna@test.local"].id)
    await add_exclusion(db, cats["Workshops"].id, people["bruno@test.local"].id)

    # v1.0.4q: add_exclusion takes no timestamp, so these are set after the
    # fact. Safe here and nowhere else: allocation_category_exclusions has no
    # updated_at, so the UPDATE cannot trip an `onupdate`.
    for row in (await db.execute(select(AllocationCategoryExclusion))).scalars().all():
        row.created_at = T_ROW
    await db.flush()

    # ── Mark assignments ──
    db.add(MarkAssignment(event_id=ev.id, mark_id=marks["Team leader"].id,
                          participant_id=people["anna@test.local"].id,
                          created_at=T_ROW))
    db.add(MarkAssignment(event_id=ev.id, mark_id=marks["First aider"].id,
                          participant_id=people["bruno@test.local"].id,
                          created_at=T_ROW))

    # ── Custom fields ──
    cfs = {}
    for label, ftype, options, order in (
        ("T-shirt size", "select", {"choices": ["S", "M", "L"]}, 3),
        ("Years attending", "number", {"min": 0, "max": 40}, 4),
    ):
        cf = CustomFieldDefinition(
            event_id=ev.id, label=label, field_type=ftype, options=options,
            is_required=True, sort_order=order,
            # v1.0.4q: False marks a field admin-only, and True is the
            # default, so False is what proves it was carried.
            show_in_form=False,
            created_at=T_ROW,
        )
        db.add(cf)
        cfs[label] = cf
    await db.flush()

    db.add(CustomFieldValue(participant_id=people["anna@test.local"].id,
                            field_id=cfs["T-shirt size"].id, value="M"))
    db.add(CustomFieldValue(participant_id=people["bruno@test.local"].id,
                            field_id=cfs["Years attending"].id, value="12"))

    # ── Registration form toggles ──
    for field_name in ("phone", "address"):
        db.add(EventFieldConfig(event_id=ev.id, field_name=field_name,
                                is_enabled=True, is_required=True,
                                created_at=T_ROW, updated_at=T_ROW))

    # ── Preferences ──
    for email, pref_number, pref_name, details, scope in (
        ("anna@test.local", 102, "Bruno Beta",
         "Same street, known each other for years",
         # Two different known targets, so a wrong mapping cannot pass.
         [str(cats["Bedrooms"].id), str(cats["Workshops"].id)]),
        ("bruno@test.local", 101, "Anna Alpha", "Travelling together", "all"),
    ):
        db.add(ParticipantPreferenceRequest(
            event_id=ev.id, participant_id=people[email].id,
            preferred_participant_number=pref_number, preferred_name=pref_name,
            preferred_details=details, category_scope=scope, resolved=True,
            # v1.0.4q: `resolved` without its note gave no reason.
            resolved_note="Seated together at the Friday meal.",
            created_at=T_ROW,
        ))

    # ── Ids inside JSON (v1.0.4p) ──
    # Set here rather than at construction, because these columns hold ids of
    # rows the fixture creates after the row that carries them.
    #
    # Carla's group code is limited to two group types AND carries one id no
    # map can know, which is what live data looks like after a group type has
    # been deleted. Anna and Bruno keep null, meaning every group type.
    #
    # It goes on Carla, the LAST participant by number, on purpose: serialised
    # into participants.csv this value contains commas, so it is quoted, and
    # test_v1_0_4o_damaged_files.py edits the FIRST data row with a plain
    # split on ",". Keeping row one free of quoted commas leaves that file
    # untouched, which it has to be.
    people["carla@test.local"].group_code_categories = [
        str(cats["Bedrooms"].id), str(cats["Workshops"].id), DEAD_ID,
    ]

    # Two entries naming two different marks, plus values that must survive
    # untouched: `behaviour` inside each entry, and the keys beside them.
    cats["Bedrooms"].settings = {
        "engine": {
            "use_group_codes": True,
            "group_remaining_by_gender": False,
            "split_oversized_groups": False,
            "mark_priorities": [
                {"id": str(marks["Team leader"].id), "behaviour": "together"},
                {"id": str(marks["First aider"].id), "behaviour": "split"},
            ],
        },
        "title": "Bedroom rules",
    }
    cats["Workshops"].settings = {
        "engine": {
            "use_group_codes": False,
            "mark_priorities": [
                {"id": str(marks["First aider"].id), "behaviour": "together"},
            ],
        },
    }
    await db.flush()

    # ── Check-in (v1.0.4s) ──
    # Two columns, each with a non-zero sort_order, because 0 is the
    # column's own default. One tick each for Anna and Bruno, on different
    # columns: keyed by participant alone, as the other link tables are, so
    # a restore that pointed every tick at the wrong column shows up as a
    # wrong `field_id` rather than as a missing row.
    ci_fields = {}
    for field_name, order in (("Wristband", 4), ("Key handed over", 5)):
        f = CheckInField(event_id=ev.id, field_name=field_name,
                         sort_order=order, created_at=T_ROW, updated_at=T_ROW)
        db.add(f)
        ci_fields[field_name] = f
    await db.flush()

    for email, field_name in (("anna@test.local", "Wristband"),
                              ("bruno@test.local", "Key handed over")):
        db.add(CheckInValue(
            event_id=ev.id, participant_id=people[email].id,
            field_id=ci_fields[field_name].id,
            # False is the column's default, so True is what proves the
            # tick was carried. A tick that is OFF is checked in
            # test_v1_0_4s_checkin_and_notes.py, where the rule is not
            # "differ from the default".
            checked=True,
            created_at=T_ROW, updated_at=T_ROW,
        ))

    # ── Notes ──
    # Two published event notes, which is all export carried before
    # v1.0.4s.
    for content in ("Minibus leaves at nine.", "Kitchen code is on the door."):
        db.add(Note(notable_type="event", notable_id=ev.id, content=content,
                    is_published=True, author_id=author.id,
                    created_at=T_ROW, updated_at=T_ROW))

    if extra_notes:
        # v1.0.4s: the three other types a note can be about, and one
        # private note, so both states of `is_published` round trip.
        # Contents are unique: the net matches a note by its content.
        for notable_type, notable_id, content, published in (
            ("participant", people["anna@test.local"].id,
             "Anna is collecting the keys on Friday.", True),
            ("category", cats["Bedrooms"].id,
             "Bedrooms were re-numbered after the refit.", True),
            ("unit", units["Lakeside"].id,
             "Lakeside window does not close properly.", True),
            ("participant", people["bruno@test.local"].id,
             "Private: Bruno asked me not to seat him by the door.", False),
        ):
            db.add(Note(
                notable_type=notable_type, notable_id=notable_id,
                content=content, is_published=published, author_id=author.id,
                created_at=T_ROW, updated_at=T_ROW,
            ))

    await db.flush()

    return {
        "user": user, "author": author, "event": ev, "people": people,
        "cats": cats, "units": units, "marks": marks, "cfs": cfs,
        "ci_fields": ci_fields,
    }


async def _make_user(db, email: str) -> User:
    u = User(
        email=email,
        hashed_password="$2b$12$round.trip.net.placeholder.hash.only....",
        full_name=f"Net {email.split('@')[0].title()}",
        role=UserRole.SUPER_ADMIN,
    )
    db.add(u)
    await db.flush()
    return u


# ─── Reading the source and the restored event back ───────────────────

async def _snapshot(db, event_id: uuid.UUID) -> dict[str, dict]:
    """{table: {natural key: row}} for one event, source or restored."""
    async def rows(stmt):
        return list((await db.execute(stmt)).scalars().all())

    ev = await db.get(Event, event_id)

    people = await rows(select(Participant).where(Participant.event_id == event_id))
    by_pid = {p.id: p.email for p in people}

    cats = await rows(select(AllocationCategory)
                      .where(AllocationCategory.event_id == event_id))
    cat_ids = [c.id for c in cats]
    by_cat = {c.id: c.name for c in cats}

    units = await rows(select(AllocationUnit)
                       .where(AllocationUnit.category_id.in_(cat_ids or [uuid.uuid4()])))

    allocs = await rows(select(Allocation).where(Allocation.event_id == event_id))
    excls = await rows(
        select(AllocationCategoryExclusion).where(
            AllocationCategoryExclusion.allocation_category_id.in_(
                cat_ids or [uuid.uuid4()])))

    marks = await rows(select(MarkDefinition)
                       .where(MarkDefinition.event_id == event_id))
    mas = await rows(select(MarkAssignment)
                     .where(MarkAssignment.event_id == event_id))

    cfs = await rows(select(CustomFieldDefinition)
                     .where(CustomFieldDefinition.event_id == event_id))
    cfvs = await rows(select(CustomFieldValue)
                      .where(CustomFieldValue.participant_id.in_(
                          list(by_pid) or [uuid.uuid4()])))

    fcs = await rows(select(EventFieldConfig)
                     .where(EventFieldConfig.event_id == event_id))
    prefs = await rows(select(ParticipantPreferenceRequest)
                       .where(ParticipantPreferenceRequest.event_id == event_id))

    ci_fields = await rows(select(CheckInField)
                           .where(CheckInField.event_id == event_id))
    ci_values = await rows(select(CheckInValue)
                           .where(CheckInValue.event_id == event_id))

    # v1.0.4s: a note can be about the event, a participant, a group type or
    # a unit, so the snapshot gathers all four. `notable_id` alone is enough
    # to select on, because every id in the schema is a distinct UUID; the
    # type still matters to the check, and test 2 resolves it by type.
    note_targets = [event_id, *by_pid, *cat_ids, *[u.id for u in units]]
    notes = await rows(select(Note).where(Note.notable_id.in_(note_targets)))

    return {
        "events": {"the event": ev},
        "participants": {p.email: p for p in people},
        "custom_field_definitions": {c.label: c for c in cfs},
        "custom_field_values": {
            by_pid[v.participant_id]: v for v in cfvs
        },
        "event_field_configs": {f.field_name: f for f in fcs},
        "checkin_fields": {f.field_name: f for f in ci_fields},
        "checkin_values": {
            by_pid[v.participant_id]: v for v in ci_values
        },
        "allocation_categories": {c.name: c for c in cats},
        "allocation_units": {u.name: u for u in units},
        "allocations": {
            by_pid[a.participant_id]: a for a in allocs
        },
        "allocation_category_exclusions": {
            by_pid[x.participant_id]: x for x in excls
        },
        "mark_definitions": {m.name: m for m in marks},
        "mark_assignments": {
            by_pid[a.participant_id]: a for a in mas
        },
        "participant_preference_requests": {
            by_pid[r.participant_id]: r for r in prefs
        },
        "notes": {n.content: n for n in notes},
    }


# ─── 1. The fixture is not lazy ───────────────────────────────────────

async def test_1_the_fixture_is_not_lazy(db):
    src = await _build(db, extra_notes=True)
    snap = await _snapshot(db, src["event"].id)

    problems = []
    for table in BACKUP_REGISTER:
        rows = snap[table]
        assert table in NATURAL_KEY, f"{table} has no documented natural key"

        # events is the event being backed up, so there is only ever one.
        if table != "events" and len(rows) < 2:
            problems.append(
                f"{table}: the fixture has {len(rows)} row(s). Two or more, "
                f"so a wrong link cannot pass by accident."
            )

        for key, row in rows.items():
            for name in _cols(table, "copied"):
                if (table, name) in BOTH_STATES_REQUIRED:
                    continue  # a different rule, applied once per table below
                value = getattr(row, name)
                if value is None:
                    problems.append(
                        f"{table}.{name} is None on row {key!r}. The register "
                        f"calls it copied, so the fixture must give it a value "
                        f"restore cannot produce by ignoring the file."
                    )
                    continue
                has_default, default = _model_default(table, name)
                if has_default and value == default:
                    problems.append(
                        f"{table}.{name} on row {key!r} holds {value!r}, which "
                        f"is the column's own default. Restore ignoring the "
                        f"file would produce the same value, so the round trip "
                        f"check would pass for the wrong reason."
                    )

    # v1.0.4s: the exempt columns, checked their own way.
    for table, name in sorted(BOTH_STATES_REQUIRED):
        states = {getattr(row, name) for row in snap[table].values()}
        if states != {True, False}:
            problems.append(
                f"{table}.{name} is {sorted(map(str, states))} across every "
                f"row of the fixture. Both states are needed: one row in "
                f"each, so that test 2 proves the value is carried rather "
                f"than forced."
            )

    # v1.0.4p: the three columns that hold ids inside JSON. A list of ids
    # that resolve to nothing proves nothing about remapping, so check the
    # fixture really carries ids the maps will know — two different ones in
    # each, so a wrong mapping cannot pass — plus, for
    # group_code_categories, one that no map can know.
    live_cats = {str(c.id) for c in snap["allocation_categories"].values()}
    live_marks = {str(m.id) for m in snap["mark_definitions"].values()}

    scoped = snap["participants"]["carla@test.local"].group_code_categories or []
    known = [i for i in scoped if i in live_cats]
    if len(set(known)) < 2:
        problems.append(
            f"participants.group_code_categories holds {len(set(known))} id(s) "
            f"the maps will know, out of {scoped!r}. Two different ones are "
            f"needed, or a wrong mapping passes."
        )
    if not [i for i in scoped if i not in live_cats]:
        problems.append(
            "participants.group_code_categories holds no unresolvable id. "
            "Live data can carry one after a group type is deleted, and the "
            "net has to prove it comes back untouched rather than dropped."
        )

    scope = snap["participant_preference_requests"]["anna@test.local"].category_scope
    in_scope = [i for i in (scope or []) if i in live_cats]
    if len(set(in_scope)) < 2:
        problems.append(
            f"participant_preference_requests.category_scope holds "
            f"{len(set(in_scope))} id(s) the maps will know, out of {scope!r}. "
            f"Two different ones are needed."
        )

    prioritised = set()
    for cat in snap["allocation_categories"].values():
        engine = (cat.settings or {}).get("engine") or {}
        for entry in engine.get("mark_priorities") or []:
            mid = entry.get("id") if isinstance(entry, dict) else entry
            if isinstance(mid, str) and mid in live_marks:
                prioritised.add(mid)
    if len(prioritised) < 2:
        problems.append(
            f"allocation_categories.settings prioritises {len(prioritised)} "
            f"mark(s) the maps will know. Two different ones are needed."
        )

    assert not problems, "\n".join(problems)


# ─── 2. Every faithful column round trips ─────────────────────────────

async def test_2_round_trip_is_faithful(db):
    src = await _build(db, extra_notes=True)
    before = await _snapshot(db, src["event"].id)

    # v1.0.4s: every private note goes in, so the private note in the
    # fixture round trips and `is_published` is checked in both states. A
    # caller that makes no choice carries no private note at all, which is
    # tested in test_v1_0_4s_checkin_and_notes.py, not here.
    content = await export_event_zip(
        src["event"].id, db, mode="full", private_notes=ALL_PRIVATE_NOTES)
    result = await confirm_restore(content, db, actor_user_id=src["user"].id)
    new_event_id = uuid.UUID(result["new_event_id"])
    after = await _snapshot(db, new_event_id)

    # The referent of each remapped foreign key, source side to restored
    # side, expressed through the natural keys above.
    def before_email(pid):
        return {p.id: p.email for p in before["participants"].values()}[pid]

    def before_cat(cid):
        return {c.id: c.name for c in before["allocation_categories"].values()}[cid]

    def before_unit(uid):
        return {u.id: u.name for u in before["allocation_units"].values()}[uid]

    def before_mark(mid):
        return {m.id: m.name for m in before["mark_definitions"].values()}[mid]

    def before_cf(fid):
        return {c.id: c.label for c in before["custom_field_definitions"].values()}[fid]

    def before_checkin_field(fid):
        return {f.id: f.field_name for f in before["checkin_fields"].values()}[fid]

    # v1.0.4s: which map a note's `notable_id` goes through depends on its
    # `notable_type`, so the expected value is built the same way: by type,
    # through the source-to-restored correspondence by name, never through
    # the id under test.
    def expect_notable_id(note):
        if note.notable_type == "event":
            return new_event_id
        if note.notable_type == "participant":
            return after["participants"][before_email(note.notable_id)].id
        if note.notable_type == "category":
            return after["allocation_categories"][before_cat(note.notable_id)].id
        if note.notable_type == "unit":
            return after["allocation_units"][before_unit(note.notable_id)].id
        raise AssertionError(
            f"the fixture holds a note of type {note.notable_type!r}, which "
            f"restore cannot place. Add the type to restore and here, or "
            f"take it out of the fixture."
        )

    # v1.0.4p: the three columns that hold ids inside JSON. The expected
    # value is built through the source-to-restored correspondence by NAME,
    # never through the ids under test, and an id neither side knows is
    # expected back exactly as it was.
    def cat_name_by_src_id() -> dict[str, str]:
        return {str(c.id): c.name for c in before["allocation_categories"].values()}

    def mark_name_by_src_id() -> dict[str, str]:
        return {str(m.id): m.name for m in before["mark_definitions"].values()}

    def expect_cat_ids(value):
        if not isinstance(value, list):
            return value            # null, or "all"
        names = cat_name_by_src_id()
        out = []
        for element in value:
            name = names.get(element) if isinstance(element, str) else None
            out.append(
                str(after["allocation_categories"][name].id) if name else element
            )
        return out

    def expect_settings(value):
        if not isinstance(value, dict):
            return value
        engine = value.get("engine")
        if not isinstance(engine, dict):
            return value
        entries = engine.get("mark_priorities")
        if not isinstance(entries, list):
            return value
        names = mark_name_by_src_id()

        def one(entry):
            if isinstance(entry, str):
                name = names.get(entry)
                return str(after["mark_definitions"][name].id) if name else entry
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                name = names.get(entry["id"])
                if not name:
                    return entry
                return {**entry, "id": str(after["mark_definitions"][name].id)}
            return entry

        out = copy.deepcopy(value)
        out["engine"]["mark_priorities"] = [one(e) for e in entries]
        return out

    def before_mark_name(mid):
        return {m.id: m.name for m in before["mark_definitions"].values()}[mid]

    RESOLVE = {
        ("notes", "notable_id"): expect_notable_id,
        ("checkin_values", "participant_id"):
            lambda r: after["participants"][before_email(r.participant_id)].id,
        ("checkin_values", "field_id"):
            lambda r: after["checkin_fields"][before_checkin_field(r.field_id)].id,
        # v1.0.4q: a real foreign key to a mark, translated through the name
        # correspondence, never through the id under test.
        ("allocation_units", "mark_restriction"):
            lambda r: after["mark_definitions"][before_mark_name(r.mark_restriction)].id,
        ("participants", "group_code_categories"):
            lambda r: expect_cat_ids(r.group_code_categories),
        ("participant_preference_requests", "category_scope"):
            lambda r: expect_cat_ids(r.category_scope),
        ("allocation_categories", "settings"):
            lambda r: expect_settings(r.settings),
        ("allocation_units", "category_id"):
            lambda r: after["allocation_categories"][before_cat(r.category_id)].id,
        ("allocations", "participant_id"):
            lambda r: after["participants"][before_email(r.participant_id)].id,
        ("allocations", "unit_id"):
            lambda r: after["allocation_units"][before_unit(r.unit_id)].id,
        ("allocation_category_exclusions", "allocation_category_id"):
            lambda r: after["allocation_categories"][before_cat(r.allocation_category_id)].id,
        ("allocation_category_exclusions", "participant_id"):
            lambda r: after["participants"][before_email(r.participant_id)].id,
        ("mark_assignments", "mark_id"):
            lambda r: after["mark_definitions"][before_mark(r.mark_id)].id,
        ("mark_assignments", "participant_id"):
            lambda r: after["participants"][before_email(r.participant_id)].id,
        ("custom_field_values", "participant_id"):
            lambda r: after["participants"][before_email(r.participant_id)].id,
        ("custom_field_values", "field_id"):
            lambda r: after["custom_field_definitions"][before_cf(r.field_id)].id,
        ("participant_preference_requests", "participant_id"):
            lambda r: after["participants"][before_email(r.participant_id)].id,
    }

    problems = []
    checked = []

    for table in BACKUP_REGISTER:
        src_rows, new_rows = before[table], after[table]
        checked.append(table)

        missing = set(src_rows) - set(new_rows)
        if missing:
            problems.append(
                f"{table}: these rows did not come back at all: "
                f"{sorted(map(str, missing))}. Matched by "
                f"{NATURAL_KEY[table]}."
            )

        for key in sorted(set(src_rows) & set(new_rows), key=str):
            old, new = src_rows[key], new_rows[key]

            for name in _cols(table, "copied"):
                want = getattr(old, name)
                transform = TRANSFORMS.get((table, name))
                if transform:
                    want = transform(want)
                got = getattr(new, name)
                if got != want:
                    problems.append(
                        f"{table}.{name} on row {key!r}: the register calls it "
                        f"copied, but the backup carried {getattr(old, name)!r} "
                        f"and the restore produced {got!r} (expected {want!r})."
                    )

            for name in _cols(table, "remapped"):
                got = getattr(new, name)
                resolver = RESOLVE.get((table, name))
                if resolver is None:
                    # A primary key that seeds one of the restore's id maps.
                    # Nothing points at it by value, so the check is that it
                    # really was renumbered.
                    if got == getattr(old, name):
                        problems.append(
                            f"{table}.{name} on row {key!r} is still "
                            f"{got!r}. A remapped id must be renumbered so the "
                            f"restored event is independent of the original."
                        )
                    continue
                want = resolver(old)
                if got != want:
                    problems.append(
                        f"{table}.{name} on row {key!r} points at {got!r}, "
                        f"not at the restored counterpart {want!r} of the row "
                        f"the backup named."
                    )

            for name in _cols(table, "parent"):
                got = getattr(new, name)
                if got != new_event_id:
                    problems.append(
                        f"{table}.{name} on row {key!r} is {got!r}, not the "
                        f"restored event {new_event_id!r}."
                    )

    assert not problems, "\n".join(problems)
    assert len(checked) == len(BACKUP_REGISTER) == 15, (
        f"checked {len(checked)} of {len(BACKUP_REGISTER)} carried tables"
    )
