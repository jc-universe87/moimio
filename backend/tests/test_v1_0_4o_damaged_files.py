"""v1.0.4o Part B — a damaged backup file costs the damaged line, not the file.

A backup is a plain unsigned ZIP, so a hand-edited or truncated file is
expected input, not an attack. Before this release a single bad line could
roll the whole restore back: a missing key raised, a duplicate broke a
unique constraint, an explicit null hit a NOT NULL column, and invalid JSON
surfaced as a 500.

The rules these tests pin, from the release brief:

  - A damaged line costs that line and whatever depends on it.
  - A member that cannot be read at all refuses the file up front, at
    preview and at confirm alike, as a 422 with a key, never a 500.
  - A damaged value falls back to the column's OWN default, never to an
    invented one. No default and NOT NULL means the line goes.
  - Duplicates: the first wins.
  - Over-long text is shortened to the column's declared length.
  - One summary warning per damaged restore, with counts and no names.

Endpoint functions are called directly with an explicit db and user, the
way test_v1_0_4k_exclusion_api_surface.py does.
"""

import copy
import io
import json
import uuid
import zipfile

import pytest
from sqlalchemy import func, select
from starlette.datastructures import UploadFile

from app.core.exceptions import MoimioAppError
from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_unit import AllocationUnit
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event import Event
from app.models.event_field_config import EventFieldConfig
from app.models.mark import MarkAssignment, MarkDefinition
from app.models.note import Note
from app.models.participant import Participant, RegistrationStatus
from app.models.preference_request import ParticipantPreferenceRequest
from app.services import backup_service
from app.services.backup_service import confirm_restore, export_event_zip

from tests.test_v1_0_4o_round_trip import _build

pytestmark = pytest.mark.asyncio

EXCL_MEMBER = "allocation_exclusions.json"
# v1.0.4ze (STRINGS-1): its own key at last. This used to borrow
# `zip_missing_files`, which said "missing" about a member that is
# present and unreadable — so an organiser went looking for a file that
# was there. `zip_missing_files` still exists and is still correct for a
# member that genuinely is not in the archive.
REFUSAL_KEY = "errors.export.zip_unreadable"


# ─── ZIP surgery ──────────────────────────────────────────────────────

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
    """Load one JSON member, hand it to `mutate`, write it back."""
    members = _members(content)
    payload = json.loads(members[name].decode("utf-8"))
    result = mutate(payload)
    members[name] = json.dumps(
        payload if result is None else result, indent=2
    ).encode("utf-8")
    return _rezip(members)


def _edit_csv(content: bytes, mutate) -> bytes:
    """Load participants.csv as a list of lines, hand it to `mutate`."""
    members = _members(content)
    lines = members["participants.csv"].decode("utf-8-sig").split("\r\n")
    members["participants.csv"] = ("﻿" + "\r\n".join(mutate(lines))).encode("utf-8")
    return _rezip(members)


async def _counts(db, event_id) -> dict[str, int]:
    """Row counts per table for one restored event, for compact asserts."""
    async def n(stmt) -> int:
        return (await db.execute(stmt)).scalar_one()

    cat_ids = list((await db.execute(
        select(AllocationCategory.id)
        .where(AllocationCategory.event_id == event_id)
    )).scalars().all()) or [uuid.uuid4()]
    p_ids = list((await db.execute(
        select(Participant.id).where(Participant.event_id == event_id)
    )).scalars().all()) or [uuid.uuid4()]

    return {
        "participants": await n(select(func.count(Participant.id))
                                .where(Participant.event_id == event_id)),
        "categories": await n(select(func.count(AllocationCategory.id))
                              .where(AllocationCategory.event_id == event_id)),
        "units": await n(select(func.count(AllocationUnit.id))
                         .where(AllocationUnit.category_id.in_(cat_ids))),
        "allocations": await n(select(func.count(Allocation.id))
                               .where(Allocation.event_id == event_id)),
        "exclusions": await n(
            select(func.count(AllocationCategoryExclusion.id))
            .where(AllocationCategoryExclusion.allocation_category_id.in_(cat_ids))),
        "marks": await n(select(func.count(MarkDefinition.id))
                         .where(MarkDefinition.event_id == event_id)),
        "mark_assignments": await n(select(func.count(MarkAssignment.id))
                                    .where(MarkAssignment.event_id == event_id)),
        "cf_definitions": await n(select(func.count(CustomFieldDefinition.id))
                                  .where(CustomFieldDefinition.event_id == event_id)),
        "cf_values": await n(select(func.count(CustomFieldValue.id))
                             .where(CustomFieldValue.participant_id.in_(p_ids))),
        "field_configs": await n(select(func.count(EventFieldConfig.id))
                                 .where(EventFieldConfig.event_id == event_id)),
        "preferences": await n(
            select(func.count(ParticipantPreferenceRequest.id))
            .where(ParticipantPreferenceRequest.event_id == event_id)),
        "notes": await n(select(func.count(Note.id))
                         .where(Note.notable_id == event_id)),
    }


