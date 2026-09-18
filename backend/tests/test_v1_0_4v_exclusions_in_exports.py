"""v1.0.4v — an exclusion is in the two people exports at last.

An exclusion is the one decision an organiser records about a person that
neither people export mentioned. It was visible only on the allocation
board. The People page spreadsheet now has an "Excluded From" column, and
a person's own data export now carries their exclusions.

The rules these tests pin, from the release brief:

  - The column is called "Excluded From" and sits straight after "Marks",
    before the custom fields. No existing column moves.
  - The cell holds the group type names, separated by ", ", exactly as
    "Marks" does, and is empty when there are none.
  - The stored name, never an id and never a translation.
  - A cancelled participant keeps their exclusions in the file. An
    exclusion records intent, and an unrelated status change does not
    undo it. (Removed people are already out of this export, because
    `list_participants` filters `deleted_at`.)
  - The person's own export carries the group type name and the date, and
    an empty list when there are none, with every other key untouched.

The endpoint function is called directly with an explicit db and user, the
way test_v1_0_4o_damaged_files.py does.
"""

import csv
import io

import pytest

from app.api.export import export_participants_csv
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.participant import RegistrationStatus
from app.services.data_export_service import export_participant_data

from tests.conftest import (
    make_category,
    make_event,
    make_participant,
    make_user,
)

pytestmark = pytest.mark.asyncio


# The header as it must read, in order. Asserted whole, so a column that
# moves fails here rather than somewhere downstream.
BASE_HEADER = [
    "First Name", "Last Name", "Email", "Gender",
    "Date of Birth", "Phone", "Address", "Country",
    "Church/Organisation", "Group Code", "GDPR Consent",
    "No.", "Status", "Checked In",
    "Marks",
    "Excluded From",
    "Message",
]


async def _exclude(db, category_id, participant_id):
    row = AllocationCategoryExclusion(
        allocation_category_id=category_id,
        participant_id=participant_id,
    )
    db.add(row)
    await db.flush()
    return row


async def _csv_rows(db, event_id, user) -> list[list[str]]:
    """Call the endpoint and parse what it streamed."""
    response = await export_participants_csv(
        event_id=event_id, mode="full", db=db, current_user=user)
    chunks = [c async for c in response.body_iterator]
    text = "".join(
        c.decode("utf-8") if isinstance(c, bytes) else c for c in chunks)
    return list(csv.reader(io.StringIO(text)))


def _cell(rows: list[list[str]], column: str, email: str) -> str:
    header = rows[0]
    i = header.index(column)
    j = header.index("Email")
    for row in rows[1:]:
        if row[j] == email:
            return row[i]
    raise AssertionError(f"no row for {email} in the file")


# ─── 1. the header ────────────────────────────────────────────────────

async def test_the_header_has_excluded_from_after_marks(db):
    user = await make_user(db, email="csv-admin@test.local")
    ev = await make_event(db, name="Header Event")
    await make_participant(db, ev.id, first_name="Alice")
    await db.flush()

    rows = await _csv_rows(db, ev.id, user)

    assert rows[0] == BASE_HEADER
    # Stated twice on purpose: the whole-header assertion above says where
    # every column is, this says the one relationship that matters.
    assert rows[0].index("Excluded From") == rows[0].index("Marks") + 1


async def test_custom_fields_still_sit_between_the_column_and_message(db):
    from app.models.custom_field import CustomFieldDefinition

    user = await make_user(db, email="cf-admin@test.local")
    ev = await make_event(db, name="Custom Field Event")
    db.add(CustomFieldDefinition(
        event_id=ev.id, label="T-shirt size", field_type="text", sort_order=0,
    ))
    await make_participant(db, ev.id, first_name="Alice")
    await db.flush()

    rows = await _csv_rows(db, ev.id, user)

    assert rows[0] == BASE_HEADER[:-1] + ["T-shirt size", "Message"]


# ─── 2. two exclusions ────────────────────────────────────────────────

async def test_two_exclusions_are_listed_comma_separated(db):
    user = await make_user(db, email="two-admin@test.local")
    ev = await make_event(db, name="Two Exclusions")
    rooms = await make_category(db, ev.id, name="Rooms")
    groups = await make_category(db, ev.id, name="Small Groups")
    p = await make_participant(db, ev.id, first_name="Alice")
    await _exclude(db, rooms.id, p.id)
    await _exclude(db, groups.id, p.id)
    await db.flush()

    rows = await _csv_rows(db, ev.id, user)

    cell = _cell(rows, "Excluded From", p.email)
    assert cell in ("Rooms, Small Groups", "Small Groups, Rooms")
    assert ", " in cell, "the separator must match the Marks column"


