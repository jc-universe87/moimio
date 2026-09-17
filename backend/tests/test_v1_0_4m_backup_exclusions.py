"""v1.0.4m — backup and restore carry allocation category exclusions.

BACKUP-1: `backup_service.py` did not know exclusions existed. Export an
event, restore it, and every exclusion was silently gone.

Governing rule on restore: the exclusion wins. If a file says someone is
both excluded from a group type and placed in it, the exclusion is
restored, the placement is not, and the restore carries on.

Covers:
  1. Round trip — a full export restores exactly the exclusions that
     travelled with their people, with no attribution, and leaves an
     unrelated placement standing.
  2. Old file — a backup with no `allocation_exclusions.json` at all
     still restores, as "nobody excluded". The member is optional on
     read and must never join the required set.
  3. Broken file — a hand-edited file that breaks the invariant loses
     the placement, keeps the exclusion, and logs one warning that
     names no person.
  4. Duplicate row — a duplicated pair is dropped before it can reach
     the UNIQUE constraint and roll the whole restore back.
  5. Structure mode — the member is written and empty, because an
     exclusion cannot travel without its person.

Every id changes on restore, so restored rows are identified by
participant email and group type name throughout.

Service-layer only, like the v1.0.4i, j and k files.
"""

import io
import json
import zipfile

import pytest
from sqlalchemy import select

from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.allocation_unit import AllocationUnit
from app.models.participant import Participant, RegistrationStatus
from app.services.allocation_service import add_exclusion
from app.services.backup_service import confirm_restore, export_event_zip
from app.services.participant_service import soft_delete_participant

from tests.conftest import (
    make_category,
    make_event,
    make_participant,
    make_unit,
)


pytestmark = pytest.mark.asyncio

MEMBER = "allocation_exclusions.json"
COUNT_KEY = "allocation_exclusions"


# ─── The event ────────────────────────────────────────────────────────
#
# Two group types: A with two units, B with one.
#
#   P1  normal          placed in A1        excluded from B
#   P2  cancelled       nothing             excluded from A
#   P3  soft-deleted    nothing             excluded from A (then removed)
#   P4  normal          placed in B1        nothing
#
# So a full export carries P1, P2 and P4, and exactly two exclusions:
# P1 from B and P2 from A. P3's row is left behind because P3 is not in
# the export, and an exclusion travels with its person.

async def _build_event(db) -> dict:
    ev = await make_event(db, name="Backup Source")
    cat_a = await make_category(db, ev.id, name="A")
    cat_b = await make_category(db, ev.id, name="B")
    a1 = await make_unit(db, cat_a.id, "A1")
    a2 = await make_unit(db, cat_a.id, "A2")
    b1 = await make_unit(db, cat_b.id, "B1")

    p1 = await make_participant(
        db, ev.id, first_name="Pauline", last_name="One", email="p1@test.local",
    )
    p2 = await make_participant(
        db, ev.id, first_name="Quentin", last_name="Two", email="p2@test.local",
        status=RegistrationStatus.CANCELLED,
    )
    p3 = await make_participant(
        db, ev.id, first_name="Rashida", last_name="Three", email="p3@test.local",
    )
    p4 = await make_participant(
        db, ev.id, first_name="Sunil", last_name="Four", email="p4@test.local",
    )

    # Placements written directly: this file is about the backup path, not
    # about what assign_participant does on the way in.
    db.add(Allocation(event_id=ev.id, participant_id=p1.id, unit_id=a1.id))
    db.add(Allocation(event_id=ev.id, participant_id=p4.id, unit_id=b1.id))
    await db.flush()

    # Exclusions through the real write path.
    await add_exclusion(db, cat_b.id, p1.id)
    await add_exclusion(db, cat_a.id, p2.id)
    await add_exclusion(db, cat_a.id, p3.id)

    # P3 is removed only once its exclusion exists.
    await soft_delete_participant(db, p3)
    await db.flush()

    return {
        "event": ev, "cat_a": cat_a, "cat_b": cat_b,
        "a1": a1, "a2": a2, "b1": b1,
        "p1": p1, "p2": p2, "p3": p3, "p4": p4,
    }


# ─── Reading a restored event back ────────────────────────────────────

async def _restored_exclusions(db, new_event_id) -> set[tuple[str, str]]:
    """(participant email, group type name) for every exclusion on the event."""
    result = await db.execute(
        select(Participant.email, AllocationCategory.name)
        .join(
            AllocationCategoryExclusion,
            AllocationCategoryExclusion.participant_id == Participant.id,
        )
        .join(
            AllocationCategory,
            AllocationCategory.id
            == AllocationCategoryExclusion.allocation_category_id,
        )
        .where(AllocationCategory.event_id == new_event_id)
    )
    return {(email, name) for email, name in result.all()}


async def _restored_holdings(db, new_event_id) -> set[tuple[str, str]]:
    """(participant email, group type name) for every unit a person holds."""
    result = await db.execute(
        select(Participant.email, AllocationCategory.name)
        .join(Allocation, Allocation.participant_id == Participant.id)
        .join(AllocationUnit, AllocationUnit.id == Allocation.unit_id)
        .join(
            AllocationCategory,
            AllocationCategory.id == AllocationUnit.category_id,
        )
        .where(Allocation.event_id == new_event_id)
    )
    return {(email, name) for email, name in result.all()}


async def _assert_invariant(db, new_event_id) -> None:
    """Nobody is both excluded from a group type and holding a unit in it."""
    excluded = await _restored_exclusions(db, new_event_id)
    held = await _restored_holdings(db, new_event_id)
    both = excluded & held
    assert not both, f"excluded and placed in the same group type: {sorted(both)}"