# A clean restore of the round-trip fixture, for comparison.
CLEAN = {
    "participants": 3, "categories": 2, "units": 3, "allocations": 2,
    "exclusions": 2, "marks": 2, "mark_assignments": 2,
    "cf_definitions": 2, "cf_values": 2, "field_configs": 2,
    "preferences": 2, "notes": 2,
}


async def _restore(db, content: bytes, src, actor=True) -> tuple[dict, dict]:
    """Restore and return (result, row counts)."""
    result = await confirm_restore(
        content, db,
        actor_user_id=src["user"].id if actor else None,
    )
    return result, await _counts(db, uuid.UUID(result["new_event_id"]))


async def _clean_export(db):
    src = await _build(db)
    return src, await export_event_zip(src["event"].id, db, mode="full")


# ─── 0. The baseline: a clean file is unaffected ──────────────────────

async def test_0_a_clean_file_restores_whole(db):
    src, content = await _clean_export(db)
    result, counts = await _restore(db, content, src)
    assert counts == CLEAN
    assert result["skipped"] == {}
    assert result["shortened"] == {}


# ─── 1. BACKUP-7: a unit whose group type is missing ──────────────────

async def test_1_unit_without_its_group_type_costs_only_those_lines(db):
    src, content = await _clean_export(db)
    # Drop the group type that holds both allocated units. Its units, and
    # the allocations naming them, go with it; nothing else does.
    damaged = _edit(
        content, "allocation_categories.json",
        lambda rows: [r for r in rows if r["name"] != "Bedrooms"],
    )
    result, counts = await _restore(db, damaged, src)

    assert counts["categories"] == 1
    assert counts["units"] == 1           # Pottery, in Workshops
    assert counts["allocations"] == 0     # both named a dropped unit
    # Everything that did not depend on Bedrooms is intact.
    assert counts["participants"] == 3
    assert counts["exclusions"] == 2      # both are on Workshops
    assert counts["marks"] == 2
    assert counts["mark_assignments"] == 2
    assert counts["notes"] == 2
    assert result["skipped"]["allocation_units.json"] == 2
    assert result["skipped"]["allocations.json"] == 2


# ─── 2. Missing keys, one case per read ───────────────────────────────

def _drop(member, path, key):
    """A case that removes one key from one line of one member."""
    def mutate(payload):
        target = payload
        for step in path:
            target = target[step]
        target.pop(key, None)
    return member, mutate


MISSING_KEY_CASES = [
    # (id, member, path to the line, key, expected counts after restore)
    ("cf_def.id", *_drop("custom_fields.json", ("definitions", 0), "id"),
     {"cf_definitions": 2, "cf_values": 1}),
    ("cf_def.label", *_drop("custom_fields.json", ("definitions", 0), "label"),
     {"cf_definitions": 1, "cf_values": 1}),
    ("cf_def.field_type", *_drop("custom_fields.json", ("definitions", 0), "field_type"),
     {"cf_definitions": 2, "cf_values": 2}),
    ("field_config.field_name", *_drop("field_configs.json", (0,), "field_name"),
     {"field_configs": 1}),
    ("category.id", *_drop("allocation_categories.json", (0,), "id"),
     {"categories": 2, "units": 1, "allocations": 0}),
    ("category.name", *_drop("allocation_categories.json", (0,), "name"),
     {"categories": 1, "units": 1, "allocations": 0}),
    ("unit.id", *_drop("allocation_units.json", (0,), "id"),
     {"units": 3, "allocations": 1}),
    ("unit.category_id", *_drop("allocation_units.json", (0,), "category_id"),
     {"units": 2, "allocations": 1}),
    ("unit.name", *_drop("allocation_units.json", (0,), "name"),
     {"units": 2, "allocations": 1}),
    ("allocation.participant_id", *_drop("allocations.json", (0,), "participant_id"),
     {"allocations": 1}),
    ("allocation.unit_id", *_drop("allocations.json", (0,), "unit_id"),
     {"allocations": 1}),
    ("mark_def.id", *_drop("marks.json", ("definitions", 0), "id"),
     {"marks": 2, "mark_assignments": 1}),
    ("mark_def.name", *_drop("marks.json", ("definitions", 0), "name"),
     {"marks": 1, "mark_assignments": 1}),
    ("mark_assignment.participant_id",
     *_drop("marks.json", ("assignments", 0), "participant_id"),
     {"mark_assignments": 1}),
    ("mark_assignment.mark_id", *_drop("marks.json", ("assignments", 0), "mark_id"),
     {"mark_assignments": 1}),
    ("preference.participant_id", *_drop("preferences.json", (0,), "participant_id"),
     {"preferences": 1}),
    ("note.content", *_drop("notes.json", (0,), "content"),
     {"notes": 1}),
    ("note.notable_type", *_drop("notes.json", (0,), "notable_type"),
     {"notes": 1}),
]


