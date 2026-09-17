"""v1.0.4r — the group-code and grouping-request limits are retired.

Two columns held limits that nothing in the product could set.

`participants.group_code_categories` limited one person's group code to
particular group types. The engine enforced it and nothing else did: no
screen in any of the six languages could see or set it, no CSV column
carried it, and no release announced it. The only way in was a hand-made
API call, and the most open of those was the unauthenticated public
registration endpoint, which did no validation at all.

`participant_preference_requests.category_scope` was the same idea for a
grouping request, and was enforced by nothing whatsoever.

Both are switched off here, at every point a user, a screen or an API
client could reach them. The columns and their stored values stay for one
release so that a rollback still finds what it expects, which is why
several of these tests write a stored value directly and then prove it has
no effect.

Endpoint functions are called directly with an explicit db and user, the
way tests/test_v1_0_4k_exclusion_api_surface.py does; the Depends wiring is
not what these assertions are about.
"""

import pytest
from sqlalchemy import select

from app.api.participants import (
    GroupCodeUpdate,
    ParticipantRegister,
    ParticipantResponse,
    ParticipantUpdate,
    patch_participant,
    public_register,
    reassign_group_code,
)
from app.api.preferences import list_preference_requests
from app.models.participant import Participant
from app.models.preference_request import ParticipantPreferenceRequest
from app.services.engine_service import run_engine

from tests.conftest import (
    make_category,
    make_event,
    make_participant,
    make_unit,
    make_user,
)

pytestmark = pytest.mark.asyncio

# An id no group type will ever have, standing in for the live case the
# addendum to v1.0.4p described: a group type was deleted and its id was
# left behind in this column.
DEAD_ID = "00000000-0000-4000-8000-00000000dead"


class _Request:
    """The request-bound values `public_register` reads on its way to
    building an email link. No email is sent: SMTP is not configured in the
    test container, so the sender logs a skip and returns."""

    headers: dict[str, str] = {}
    base_url = "http://test.local/"


async def _event_with_two_group_types(db):
    """Two group types, each with two roomy units, and two people sharing a
    group code. `use_group_codes` is on by default in both.

    Two sharers is the minimum: PASS 1 of the engine drops a cluster of one
    on purpose, so a single person would prove nothing.
    """
    ev = await make_event(db, name="Two Group Types")
    cats = {}
    for name in ("Alpha", "Beta"):
        cats[name] = await make_category(db, ev.id, name=name)
        await make_unit(db, cats[name].id, f"{name} 1", capacity=10)
        await make_unit(db, cats[name].id, f"{name} 2", capacity=10)
    people = [
        await make_participant(db, ev.id, first_name=first, email=email,
                               group_code="SMITH-100")
        for first, email in (("Ola", "ola@test.local"), ("Pia", "pia@test.local"))
    ]
    return {"event": ev, "cats": cats, "people": people}


async def _group_code_applies_in(db, event_id, category_id) -> bool:
    """Does the group code keep its members together in this group type?

    Asked of the real reader: PASS 1 of the engine, reached through
    `run_engine`. A member placed as part of a code cluster carries a
    placement reason of `group_code` (or `group_code_split`).
    """
    proposal = await run_engine(db, event_id, category_id, mode="replace")
    assert "error_key" not in proposal, proposal
    return any(
        str(r.get("reason", "")).startswith("group_code")
        for r in proposal.get("placement_reasons", {}).values()
    )


# ─── 1. The engine ignores the limit ──────────────────────────────────

@pytest.mark.parametrize(
    "stored,description",
    [
        (None, "no limit at all"),
        ("ALPHA", "a limit naming only Alpha"),
        ([DEAD_ID], "a limit naming only ids that resolve to nothing"),
    ],
    ids=["no_limit", "alpha_only", "only_unresolvable_ids"],
)
async def test_1_engine_ignores_a_stored_group_code_limit(db, stored, description):
    src = await _event_with_two_group_types(db)
    if stored == "ALPHA":
        stored = [str(src["cats"]["Alpha"].id)]
    if stored is not None:
        for p in src["people"]:
            p.group_code_categories = list(stored)
        await db.flush()

    # The code applies in BOTH group types, whatever the stored value says.
    # Before v1.0.4r, "alpha_only" applied in Alpha alone, and
    # "only_unresolvable_ids" applied nowhere.
    for name in ("Alpha", "Beta"):
        assert await _group_code_applies_in(
            db, src["event"].id, src["cats"][name].id
        ), f"with {description}, the group code should still apply in {name}"


# ─── 2. Public registration ───────────────────────────────────────────