async def _created_by_values(db, new_event_id) -> list:
    result = await db.execute(
        select(AllocationCategoryExclusion.created_by)
        .join(
            AllocationCategory,
            AllocationCategory.id
            == AllocationCategoryExclusion.allocation_category_id,
        )
        .where(AllocationCategory.event_id == new_event_id)
    )
    return list(result.scalars().all())


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


def _manifest(content: bytes) -> dict:
    return json.loads(_members(content)["manifest.json"])


def _exclusion_rows(content: bytes) -> list:
    return json.loads(_members(content)[MEMBER])


# ─── 1. Round trip ────────────────────────────────────────────────────

async def test_round_trip_carries_the_exclusions_that_travel(db):
    src = await _build_event(db)

    content = await export_event_zip(src["event"].id, db, mode="full")

    # Exactly the two whose participant and group type are both exported.
    assert _manifest(content)["counts"][COUNT_KEY] == 2
    assert len(_exclusion_rows(content)) == 2

    result = await confirm_restore(content, db)
    new_event_id = result["new_event_id"]

    assert result["counts"][COUNT_KEY] == 2
    assert await _restored_exclusions(db, new_event_id) == {
        ("p1@test.local", "B"),
        ("p2@test.local", "A"),
    }

    # No attribution: nobody on this instance made those decisions.
    values = await _created_by_values(db, new_event_id)
    assert values == [None, None]

    # P1's placement in A is unrelated to P1's exclusion from B, so it stands.
    assert ("p1@test.local", "A") in await _restored_holdings(db, new_event_id)
    await _assert_invariant(db, new_event_id)


# ─── 2. Old file ──────────────────────────────────────────────────────

async def test_old_file_without_the_member_restores_with_nobody_excluded(db):
    src = await _build_event(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    members = _members(content)
    assert MEMBER in members, "the member must exist before we take it away"
    del members[MEMBER]
    manifest = json.loads(members["manifest.json"])
    del manifest["counts"][COUNT_KEY]
    members["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")
    old_content = _rezip(members)

    result = await confirm_restore(old_content, db)
    new_event_id = result["new_event_id"]

    assert result["counts"][COUNT_KEY] == 0
    assert await _restored_exclusions(db, new_event_id) == set()
    assert ("p1@test.local", "A") in await _restored_holdings(db, new_event_id)


# ─── 3. Broken file ───────────────────────────────────────────────────

async def test_broken_file_keeps_the_exclusion_and_drops_the_placement(db, capsys):
    src = await _build_event(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    # Hand-edit: P1 is now also excluded from A, where P1 holds a unit.
    members = _members(content)
    rows = json.loads(members[MEMBER])
    rows.append({
        "id": "00000000-0000-0000-0000-0000000000ff",
        "allocation_category_id": str(src["cat_a"].id),
        "participant_id": str(src["p1"].id),
        "created_at": None,
    })
    members[MEMBER] = json.dumps(rows, indent=2).encode("utf-8")
    broken = _rezip(members)

    capsys.readouterr()  # drop anything printed while building the event
    result = await confirm_restore(broken, db)
    captured = capsys.readouterr().out
    new_event_id = result["new_event_id"]

    assert result["counts"][COUNT_KEY] == 3
    assert await _restored_exclusions(db, new_event_id) == {
        ("p1@test.local", "A"),
        ("p1@test.local", "B"),
        ("p2@test.local", "A"),
    }

    holdings = await _restored_holdings(db, new_event_id)
    assert ("p1@test.local", "A") not in holdings, "the exclusion must win"
    assert ("p4@test.local", "B") in holdings, "an unrelated placement must stand"
    await _assert_invariant(db, new_event_id)

    # One warning, naming the event and the count, and nobody at all.
    assert captured.count("[RESTORE WARNING]") == 1
    assert str(new_event_id) in captured
    assert "1 placement" in captured
    assert "Pauline" not in captured
    assert "p1@test.local" not in captured
    assert str(src["p1"].id) not in captured


# ─── 4. Duplicate row ────────────────────────────────────────────────

async def test_duplicate_row_is_dropped_before_the_unique_constraint(db):
    src = await _build_event(db)
    content = await export_event_zip(src["event"].id, db, mode="full")

    members = _members(content)
    rows = json.loads(members[MEMBER])
    p2_rows = [r for r in rows if r["participant_id"] == str(src["p2"].id)]
    assert len(p2_rows) == 1
    rows.append(dict(p2_rows[0], id="00000000-0000-0000-0000-0000000000ee"))
    members[MEMBER] = json.dumps(rows, indent=2).encode("utf-8")

    result = await confirm_restore(_rezip(members), db)
    new_event_id = result["new_event_id"]

    assert result["counts"][COUNT_KEY] == 2
    restored = await _restored_exclusions(db, new_event_id)
    assert restored == {("p1@test.local", "B"), ("p2@test.local", "A")}
    assert len([r for r in restored if r[0] == "p2@test.local"]) == 1


# ─── 5. Structure mode ───────────────────────────────────────────────

async def test_structure_mode_writes_the_member_empty(db):
    src = await _build_event(db)
    content = await export_event_zip(src["event"].id, db, mode="structure")

    members = _members(content)
    assert MEMBER in members
    assert json.loads(members[MEMBER]) == []
    assert _manifest(content)["counts"][COUNT_KEY] == 0

    result = await confirm_restore(content, db)
    assert result["counts"][COUNT_KEY] == 0
    assert await _restored_exclusions(db, result["new_event_id"]) == set()