@pytest.mark.parametrize(
    "case_id,member,mutate,expected",
    MISSING_KEY_CASES,
    ids=[c[0] for c in MISSING_KEY_CASES],
)
async def test_2_a_missing_key_costs_its_line(db, case_id, member, mutate, expected):
    src, content = await _clean_export(db)
    result, counts = await _restore(db, _edit(content, member, mutate), src)
    for table, want in expected.items():
        assert counts[table] == want, (
            f"{case_id}: {table} came back {counts[table]}, expected {want}"
        )
    # Whatever the case, the restore itself succeeded and the event exists.
    assert counts["participants"] == 3


async def test_2b_a_blank_participant_id_cell_still_restores_the_person(db):
    """The CSV `id` read, blanked rather than removed: the row is created,
    but nothing in the file can refer to it."""
    src, content = await _clean_export(db)

    def blank_first_id(lines):
        header = lines[0].split(",")
        i = header.index("id")
        cells = lines[1].split(",")
        cells[i] = ""
        lines[1] = ",".join(cells)
        return lines

    result, counts = await _restore(db, _edit_csv(content, blank_first_id), src)
    assert counts["participants"] == 3          # the person is still restored
    assert counts["allocations"] == 1           # their allocation is not
    assert counts["exclusions"] == 1
    assert counts["mark_assignments"] == 1
    assert counts["cf_values"] == 1
    assert counts["preferences"] == 1


# ─── 3. Empty old ids ─────────────────────────────────────────────────

async def test_3_an_empty_old_id_is_never_a_map_key(db):
    src, content = await _clean_export(db)
    anna = str(src["people"]["anna@test.local"].id)

    def blank_anna(lines):
        header = lines[0].split(",")
        i = header.index("id")
        for k, line in enumerate(lines[1:], start=1):
            cells = line.split(",")
            if len(cells) > i and cells[i] == anna:
                cells[i] = ""
                lines[k] = ",".join(cells)
        return lines

    damaged = _edit_csv(content, blank_anna)

    def blank_alloc(rows):
        for r in rows:
            if r["participant_id"] == anna:
                r["participant_id"] = ""
        return rows

    damaged = _edit(damaged, "allocations.json", blank_alloc)
    result, counts = await _restore(db, damaged, src)

    assert counts["participants"] == 3
    # Anna's allocation named a blank id, and her own row was never mapped,
    # so the allocation cannot be linked either way.
    assert counts["allocations"] == 1
    restored = uuid.UUID(result["new_event_id"])
    held = (await db.execute(
        select(Participant.email)
        .join(Allocation, Allocation.participant_id == Participant.id)
        .where(Allocation.event_id == restored)
    )).scalars().all()
    assert "anna@test.local" not in held


# ─── 4. Duplicates: the first wins ────────────────────────────────────

def _dup_list(member, path=()):
    def mutate(payload):
        target = payload
        for step in path:
            target = target[step]
        target.append(copy.deepcopy(target[0]))
    return member, mutate


DUPLICATE_CASES = [
    ("allocations", *_dup_list("allocations.json"), "allocations", 2),
    ("exclusions", *_dup_list(EXCL_MEMBER), "exclusions", 2),
    ("mark_assignments", *_dup_list("marks.json", ("assignments",)),
     "mark_assignments", 2),
    ("category_old_id", *_dup_list("allocation_categories.json"), "categories", 2),
    ("unit_old_id", *_dup_list("allocation_units.json"), "units", 3),
    ("mark_old_id", *_dup_list("marks.json", ("definitions",)), "marks", 2),
    ("cf_def_old_id", *_dup_list("custom_fields.json", ("definitions",)),
     "cf_definitions", 2),
]


