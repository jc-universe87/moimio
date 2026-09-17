"""v1.0.4t — the history in a backup.

`allocation_events` was the last table a backup did not carry. A restored
event showed placements and exclusions in force with nothing behind them:
no record of who was moved where, when, or why.

It is carried now, with three things decided about it.

**The actor is not carried.** The account that did it does not exist where
the backup is restored, the column is nullable by design, and the history
screen already renders a missing actor as a removed user.

**A row travels with its person.** Only rows about exported participants go
in, which drops rows about removed people and rows whose participant is
already NULL from an erasure.

**Names of people who are not in the backup come out of the details.** A
placement's `cluster_members` names everyone placed together, and some of
them may not be in this file. Their names are dropped; the counts beside
them are not, because the counts describe what happened. A line may
therefore say three and name two, which is truthful.

The ids inside `meta` follow the v1.0.4p rule: translate every id the maps
know, and leave every other value exactly as the file has it. The trap is
`cluster_id`, which holds `mark:<mark id>` for a mark cluster and the group
code itself for a group-code cluster, and a group code is free organiser
text that may legitimately begin with `mark:`.

Checked through the real reader wherever one exists, which for history is
`list_allocation_events`, the one read path the screen uses.
"""

import io
import json
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.allocation_category import AllocationCategory
from app.models.allocation_event import (
    AllocationEvent,
    AllocationEventSource,
    AllocationEventType,
)
from app.models.allocation_unit import AllocationUnit
from app.models.mark import MarkDefinition
from app.models.participant import Participant
from app.services.allocation_events_service import list_allocation_events
from app.services.backup_service import (
    BACKUP_REGISTER,
    KNOWN_GAP_PREFIX,
    NOT_CARRIED,
    confirm_restore,
    export_event_zip,
)
from app.services.participant_service import soft_delete_participant

from tests.conftest import (
    make_category,
    make_event,
    make_mark,
    make_participant,
    make_unit,
    make_user,
)

pytestmark = pytest.mark.asyncio

TZ = timezone(timedelta(hours=1))

# One fixed time per history row: `occurred_at` is what orders the timeline
# and what these tests match rows by, and clock_timestamp() would give
# values no test could name.
T = {
    "exclude": datetime(2026, 5, 1, 9, 0, tzinfo=TZ),
    "cluster": datetime(2026, 5, 1, 10, 0, tzinfo=TZ),
    "equalise": datetime(2026, 5, 1, 10, 5, tzinfo=TZ),
    "drain": datetime(2026, 5, 1, 10, 10, tzinfo=TZ),
    "collision": datetime(2026, 5, 1, 10, 12, tzinfo=TZ),
    "removed": datetime(2026, 5, 1, 10, 15, tzinfo=TZ),
    "erased": datetime(2026, 5, 1, 10, 20, tzinfo=TZ),
}

# A unit id no map will ever know. Live data carries these: deleting a unit
# nulls `unit_id` through ON DELETE SET NULL, but the copy inside `meta`
# stays behind.
DEAD_ID = "00000000-0000-4000-8000-00000000dead"

# The removed participant, whose name must not leave the instance.
GONE = "Carla Withdrawn"


# ─── Fixture ──────────────────────────────────────────────────────────

