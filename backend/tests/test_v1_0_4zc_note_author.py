"""v1.0.4zc — a note says who wrote it, and the export still does not.

NOTE-1. `api/notes.py` returned `author_id` as a raw UUID and no screen read
it, so a note card showed a badge and a timestamp and nothing else. The
consequence Johannes hit testing v1.0.4zb: a note whose author has since
been deleted looks like every other note, so that release's careful answer —
the note stays, with no author — was invisible.

The API now resolves the name. Three things need pinning:

  - the name is on the payload, so the screen has something to render;
  - a note whose author has been deleted carries None and the endpoint does
    not fail, which is the v1.0.4zb case that started this;
  - **the participant's own data export does NOT gain the author.** That
    export deliberately coarsens who did what and says so in its own
    metadata. Putting an author on the wire elsewhere makes it easy to leak
    here by accident, which is exactly why this is a test and not a
    reading.

Endpoint functions are called directly with an explicit db and user, the way
test_v1_0_4o_damaged_files.py does.
"""

import pytest
from sqlalchemy import select

from app.api.notes import NoteCreate, create_note, list_notes
from app.api.users import delete_user
from app.models.note import Note
from app.models.user import User, UserRole
from app.services.data_export_service import export_participant_data

from tests.conftest import make_event, make_participant, make_user

pytestmark = pytest.mark.asyncio


async def _staff(db, email, name="Vera Note"):
    u = User(
        email=email,
        hashed_password="$2b$12$v1041zc.placeholder.hash.for.fixtures..",
        full_name=name,
        role=UserRole.STAFF,
    )
    db.add(u)
    await db.flush()
    return u


async def _note(db, notable_type, notable_id, author, content, published=True):
    n = Note(
        notable_type=notable_type, notable_id=notable_id,
        content=content, is_published=published, author_id=author.id,
    )
    db.add(n)
    await db.flush()
    return n


# ─── the payload carries the name ─────────────────────────────────────

async def test_the_list_carries_the_authors_name(db):
    author = await _staff(db, "author-name@test.local", name="Vera Note")
    ev = await make_event(db, name="Author Event")
    await _note(db, "event", ev.id, author, "the team should know")
    await db.flush()

    out = await list_notes(
        notable_type="event", notable_id=ev.id, db=db, current_user=author)

    assert len(out) == 1
    assert out[0]["author_name"] == "Vera Note"
    # The id stays: it is what the delete permission check compares.
    assert out[0]["author_id"] == author.id


async def test_creating_a_note_answers_with_the_name(db):
    author = await _staff(db, "author-create@test.local", name="Nils Writer")
    ev = await make_event(db, name="Create Event")
    await db.flush()

    out = await create_note(
        data=NoteCreate(
            notable_type="event", notable_id=ev.id,
            content="just written", is_published=True,
        ),
        db=db, current_user=author,
    )

    assert out["author_name"] == "Nils Writer"


async def test_one_query_serves_several_authors(db):
    """The names are resolved in one query for the whole list, not one per
    note. Two authors and three notes is the shape that would expose a
    lookup keyed wrongly."""
    a = await _staff(db, "author-multi-a@test.local", name="Ada")
    b = await _staff(db, "author-multi-b@test.local", name="Bruno")
    ev = await make_event(db, name="Multi Event")
    await _note(db, "event", ev.id, a, "first")
    await _note(db, "event", ev.id, b, "second")
    await _note(db, "event", ev.id, a, "third")
    await db.flush()

    out = await list_notes(
        notable_type="event", notable_id=ev.id, db=db, current_user=a)

    by_content = {n["content"]: n["author_name"] for n in out}
    assert by_content == {"first": "Ada", "second": "Bruno", "third": "Ada"}


# ─── the author who is gone ───────────────────────────────────────────

async def test_a_deleted_authors_note_carries_no_name_and_does_not_fail(db):
    """The v1.0.4zb case. `author_id` is NULL, so there is no name to give,
    and the endpoint must answer rather than raise. None, not "", so the
    screen can tell 'nobody' from 'somebody with a blank name' — it renders
    the removed-user wording for the first."""
    admin = await make_user(db, email="zc-deleter@test.local")
    author = await _staff(db, "author-going@test.local", name="Departing")
    ev = await make_event(db, name="Departed Event")
    kept = await _note(db, "event", ev.id, author, "still worth knowing")
    await db.flush()

    await delete_user(user_id=author.id, db=db, current_user=admin)
    # The FK's ON DELETE SET NULL fires in the DATABASE, so this session's
    # identity map still holds the row as it was loaded. A real request reads
    # the notes on a new session and sees the null; expiring is what makes
    # this test read the same thing rather than its own stale copy. Expunge
    # rather than expire: expiring would make the next attribute access do a
    # synchronous lazy refresh, which the async driver cannot do.
    db.expunge_all()

    out = await list_notes(
        notable_type="event", notable_id=ev.id, db=db, current_user=admin)

    assert len(out) == 1, "the published note survived its author"
    assert out[0]["content"] == "still worth knowing"
    assert out[0]["author_id"] is None
    assert out[0]["author_name"] is None, "None, not an empty string"


# ─── the export must not gain it ──────────────────────────────────────

async def test_the_participants_own_export_does_not_name_the_author(db):
    """§4.4. This export coarsens who did what on purpose, and its own
    metadata promises the reader so. A note's author must not arrive here
    just because it now travels elsewhere."""
    author = await _staff(db, "author-export@test.local", name="Should Not Appear")
    ev = await make_event(db, name="Export Event")
    p = await make_participant(db, ev.id, first_name="Alice")
    await _note(db, "participant", p.id, author, "a published note about Alice")
    await db.flush()

    payload = await export_participant_data(db, ev.id, p.id)

    assert len(payload["notes"]) == 1, "the note is in the export"
    note = payload["notes"][0]
    assert set(note) == {"content", "created_at", "updated_at"}, (
        "the export's note shape gained a field")
    # Belt and braces: the name must not appear anywhere in the whole export,
    # however it might have arrived.
    assert "Should Not Appear" not in str(payload)
    assert "author" not in str(note)


async def test_the_export_still_carries_the_note_itself(db):
    """The opposite failure: keeping the author out by dropping the note."""
    author = await _staff(db, "author-export2@test.local")
    ev = await make_event(db, name="Export Event 2")
    p = await make_participant(db, ev.id, first_name="Bob")
    await _note(db, "participant", p.id, author, "readable content")
    await db.flush()

    payload = await export_participant_data(db, ev.id, p.id)

    assert payload["notes"][0]["content"] == "readable content"