@pytest.mark.parametrize(
    "case_id,member,mutate,table,want",
    DUPLICATE_CASES,
    ids=[c[0] for c in DUPLICATE_CASES],
)
async def test_4_a_duplicate_line_is_dropped(db, case_id, member, mutate, table, want):
    src, content = await _clean_export(db)
    result, counts = await _restore(db, _edit(content, member, mutate), src)
    assert counts[table] == want, f"{case_id}: {table} came back {counts[table]}"
    assert result["skipped"], "the dropped duplicate should be counted"


async def test_4b_a_duplicate_participant_line_is_dropped(db):
    src, content = await _clean_export(db)

    def dup_first(lines):
        return [lines[0], lines[1], *lines[1:]]

    result, counts = await _restore(db, _edit_csv(content, dup_first), src)
    assert counts["participants"] == 3
    assert result["skipped"]["participants.csv"] == 1


# ─── 5. Explicit nulls in NOT NULL columns ────────────────────────────

def _null(member, path, key):
    def mutate(payload):
        target = payload
        for step in path:
            target = target[step]
        target[key] = None
    return member, mutate


NULL_CASES = [
    # No model default, NOT NULL → the line goes.
    ("category.name", *_null("allocation_categories.json", (0,), "name"),
     {"categories": 1}),
    ("unit.name", *_null("allocation_units.json", (0,), "name"),
     {"units": 2}),
    ("unit.capacity", *_null("allocation_units.json", (0,), "capacity"),
     {"units": 2}),
    ("mark_def.name", *_null("marks.json", ("definitions", 0), "name"),
     {"marks": 1}),
    ("cf_def.label", *_null("custom_fields.json", ("definitions", 0), "label"),
     {"cf_definitions": 1}),
    ("field_config.field_name", *_null("field_configs.json", (0,), "field_name"),
     {"field_configs": 1}),
    ("note.content", *_null("notes.json", (0,), "content"), {"notes": 1}),
    # A model default exists → the default is used and the line stays.
    ("category.rule_type", *_null("allocation_categories.json", (0,), "rule_type"),
     {"categories": 2}),
    ("category.sort_order", *_null("allocation_categories.json", (0,), "sort_order"),
     {"categories": 2}),
    ("category.is_default", *_null("allocation_categories.json", (0,), "is_default"),
     {"categories": 2}),
    ("unit.sort_order", *_null("allocation_units.json", (0,), "sort_order"),
     {"units": 3}),
    ("cf_def.field_type", *_null("custom_fields.json", ("definitions", 0), "field_type"),
     {"cf_definitions": 2}),
    ("cf_def.is_required", *_null("custom_fields.json", ("definitions", 0), "is_required"),
     {"cf_definitions": 2}),
    ("cf_def.sort_order", *_null("custom_fields.json", ("definitions", 0), "sort_order"),
     {"cf_definitions": 2}),
    ("field_config.is_enabled", *_null("field_configs.json", (0,), "is_enabled"),
     {"field_configs": 2}),
    ("mark_def.colour", *_null("marks.json", ("definitions", 0), "colour"),
     {"marks": 2}),
    ("mark_def.visible_in", *_null("marks.json", ("definitions", 0), "visible_in"),
     {"marks": 2}),
    ("preference.resolved", *_null("preferences.json", (0,), "resolved"),
     {"preferences": 2}),
]


@pytest.mark.parametrize(
    "case_id,member,mutate,expected",
    NULL_CASES,
    ids=[c[0] for c in NULL_CASES],
)
async def test_5_a_null_uses_the_model_default_or_skips_the_line(
    db, case_id, member, mutate, expected
):
    src, content = await _clean_export(db)
    _, counts = await _restore(db, _edit(content, member, mutate), src)
    for table, want in expected.items():
        assert counts[table] == want, (
            f"{case_id}: {table} came back {counts[table]}, expected {want}"
        )


async def test_5b_a_null_name_or_email_costs_the_participant(db):
    src, content = await _clean_export(db)

    def blank_email(lines):
        header = lines[0].split(",")
        i = header.index("email")
        cells = lines[1].split(",")
        cells[i] = ""
        lines[1] = ",".join(cells)
        return lines

    result, counts = await _restore(db, _edit_csv(content, blank_email), src)
    assert counts["participants"] == 2
    assert result["skipped"]["participants.csv"] == 1


