"""v1.0.4s — check-in and notes in a backup.

Two things an organiser had put into Moimio did not survive a restore.

**Check-in.** The columns an organiser added to the check-in desk, and every
tick against them, were not in a backup at all. A restored event came back
with an empty check-in desk and nothing to say so.

**Notes.** Notes were carried, but only the event-level ones, and no screen
writes those, so in practice `notes.json` was always empty. Restore also
pointed every note at the restored event and forced it published, so a note
about one person would have come back on the event, and a private note would
have come back shared.

The private-note rule this release adds is the reason most of these tests
exist. A private note is visible in the app only to its author, not even to
a Super Admin, and any event admin can download an event backup. So the
export asks its caller whose private notes belong in the file, and the
default carries none:

  • the per-event download passes the downloader's id
  • the leaving export passes ALL_PRIVATE_NOTES, because that file is the
    organisation's own copy of its own data

Endpoint functions are called directly with an explicit db and user, the way
tests/test_v1_0_4k_exclusion_api_surface.py does.
"""

import io
import json
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.api.export import export_backup_zip
from app.api.notes import list_notes
from app.cli import export_all
from app.models.allocation_category import AllocationCategory
from app.models.allocation_unit import AllocationUnit
from app.models.checkin_field import CheckInField
from app.models.checkin_value import CheckInValue
from app.models.note import Note
from app.models.participant import Participant
from app.services.backup_service import (
    ALL_PRIVATE_NOTES,
    BACKUP_REGISTER,
    NOT_CARRIED,
    confirm_restore,
    export_event_zip,
)
from app.services.participant_service import soft_delete_participant

from tests.conftest import (
    make_category,
    make_event,
    make_participant,
    make_unit,
    make_user,
)

pytestmark = pytest.mark.asyncio

TZ = timezone(timedelta(hours=1))
T_ROW = datetime(2026, 4, 7, 9, 30, tzinfo=TZ)

# The four notes every export carries whatever the private-notes choice is.
PUBLISHED = {
    "The minibus leaves at nine.",
    "Anna is collecting the keys.",
    "Bedrooms were re-numbered after the refit.",
    "Lakeside window does not close.",
}
MINE = "Private, mine: check Anna's travel dates."
THEIRS = "Private, theirs: Bruno asked to sit away from the door."


# ─── Fixture ──────────────────────────────────────────────────────────

async def _source(db) -> dict:
    """One event carrying every case these tests need: two check-in
    columns with a ticked and an unticked value, a removed participant with
    a tick and a note of her own, notes of all four types, and two private
    notes by different people."""
    restorer = await make_user(db, email="restorer-s@test.local")
    other = await make_user(db, email="other-admin-s@test.local")

    ev = await make_event(db, name="Check-in Source")
    # v1.0.4s (BACKUP-11): these two are the organiser's own contact
    # details. A full backup keeps them; a structure backup does not.
    ev.settings = {
        "require_email_confirmation": True,
        "email_from_name": "Grace Fellowship Office",
        "email_reply_to": "office@grace.example",
    }
    cat = await make_category(db, ev.id, name="Bedrooms")
    unit = await make_unit(db, cat.id, "Lakeside", capacity=6)

    anna = await make_participant(db, ev.id, first_name="Anna",
                                  email="anna-s@test.local")
    bruno = await make_participant(db, ev.id, first_name="Bruno",
                                   email="bruno-s@test.local")
    carla = await make_participant(db, ev.id, first_name="Carla",
                                   email="carla-s@test.local")

    fields = {}
    for field_name, order in (("Wristband", 1), ("Key handed over", 2)):
        f = CheckInField(event_id=ev.id, field_name=field_name,
                         sort_order=order, created_at=T_ROW, updated_at=T_ROW)
        db.add(f)
        fields[field_name] = f
    await db.flush()

    # Anna: one column ticked, the other explicitly not. Bruno: one ticked.
    # Carla is removed below, so her tick must never leave the instance.
    for person, field_name, checked in (
        (anna, "Wristband", True),
        (anna, "Key handed over", False),
        (bruno, "Wristband", True),
        (carla, "Wristband", True),
    ):
        db.add(CheckInValue(
            event_id=ev.id, participant_id=person.id,
            field_id=fields[field_name].id, checked=checked,
            created_at=T_ROW, updated_at=T_ROW,
        ))

    for notable_type, notable_id, content, published, author in (
        ("event", ev.id, "The minibus leaves at nine.", True, restorer),
        ("participant", anna.id, "Anna is collecting the keys.", True, restorer),
        ("category", cat.id, "Bedrooms were re-numbered after the refit.",
         True, other),
        ("unit", unit.id, "Lakeside window does not close.", True, other),
        ("participant", anna.id, MINE, False, restorer),
        ("participant", bruno.id, THEIRS, False, other),
        # A note about somebody who has been removed. It must not be
        # exported, exactly as her check-in tick must not.
        ("participant", carla.id, "Carla withdrew, keep her file.", True,
         restorer),
    ):
        db.add(Note(
            notable_type=notable_type, notable_id=notable_id, content=content,
            is_published=published, author_id=author.id,
            created_at=T_ROW, updated_at=T_ROW,
        ))
    await db.flush()

    await soft_delete_participant(db, carla)
    await db.flush()

    return {"restorer": restorer, "other": other, "event": ev, "cat": cat,
            "unit": unit, "anna": anna, "bruno": bruno, "carla": carla,
            "fields": fields}


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


