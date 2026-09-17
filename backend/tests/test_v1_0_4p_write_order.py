"""v1.0.4p — ids that live inside a JSON column.

Three columns hold ids inside JSON rather than in a column of their own, so
restore's id maps could not reach them: a group code's group type scope, a
grouping request's scope, and a group type's per-mark priorities. Until this
release they came back naming group types and marks that no longer existed,
so the rule behind each one silently stopped working.

THE RULE: translate every id the maps know; leave every other value exactly
as the file has it, in place. Order and length never change.

Why nothing is dropped: to the engine a list of ids that resolve to nothing
means "applies nowhere", while an EMPTY list means "applies everywhere"
(`if scope and cat_id_str not in ...` in engine_service is a falsy check, and
its own comment reads "default = all categories"). Dropping the last
untranslatable id would therefore invert the rule rather than lose it.

Every case here is checked through the column's REAL reader wherever one
enforces it:

  - group_code_categories — the engine's PASS 1 clustering, by running the
    engine on the restored event and reading the placement reason.
  - mark_priorities — `_mark_behaviour_for`, the per-group-type override
    lookup.
  - category_scope — nothing enforces it (it is stored, displayed and
    exported, never read by the engine or allocation service), so only the
    stored value is checked. That is a finding, not an omission.
"""

import copy
import io
import json
import uuid
import zipfile

import pytest
from sqlalchemy import select

from app.models.allocation_category import AllocationCategory
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event import Event
from app.models.mark import MarkDefinition
from app.models.participant import Participant
from app.models.preference_request import ParticipantPreferenceRequest
from app.services.allocation_service import _mark_behaviour_for
from app.services.backup_service import confirm_restore, export_event_zip
from app.services.engine_service import run_engine

from tests.conftest import (
    make_category,
    make_event,
    make_participant,
    make_unit,
    make_user,
)

pytestmark = pytest.mark.asyncio

# An id no map will ever know, standing in for a group type or mark that was
# deleted before the backup was taken. Live data really does carry these:
# delete_category leaves the id behind in group_code_categories.
DEAD_ID = "00000000-0000-4000-8000-00000000dead"


# ─── Fixtures ─────────────────────────────────────────────────────────

async def _event_with_group_code(db, scope=None):
    """Three group types, and two people sharing a group code whose scope is
    `scope`. Two sharers is the minimum: the engine drops clusters of one.

    A scope naming group types has to be set by the caller after the fact,
    because the group types do not exist until this function has run.
    """
    ev = await make_event(db, name="Scope Source")
    cats = {}
    for name in ("Alpha", "Beta", "Gamma"):
        cats[name] = await make_category(db, ev.id, name=name)
        await make_unit(db, cats[name].id, f"{name} 1", capacity=10)
        await make_unit(db, cats[name].id, f"{name} 2", capacity=10)

    people = {}
    for first, email in (("Sara", "sara@test.local"), ("Tomas", "tomas@test.local")):
        p = await make_participant(
            db, ev.id, first_name=first, email=email, group_code="SMITH",
        )
        p.group_code_categories = copy.deepcopy(scope) if scope else scope
        people[email] = p
    # A third person with no code, so the engine has someone to place the
    # ordinary way and a cluster is not the only thing in the pool.
    await make_participant(db, ev.id, first_name="Ute", email="ute@test.local")
    await db.flush()
    return {"event": ev, "cats": cats, "people": people}


async def _event_with_scope(db, scope=None):
    """One grouping request carrying `scope`."""
    ev = await make_event(db, name="Request Source")
    cats = {
        name: await make_category(db, ev.id, name=name)
        for name in ("Alpha", "Beta", "Gamma")
    }
    p = await make_participant(db, ev.id, first_name="Vera", email="vera@test.local")
    db.add(ParticipantPreferenceRequest(
        event_id=ev.id, participant_id=p.id, preferred_name="Someone Else",
        category_scope=copy.deepcopy(scope) if isinstance(scope, list) else scope,
    ))
    await db.flush()
    return {"event": ev, "cats": cats, "participant": p}


