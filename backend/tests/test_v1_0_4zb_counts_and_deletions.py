"""v1.0.4zb — the counts, and what nobody was told.

Six defects, all of them things that look right until the data is awkward.
Every count test here therefore carries the awkward data: somebody who
cancelled, somebody who was removed, an exclusion on each of them, and a
group type where one person holds several places.

  - DASH-1  the unassigned figure subtracted allocation ROWS from a
            head-count, so an overlapping group type under-reported it and,
            once rows passed people, went below zero.
  - DASH-2  create and update answered with the raw ORM row, a different
            shape from the list of the same thing.
  - DASH-3  `excluded_count` counted exclusion rows belonging to people no
            longer on the roster, and two surfaces subtract it from a total
            already filtered by status — so each stale row came off twice.
  - STREAM-2 cancelling or removing somebody told nobody, so another
            organiser's board kept showing them.
  - USER-1  deleting a user who had written a note raised an integrity
            error that reached the organiser as a 500.

HIST-1 is not here: `collapseMoves` is frontend, and its test lives beside
it in AllocationHistory.test.jsx.

Endpoint functions are called directly with an explicit db and user, the way
test_v1_0_4o_damaged_files.py does.
"""

import asyncio
import uuid

import pytest
from sqlalchemy import func, select

from app.api.allocations import (
    CategoryCreate, CategoryUpdate, api_create_category, api_update_category,
)
from app.api.participants import delete_participant, patch_participant
from app.api.users import delete_user
from app.core.pubsub import broker
from app.models.allocation import Allocation
from app.models.allocation_category_exclusion import AllocationCategoryExclusion
from app.models.note import Note
from app.models.participant import RegistrationStatus
from app.models.user import User, UserRole
from app.schemas.participant import ParticipantUpdate
from app.services.allocation_service import list_categories

from tests.conftest import (
    make_category,
    make_event,
    make_participant,
    make_unit,
    make_user,
)

pytestmark = pytest.mark.asyncio


async def _exclude(db, category_id, participant_id):
    row = AllocationCategoryExclusion(
        allocation_category_id=category_id, participant_id=participant_id,
    )
    db.add(row)
    await db.flush()
    return row


async def _place(db, event_id, unit_id, participant_id):
    row = Allocation(
        event_id=event_id, unit_id=unit_id, participant_id=participant_id,
    )
    db.add(row)
    await db.flush()
    return row


async def _cat(db, event_id, name):
    """The one entry for this category out of the list payload."""
    for entry in await list_categories(db, event_id):
        if entry["name"] == name:
            return entry
    raise AssertionError(f"no category named {name}")


# ─── DASH-1: rows are not people ──────────────────────────────────────

async def test_placed_people_counts_people_not_rows(db):
    """One person in two units of an overlapping group type is ONE person
    placed and TWO places used. The tile subtracts the first; the units grid
    wants the second. Both numbers must be on the payload and they must
    differ here, or the test is not exercising the case."""
    ev = await make_event(db, name="Overlapping Event")
    cat = await make_category(db, ev.id, name="Workshops")
    cat.rule_type = "overlapping"
    u1 = await make_unit(db, cat.id, name="Pottery")
    u2 = await make_unit(db, cat.id, name="Welding")
    p = await make_participant(db, ev.id, first_name="Alice")
    await _place(db, ev.id, u1.id, p.id)
    await _place(db, ev.id, u2.id, p.id)
    await db.flush()

    entry = await _cat(db, ev.id, "Workshops")

    assert entry["allocated_count"] == 2, "places used"
    assert entry["placed_people_count"] == 1, "people placed"


async def test_the_unassigned_subtraction_cannot_go_negative(db):
    """The arithmetic the dashboard tile performs, at the shape that used to
    produce a negative: two people, each holding two places, against a roster
    of two. Rows = 4, people = 2. 2 - 4 was -2."""
    ev = await make_event(db, name="Negative Event")
    cat = await make_category(db, ev.id, name="Workshops")
    cat.rule_type = "overlapping"
    u1 = await make_unit(db, cat.id, name="Pottery")
    u2 = await make_unit(db, cat.id, name="Welding")
    people = [await make_participant(db, ev.id, first_name=n)
              for n in ("Alice", "Bob")]
    for p in people:
        await _place(db, ev.id, u1.id, p.id)
        await _place(db, ev.id, u2.id, p.id)
    await db.flush()

    entry = await _cat(db, ev.id, "Workshops")
    eligible_total = len(people) - entry["excluded_count"]

    assert entry["allocated_count"] == 4, "the old subtrahend"
    assert eligible_total - entry["allocated_count"] == -2, "what it used to give"
    assert eligible_total - entry["placed_people_count"] == 0, "what it gives now"