def _member(content: bytes, name: str):
    return json.loads(_members(content)[name].decode("utf-8"))


def _note_contents(content: bytes) -> set[str]:
    return {n["content"] for n in _member(content, "notes.json")}


async def _restore(db, content: bytes, src) -> uuid.UUID:
    result = await confirm_restore(db=db, content=content,
                                   actor_user_id=src["restorer"].id)
    return uuid.UUID(result["new_event_id"])


async def _restored_checkin(db, event_id) -> dict[tuple[str, str], bool]:
    """{(participant email, column name): tick} for a restored event."""
    emails = dict((await db.execute(
        select(Participant.id, Participant.email)
        .where(Participant.event_id == event_id)
    )).all())
    names = dict((await db.execute(
        select(CheckInField.id, CheckInField.field_name)
        .where(CheckInField.event_id == event_id)
    )).all())
    values = (await db.execute(
        select(CheckInValue).where(CheckInValue.event_id == event_id)
    )).scalars().all()
    return {
        (emails[v.participant_id], names[v.field_id]): v.checked
        for v in values
    }


# ─── 1. Check-in round trip ───────────────────────────────────────────

async def test_1_checkin_columns_and_ticks_come_back(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")
    new_id = await _restore(db, content, src)

    fields = (await db.execute(
        select(CheckInField).where(CheckInField.event_id == new_id)
        .order_by(CheckInField.sort_order)
    )).scalars().all()
    assert [(f.field_name, f.sort_order) for f in fields] == [
        ("Wristband", 1), ("Key handed over", 2),
    ]
    # New ids, so the restored event is independent of the original.
    assert {f.id for f in fields}.isdisjoint(
        {f.id for f in src["fields"].values()})

    # Linked to the restored people and the restored columns, with the tick
    # as it was — including the one that was deliberately NOT ticked.
    assert await _restored_checkin(db, new_id) == {
        ("anna-s@test.local", "Wristband"): True,
        ("anna-s@test.local", "Key handed over"): False,
        ("bruno-s@test.local", "Wristband"): True,
    }


# ─── 2. Check-in in structure mode ────────────────────────────────────

async def test_2_structure_mode_keeps_the_columns_and_no_ticks(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="structure")

    checkin = _member(content, "checkin.json")
    assert [f["field_name"] for f in checkin["fields"]] == [
        "Wristband", "Key handed over",
    ], "the columns are part of the event's shape"
    assert checkin["values"] == [], "a tick is personal"

    new_id = await _restore(db, content, src)
    assert await _restored_checkin(db, new_id) == {}


# ─── 3. Removed people ────────────────────────────────────────────────

async def test_3_a_removed_participant_takes_her_ticks_with_her(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    values = _member(content, "checkin.json")["values"]
    assert len(values) == 3, "Anna's two and Bruno's one, not Carla's"
    assert str(src["carla"].id) not in {v["participant_id"] for v in values}


# ─── 4. A file made before this release ───────────────────────────────

async def test_4_a_file_without_the_member_still_restores(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    members = _members(content)
    assert "checkin.json" in members, "it must be there before we take it away"
    del members["checkin.json"]

    new_id = await _restore(db, _rezip(members), src)
    assert await _restored_checkin(db, new_id) == {}
    # The rest of the event is unaffected.
    assert (await db.execute(
        select(Participant).where(Participant.event_id == new_id)
    )).scalars().all()


# ─── 5. A duplicated tick ─────────────────────────────────────────────

async def test_5_a_duplicated_tick_keeps_the_first(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    members = _members(content)
    checkin = json.loads(members["checkin.json"])
    # Found by what it is, never by its position: the export orders ticks by
    # created_at and then by id, and the fixture's three share a timestamp,
    # so which one comes first is decided by a random UUID.
    ticked = next(
        v for v in checkin["values"]
        if v["participant_id"] == str(src["anna"].id)
        and v["field_id"] == str(src["fields"]["Wristband"].id)
    )
    assert ticked["checked"] is True, "the fixture ticked this one"
    # The table is UNIQUE on (participant, field): letting a duplicate
    # reach the constraint would roll the whole restore back. Appended, so
    # the duplicate is the SECOND of the pair and "the first wins" means
    # the original.
    checkin["values"].append({**ticked, "id": str(uuid.uuid4()),
                              "checked": False})
    members["checkin.json"] = json.dumps(checkin, indent=2).encode("utf-8")

    new_id = await _restore(db, _rezip(members), src)
    restored = await _restored_checkin(db, new_id)
    assert len(restored) == 3
    assert restored[("anna-s@test.local", "Wristband")] is True, (
        "the first line wins, so the tick is the original one"
    )


# ─── 6. Notes round trip ──────────────────────────────────────────────

async def test_6_notes_come_back_on_what_they_are_about(db):
    src = await _source(db)
    content = await export_event_zip(
        src["event"].id, db, mode="full", private_notes=ALL_PRIVATE_NOTES)
    new_id = await _restore(db, content, src)

    new_cat = (await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == new_id)
    )).scalar_one()
    new_unit = (await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id == new_cat.id)
    )).scalar_one()
    people = {p.email: p for p in (await db.execute(
        select(Participant).where(Participant.event_id == new_id)
    )).scalars().all()}

    notes = (await db.execute(
        select(Note).where(Note.notable_id.in_(
            [new_id, new_cat.id, new_unit.id, *[p.id for p in people.values()]]
        ))
    )).scalars().all()
    placed = {n.content: (n.notable_type, n.notable_id) for n in notes}

    assert placed == {
        "The minibus leaves at nine.": ("event", new_id),
        "Anna is collecting the keys.":
            ("participant", people["anna-s@test.local"].id),
        "Bedrooms were re-numbered after the refit.": ("category", new_cat.id),
        "Lakeside window does not close.": ("unit", new_unit.id),
        MINE: ("participant", people["anna-s@test.local"].id),
        THEIRS: ("participant", people["bruno-s@test.local"].id),
    }

    by_content = {n.content: n for n in notes}
    # Both states carried, not forced.
    assert by_content[MINE].is_published is False
    assert by_content[THEIRS].is_published is False
    assert by_content["The minibus leaves at nine."].is_published is True
    # The author is whoever restored: the original author may have no
    # account on the receiving instance.
    assert {n.author_id for n in notes} == {src["restorer"].id}