async def test_5c_a_null_default_really_is_the_models_own(db):
    """rule_type falls back to `exclusive`, the column's default, not to
    the `none` this line used to invent."""
    src, content = await _clean_export(db)
    def drop_rule_type(rows):
        rows[0].pop("rule_type")

    damaged = _edit(content, "allocation_categories.json", drop_rule_type)
    result, _ = await _restore(db, damaged, src)
    rule_types = (await db.execute(
        select(AllocationCategory.rule_type)
        .where(AllocationCategory.event_id == uuid.UUID(result["new_event_id"]))
    )).scalars().all()
    assert "exclusive" in rule_types
    assert "none" not in rule_types


# ─── 6. Unreadable members are refused up front ───────────────────────

def _upload(content: bytes) -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename="backup.zip")


UNREADABLE_CASES = [
    ("invalid_json",
     lambda c: _rezip({**_members(c), "allocations.json": b"{not json at all"})),
    ("wrong_top_level_shape",
     lambda c: _rezip({**_members(c), "allocations.json": b'{"rows": []}'})),
    ("inner_key_wrong_shape",
     lambda c: _rezip({**_members(c), "marks.json": b'{"definitions": {}}'})),
    ("csv_without_id_column",
     lambda c: _rezip({**_members(c), "participants.csv": b"first_name,email\r\nA,a@b.c\r\n"})),
]


@pytest.mark.parametrize(
    "case_id,damage", UNREADABLE_CASES, ids=[c[0] for c in UNREADABLE_CASES]
)
async def test_6_an_unreadable_member_refuses_the_file(db, case_id, damage):
    from app.api.export import restore_confirm, restore_preview

    src, content = await _clean_export(db)
    damaged = damage(content)
    before = (await db.execute(select(func.count(Event.id)))).scalar_one()

    with pytest.raises(MoimioAppError) as preview_err:
        await restore_preview(file=_upload(damaged), current_user=src["user"])
    assert preview_err.value.key == REFUSAL_KEY
    assert preview_err.value.status_code == 422

    with pytest.raises(MoimioAppError) as confirm_err:
        await restore_confirm(
            file=_upload(damaged), db=db, current_user=src["user"],
        )
    assert confirm_err.value.key == REFUSAL_KEY
    assert confirm_err.value.status_code == 422

    after = (await db.execute(select(func.count(Event.id)))).scalar_one()
    assert after == before, "a refused file must create no event"


# ─── 7. A line of the wrong type ──────────────────────────────────────

WRONG_TYPE_CASES = [
    ("allocations.json", (), "allocations", 2),
    ("allocation_categories.json", (), "categories", 2),
    ("allocation_units.json", (), "units", 3),
    ("field_configs.json", (), "field_configs", 2),
    ("preferences.json", (), "preferences", 2),
    ("notes.json", (), "notes", 2),
    ("marks.json", ("definitions",), "marks", 2),
    ("marks.json", ("assignments",), "mark_assignments", 2),
    ("custom_fields.json", ("definitions",), "cf_definitions", 2),
]


@pytest.mark.parametrize(
    "member,path,table,want",
    WRONG_TYPE_CASES,
    ids=[f"{c[0]}{':' + c[1][0] if c[1] else ''}" for c in WRONG_TYPE_CASES],
)
async def test_7_a_wrong_typed_line_is_skipped(db, member, path, table, want):
    src, content = await _clean_export(db)

    def mutate(payload):
        target = payload
        for step in path:
            target = target[step]
        target.append("a string where an object belongs")

    result, counts = await _restore(db, _edit(content, member, mutate), src)
    assert counts[table] == want
    assert result["skipped"], "the skipped line should be counted"


# ─── 8. Over-long text is shortened ───────────────────────────────────

async def test_8_over_long_text_is_shortened_and_counted(db):
    src, content = await _clean_export(db)
    long_name = "L" * 400  # allocation_categories.name is String(100)

    def stretch(rows):
        rows[0]["name"] = long_name

    result, counts = await _restore(db, _edit(content, "allocation_categories.json", stretch), src)

    assert counts["categories"] == 2, "shortening must not cost the line"
    names = (await db.execute(
        select(AllocationCategory.name)
        .where(AllocationCategory.event_id == uuid.UUID(result["new_event_id"]))
    )).scalars().all()
    assert "L" * 100 in names
    assert result["shortened"]["allocation_categories.name"] == 1