async def _source(db) -> dict:
    """One event with a history covering every case: an exclusion with no
    unit, a mark cluster, the equalising sweep with a nested group-code
    cluster whose code begins with "mark:", a drained unit naming a unit
    that no longer exists, a row about a removed person, and a row whose
    participant has been erased."""
    restorer = await make_user(db, email="restorer-t@test.local")
    actor = await make_user(db, email="actor-t@test.local")

    ev = await make_event(db, name="History Source")
    cat = await make_category(db, ev.id, name="Bedrooms")
    lakeside = await make_unit(db, cat.id, "Lakeside", capacity=6)
    hillside = await make_unit(db, cat.id, "Hillside", capacity=6)
    mark = await make_mark(db, ev.id, name="Team leader")

    anna = await make_participant(db, ev.id, first_name="Anna",
                                  last_name="Alpha", email="anna-t@test.local")
    bruno = await make_participant(db, ev.id, first_name="Bruno",
                                   last_name="Beta", email="bruno-t@test.local")
    carla = await make_participant(db, ev.id, first_name="Carla",
                                   last_name="Withdrawn",
                                   email="carla-t@test.local")

    members = [
        {"id": str(anna.id), "name": "Anna Alpha"},
        {"id": str(bruno.id), "name": "Bruno Beta"},
        # Not in the export: soft-deleted below. Her name comes out.
        {"id": str(carla.id), "name": GONE},
    ]

    rows = {}
    for key, person, unit, kind, source, unit_name, meta in (
        # No unit is involved in an exclusion, so unit_id is NULL and the
        # unit name snapshot is empty.
        ("exclude", anna, None, AllocationEventType.EXCLUDE,
         AllocationEventSource.MANUAL, "", None),
        # A mark cluster. `cluster_id` is "mark:<mark id>": the prefix
        # stays and the id behind it is translated.
        ("cluster", anna, lakeside, AllocationEventType.ASSIGN,
         AllocationEventSource.ENGINE_COMMIT, "Lakeside", {
             "run_id": "run-0001",
             "placement": {
                 "reason": "mark_together",
                 "cluster_id": f"mark:{mark.id}",
                 "cluster_size": 3,
                 "cluster_placed_here": 3,
                 "unit_id": str(lakeside.id),
                 "cluster_members": members,
             },
         }),
        # The equalising sweep, which wraps the original reason in
        # `previous`. That original is a GROUP CODE cluster, and this group
        # code begins with "mark:" on purpose: it is free organiser text
        # and must come back byte for byte.
        ("equalise", bruno, hillside, AllocationEventType.ASSIGN,
         AllocationEventSource.ENGINE_COMMIT, "Hillside", {
             "run_id": "run-0001",
             "placement": {
                 "reason": "equalise",
                 "from_unit_id": str(lakeside.id),
                 "to_unit_id": str(hillside.id),
                 "previous": {
                     "reason": "group_code",
                     "cluster_id": "mark:SMITH-100",
                     "cluster_size": 2,
                     "cluster_placed_here": 2,
                     "unit_id": str(lakeside.id),
                     "cluster_members": members[:2],
                 },
             },
         }),
        # A restricted unit drained. `mark_restriction` is a bare mark id,
        # and `unit_id` names a unit that was deleted before the backup was
        # taken, which no map can know.
        ("drain", bruno, lakeside, AllocationEventType.ASSIGN,
         AllocationEventSource.ENGINE_COMMIT, "Lakeside", {
             "run_id": "run-0002",
             "placement": {
                 "reason": "mark_drain",
                 "unit_id": DEAD_ID,
                 "unit_name": "The Old Barn",
                 "gender_restriction": "female",
                 "mark_restriction": str(mark.id),
             },
         }),
        # The sharpest form of the same trap: a group code that is
        # CHARACTER FOR CHARACTER what a mark cluster's id would be. A
        # group code is free organiser text and nothing validates it, so
        # only the reason keeps this one from being rewritten into another
        # event's mark id.
        ("collision", anna, hillside, AllocationEventType.ASSIGN,
         AllocationEventSource.ENGINE_COMMIT, "Hillside", {
             "run_id": "run-0002",
             "placement": {
                 "reason": "group_code_split",
                 "cluster_id": f"mark:{mark.id}",
                 "cluster_size": 2,
                 "cluster_placed_here": 1,
                 "unit_id": str(hillside.id),
                 "cluster_members": members[:2],
             },
         }),
        # About somebody who is removed below: not exported at all.
        ("removed", carla, lakeside, AllocationEventType.ASSIGN,
         AllocationEventSource.MANUAL, "Lakeside", None),
    ):
        row = AllocationEvent(
            event_id=ev.id,
            participant_id=person.id,
            unit_id=unit.id if unit else None,
            category_id=cat.id,
            actor_user_id=actor.id,
            event_type=kind,
            source=source,
            unit_name_snapshot=unit_name,
            category_name_snapshot=cat.name,
            action_id=uuid.uuid4(),
            meta=meta,
            occurred_at=T[key],
        )
        db.add(row)
        rows[key] = row

    # An erasure has already nulled this row's participant. There is nobody
    # left for it to be about, so it is not exported either.
    erased = AllocationEvent(
        event_id=ev.id, participant_id=None, unit_id=lakeside.id,
        category_id=cat.id, actor_user_id=actor.id,
        event_type=AllocationEventType.UNASSIGN,
        source=AllocationEventSource.MANUAL,
        unit_name_snapshot="Lakeside", category_name_snapshot=cat.name,
        action_id=uuid.uuid4(), meta=None, occurred_at=T["erased"],
    )
    db.add(erased)
    rows["erased"] = erased
    await db.flush()

    await soft_delete_participant(db, carla)
    await db.flush()

    return {"restorer": restorer, "actor": actor, "event": ev, "cat": cat,
            "lakeside": lakeside, "hillside": hillside, "mark": mark,
            "anna": anna, "bruno": bruno, "carla": carla, "rows": rows,
            "members": members}


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