async def _event_with_priorities(db, build_settings):
    """Two marks, and a group type whose settings `build_settings(marks)`
    returns."""
    ev = await make_event(db, name="Priorities Source")
    marks = {}
    for name, behaviour in (("Leader", "none"), ("Helper", "none")):
        m = MarkDefinition(event_id=ev.id, name=name, colour="#123456",
                           visible_in=["allocation"], cluster_behaviour=behaviour)
        db.add(m)
        marks[name] = m
    await db.flush()

    cat = await make_category(db, ev.id, name="Alpha")
    await make_unit(db, cat.id, "Alpha 1", capacity=10)
    cat.settings = build_settings(marks)
    await db.flush()
    return {"event": ev, "cat": cat, "marks": marks}


async def _round_trip(db, event_id):
    """Export and restore, returning the restored event id."""
    user = await make_user(db, email=f"p-{uuid.uuid4().hex[:8]}@test.local")
    content = await export_event_zip(event_id, db, mode="full")
    result = await confirm_restore(content, db, actor_user_id=user.id)
    return uuid.UUID(result["new_event_id"])


async def _restored_cats(db, event_id) -> dict[str, AllocationCategory]:
    rows = (await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == event_id)
    )).scalars().all()
    return {c.name: c for c in rows}


async def _restored_marks(db, event_id) -> dict[str, MarkDefinition]:
    rows = (await db.execute(
        select(MarkDefinition).where(MarkDefinition.event_id == event_id)
    )).scalars().all()
    return {m.name: m for m in rows}


async def _restored_person(db, event_id, email) -> Participant:
    return (await db.execute(
        select(Participant).where(
            Participant.event_id == event_id, Participant.email == email,
        )
    )).scalar_one()


# ─── The real reader for group_code_categories ────────────────────────

async def _group_code_applies_in(db, event_id, category_id) -> bool:
    """Does the group code cluster its members in this group type?

    This is the engine's PASS 1, reached through `run_engine`, which is the
    only thing that reads group_code_categories for behaviour. A clustered
    member carries a placement reason of `group_code` (or
    `group_code_split`); an unclustered one is placed by fill or round
    robin.
    """
    proposal = await run_engine(db, event_id, category_id, mode="replace")
    reasons = proposal.get("placement_reasons", {})
    return any(
        str(r.get("reason", "")).startswith("group_code")
        for r in reasons.values()
    )


# ─── 1. group_code_categories ─────────────────────────────────────────

async def test_1_1_two_known_ids_come_back_as_the_two_restored_ids(db):
    src = await _event_with_group_code(db)
    scope = [str(src["cats"]["Alpha"].id), str(src["cats"]["Beta"].id)]
    for p in src["people"].values():
        p.group_code_categories = list(scope)
    await db.flush()

    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    sara = await _restored_person(db, new_id, "sara@test.local")

    # Translated, in the same order, same length.
    assert sara.group_code_categories == [
        str(cats["Alpha"].id), str(cats["Beta"].id),
    ]

    # And the rule works: the code applies to those two group types only.
    assert await _group_code_applies_in(db, new_id, cats["Alpha"].id)
    assert await _group_code_applies_in(db, new_id, cats["Beta"].id)
    assert not await _group_code_applies_in(db, new_id, cats["Gamma"].id)


async def test_1_2_null_stays_null_and_the_code_applies_everywhere(db):
    src = await _event_with_group_code(db, None)
    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    sara = await _restored_person(db, new_id, "sara@test.local")

    assert sara.group_code_categories is None
    for name in ("Alpha", "Beta", "Gamma"):
        assert await _group_code_applies_in(db, new_id, cats[name].id), name


async def test_1_3_one_known_and_one_unknown_id(db):
    src = await _event_with_group_code(db)
    scope = [str(src["cats"]["Alpha"].id), DEAD_ID]
    for p in src["people"].values():
        p.group_code_categories = list(scope)
    await db.flush()

    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    sara = await _restored_person(db, new_id, "sara@test.local")

    # The known one translated; the unknown one untouched, in place.
    assert sara.group_code_categories == [str(cats["Alpha"].id), DEAD_ID]
    assert len(sara.group_code_categories) == 2

    assert await _group_code_applies_in(db, new_id, cats["Alpha"].id)
    assert not await _group_code_applies_in(db, new_id, cats["Beta"].id)
    assert not await _group_code_applies_in(db, new_id, cats["Gamma"].id)