async def test_8b_a_name_at_the_limit_survives_the_restored_suffix(db):
    """events.name is String(255) and restore appends " (Restored)", so a
    name already at the limit would overflow the column."""
    src, content = await _clean_export(db)
    damaged = _edit(content, "event.json", lambda ev: ev.update({"name": "E" * 255}))
    result, _ = await _restore(db, damaged, src)
    restored = await db.get(Event, uuid.UUID(result["new_event_id"]))
    assert len(restored.name) == 255
    assert result["shortened"]["events.name"] == 1


# ─── 9. A value outside a fixed set ───────────────────────────────────

async def test_9_an_unknown_status_becomes_the_model_default(db):
    src, content = await _clean_export(db)

    def scramble(lines):
        header = lines[0].split(",")
        i = header.index("registration_status")
        cells = lines[1].split(",")
        cells[i] = "not_a_status"
        lines[1] = ",".join(cells)
        return lines

    result, counts = await _restore(db, _edit_csv(content, scramble), src)
    assert counts["participants"] == 3
    statuses = (await db.execute(
        select(Participant.registration_status)
        .where(Participant.event_id == uuid.UUID(result["new_event_id"]))
    )).scalars().all()
    # PENDING is the model's own default. CONFIRMED was the invented
    # fallback before v1.0.4o, and would have promoted this person into
    # the active roster.
    assert RegistrationStatus.PENDING in statuses


# ─── 10. Optional-member defaults are deep-copied ─────────────────────

async def test_10_an_optional_member_default_is_deep_copied(db, monkeypatch):
    src, content = await _clean_export(db)
    default = {"rows": [], "meta": {"nested": True}}
    monkeypatch.setitem(
        backup_service._OPTIONAL_MEMBERS, "future_member.json", default,
    )
    # The member is absent from every file made so far, which is the point.
    parsed = backup_service._parse_zip(content)

    got = parsed["future_member.json"]
    assert got == default, "a dict default must come back as an equal dict"
    assert got is not default, "and not as the object on the module constant"
    assert got["meta"] is not default["meta"], "nested values too"
    got["meta"]["nested"] = False
    assert default["meta"]["nested"] is True


# ─── 11. Notes and the restoring user ─────────────────────────────────

async def test_11_a_note_is_authored_by_whoever_restores(db):
    src, content = await _clean_export(db)
    result, counts = await _restore(db, content, src)
    assert counts["notes"] == 2
    authors = (await db.execute(
        select(Note.author_id)
        .where(Note.notable_id == uuid.UUID(result["new_event_id"]))
    )).scalars().all()
    assert set(authors) == {src["user"].id}
    # Not the original author, who may not exist on a receiving instance.
    assert src["author"].id not in authors


async def test_11b_without_an_actor_the_note_lines_are_skipped(db):
    src, content = await _clean_export(db)
    result, counts = await _restore(db, content, src, actor=False)
    assert counts["notes"] == 0
    assert result["skipped"]["notes.json"] == 2
    # The rest of the restore is unaffected.
    assert counts["participants"] == 3
    assert counts["allocations"] == 2


# ─── 12. The summary warning ──────────────────────────────────────────

async def test_12_one_summary_warning_per_damaged_restore(db, capsys):
    src, content = await _clean_export(db)
    damaged = _edit(
        content, "allocation_categories.json",
        lambda rows: rows[0].update({"name": "N" * 400}),
    )
    capsys.readouterr()
    result, _ = await _restore(db, damaged, src)
    out = capsys.readouterr().out

    records = [l for l in out.splitlines() if "[RESTORE WARNING]" in l]
    assert len(records) == 1, f"expected one warning, got {records}"
    record = records[0]
    assert result["new_event_id"] in record
    assert "allocation_categories.name" in record
    # No person in it.
    for leak in ("Anna", "anna@test.local", "Bruno", "bruno@test.local",
                 str(src["people"]["anna@test.local"].id)):
        assert leak not in record, f"{leak!r} must not appear in the log"
    assert result["shortened"] == {"allocation_categories.name": 1}


async def test_12b_a_clean_restore_logs_no_summary_warning(db, capsys):
    src, content = await _clean_export(db)
    capsys.readouterr()
    result, _ = await _restore(db, content, src)
    out = capsys.readouterr().out
    assert "[RESTORE WARNING]" not in out
    assert result["skipped"] == {} and result["shortened"] == {}