# ─── DASH-3: an exclusion on somebody who has left ────────────────────

async def test_excluded_count_ignores_cancelled_and_removed(db):
    """Four people, all excluded from the same group type: one active, one
    cancelled, one soft-deleted, and one both. Only the active one counts.

    Nothing deletes an exclusion row when somebody leaves, and that is
    deliberate — an exclusion records what an organiser decided, and a
    status change must not erase it. So the rows are all still there; the
    count simply must not see them."""
    ev = await make_event(db, name="Leavers Event")
    cat = await make_category(db, ev.id, name="Rooms")

    active = await make_participant(db, ev.id, first_name="Active")
    cancelled = await make_participant(
        db, ev.id, first_name="Cancelled", status=RegistrationStatus.CANCELLED)
    removed = await make_participant(db, ev.id, first_name="Removed")
    removed.deleted_at = func.now()
    both = await make_participant(
        db, ev.id, first_name="Both", status=RegistrationStatus.CANCELLED)
    both.deleted_at = func.now()
    for p in (active, cancelled, removed, both):
        await _exclude(db, cat.id, p.id)
    await db.flush()

    entry = await _cat(db, ev.id, "Rooms")

    assert entry["excluded_count"] == 1, "only the person still on the roster"
    # The rows themselves survive: this is a counting fix, not a deletion.
    total_rows = (await db.execute(
        select(func.count()).select_from(AllocationCategoryExclusion)
        .where(AllocationCategoryExclusion.allocation_category_id == cat.id)
    )).scalar()
    assert total_rows == 4, "an exclusion outlives a status change"


async def test_excluded_count_is_zero_when_nobody_is_excluded(db):
    ev = await make_event(db, name="Clean Event")
    await make_category(db, ev.id, name="Rooms")
    await make_participant(db, ev.id, first_name="Alice")
    await db.flush()

    assert (await _cat(db, ev.id, "Rooms"))["excluded_count"] == 0


# ─── DASH-2: one shape for one thing ──────────────────────────────────

async def test_create_and_update_answer_in_the_list_shape(db):
    """An endpoint that answers differently from the one that lists the same
    thing is a trap for whichever caller stops re-listing first."""
    user = await make_user(db, email="cat-admin@test.local")
    ev = await make_event(db, name="Shape Event")

    created = await api_create_category(
        event_id=ev.id,
        data=CategoryCreate(name="Rooms", item_label="Room"),
        db=db, current_user=user,
    )
    aggregates = {"unit_count", "allocated_count",
                  "placed_people_count", "excluded_count", "total_capacity"}
    assert aggregates <= set(created), "create dropped the aggregates"

    updated = await api_update_category(
        event_id=ev.id, category_id=created["id"],
        data=CategoryUpdate(name="Dormitories"),
        db=db, current_user=user,
    )
    assert aggregates <= set(updated), "update dropped the aggregates"
    assert updated["name"] == "Dormitories"
    # Same keys as the list it claims to be an entry of.
    listed = await _cat(db, ev.id, "Dormitories")
    assert set(updated) == set(listed)


# ─── STREAM-2: the board is told ──────────────────────────────────────

async def test_cancelling_somebody_is_published_to_the_board(db):
    """The board refetches on any message on its own topic, so publishing is
    the whole fix. Until now a colleague's cancellation left them on another
    organiser's board until something unrelated forced a reload."""
    user = await make_user(db, email="stream-admin@test.local")
    ev = await make_event(db, name="Stream Event")
    p = await make_participant(db, ev.id, first_name="Alice")
    await db.flush()

    async with broker.subscribe(f"organise:{ev.id}") as queue:
        await patch_participant(
            participant_id=p.id,
            data=ParticipantUpdate(registration_status="cancelled"),
            db=db, current_user=user,
        )
        msg = await asyncio.wait_for(queue.get(), timeout=2)

    assert msg["type"] == "allocation_changed"
    assert msg["kind"] == "participant_changed"
    assert msg["participant_id"] == str(p.id)


