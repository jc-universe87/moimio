"""v1.0.4ze — the validation handler, and the roster's "Not allocated" page.

Two mechanisms this release needed in order for its wording to be true.

FORM-1. FastAPI answers its own validation failures with a LIST of
{loc, msg, type} dicts, in English, naming internal field paths. The public
registration form rendered that list under a correctly translated heading,
so a registrant who mistyped an address was shown the inside of the server.
A handler now turns it into the app's own {key, params} shape plus a
per-field map, so the form can mark the box rather than print a paragraph.

PDF-3. The roster lumped together somebody the organiser deliberately kept
out of a group type and somebody the engine could not place. Those are
different facts and want different answers on the day, so they are now two
labelled blocks on a page of their own — and the second is omitted when
nobody is unplaced, because an empty band saying nothing is worse than no
band.
"""

import io
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app as fastapi_app
from app.services.pdf_service import RENDERERS, _build_category_data

from tests.conftest import (
    make_category, make_event, make_participant, make_unit, make_user,
)

pytestmark = pytest.mark.asyncio


# ─── FORM-1: the validation handler ───────────────────────────────────

async def _post_registration(body: dict, event_id) -> tuple[int, dict]:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(f"/api/events/{event_id}/register", json=body)
    return r.status_code, r.json()


async def test_a_rejected_field_answers_in_the_apps_own_shape(db):
    """The whole point: no raw FastAPI body reaches a registrant. The
    response must carry a translatable key, not a list of dicts naming
    `body.email`."""
    ev = await make_event(db, name="Validation Event")
    await db.commit()

    status, body = await _post_registration(
        {"first_name": "Alice", "last_name": "Test",
         "email": "rest@gmail.com3242", "gdpr_consent": True},
        ev.id,
    )

    assert status == 422
    detail = body["detail"]
    assert isinstance(detail, dict), "the raw list reached the client"
    assert detail["key"] == "errors.validation.summary"


async def test_the_offending_field_is_named_with_a_key(db):
    """So the form can mark the box. A paragraph under the heading is what
    this release exists to stop."""
    ev = await make_event(db, name="Field Event")
    await db.commit()

    _, body = await _post_registration(
        {"first_name": "Alice", "last_name": "Test",
         "email": "not-an-address", "gdpr_consent": True},
        ev.id,
    )

    fields = body["detail"]["fields"]
    assert "email" in fields, f"email was not named: {fields}"
    assert fields["email"] == "errors.field.email"


async def test_a_missing_field_says_so_rather_than_invalid(db):
    """"Required" and "not valid" are different things to somebody filling
    in a form, and the mapping keeps them apart."""
    ev = await make_event(db, name="Missing Event")
    await db.commit()

    _, body = await _post_registration(
        {"last_name": "Test", "email": "alice@example.org",
         "gdpr_consent": True},
        ev.id,
    )

    fields = body["detail"]["fields"]
    assert any(v == "errors.field.required" for v in fields.values()), fields


async def test_no_internal_field_path_reaches_the_client(db):
    """The specific thing Johannes saw: `"loc":["body","email"]`."""
    ev = await make_event(db, name="No Paths Event")
    await db.commit()

    _, body = await _post_registration(
        {"first_name": "Alice", "email": "bad", "gdpr_consent": True}, ev.id)

    text = str(body)
    assert '"loc"' not in text and "'loc'" not in text
    assert "value_error" not in text
    assert "body" not in str(body["detail"].get("fields", {}).keys())


# ─── PDF-3: the "Not allocated" page ──────────────────────────────────

def page_count(raw: bytes) -> int:
    """How many pages the document has.

    NOT a text search: fpdf2 embeds a subsetted font with Identity-H
    encoding, so the content streams hold 2-byte glyph indices rather than
    characters, and any assertion over "the words in the PDF" is either
    impossible or accidentally true. The page tree's /Count is plain,
    and whether the page was drawn at all is the behaviour worth pinning.
    """
    import re
    counts = [int(m.group(1)) for m in re.finditer(rb"/Count\s+(\d+)", raw)]
    assert counts, "no page tree in the document"
    return max(counts)


