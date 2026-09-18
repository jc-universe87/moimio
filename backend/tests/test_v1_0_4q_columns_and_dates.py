"""v1.0.4q — the columns the backup dropped, and the dates it re-wrote.

BACKUP-2 listed columns export never wrote, so an organiser's own settings
and rules came back at their defaults: a room's mark restriction, its
keep-as-is lock, a group type's translated name, whether a custom field was
admin-only. BACKUP-8 was simpler and wider: every restored row was dated the
day of the restore, so "Registered at", the sort order and the registration
sparkline all became meaningless.

Both are closed here. Every case is checked through the column's real reader
where one exists, and the reader is named in the test:

  mark_restriction        the engine's mark_eligible, via run_engine
  is_kept                 the engine, which treats a kept unit as claimed
  exclusive_group_codes   the engine's PASS 1 exclusive claim
  cluster_behaviour       _mark_behaviour_for
  show_in_form            list_custom_fields_public, the public form endpoint
  name_key                core/default_type_names, the app's own key sets
  timezone                nothing: see test 7
  the timestamps          the stored values, and the events-list ordering
"""

import copy
import csv
import io
import json
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.api.custom_fields import list_custom_fields_public
from app.core.default_type_names import ITEM_LABEL_KEYS, NAME_KEYS
from app.models.allocation_category import AllocationCategory
from app.models.allocation_unit import AllocationUnit
from app.models.custom_field import CustomFieldDefinition
from app.models.event import Event
from app.models.mark import MarkAssignment, MarkDefinition
from app.models.participant import Participant
from app.services.allocation_service import _mark_behaviour_for
from app.services.backup_service import (
    BACKUP_REGISTER,
    CLUSTER_BEHAVIOURS,
    confirm_restore,
    export_event_zip,
)
from app.services.engine_service import run_engine

from tests.conftest import make_event, make_participant, make_unit, make_user

pytestmark = pytest.mark.asyncio

TZ = timezone(timedelta(hours=2))
T_EVENT = datetime(2025, 11, 4, 9, 15, tzinfo=TZ)
T_LATER = datetime(2026, 1, 20, 17, 5, tzinfo=TZ)
T_CHECKIN = datetime(2026, 6, 2, 8, 40, tzinfo=TZ)
DEAD_ID = "00000000-0000-4000-8000-00000000dead"

# Every key v1.0.4q added to the file, by member. Test 1 strips these to make
# a file with the pre-q shape.
NEW_KEYS = {
    "event.json": ("timezone", "is_archived"),
    "custom_fields.json:definitions": ("show_in_form",),
    "field_configs.json": ("updated_at",),
    "allocation_categories.json": (
        "name_key", "item_label_key", "exclusive_group_codes", "updated_at",
    ),
    "allocation_units.json": ("mark_restriction", "is_kept", "updated_at"),
    "allocations.json": ("updated_at",),
    "marks.json:definitions": ("cluster_behaviour",),
    "preferences.json": ("resolved_note",),
    "notes.json": ("updated_at",),
}
NEW_CSV_COLUMNS = ("override_group_room", "checked_in_at", "updated_at")


# ─── ZIP helpers ──────────────────────────────────────────────────────