# ─── 7. Which private notes an export carries ─────────────────────────

async def test_7_the_caller_chooses_whose_private_notes_go_in(db):
    src = await _source(db)

    async def contents(**kwargs):
        return _note_contents(
            await export_event_zip(src["event"].id, db, mode="full", **kwargs))

    # No choice: no private note at all. This is the default, so a caller
    # that has not thought about it cannot leak one.
    assert await contents() == PUBLISHED

    # A user id: that user's own private notes, and nobody else's.
    assert await contents(private_notes=src["restorer"].id) == PUBLISHED | {MINE}
    assert await contents(private_notes=src["other"].id) == PUBLISHED | {THEIRS}

    # The sentinel: every private note.
    assert await contents(private_notes=ALL_PRIVATE_NOTES) == (
        PUBLISHED | {MINE, THEIRS})


# ─── 8. The download endpoint ─────────────────────────────────────────

async def test_8_a_download_carries_the_downloaders_own_private_notes(db):
    src = await _source(db)

    mine = await export_backup_zip(
        event_id=src["event"].id, mode="full", db=db,
        current_user=src["restorer"])
    assert _note_contents(mine.body) == PUBLISHED | {MINE}

    # The same file downloaded by the other admin carries theirs instead.
    theirs = await export_backup_zip(
        event_id=src["event"].id, mode="full", db=db,
        current_user=src["other"])
    assert _note_contents(theirs.body) == PUBLISHED | {THEIRS}


# ─── 9. The leaving export ────────────────────────────────────────────

async def test_9_the_workspace_export_carries_every_private_note(db):
    src = await _source(db)

    archive = await export_all.build_archive(db)
    inner = _members(archive)[f"events/{src['event'].id}.zip"]
    assert _note_contents(inner) == PUBLISHED | {MINE, THEIRS}


# ─── 10. Structure mode ───────────────────────────────────────────────