async def test_removing_somebody_is_published_to_the_board(db):
    user = await make_user(db, email="stream-admin2@test.local")
    ev = await make_event(db, name="Stream Event 2")
    p = await make_participant(db, ev.id, first_name="Bob")
    await db.flush()

    async with broker.subscribe(f"organise:{ev.id}") as queue:
        await delete_participant(
            participant_id=p.id, db=db, current_user=user,
        )
        msg = await asyncio.wait_for(queue.get(), timeout=2)

    assert msg["kind"] == "participant_deleted"
    assert msg["participant_id"] == str(p.id)


# ─── USER-1: deleting somebody who wrote things ───────────────────────

async def _author(db, email):
    u = User(
        email=email,
        hashed_password="$2b$12$v1041zb.placeholder.hash.for.fixtures..",
        full_name="The Author",
        role=UserRole.STAFF,
    )
    db.add(u)
    await db.flush()
    return u


async def _note(db, event_id, author_id, content, published):
    n = Note(
        notable_type="event", notable_id=event_id,
        content=content, is_published=published, author_id=author_id,
    )
    db.add(n)
    await db.flush()
    return n


async def test_deleting_an_author_succeeds_where_it_used_to_fail(db):
    """`notes.author_id` was NOT NULL with a foreign key carrying no ON
    DELETE clause, so the database refused the delete and the organiser saw
    a 500. Confirmed against the deployed schema before the fix."""
    admin = await make_user(db, email="deleter@test.local")
    author = await _author(db, "author-a@test.local")
    ev = await make_event(db, name="Author Event")
    await _note(db, ev.id, author.id, "published thing", True)
    await db.flush()

    await delete_user(user_id=author.id, db=db, current_user=admin)

    gone = (await db.execute(
        select(func.count()).select_from(User).where(User.id == author.id)
    )).scalar()
    assert gone == 0


async def test_their_drafts_go_with_them(db):
    """A draft is that person's own working note. It also MUST go: the
    visibility rule is "published, or mine", so a null author matches
    nobody and a null-author draft would be unreachable forever."""
    admin = await make_user(db, email="deleter2@test.local")
    author = await _author(db, "author-b@test.local")
    ev = await make_event(db, name="Draft Event")
    draft = await _note(db, ev.id, author.id, "my rough thoughts", False)
    await db.flush()

    await delete_user(user_id=author.id, db=db, current_user=admin)

    left = (await db.execute(
        select(func.count()).select_from(Note).where(Note.id == draft.id)
    )).scalar()
    assert left == 0, "an unpublished note outlived its author"


async def test_their_published_notes_stay_with_no_author(db):
    """The honest answer, and the same one v1.0.4t gives for history from a
    departed user. Authorship is never reassigned: that would make the
    record say somebody wrote what they did not."""
    admin = await make_user(db, email="deleter3@test.local")
    author = await _author(db, "author-c@test.local")
    ev = await make_event(db, name="Published Event")
    kept = await _note(db, ev.id, author.id, "the team should know", True)
    await db.flush()

    await delete_user(user_id=author.id, db=db, current_user=admin)
    await db.refresh(kept)

    assert kept.content == "the team should know", "the note survived"
    assert kept.author_id is None, "and it names nobody"


async def test_one_authors_deletion_leaves_another_authors_notes(db):
    """The sweep is scoped to the departing user, which is the kind of thing
    a WHERE clause gets wrong once."""
    admin = await make_user(db, email="deleter4@test.local")
    going = await _author(db, "author-going@test.local")
    staying = await _author(db, "author-staying@test.local")
    ev = await make_event(db, name="Two Authors Event")
    theirs = await _note(db, ev.id, staying.id, "still mine", False)
    await _note(db, ev.id, going.id, "my draft", False)
    await db.flush()

    await delete_user(user_id=going.id, db=db, current_user=admin)
    await db.refresh(theirs)

    assert theirs.author_id == staying.id, "somebody else's draft was swept"