async def _event_with(db, *, excluded=0, unplaced=0, placed=0):
    from app.models.allocation_category_exclusion import AllocationCategoryExclusion
    from app.models.allocation import Allocation

    ev = await make_event(db, name="Roster Event")
    cat = await make_category(db, ev.id, name="Rooms")
    unit = await make_unit(db, cat.id, name="Room A")
    for i in range(placed):
        p = await make_participant(db, ev.id, first_name=f"Placed{i}")
        db.add(Allocation(event_id=ev.id, unit_id=unit.id, participant_id=p.id))
    for i in range(excluded):
        p = await make_participant(db, ev.id, first_name=f"Excluded{i}")
        db.add(AllocationCategoryExclusion(
            allocation_category_id=cat.id, participant_id=p.id))
    for i in range(unplaced):
        await make_participant(db, ev.id, first_name=f"Unplaced{i}")
    await db.flush()
    return ev, cat


async def test_the_data_splits_excluded_from_unplaced(db):
    """The split is the substance; the two blocks are its presentation."""
    ev, cat = await _event_with(db, excluded=2, unplaced=3, placed=1)

    data = await _build_category_data(db, ev.id, cat.id)

    assert len(data["excluded"]) == 2
    assert len(data["unplaced"]) == 3
    # The combined list stays, and is still the sum of the two.
    assert len(data["unallocated"]) == 5


@pytest.mark.parametrize("renderer", ["compact", "detailed", "signin"])
async def test_all_three_renderers_draw_the_page(db, renderer):
    """Including the sign-in sheet, which never showed unallocated people at
    all: somebody who is not in a group still walks through the door."""
    ev, cat = await _event_with(db, excluded=2, unplaced=2, placed=1)
    data = await _build_category_data(db, ev.id, cat.id)
    with_page = RENDERERS[renderer](data, lang="en", exported_by="Tester")

    # The same document with nobody left over, as the control.
    data_clean = dict(data, excluded=[], unplaced=[], unallocated=[])
    without = RENDERERS[renderer](data_clean, lang="en", exported_by="Tester")

    assert page_count(bytes(with_page)) == page_count(bytes(without)) + 1, (
        "the Not allocated page was not added")


async def test_the_second_block_is_omitted_when_nobody_is_unplaced(db, monkeypatch):
    """An empty band saying nothing is worse than no band.

    Which blocks were drawn is recorded at the renderer rather than read
    back out of the PDF, for the reason `page_count` gives."""
    from app.services import pdf_service

    drawn = []
    real = pdf_service._render_unallocated_block
    monkeypatch.setattr(
        pdf_service, "_render_unallocated_block",
        lambda pdf, people, compact, label_key="unallocated.banner": (
            drawn.append((label_key, len(people))),
            real(pdf, people, compact, label_key),
        )[1],
    )

    ev, cat = await _event_with(db, excluded=2, unplaced=0, placed=1)
    data = await _build_category_data(db, ev.id, cat.id)
    assert data["unplaced"] == []
    RENDERERS["compact"](data, lang="en", exported_by="Tester")

    assert drawn == [("unallocated.excluded", 2)], (
        f"expected only the excluded block, got {drawn}")


async def test_both_blocks_are_drawn_when_both_have_people(db, monkeypatch):
    """The other half of the same decision."""
    from app.services import pdf_service

    drawn = []
    real = pdf_service._render_unallocated_block
    monkeypatch.setattr(
        pdf_service, "_render_unallocated_block",
        lambda pdf, people, compact, label_key="unallocated.banner": (
            drawn.append((label_key, len(people))),
            real(pdf, people, compact, label_key),
        )[1],
    )

    ev, cat = await _event_with(db, excluded=2, unplaced=3, placed=1)
    data = await _build_category_data(db, ev.id, cat.id)
    RENDERERS["compact"](data, lang="en", exported_by="Tester")

    assert drawn == [
        ("unallocated.excluded", 2),
        ("unallocated.unplaced", 3),
    ], f"got {drawn}"


async def test_the_page_is_omitted_when_everybody_is_placed(db):
    """The ordinary case for a finished allocation."""
    ev, cat = await _event_with(db, excluded=0, unplaced=0, placed=2)
    data = await _build_category_data(db, ev.id, cat.id)

    assert data["excluded"] == [] and data["unplaced"] == []
    out = RENDERERS["compact"](data, lang="en", exported_by="Tester")

    # Identical to a document rendered from data that never had the keys.
    bare = dict(data)
    bare.pop("excluded"); bare.pop("unplaced")
    assert page_count(bytes(out)) == page_count(
        bytes(RENDERERS["compact"](bare, lang="en", exported_by="Tester")))