async def test_10_structure_mode_carries_no_notes_and_no_sender_details(db):
    src = await _source(db)

    structure = await export_event_zip(
        src["event"].id, db, mode="structure",
        # Even asked for every private note, a structure backup has none:
        # notes are not part of an event's shape.
        private_notes=ALL_PRIVATE_NOTES)
    assert _member(structure, "notes.json") == []

    settings = _member(structure, "event.json")["settings"]
    assert "email_from_name" not in settings
    assert "email_reply_to" not in settings
    assert settings["require_email_confirmation"] is True, (
        "the rest of the settings are untouched"
    )

    full = await export_event_zip(src["event"].id, db, mode="full")
    full_settings = _member(full, "event.json")["settings"]
    assert full_settings["email_from_name"] == "Grace Fellowship Office"
    assert full_settings["email_reply_to"] == "office@grace.example"


# ─── 11. A note that cannot be placed ─────────────────────────────────

async def test_11_an_unplaceable_note_is_skipped_and_counted(db):
    src = await _source(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    members = _members(content)
    notes = json.loads(members["notes.json"])
    kept = len(notes)
    # A hand-edited file: one note about a participant the file does not
    # carry, and one of a type restore knows nothing about.
    notes.append({**notes[0], "id": str(uuid.uuid4()),
                  "notable_type": "participant",
                  "notable_id": str(uuid.uuid4()),
                  "content": "About somebody who is not in this file."})
    notes.append({**notes[0], "id": str(uuid.uuid4()),
                  "notable_type": "room",
                  "content": "About a room, whatever that is."})
    members["notes.json"] = json.dumps(notes, indent=2).encode("utf-8")

    result = await confirm_restore(db=db, content=_rezip(members),
                                   actor_user_id=src["restorer"].id)
    new_id = uuid.UUID(result["new_event_id"])

    assert result["skipped"]["notes.json"] == 2
    restored = (await db.execute(
        select(Note).where(Note.author_id == src["restorer"].id)
    )).scalars().all()
    assert len([n for n in restored
                if n.content == "About a room, whatever that is."]) == 0
    # And the restore succeeded: the event and its people are there.
    assert (await db.execute(
        select(Participant).where(Participant.event_id == new_id)
    )).scalars().all()
    assert kept == 4, "the four published notes, as the default carries them"


# ─── 12. A removed person's notes ─────────────────────────────────────

async def test_12_a_removed_participants_notes_are_not_exported(db):
    src = await _source(db)
    content = await export_event_zip(
        src["event"].id, db, mode="full", private_notes=ALL_PRIVATE_NOTES)

    assert "Carla withdrew, keep her file." not in _note_contents(content)
    assert _note_contents(content) == PUBLISHED | {MINE, THEIRS}


# ─── 13. A restored private note is still private ─────────────────────

async def test_13_a_restored_private_note_stays_private(db):
    src = await _source(db)
    content = await export_event_zip(
        src["event"].id, db, mode="full", private_notes=ALL_PRIVATE_NOTES)
    new_id = await _restore(db, content, src)

    anna = (await db.execute(
        select(Participant).where(
            Participant.event_id == new_id,
            Participant.email == "anna-s@test.local",
        )
    )).scalar_one()

    async def visible_to(user):
        listed = await list_notes(
            notable_type="participant", notable_id=anna.id, db=db,
            current_user=user)
        return {n["content"] for n in listed}

    # Through the notes API's own filter: published plus your own private.
    visible = await visible_to(src["restorer"])
    assert MINE in visible, "the restoring user authored it, so they see it"

    # And not to anybody else, Super Admin or not.
    assert MINE not in await visible_to(src["other"])
    assert "Anna is collecting the keys." in await visible_to(src["other"]), (
        "the published note is visible to both"
    )


# ─── 14. The register ─────────────────────────────────────────────────

async def test_14_the_register_records_this_release(db):
    tags = [
        col.reason for table in BACKUP_REGISTER.values()
        for col in table.columns.values() if col.reason
    ] + list(NOT_CARRIED.values())

    assert not [t for t in tags if t in
                ("known_gap:BACKUP-4", "known_gap:BACKUP-11")], (
        "BACKUP-4 and BACKUP-11 are closed by this release"
    )

    # A permission must never come from a file.
    assert NOT_CARRIED["event_user_assignments"] == "not_meaningful_elsewhere"

    # Check-in is carried now, so it is no longer in the not-carried list.
    assert "checkin_fields" in BACKUP_REGISTER
    assert "checkin_values" in BACKUP_REGISTER
    assert "checkin_fields" not in NOT_CARRIED
    assert "checkin_values" not in NOT_CARRIED

    # What is left in the register is deliberately NOT asserted here. An
    # absolute list would make every later release come back and edit this
    # test; each release proves its own work instead (Johannes, session 86).
    # The "no known_gap at all" check belongs to the LAST backup release
    # before v1.0.5, as BACKUP_REGISTER_DOC says. Not here, and not early.