async def test_2_public_registration_stores_no_limit(db):
    ev = await make_event(db, name="Registration Source")
    cat = await make_category(db, ev.id, name="Alpha")

    # The schemas set no `extra`, so Pydantic v2's default applies and an
    # unknown key is IGNORED rather than rejected. It goes through
    # model_validate, the way a request body does; passing it as a keyword
    # argument would raise instead. The address is an example.com one because
    # `EmailStr` rejects the `.local` domain the ORM fixtures use.
    payload = ParticipantRegister.model_validate({
        "first_name": "Quinn", "last_name": "Rivera",
        "email": "quinn@example.com", "gdpr_consent": True,
        "group_code": "RIVERA",
        "group_code_categories": [str(cat.id)],
    })
    assert not hasattr(payload, "group_code_categories"), (
        "the field has left the schema, so the key is dropped on the way in"
    )

    returned = await public_register(
        request=_Request(), event_id=ev.id, data=payload, db=db)

    stored = (await db.execute(
        select(Participant).where(Participant.email == "quinn@example.com")
    )).scalar_one()
    # Nothing is stored. The value is the JSON `null` literal rather than
    # SQL NULL, because the column is JSONB without none_as_null; both read
    # back as None.
    assert stored.group_code_categories is None
    assert stored.group_code, "the group code itself still works"

    # And nothing comes back out. The endpoint returns the ORM object and
    # FastAPI serialises it through this schema, so the schema is the
    # response contract.
    assert "group_code_categories" not in ParticipantResponse.model_fields
    assert "group_code_categories" not in (
        ParticipantResponse.model_validate(returned).model_dump())


# ─── 3. Participant update ────────────────────────────────────────────

async def test_3_patch_carrying_a_limit_leaves_the_stored_value_alone(db):
    ev = await make_event(db, name="Patch Source")
    cat = await make_category(db, ev.id, name="Alpha")
    user = await make_user(db, email="patcher@test.local")
    person = await make_participant(
        db, ev.id, first_name="Rae", email="rae@test.local",
        # A value only a hand-made API call could have set before v1.0.4r.
        group_code_categories=[str(cat.id)],
    )

    data = ParticipantUpdate.model_validate({
        "group_code": "RAE-100",
        "group_code_categories": [DEAD_ID],
    })
    assert not hasattr(data, "group_code_categories")

    await patch_participant(participant_id=person.id, data=data, db=db,
                            current_user=user)

    await db.refresh(person)
    assert person.group_code == "RAE-100", "the rest of the update still works"
    assert person.group_code_categories == [str(cat.id)], (
        "the stored limit is neither changed nor wiped"
    )


# ─── 4. Group-code reassignment ───────────────────────────────────────

async def test_4_reassigning_a_code_neither_sets_nor_wipes_a_limit(db):
    ev = await make_event(db, name="Reassign Source")
    cat = await make_category(db, ev.id, name="Alpha")
    user = await make_user(db, email="reassigner@test.local")
    person = await make_participant(
        db, ev.id, first_name="Sam", email="sam@test.local",
        group_code="OLD-100", group_code_categories=[str(cat.id)],
    )

    data = GroupCodeUpdate.model_validate({
        "group_code": "NEW-200",
        "group_code_categories": [DEAD_ID],
    })
    assert not hasattr(data, "group_code_categories")

    await reassign_group_code(participant_id=person.id, data=data, db=db,
                              current_user=user)

    await db.refresh(person)
    assert person.group_code == "NEW-200"
    # Before v1.0.4r this call WIPED the stored limit, because the service
    # took it as a parameter that defaulted to None and assigned it
    # unconditionally. No caller ever sent it.
    assert person.group_code_categories == [str(cat.id)]


# ─── 5. Grouping-request scope ────────────────────────────────────────

async def test_5_a_registration_scope_is_not_read(db):
    ev = await make_event(db, name="Scope Source")
    cat = await make_category(db, ev.id, name="Alpha")

    payload = ParticipantRegister.model_validate({
        "first_name": "Tess", "last_name": "Uhl", "email": "tess@example.com",
        "gdpr_consent": True,
        "preference_requests": [{
            "preferred_name": "Somebody Else",
            "category_scope": [str(cat.id)],
        }],
    })
    # There is no typed schema for a preference: the field is a list of
    # untyped dicts, so unlike the cases above the key survives validation.
    # It is simply never read.
    assert payload.preference_requests[0]["category_scope"] == [str(cat.id)]

    await public_register(request=_Request(), event_id=ev.id, data=payload, db=db)

    request = (await db.execute(
        select(ParticipantPreferenceRequest)
        .where(ParticipantPreferenceRequest.event_id == ev.id)
    )).scalar_one()
    assert request.preferred_name == "Somebody Else", "the request itself is saved"
    assert request.category_scope == "all", "the model default, not the payload"


# ─── 6. Neither key comes back in a response ──────────────────────────

async def test_6_responses_carry_neither_key(db):
    src = await _event_with_two_group_types(db)
    user = await make_user(db, email="reader@test.local")
    person = src["people"][0]
    person.group_code_categories = [DEAD_ID]
    db.add(ParticipantPreferenceRequest(
        event_id=src["event"].id, participant_id=person.id,
        preferred_name="Somebody", category_scope=[DEAD_ID],
    ))
    await db.flush()

    # The participant response shape.
    returned = await patch_participant(
        participant_id=person.id,
        data=ParticipantUpdate.model_validate({"group_code": "OLA-100"}),
        db=db, current_user=user)
    assert "group_code_categories" not in ParticipantResponse.model_fields
    assert "group_code_categories" not in (
        ParticipantResponse.model_validate(returned).model_dump())

    # The preference-request list, which is built by hand rather than by a
    # schema, so the response itself is checked.
    rows = await list_preference_requests(
        event_id=src["event"].id, db=db, current_user=user)
    assert len(rows) == 1, "the fixture added one request"
    assert "category_scope" not in rows[0]

    # Both stored values are still there, untouched, until step 2 drops the
    # columns.
    await db.refresh(person)
    assert person.group_code_categories == [DEAD_ID]