def _members(content: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def _rezip(members: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, raw in members.items():
            zf.writestr(name, raw)
    return out.getvalue()


def _edit(content: bytes, name: str, mutate) -> bytes:
    members = _members(content)
    payload = json.loads(members[name].decode("utf-8"))
    result = mutate(payload)
    members[name] = json.dumps(
        payload if result is None else result, indent=2, default=str
    ).encode("utf-8")
    return _rezip(members)


def _drop_csv_columns(content: bytes, columns) -> bytes:
    """Rewrite participants.csv without the named columns, through the csv
    module so quoted cells survive."""
    members = _members(content)
    text = members["participants.csv"].decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    keep = [c for c in (reader.fieldnames or []) if c not in columns]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=keep, lineterminator="\r\n")
    writer.writeheader()
    for row in reader:
        writer.writerow({k: row.get(k) for k in keep})
    members["participants.csv"] = ("﻿" + buf.getvalue()).encode("utf-8")
    return _rezip(members)


# ─── A source event with every newly carried column set ───────────────

async def _source(db, *, archived=True, tz="Europe/London"):
    user = await make_user(db, email=f"q-{uuid.uuid4().hex[:8]}@test.local")
    ev = Event(
        name="Autumn Weekend", description="Two nights.", location="The Barn",
        settings={"require_email_confirmation": True},
        created_by=user.id, timezone=tz, is_archived=archived,
        created_at=T_EVENT, updated_at=T_LATER,
    )
    db.add(ev)
    await db.flush()

    mark = MarkDefinition(
        event_id=ev.id, name="Leader", colour="#AA3311",
        visible_in=["allocation"], cluster_behaviour="together",
        created_at=T_EVENT,
    )
    db.add(mark)
    await db.flush()

    cat = AllocationCategory(
        event_id=ev.id, name="Bedrooms", item_label="Room",
        rule_type="exclusive", sort_order=1, name_key="rooms",
        item_label_key="room", exclusive_group_codes=True,
        created_at=T_EVENT, updated_at=T_LATER,
    )
    db.add(cat)
    await db.flush()

    unit = AllocationUnit(
        category_id=cat.id, name="Loft", description="Under the eaves",
        capacity=6, sort_order=1, mark_restriction=mark.id, is_kept=True,
        created_at=T_EVENT, updated_at=T_LATER,
    )
    db.add(unit)
    await db.flush()

    p = Participant(
        event_id=ev.id, first_name="Ida", last_name="Ionescu",
        email="ida@test.local", gdpr_consent=True, checked_in=True,
        checked_in_at=T_CHECKIN, override_group_room=True,
        created_at=T_EVENT, updated_at=T_LATER,
    )
    db.add(p)
    await db.flush()
    db.add(MarkAssignment(event_id=ev.id, mark_id=mark.id,
                          participant_id=p.id, created_at=T_EVENT))

    cf = CustomFieldDefinition(
        event_id=ev.id, label="Internal note", field_type="text",
        sort_order=0, show_in_form=False, created_at=T_EVENT,
    )
    db.add(cf)
    await db.flush()
    return {"user": user, "event": ev, "mark": mark, "cat": cat,
            "unit": unit, "participant": p, "cf": cf}


async def _restore(db, content, actor):
    result = await confirm_restore(
        content, db, actor_user_id=actor.id if actor else None)
    return result, uuid.UUID(result["new_event_id"])


async def _one(db, model, event_id, **where):
    stmt = select(model).where(model.event_id == event_id)
    for k, v in where.items():
        stmt = stmt.where(getattr(model, k) == v)
    return (await db.execute(stmt)).scalars().first()


async def _restored_unit(db, event_id):
    cat = await _one(db, AllocationCategory, event_id)
    return (await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id == cat.id)
    )).scalars().first()


# ─── 1. A file with the pre-q shape ───────────────────────────────────