def _history(content: bytes) -> list[dict]:
    return json.loads(_members(content)["allocation_events.json"].decode("utf-8"))


def _edit_history(content: bytes, mutate) -> bytes:
    members = _members(content)
    rows = json.loads(members["allocation_events.json"])
    result = mutate(rows)
    members["allocation_events.json"] = json.dumps(
        rows if result is None else result, indent=2).encode("utf-8")
    return _rezip(members)


async def _export(db, src, mode: str = "full") -> bytes:
    return await export_event_zip(src["event"].id, db, mode=mode)


async def _restore(db, content: bytes, src) -> tuple[dict, uuid.UUID]:
    result = await confirm_restore(content, db,
                                   actor_user_id=src["restorer"].id)
    return result, uuid.UUID(result["new_event_id"])


async def _restored_mark_id(db, event_id) -> str:
    """The restored mark's id, read from the marks table by name.

    Never taken from another field of the same `meta`: a restore that
    translated nothing would keep the old id in both places, and a check
    that compared the two would pass while everything was wrong.
    """
    mark = (await db.execute(
        select(MarkDefinition).where(
            MarkDefinition.event_id == event_id,
            MarkDefinition.name == "Team leader",
        )
    )).scalar_one()
    return str(mark.id)


async def _restored(db, event_id) -> dict[datetime, AllocationEvent]:
    """The restored history, keyed by when it happened, which is the one
    thing a restored row keeps and nothing else in it derives from."""
    rows = (await db.execute(
        select(AllocationEvent).where(AllocationEvent.event_id == event_id)
    )).scalars().all()
    return {r.occurred_at: r for r in rows}


def _when(row: dict) -> datetime:
    """One row's `occurred_at` as an instant.

    Never compared as a string: the value is read back through the driver,
    which normalises it to UTC, so "10:00+01:00" comes out as "09:00+00:00".
    Those are the same moment and equal as datetimes, and unequal as text.
    """
    return datetime.fromisoformat(row["occurred_at"])


def _by_time(rows: list[dict]) -> dict[str, dict]:
    """Exported rows, keyed back to the fixture's names for readability."""
    at = {v: k for k, v in T.items()}
    return {at[_when(r)]: r for r in rows if _when(r) in at}


# ─── 1. Round trip ────────────────────────────────────────────────────

async def test_1_every_exported_row_comes_back(db):
    src = await _source(db)
    content = await _export(db, src)
    result, new_id = await _restore(db, content, src)

    assert result["counts"]["allocation_events"] == 5, (
        "Anna's three rows and Bruno's two, not the removed or erased ones"
    )

    restored = await _restored(db, new_id)
    people = {p.email: p for p in (await db.execute(
        select(Participant).where(Participant.event_id == new_id)
    )).scalars().all()}
    new_cat = (await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == new_id)
    )).scalar_one()
    new_units = {u.name: u for u in (await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id == new_cat.id)
    )).scalars().all()}

    # The exclusion row: kind, source, an empty unit name, no unit.
    exclude = restored[T["exclude"]]
    assert exclude.event_type == AllocationEventType.EXCLUDE
    assert exclude.source == AllocationEventSource.MANUAL
    assert exclude.unit_id is None
    assert exclude.unit_name_snapshot == ""
    assert exclude.category_name_snapshot == "Bedrooms"
    assert exclude.participant_id == people["anna-t@test.local"].id
    assert exclude.category_id == new_cat.id
    assert exclude.action_id == src["rows"]["exclude"].action_id, (
        "action_id is copied exactly: it is what groups the rows one action "
        "wrote, and a restored burst must still read as one action"
    )

    # A placement row: the unit and group type it names are the restored
    # ones, not the originals.
    cluster = restored[T["cluster"]]
    assert cluster.event_type == AllocationEventType.ASSIGN
    assert cluster.source == AllocationEventSource.ENGINE_COMMIT
    assert cluster.unit_id == new_units["Lakeside"].id
    assert cluster.unit_id != src["lakeside"].id
    assert cluster.unit_name_snapshot == "Lakeside"
    assert cluster.category_id == new_cat.id

    # The actor is not carried: that account does not exist here.
    assert {r.actor_user_id for r in restored.values()} == {None}