async def test_1_4_only_unknown_ids_still_apply_nowhere(db):
    src = await _event_with_group_code(db, [DEAD_ID])
    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    sara = await _restored_person(db, new_id, "sara@test.local")

    # Unchanged. Emptying it would mean "every group type", the opposite of
    # what it meant before the backup.
    assert sara.group_code_categories == [DEAD_ID]
    for name in ("Alpha", "Beta", "Gamma"):
        assert not await _group_code_applies_in(db, new_id, cats[name].id), name


# ─── 2. category_scope ────────────────────────────────────────────────
#
# Nothing enforces this column: it appears nowhere in engine_service or
# allocation_service. So these four cases check the STORED value only. If
# anything ever does enforce it, the same four cases become behavioural.

async def _restored_scope(db, event_id):
    row = (await db.execute(
        select(ParticipantPreferenceRequest)
        .where(ParticipantPreferenceRequest.event_id == event_id)
    )).scalar_one()
    return row.category_scope


async def test_2_1_two_known_ids_are_translated_in_order(db):
    src = await _event_with_scope(db)
    scope = [str(src["cats"]["Alpha"].id), str(src["cats"]["Beta"].id)]
    row = (await db.execute(
        select(ParticipantPreferenceRequest)
        .where(ParticipantPreferenceRequest.event_id == src["event"].id)
    )).scalar_one()
    row.category_scope = list(scope)
    await db.flush()

    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    assert await _restored_scope(db, new_id) == [
        str(cats["Alpha"].id), str(cats["Beta"].id),
    ]


async def test_2_2_all_passes_through_untouched(db):
    src = await _event_with_scope(db, "all")
    new_id = await _round_trip(db, src["event"].id)
    assert await _restored_scope(db, new_id) == "all"


async def test_2_3_one_known_and_one_unknown_id(db):
    src = await _event_with_scope(db)
    row = (await db.execute(
        select(ParticipantPreferenceRequest)
        .where(ParticipantPreferenceRequest.event_id == src["event"].id)
    )).scalar_one()
    row.category_scope = [str(src["cats"]["Alpha"].id), DEAD_ID]
    await db.flush()

    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    assert await _restored_scope(db, new_id) == [str(cats["Alpha"].id), DEAD_ID]


async def test_2_4_only_unknown_ids_are_unchanged(db):
    src = await _event_with_scope(db, [DEAD_ID])
    new_id = await _round_trip(db, src["event"].id)
    assert await _restored_scope(db, new_id) == [DEAD_ID]


# ─── 3. mark_priorities ───────────────────────────────────────────────

def _settings_with(marks, entries, extra=True):
    engine = {
        "use_group_codes": True,
        "group_remaining_by_gender": False,
        "mark_priorities": entries,
    }
    settings = {"engine": engine}
    if extra:
        settings["title"] = "Alpha rules"
    return settings


async def test_3_1_known_ids_translated_other_keys_kept(db):
    src = await _event_with_priorities(db, lambda marks: _settings_with(
        marks,
        [
            {"id": str(marks["Leader"].id), "behaviour": "together", "note": "keep"},
            {"id": str(marks["Helper"].id), "behaviour": "split"},
        ],
    ))
    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    marks = await _restored_marks(db, new_id)
    entries = cats["Alpha"].settings["engine"]["mark_priorities"]

    # Ids translated, in order.
    assert [e["id"] for e in entries] == [
        str(marks["Leader"].id), str(marks["Helper"].id),
    ]
    # Every other key in each entry kept exactly.
    assert entries[0]["behaviour"] == "together"
    assert entries[0]["note"] == "keep"
    assert entries[1]["behaviour"] == "split"
    # Every other settings key untouched.
    assert cats["Alpha"].settings["title"] == "Alpha rules"
    assert cats["Alpha"].settings["engine"]["use_group_codes"] is True
    assert cats["Alpha"].settings["engine"]["group_remaining_by_gender"] is False

    # And the rule works, through the override reader. The marks' own
    # cluster_behaviour is "none", so anything but "none" can only have come
    # from the per-group-type override.
    assert await _mark_behaviour_for(
        db, event_id=new_id, category_id=cats["Alpha"].id,
        mark_id=str(marks["Leader"].id),
    ) == "together"
    assert await _mark_behaviour_for(
        db, event_id=new_id, category_id=cats["Alpha"].id,
        mark_id=str(marks["Helper"].id),
    ) == "split"