# ─── 3. no exclusions ─────────────────────────────────────────────────

async def test_no_exclusions_leaves_the_cell_empty(db):
    user = await make_user(db, email="none-admin@test.local")
    ev = await make_event(db, name="No Exclusions")
    await make_category(db, ev.id, name="Rooms")
    p = await make_participant(db, ev.id, first_name="Alice")
    await db.flush()

    rows = await _csv_rows(db, ev.id, user)

    assert _cell(rows, "Excluded From", p.email) == ""


# ─── 4. a cancelled participant ───────────────────────────────────────

async def test_a_cancelled_participant_keeps_their_exclusion(db):
    user = await make_user(db, email="cancelled-admin@test.local")
    ev = await make_event(db, name="Cancelled Event")
    rooms = await make_category(db, ev.id, name="Rooms")
    p = await make_participant(
        db, ev.id, first_name="Alice", status=RegistrationStatus.CANCELLED)
    await _exclude(db, rooms.id, p.id)
    await db.flush()

    rows = await _csv_rows(db, ev.id, user)

    # They are still in the file, and so is what was decided about them.
    assert _cell(rows, "Status", p.email) == "cancelled"
    assert _cell(rows, "Excluded From", p.email) == "Rooms"


# ─── 5. stored names, not ids ─────────────────────────────────────────

async def test_the_cell_holds_the_stored_name_not_an_id(db):
    user = await make_user(db, email="named-admin@test.local")
    ev = await make_event(db, name="Renamed Event")
    # A name that is neither a stored default nor anything a translation
    # would produce, so only the stored value can put it in the cell.
    cat = await make_category(db, ev.id, name="Dormitory Wings")
    p = await make_participant(db, ev.id, first_name="Alice")
    await _exclude(db, cat.id, p.id)
    await db.flush()

    rows = await _csv_rows(db, ev.id, user)

    cell = _cell(rows, "Excluded From", p.email)
    assert cell == "Dormitory Wings"
    assert str(cat.id) not in cell
    assert str(p.id) not in cell


# ─── 6. the person's own export ───────────────────────────────────────

async def test_the_persons_export_carries_their_exclusions(db):
    ev = await make_event(db, name="Person Export Event")
    rooms = await make_category(db, ev.id, name="Rooms")
    groups = await make_category(db, ev.id, name="Small Groups")
    p = await make_participant(db, ev.id, first_name="Alice")
    await _exclude(db, rooms.id, p.id)
    await _exclude(db, groups.id, p.id)
    await db.flush()

    payload = await export_participant_data(db, ev.id, p.id)

    names = [e["category_name"] for e in payload["exclusions"]]
    assert sorted(names) == ["Rooms", "Small Groups"]
    for entry in payload["exclusions"]:
        assert entry["created_at"], "an exclusion must say when it was recorded"
        # Names, never ids, exactly as `allocations` does it.
        assert set(entry) == {"category_name", "created_at"}
    assert str(rooms.id) not in str(payload["exclusions"])


async def test_the_persons_export_has_an_empty_list_when_there_are_none(db):
    ev = await make_event(db, name="Clean Person Event")
    await make_category(db, ev.id, name="Rooms")
    p = await make_participant(db, ev.id, first_name="Alice")
    await db.flush()

    payload = await export_participant_data(db, ev.id, p.id)

    assert payload["exclusions"] == []


# ─── 7. nothing else in that export changed ───────────────────────────

async def test_the_rest_of_the_persons_export_is_untouched(db):
    ev = await make_event(db, name="Whole Export Event")
    rooms = await make_category(db, ev.id, name="Rooms")
    p = await make_participant(db, ev.id, first_name="Alice")
    await _exclude(db, rooms.id, p.id)
    await db.flush()

    payload = await export_participant_data(db, ev.id, p.id)

    assert list(payload) == [
        "export_metadata",
        "event",
        "participant",
        "custom_fields",
        "marks",
        "preference_requests",
        "allocations",
        "exclusions",
        "allocation_history",
        "notes",
        "checkin_values",
    ]
    # The one new key aside, the shape the file has always had.
    assert payload["participant"]["first_name"] == "Alice"
    assert payload["event"]["name"] == "Whole Export Event"
    assert payload["export_metadata"]["kind"] == (
        "admin_on_behalf_participant_export")