# ─── 2. Times and order ───────────────────────────────────────────────

async def test_2_the_timeline_keeps_its_own_times_and_order(db):
    src = await _source(db)
    content = await _export(db, src)
    _, new_id = await _restore(db, content, src)

    restored = await _restored(db, new_id)
    assert set(restored) == {T["exclude"], T["cluster"], T["equalise"],
                             T["drain"], T["collision"]}, (
        "every restored row keeps the time it happened, not the time of the "
        "restore"
    )

    # Through the read path, which is what the screen shows: newest first.
    timeline = await list_allocation_events(db, event_id=new_id)
    assert [_when(r) for r in timeline] == [
        T["collision"], T["drain"], T["equalise"], T["cluster"], T["exclude"],
    ]


# ─── 3. Removed people ────────────────────────────────────────────────

async def test_3_no_row_about_a_removed_or_erased_person_is_exported(db):
    src = await _source(db)
    rows = _history(await _export(db, src))

    assert len(rows) == 5
    keyed = _by_time(rows)
    assert set(keyed) == {"exclude", "cluster", "equalise", "drain",
                          "collision"}
    assert "removed" not in keyed, "her row goes with her"
    assert "erased" not in keyed, "a row with no participant is about nobody"

    ids = {r["participant_id"] for r in rows}
    assert str(src["carla"].id) not in ids
    assert None not in ids


# ─── 4. The scrub ─────────────────────────────────────────────────────

async def test_4_a_cluster_does_not_name_people_the_backup_leaves_out(db):
    src = await _source(db)
    content = await _export(db, src)

    # Nowhere in the whole file, not merely nowhere in this member.
    for name, raw in _members(content).items():
        assert GONE.encode() not in raw, f"{GONE!r} leaked into {name}"
        assert str(src["carla"].id).encode() not in raw

    placement = _by_time(_history(content))["cluster"]["meta"]["placement"]
    names = [m["name"] for m in placement["cluster_members"]]
    assert names == ["Anna Alpha", "Bruno Beta"], "the others are all there"
    # The counts describe what happened, so they are left as they are. This
    # line says three and names two, which is the truth.
    assert placement["cluster_size"] == 3
    assert placement["cluster_placed_here"] == 3


# ─── 5. Ids inside meta ───────────────────────────────────────────────

async def test_5_the_ids_inside_meta_are_translated(db):
    src = await _source(db)
    content = await _export(db, src)
    _, new_id = await _restore(db, content, src)

    restored = await _restored(db, new_id)
    people = {p.email: p for p in (await db.execute(
        select(Participant).where(Participant.event_id == new_id)
    )).scalars().all()}
    new_cat = (await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == new_id)
    )).scalar_one()
    units = {u.name: u for u in (await db.execute(
        select(AllocationUnit).where(AllocationUnit.category_id == new_cat.id)
    )).scalars().all()}
    new_mark_id = await _restored_mark_id(db, new_id)

    # A unit inside a cluster, and the members of that cluster.
    cluster = restored[T["cluster"]].meta
    assert cluster["run_id"] == "run-0001", "not an id: left alone"
    assert cluster["placement"]["unit_id"] == str(units["Lakeside"].id)
    assert cluster["placement"]["cluster_members"] == [
        {"id": str(people["anna-t@test.local"].id), "name": "Anna Alpha"},
        {"id": str(people["bruno-t@test.local"].id), "name": "Bruno Beta"},
    ], "the ids are translated and the name snapshots are left as they are"

    # Both ends of a move, and the nested `previous` under it.
    equalise = restored[T["equalise"]].meta["placement"]
    assert equalise["from_unit_id"] == str(units["Lakeside"].id)
    assert equalise["to_unit_id"] == str(units["Hillside"].id)
    previous = equalise["previous"]
    assert previous["unit_id"] == str(units["Lakeside"].id), (
        "a nested placement is translated too"
    )
    assert previous["cluster_members"][0]["id"] == str(
        people["anna-t@test.local"].id)

    # A bare mark id, and an id no map can know.
    drain = restored[T["drain"]].meta["placement"]
    assert new_mark_id != str(src["mark"].id), "the mark was renumbered"
    assert drain["mark_restriction"] == new_mark_id
    assert drain["unit_id"] == DEAD_ID, (
        "a unit the file does not carry is left exactly as it was, not "
        "dropped and not invented"
    )
    assert drain["unit_name"] == "The Old Barn"
    assert drain["gender_restriction"] == "female"