async def test_1_an_older_file_restores_with_defaults(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    for member, keys in NEW_KEYS.items():
        name, _, inner = member.partition(":")

        def strip(payload, keys=keys, inner=inner):
            rows = payload[inner] if inner else payload
            rows = rows if isinstance(rows, list) else [rows]
            for row in rows:
                for key in keys:
                    row.pop(key, None)

        content = _edit(content, name, strip)
    content = _drop_csv_columns(content, NEW_CSV_COLUMNS)

    result, new_id = await _restore(db, content, src["user"])
    ev = await db.get(Event, new_id)
    cat = await _one(db, AllocationCategory, new_id)
    unit = await _restored_unit(db, new_id)
    person = await _one(db, Participant, new_id)
    cf = await _one(db, CustomFieldDefinition, new_id)
    mark = await _one(db, MarkDefinition, new_id)

    # The new columns fall back to their model defaults.
    assert ev.timezone == "UTC"
    assert ev.is_archived is False
    assert cat.name_key is None and cat.item_label_key is None
    assert cat.exclusive_group_codes is False
    assert unit.mark_restriction is None
    assert unit.is_kept is False
    assert mark.cluster_behaviour == "none"
    assert cf.show_in_form is True
    assert person.override_group_room is False
    assert person.checked_in_at is None

    # created_at was exported before this release, so an older file has it
    # and it is now restored.
    assert ev.created_at == T_EVENT
    assert person.created_at == T_EVENT


# ─── 2. A structure backup is dated when it is restored ───────────────

async def test_2_a_structure_backup_takes_the_restores_own_dates(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="structure")
    _, new_id = await _restore(db, content, src["user"])

    ev = await db.get(Event, new_id)
    cat = await _one(db, AllocationCategory, new_id)
    unit = await _restored_unit(db, new_id)

    # A template is a new event built from somebody's setup, so its rows are
    # dated by the restore, not by the file.
    #
    # Checked as "not the source value, and recent" rather than against a
    # marker taken in the test: the server default is `now()`, which in
    # Postgres is the TRANSACTION timestamp, so it is a little EARLIER than
    # any wall-clock reading taken after the restore began.
    now = datetime.now(timezone.utc)
    for row in (ev, cat, unit):
        assert row.created_at != T_EVENT, f"{type(row).__name__} kept a source date"
        assert abs(now - row.created_at) < timedelta(minutes=5)
    assert ev.updated_at != T_LATER


# ─── 3. A full backup keeps every original timestamp ──────────────────

async def test_3_a_full_backup_keeps_every_timestamp(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])

    ev = await db.get(Event, new_id)
    cat = await _one(db, AllocationCategory, new_id)
    unit = await _restored_unit(db, new_id)
    person = await _one(db, Participant, new_id)

    assert ev.created_at == T_EVENT and ev.updated_at == T_LATER
    assert cat.created_at == T_EVENT and cat.updated_at == T_LATER
    assert unit.created_at == T_EVENT and unit.updated_at == T_LATER
    assert person.created_at == T_EVENT and person.updated_at == T_LATER
    assert person.checked_in_at == T_CHECKIN


async def test_3b_restored_events_sort_where_the_originals_did(db):
    """The events list orders by created_at, so a restored event has to sit
    where its original sat, not at the top."""
    older = await _source(db)
    newer_user = await make_user(db, email="q-newer@test.local")
    newer = Event(
        name="Later Event", created_by=newer_user.id,
        created_at=datetime(2026, 5, 5, 9, 0, tzinfo=TZ),
    )
    db.add(newer)
    await db.flush()

    for source in (older["event"], newer):
        content = await export_event_zip(source.id, db, mode="full")
        await _restore(db, content, older["user"])

    restored = (await db.execute(
        select(Event.name, Event.created_at)
        .where(Event.name.like("%(Restored)"))
        .order_by(Event.created_at)
    )).all()
    assert [r[0] for r in restored] == [
        "Autumn Weekend (Restored)", "Later Event (Restored)",
    ], "restored events must keep the order their originals had"


# ─── 4. mark_restriction, through the engine ──────────────────────────

async def test_4_mark_restriction_is_translated_and_still_binds(db):
    src = await _source(db)
    # Somebody without the mark, so the restriction has something to refuse.
    await make_participant(db, src["event"].id, first_name="Jonas",
                           email="jonas@test.local")
    # A kept unit is treated as claimed, so unlock it for this test and give
    # the group type a second, open unit for the unmarked person to go to.
    src["unit"].is_kept = False
    await make_unit(db, src["cat"].id, "Annexe", capacity=6)
    await db.flush()

    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])

    mark = await _one(db, MarkDefinition, new_id)
    cat = await _one(db, AllocationCategory, new_id)
    loft = (await db.execute(
        select(AllocationUnit).where(
            AllocationUnit.category_id == cat.id, AllocationUnit.name == "Loft")
    )).scalar_one()

    # Translated to the restored mark, not left pointing at the old one.
    assert loft.mark_restriction == mark.id
    assert loft.mark_restriction != src["mark"].id

    # And the rule binds: the engine's mark_eligible keeps the unmarked
    # person out of the restricted unit.
    jonas = await _one(db, Participant, new_id, email="jonas@test.local")
    proposal = await run_engine(db, new_id, cat.id, mode="replace")
    in_loft = proposal["proposed"].get(str(loft.id), [])
    assert str(jonas.id) not in in_loft, (
        "a participant without the mark must not be placed in a unit "
        "restricted to it"
    )