async def test_3_2_an_unknown_entry_stays_exactly_as_it_was(db):
    src = await _event_with_priorities(db, lambda marks: _settings_with(
        marks,
        [
            {"id": DEAD_ID, "behaviour": "together"},
            {"id": str(marks["Leader"].id), "behaviour": "split"},
        ],
    ))
    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    marks = await _restored_marks(db, new_id)
    entries = cats["Alpha"].settings["engine"]["mark_priorities"]

    # In place, unchanged, and the known one beside it translated.
    assert entries[0] == {"id": DEAD_ID, "behaviour": "together"}
    assert entries[1]["id"] == str(marks["Leader"].id)
    assert len(entries) == 2


async def test_3_3_only_unknown_entries_read_as_they_did_before(db):
    entries = [{"id": DEAD_ID, "behaviour": "together"}]
    src = await _event_with_priorities(
        db, lambda marks: _settings_with(marks, copy.deepcopy(entries)),
    )
    # What the reader says on the SOURCE event, for the mark that is real.
    before = await _mark_behaviour_for(
        db, event_id=src["event"].id, category_id=src["cat"].id,
        mark_id=str(src["marks"]["Leader"].id),
    )

    new_id = await _round_trip(db, src["event"].id)
    cats = await _restored_cats(db, new_id)
    marks = await _restored_marks(db, new_id)

    assert cats["Alpha"].settings["engine"]["mark_priorities"] == entries
    after = await _mark_behaviour_for(
        db, event_id=new_id, category_id=cats["Alpha"].id,
        mark_id=str(marks["Leader"].id),
    )
    assert after == before == "none", (
        "an override naming a mark nobody knows must leave the mark's own "
        "behaviour in charge, on the restored event exactly as on the source"
    )


# ─── 5. Custom field values: the first line wins ──────────────────────

async def test_5_a_duplicated_custom_field_value_keeps_the_first(db):
    ev = await make_event(db, name="Duplicate Source")
    user = await make_user(db, email="dup@test.local")
    p = await make_participant(db, ev.id, first_name="Wilma", email="wilma@test.local")
    cf = CustomFieldDefinition(
        event_id=ev.id, label="T-shirt size", field_type="text", sort_order=0,
    )
    db.add(cf)
    await db.flush()
    db.add(CustomFieldValue(participant_id=p.id, field_id=cf.id, value="first"))
    await db.flush()

    content = await export_event_zip(ev.id, db, mode="full")

    # Duplicate the line, with a different value so we can tell which won.
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    payload = json.loads(members["custom_fields.json"].decode("utf-8"))
    (pid, rows), = payload["values"].items()
    payload["values"][pid] = [rows[0], {**rows[0], "value": "second"}]
    members["custom_fields.json"] = json.dumps(payload, indent=2).encode("utf-8")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, raw in members.items():
            zf.writestr(name, raw)

    result = await confirm_restore(out.getvalue(), db, actor_user_id=user.id)
    new_id = uuid.UUID(result["new_event_id"])

    values = (await db.execute(
        select(CustomFieldValue.value)
        .join(Participant, Participant.id == CustomFieldValue.participant_id)
        .where(Participant.event_id == new_id)
    )).scalars().all()
    assert values == ["first"], "the first line must win"
    assert result["skipped"]["custom_fields.json:values"] == 1