# ─── 6. The mark: trap ────────────────────────────────────────────────

async def test_6_a_mark_cluster_id_is_translated_and_a_group_code_is_not(db):
    src = await _source(db)
    content = await _export(db, src)
    _, new_id = await _restore(db, content, src)

    restored = await _restored(db, new_id)
    new_mark_id = await _restored_mark_id(db, new_id)
    assert new_mark_id != str(src["mark"].id), "the mark was renumbered"

    # A mark cluster: the prefix is kept exactly and the id behind it is
    # the restored mark's.
    assert restored[T["cluster"]].meta["placement"]["cluster_id"] == (
        f"mark:{new_mark_id}")

    # A group code IS the cluster id, and this one begins with "mark:".
    # It is free organiser text: byte for byte, nothing translated and
    # nothing stripped.
    assert restored[T["equalise"]].meta["placement"]["previous"]["cluster_id"] == (
        "mark:SMITH-100")

    # And the sharp case: a group code that is exactly what a mark
    # cluster's id would be. Only the reason tells them apart, so this one
    # must come back naming the SOURCE event's mark id, untouched, while
    # the mark cluster above names the restored one.
    assert restored[T["collision"]].meta["placement"]["cluster_id"] == (
        f"mark:{src['mark'].id}")
    assert restored[T["collision"]].meta["placement"]["cluster_id"] != (
        f"mark:{new_mark_id}")


# ─── 7. Structure mode ────────────────────────────────────────────────

async def test_7_a_template_carries_no_history(db):
    src = await _source(db)
    content = await _export(db, src, mode="structure")

    assert _history(content) == []

    result, new_id = await _restore(db, content, src)
    assert result["counts"]["allocation_events"] == 0
    assert await _restored(db, new_id) == {}


# ─── 8. A file made before this release ───────────────────────────────

async def test_8_a_file_without_the_member_still_restores(db):
    src = await _source(db)
    members = _members(await _export(db, src))
    assert "allocation_events.json" in members, (
        "it must be there before we take it away"
    )
    del members["allocation_events.json"]

    result, new_id = await _restore(db, _rezip(members), src)
    assert result["counts"]["allocation_events"] == 0
    assert await _restored(db, new_id) == {}
    # The rest of the event is unaffected.
    assert result["counts"]["participants"] == 2


# ─── 9. A duplicated line ─────────────────────────────────────────────

async def test_9_a_duplicated_line_keeps_the_first(db):
    src = await _source(db)
    content = await _export(db, src)

    def duplicate(rows):
        original = next(r for r in rows if _when(r) == T["exclude"])
        assert original["source"] == AllocationEventSource.MANUAL
        # Same old id, a different (and valid) source: if the second line
        # won, the restored row would read clear_category.
        rows.append({**original,
                     "source": AllocationEventSource.CLEAR_CATEGORY})

    result, new_id = await _restore(db, _edit_history(content, duplicate), src)

    assert result["counts"]["allocation_events"] == 5, "not six"
    assert result["skipped"]["allocation_events.json"] == 1
    restored = await _restored(db, new_id)
    assert restored[T["exclude"]].source == AllocationEventSource.MANUAL


# ─── 10. A kind or source this instance does not know ─────────────────