async def test_5_an_unknown_mark_restriction_becomes_null(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")
    damaged = _edit(
        content, "allocation_units.json",
        lambda rows: rows[0].update({"mark_restriction": DEAD_ID}),
    )
    result, new_id = await _restore(db, damaged, src["user"])

    unit = await _restored_unit(db, new_id)
    # It is a real foreign key, so a dead id cannot be written. NULL is the
    # model default and what the database itself does when a mark goes.
    assert unit.mark_restriction is None
    assert result["defaulted"]["allocation_units.mark_restriction"] == 1


# ─── 6. name_key and item_label_key ───────────────────────────────────

async def test_6_known_keys_come_back_and_unknown_ones_do_not(db):
    src = await _source(db)
    assert src["cat"].name_key in NAME_KEYS
    assert src["cat"].item_label_key in ITEM_LABEL_KEYS

    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])
    cat = await _one(db, AllocationCategory, new_id)
    assert cat.name_key == "rooms"
    assert cat.item_label_key == "room"

    damaged = _edit(
        content, "allocation_categories.json",
        lambda rows: rows[0].update(
            {"name_key": "not_a_key", "item_label_key": "rooms"}),
    )
    result, new_id = await _restore(db, damaged, src["user"])
    cat = await _one(db, AllocationCategory, new_id)
    # An unknown key, and a key belonging to the OTHER field, both become
    # NULL, which is how the stored name shows through.
    assert cat.name_key is None
    assert cat.item_label_key is None
    assert result["defaulted"]["allocation_categories.name_key"] == 1
    assert result["defaulted"]["allocation_categories.item_label_key"] == 1


# ─── 7. timezone ──────────────────────────────────────────────────────

async def test_7_timezone_is_carried_as_it_is(db):
    """The app has no notion of a valid zone: there is no VALID_TIMEZONES
    beside VALID_DATE_FORMATS, no check on the event or preference write
    paths, and nothing anywhere imports zoneinfo. So per the release's own
    rule for a value the app does not validate, restore carries the column
    as it is rather than inventing a rule the product does not have."""
    src = await _source(db, tz="Europe/London")
    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])
    assert (await db.get(Event, new_id)).timezone == "Europe/London"

    odd = _edit(content, "event.json",
                lambda ev: ev.update({"timezone": "Mars/Olympus_Mons"}))
    result, new_id = await _restore(db, odd, src["user"])
    assert (await db.get(Event, new_id)).timezone == "Mars/Olympus_Mons"
    assert "events.timezone" not in result["defaulted"]

    # A wrong TYPE is still damage, because the column is text.
    wrong = _edit(content, "event.json", lambda ev: ev.update({"timezone": 7}))
    result, new_id = await _restore(db, wrong, src["user"])
    assert (await db.get(Event, new_id)).timezone == "UTC"
    assert result["defaulted"]["events.timezone"] == 1


# ─── 8. cluster_behaviour ─────────────────────────────────────────────

async def test_8_cluster_behaviour_is_carried_and_takes_effect(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])

    mark = await _one(db, MarkDefinition, new_id)
    cat = await _one(db, AllocationCategory, new_id)
    assert mark.cluster_behaviour == "together"
    # The real reader. No per-group-type override is set, so anything but
    # "none" can only come from the mark's own restored column.
    assert await _mark_behaviour_for(
        db, event_id=new_id, category_id=cat.id, mark_id=str(mark.id),
    ) == "together"

    damaged = _edit(
        content, "marks.json",
        lambda payload: payload["definitions"][0].update(
            {"cluster_behaviour": "sideways"}),
    )
    result, new_id = await _restore(db, damaged, src["user"])
    mark = await _one(db, MarkDefinition, new_id)
    assert "sideways" not in CLUSTER_BEHAVIOURS
    assert mark.cluster_behaviour == "none"
    assert result["defaulted"]["mark_definitions.cluster_behaviour"] == 1


# ─── 9. events.created_by ─────────────────────────────────────────────