async def test_10_an_unknown_kind_or_source_costs_its_line(db):
    src = await _source(db)
    content = await _export(db, src)

    def scramble(rows):
        by_time = {_when(r): r for r in rows}
        by_time[T["exclude"]]["event_type"] = "teleport"
        by_time[T["cluster"]]["source"] = "telepathy"

    result, new_id = await _restore(db, _edit_history(content, scramble), src)

    assert result["skipped"]["allocation_events.json"] == 2
    assert result["counts"]["allocation_events"] == 3
    restored = await _restored(db, new_id)
    assert set(restored) == {T["equalise"], T["drain"], T["collision"]}
    # The restore itself succeeded.
    assert result["counts"]["participants"] == 2


# ─── 11. A unit the file does not carry ───────────────────────────────

async def test_11_an_unresolvable_unit_becomes_null_and_is_counted(db):
    src = await _source(db)
    content = await _export(db, src)

    def orphan(rows):
        row = next(r for r in rows if _when(r) == T["cluster"])
        row["unit_id"] = DEAD_ID

    result, new_id = await _restore(db, _edit_history(content, orphan), src)

    assert result["counts"]["allocation_events"] == 5, "the row is kept"
    assert result["defaulted"]["allocation_events.unit_id"] == 1
    assert not result["skipped"], "nothing was skipped over this"

    restored = await _restored(db, new_id)
    row = restored[T["cluster"]]
    assert row.unit_id is None, (
        "which is what the database itself does when the unit is deleted"
    )
    # And the line still reads: the snapshot is why it is kept.
    assert row.unit_name_snapshot == "Lakeside"
    through_the_screen = next(
        r for r in await list_allocation_events(db, event_id=new_id)
        if _when(r) == T["cluster"]
    )
    assert through_the_screen["unit_id"] is None
    assert through_the_screen["unit_name"] == "Lakeside"


# ─── 12. What the screen shows ────────────────────────────────────────

async def test_12_the_read_path_shows_a_restored_row_whole(db):
    src = await _source(db)
    content = await _export(db, src)
    _, new_id = await _restore(db, content, src)

    anna = (await db.execute(
        select(Participant).where(
            Participant.event_id == new_id,
            Participant.email == "anna-t@test.local",
        )
    )).scalar_one()

    timeline = await list_allocation_events(
        db, event_id=new_id, participant_id=anna.id)
    assert len(timeline) == 3, (
        "her exclusion, her mark-cluster placement and her group-code one"
    )

    placement = next(r for r in timeline if _when(r) == T["cluster"])
    assert placement["event_type"] == AllocationEventType.ASSIGN
    assert placement["source"] == AllocationEventSource.ENGINE_COMMIT
    assert placement["unit_name"] == "Lakeside"
    assert placement["category_name"] == "Bedrooms"
    assert placement["participant_name"] == "Anna Alpha"
    # The screen renders a missing actor as a removed user, with no new
    # string, which is why NULL is the right answer and not a placeholder.
    assert placement["actor_user_id"] is None
    assert placement["actor_display_name"] is None
    assert placement["meta"]["placement"]["reason"] == "mark_together"


# ─── 13. The register runs out of gaps ────────────────────────────────

async def test_13_no_known_gap_is_left_anywhere_in_the_register():
    """The check BACKUP_REGISTER_DOC has promised since v1.0.4n.

    This is the last backup release before v1.0.5, so this is where the
    promise comes due: the register shrinking to zero gaps is the
    definition of done, not a judgement call.
    """
    columns = sorted(
        f"{table}.{column} ({col.reason})"
        for table, rule in BACKUP_REGISTER.items()
        for column, col in rule.columns.items()
        if col.reason and col.reason.startswith(KNOWN_GAP_PREFIX)
    )
    tables = sorted(
        f"{table} ({reason})"
        for table, reason in NOT_CARRIED.items()
        if reason.startswith(KNOWN_GAP_PREFIX)
    )
    assert not columns and not tables, (
        "v1.0.5 cannot ship while a known_gap is left in the backup "
        f"register. Columns: {columns or 'none'}. Tables: {tables or 'none'}."
    )

    # `event_user_assignments` is still not carried, and that is a decision
    # rather than a gap: a permission must never come from a file.
    assert NOT_CARRIED["event_user_assignments"] == "not_meaningful_elsewhere"