async def test_9_created_by_is_the_restoring_user(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    _, with_actor = await _restore(db, content, src["user"])
    assert (await db.get(Event, with_actor)).created_by == src["user"].id

    _, no_actor = await _restore(db, content, None)
    # v1.0.4zd: with nobody to name, this is now None.
    #
    # It used to be the new event's OWN id, a stand-in that was only ever
    # safe because `events.created_by` had no foreign key. USER-1 gave it one
    # (ON DELETE SET NULL, so an event survives its creator's departure), and
    # an event id is not a user id — the old stand-in would now violate that
    # key. None is the truthful answer in any case: nobody on this instance
    # created the event, and the column is nullable for exactly that reason.
    assert (await db.get(Event, no_actor)).created_by is None


# ─── 10. show_in_form ─────────────────────────────────────────────────

async def test_10_an_admin_only_field_stays_off_the_public_form(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])

    cf = await _one(db, CustomFieldDefinition, new_id)
    assert cf.show_in_form is False
    # The real reader: the endpoint the public registration form calls.
    public = await list_custom_fields_public(event_id=new_id, db=db)
    assert [f.label for f in public] == [], (
        "an admin-only field must not reappear on the public form"
    )


# ─── 11. is_kept ──────────────────────────────────────────────────────

async def test_11_a_kept_unit_stays_kept(db):
    src = await _source(db)
    await make_participant(db, src["event"].id, first_name="Karin",
                           email="karin@test.local")
    open_unit = await make_unit(db, src["cat"].id, "Annexe", capacity=6)
    await db.flush()

    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])

    cat = await _one(db, AllocationCategory, new_id)
    units = {u.name: u for u in (await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id == cat.id)
    )).scalars().all()}
    assert units["Loft"].is_kept is True
    assert units["Annexe"].is_kept is False

    # The real reader: the engine treats a kept unit as already claimed and
    # proposes nobody into it.
    proposal = await run_engine(db, new_id, cat.id, mode="replace")
    assert proposal["proposed"].get(str(units["Loft"].id), []) == [], (
        "the engine must leave a kept unit alone"
    )


# ─── 12. exclusive_group_codes ────────────────────────────────────────

async def test_12_exclusive_group_codes_still_takes_effect(db):
    """With the flag on, a group-code cluster claims its whole unit: nobody
    else is placed there even though capacity is left."""
    src = await _source(db)
    src["unit"].is_kept = False
    src["unit"].mark_restriction = None
    src["unit"].capacity = 6
    for first, email in (("Lena", "lena@test.local"), ("Mo", "mo@test.local")):
        await make_participant(db, src["event"].id, first_name=first,
                               email=email, group_code="SMITH")
    await make_participant(db, src["event"].id, first_name="Nils",
                           email="nils@test.local")
    await db.flush()

    content = await export_event_zip(src["event"].id, db, mode="full")
    _, new_id = await _restore(db, content, src["user"])

    cat = await _one(db, AllocationCategory, new_id)
    assert cat.exclusive_group_codes is True
    unit = (await db.execute(
        select(AllocationUnit).where(
            AllocationUnit.category_id == cat.id, AllocationUnit.name == "Loft")
    )).scalar_one()

    proposal = await run_engine(db, new_id, cat.id, mode="replace")
    placed = set(proposal["proposed"].get(str(unit.id), []))
    coded = {
        str(p.id) for p in (await db.execute(
            select(Participant).where(
                Participant.event_id == new_id,
                Participant.group_code == "SMITH")
        )).scalars().all()
    }
    assert placed == coded, (
        "the cluster's unit must hold the cluster and nobody else"
    )


# ─── 13. The register ─────────────────────────────────────────────────

async def test_13_no_backup_2_or_backup_8_gap_remains():
    gaps = sorted({
        col.reason
        for rule in BACKUP_REGISTER.values()
        for col in rule.columns.values()
        if col.reason and col.reason.startswith("known_gap:")
    })
    # This release's own two gaps, and only those. An absolute list of
    # what is left would make every later release come back and edit this
    # test; each release proves its own work instead (Johannes, session 86).
    assert "known_gap:BACKUP-2" not in gaps
    assert "known_gap:BACKUP-8" not in gaps
    # The "no known_gap at all" check belongs to the LAST backup release
    # before v1.0.5, as BACKUP_REGISTER_DOC says. Not here, and not early.
