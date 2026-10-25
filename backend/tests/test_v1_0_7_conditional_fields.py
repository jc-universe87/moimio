"""v1.0.7 — conditional registration fields, info texts and text formats.

A custom field may be shown only when its conditions hold ("Teamer" is Yes,
the person is under 18 on the event's start date, the phone is empty …),
all of them or any one. An `info` field is the organiser's text; when it has
a rule, the people it applied to carry an "applies" mark that check-in and
People can show. A text field may require a phone number, an email address
or digits only.

  1-9    the rule itself, every kind of source
  10-15  public registration: hidden answers dropped, marks, formats
  16-18  People edits: a changed built-in field moves the mark
  19-26  saving rules and order: the API refuses what cannot stand
  27-28  start date moves, type changes
  29-32  CSV import and template
  33-36  copy, form export/import, People CSV export
"""

import csv
import io
import uuid
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.main import app as fastapi_app
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.participant import Participant
from app.schemas.event import CopyOptions
from app.services.field_conditions import age_on, evaluate, fits_format
from tests.conftest import make_event, make_user

pytestmark = pytest.mark.asyncio

UNDER_18 = "2008-06-02"   # 17 on the fixture event's start, 2026-06-01
TURNS_18 = "2008-06-01"   # 18 on that very day
START = date(2026, 6, 1)


# ─── helpers ──────────────────────────────────────────────────────────

def C(source, op, value=None):
    c = {"source": str(source), "op": op}
    if value is not None:
        c["value"] = value
    return c


def R(*conditions, match="all"):
    return {"match": match, "conditions": list(conditions)}


def _cf(event, label, field_type, order, **kw):
    return CustomFieldDefinition(
        id=uuid.uuid4(), event_id=event.id, label=label, field_type=field_type,
        sort_order=order, **kw,
    )


async def _teamer_event(db):
    """Teamer (yes/no) → Which team (text, required); a consent note for
    under-18s; a role dropdown → Kitchen shift; a phone-format text field."""
    ev = await make_event(db, name="Camp")
    teamer = _cf(ev, "Teamer", "boolean", 0)
    team = _cf(ev, "Which team", "text", 1, is_required=True,
               show_if=R(C(teamer.id, "one_of", ["true"])))
    note = _cf(ev, "Parental consent", "info", 2,
               options={"text": "Bring the signed form."},
               show_if=R(C("date_of_birth", "age_under", 18)))
    welcome = _cf(ev, "Welcome", "info", 3, options={"text": "Hello"})
    role = _cf(ev, "Role", "select", 4, options={"choices": ["Cook", "Driver", "Other"]})
    shift = _cf(ev, "Kitchen shift", "text", 5, show_if=R(C(role.id, "one_of", ["Cook"])))
    emergency = _cf(ev, "Emergency number", "text", 6, options={"format": "phone"})
    db.add_all([teamer, team, note, welcome, role, shift, emergency])
    await db.flush()
    return ev, dict(teamer=teamer, team=team, note=note, welcome=welcome, role=role,
                    shift=shift, emergency=emergency)


def _shown(defs, answers=None, **person):
    kept, applied = evaluate(defs, answers or {}, person, START)
    return set(kept) | applied


async def _client():
    return AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test")


async def _admin_headers(db):
    user = await make_user(db, email=f"a-{uuid.uuid4().hex[:6]}@test.local")
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role.value)}"}


async def _post_register(event_id, **body):
    payload = {"first_name": "Ana", "last_name": "Test",
               "email": f"{uuid.uuid4().hex[:8]}@example.com", "gdpr_consent": True, **body}
    async with await _client() as ac:
        return await ac.post(f"/api/events/{event_id}/register", json=payload)


async def _register(event_id, **body):
    r = await _post_register(event_id, **body)
    assert r.status_code == 201, r.text
    return r.json()


async def _values(db, participant_id) -> dict[str, str]:
    rows = (await db.execute(
        select(CustomFieldValue).where(CustomFieldValue.participant_id == uuid.UUID(str(participant_id)))
    )).scalars().all()
    return {str(r.field_id): r.value for r in rows}


# ─── 1-9: the rule ────────────────────────────────────────────────────

async def test_1_age_is_counted_on_the_day():
    assert age_on(date(2008, 6, 1), START) == 18
    assert age_on(date(2008, 6, 2), START) == 17
    assert age_on(date(2008, 2, 29), date(2026, 2, 28)) == 17


async def test_2_age_under_at_least_and_exactly(db):
    ev = await make_event(db)
    f = {op: _cf(ev, op, "info", i, options={"text": "x"}, show_if=R(C("date_of_birth", op, 18)))
         for i, op in enumerate(("age_under", "age_at_least", "age_exactly"))}
    defs = list(f.values())
    ids = {op: str(d.id) for op, d in f.items()}
    assert _shown(defs, date_of_birth=UNDER_18) == {ids["age_under"]}
    assert _shown(defs, date_of_birth=TURNS_18) == {ids["age_at_least"], ids["age_exactly"]}
    assert _shown(defs, date_of_birth="1990-01-01") == {ids["age_at_least"]}
    assert _shown(defs) == set(), "no date of birth meets no age condition"


async def test_3_yes_no_rule_accepts_the_import_spellings(db):
    ev, f = await _teamer_event(db)
    defs = list(f.values())
    team = str(f["team"].id)
    for raw in ("true", "yes", "1"):
        assert team in _shown(defs, {str(f["teamer"].id): raw, team: "Kitchen"}), raw
    assert team not in _shown(defs, {str(f["teamer"].id): "false", team: "Kitchen"})


async def test_4_dropdown_one_of_and_not_one_of(db):
    ev = await make_event(db)
    role = _cf(ev, "Role", "select", 0, options={"choices": ["Cook", "Driver"]})
    cook = _cf(ev, "Cook", "text", 1, show_if=R(C(role.id, "one_of", ["Cook"])))
    other = _cf(ev, "Not cook", "text", 2, show_if=R(C(role.id, "not_one_of", ["Cook"])))
    defs = [role, cook, other]
    ans = lambda v: {str(role.id): v, str(cook.id): "a", str(other.id): "b"}  # noqa: E731
    assert str(cook.id) in _shown(defs, ans("Cook")) and str(other.id) not in _shown(defs, ans("Cook"))
    assert str(other.id) in _shown(defs, ans("Driver"))
    # Not answered yet: "is not one of" does not open the field early.
    assert str(other.id) not in _shown(defs, {str(other.id): "b"})


async def test_5_text_ignores_capitals_and_spacing(db):
    ev = await make_event(db)
    f = {op: _cf(ev, op, "info", i, options={"text": "x"}, show_if=R(C("country", op, "Deutschland")))
         for i, op in enumerate(("equals", "contains", "not_contains"))}
    ids = {op: str(d.id) for op, d in f.items()}
    defs = list(f.values())
    assert _shown(defs, country="  deutschland ") == {ids["equals"], ids["contains"]}
    assert _shown(defs, country="Süddeutschland") == {ids["contains"]}
    assert _shown(defs, country="Österreich") == {ids["not_contains"]}
    assert _shown(defs, country="") == set(), "an empty answer matches only 'is empty'"


async def test_6_is_empty_and_is_filled_work_on_any_source(db):
    ev = await make_event(db)
    teamer = _cf(ev, "Teamer", "boolean", 0)
    no_phone = _cf(ev, "Other contact", "text", 1, show_if=R(C("phone", "is_empty")))
    answered = _cf(ev, "Thanks", "info", 2, options={"text": "x"}, show_if=R(C(teamer.id, "is_filled")))
    defs = [teamer, no_phone, answered]
    assert str(no_phone.id) in _shown(defs, {str(no_phone.id): "mum"}, phone="  ")
    assert str(no_phone.id) in _shown(defs, {str(no_phone.id): "mum"}, phone=None)
    assert str(no_phone.id) not in _shown(defs, {str(no_phone.id): "mum"}, phone="0171 234567")
    assert str(answered.id) in _shown(defs, {str(teamer.id): "false"})
    assert str(answered.id) not in _shown(defs, {})


async def test_7_numbers_dates_and_gender(db):
    ev = await make_event(db)
    kids = _cf(ev, "Children", "number", 0)
    ages = _cf(ev, "Ages", "text", 1, show_if=R(C(kids.id, "gt", 0)))
    arrive = _cf(ev, "Arrival", "date", 2)
    early = _cf(ev, "Early bed", "info", 3, options={"text": "x"}, show_if=R(C(arrive.id, "before", "2026-06-01")))
    women = _cf(ev, "Women's room", "info", 4, options={"text": "x"}, show_if=R(C("gender", "one_of", ["female"])))
    defs = [kids, ages, arrive, early, women]
    shown = _shown(defs, {str(kids.id): "2", str(ages.id): "3, 5", str(arrive.id): "2026-05-31"}, gender="female")
    assert {str(ages.id), str(early.id), str(women.id)} <= shown
    shown = _shown(defs, {str(kids.id): "0", str(ages.id): "x", str(arrive.id): "2026-06-01"}, gender="male")
    assert not {str(ages.id), str(early.id), str(women.id)} & shown


async def test_8_all_versus_any(db):
    ev = await make_event(db)
    teamer = _cf(ev, "Teamer", "boolean", 0)
    both = _cf(ev, "Both", "info", 1, options={"text": "x"}, show_if=R(
        C(teamer.id, "one_of", ["true"]), C("date_of_birth", "age_under", 18)))
    either = _cf(ev, "Either", "info", 2, options={"text": "x"}, show_if=R(
        C(teamer.id, "one_of", ["true"]), C("date_of_birth", "age_under", 18), match="any"))
    defs = [teamer, both, either]
    yes = {str(teamer.id): "true"}
    assert _shown(defs, yes, date_of_birth=UNDER_18) >= {str(both.id), str(either.id)}
    shown = _shown(defs, yes, date_of_birth="1990-01-01")
    assert str(either.id) in shown and str(both.id) not in shown
    assert not {str(both.id), str(either.id)} & _shown(defs, {str(teamer.id): "false"}, date_of_birth="1990-01-01")


async def test_9_a_field_behind_a_hidden_field_is_hidden_too(db):
    ev = await make_event(db)
    a = _cf(ev, "A", "boolean", 0)
    b = _cf(ev, "B", "select", 1, options={"choices": ["x", "y"]}, show_if=R(C(a.id, "one_of", ["true"])))
    c = _cf(ev, "C", "text", 2, show_if=R(C(b.id, "one_of", ["x"])))
    # A is No, so B was never shown; a stale B answer must not open C.
    kept, _ = evaluate([a, b, c], {str(a.id): "false", str(b.id): "x", str(c.id): "c"}, {}, START)
    assert kept == {str(a.id): "false"}


async def test_9b_formats_are_loose_but_not_blind():
    assert fits_format("phone", "+49 (0)171 / 234-567")
    assert not fits_format("phone", "call me")
    assert not fits_format("phone", "12345")
    assert fits_format("email", "a@b.de") and not fits_format("email", "a@b")
    assert fits_format("digits", "00123") and not fits_format("digits", "12a")
    assert fits_format("phone", "") and fits_format(None, "anything")


# ─── 10-15: public registration ───────────────────────────────────────

async def test_10_an_answer_to_a_hidden_field_is_not_stored(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(f["teamer"].id): "false", str(f["team"].id): "Kitchen"})
    assert await _values(db, p["id"]) == {str(f["teamer"].id): "false"}


async def test_11_under_18_on_the_start_date_gets_the_mark(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    minor = await _register(ev.id, date_of_birth=UNDER_18)
    adult = await _register(ev.id, date_of_birth=TURNS_18)
    nodob = await _register(ev.id)
    assert (await _values(db, minor["id"])).get(str(f["note"].id)) == "true"
    assert str(f["note"].id) not in await _values(db, adult["id"])
    assert str(f["note"].id) not in await _values(db, nodob["id"])
    assert minor["custom_fields"].get(str(f["note"].id)) == "true"


async def test_12_an_info_text_without_a_rule_stores_nothing(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(f["welcome"].id): "typed anyway"})
    assert str(f["welcome"].id) not in await _values(db, p["id"])


async def test_13_a_field_of_another_event_is_not_stored(db):
    ev, f = await _teamer_event(db)
    other, g = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(g["teamer"].id): "true"})
    assert await _values(db, p["id"]) == {}


async def test_14_a_bad_phone_is_refused_and_named(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    r = await _post_register(ev.id, phone="ring me")
    assert r.status_code == 422
    assert r.json()["detail"]["fields"] == {"phone": "errors.field.phone"}
    r = await _post_register(ev.id, custom_fields={str(f["emergency"].id): "mum"})
    assert r.json()["detail"]["fields"] == {f"cf_{f['emergency'].id}": "errors.field.phone"}
    assert (await _post_register(ev.id, phone="+49 171 2345678")).status_code == 201


async def test_15_a_hidden_fields_bad_answer_never_blocks(db):
    ev = await make_event(db)
    teamer = _cf(ev, "Teamer", "boolean", 0)
    mail = _cf(ev, "Team email", "text", 1, options={"format": "email"},
               show_if=R(C(teamer.id, "one_of", ["true"])))
    db.add_all([teamer, mail])
    await db.commit()
    p = await _register(ev.id, custom_fields={str(teamer.id): "false", str(mail.id): "not an email"})
    assert await _values(db, p["id"]) == {str(teamer.id): "false"}


# ─── 16-18: People edits ──────────────────────────────────────────────

async def test_16_editing_a_built_in_field_moves_the_mark(db):
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    p = await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.patch(f"/api/participants/{p['id']}", json={"date_of_birth": "1990-01-01"}, headers=headers)
        assert r.status_code == 200, r.text
        assert str(f["note"].id) not in r.json()["custom_fields"]
        r = await ac.patch(f"/api/participants/{p['id']}", json={"date_of_birth": UNDER_18}, headers=headers)
        assert r.json()["custom_fields"].get(str(f["note"].id)) == "true"


async def test_17_a_mark_cannot_be_typed_in(db):
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    p = await _register(ev.id, date_of_birth="1990-01-01")
    async with await _client() as ac:
        r = await ac.patch(f"/api/participants/{p['id']}",
                           json={"custom_fields": {str(f["note"].id): "true"}}, headers=headers)
    assert r.status_code == 200
    assert str(f["note"].id) not in await _values(db, p["id"])


async def test_18_an_organisers_answer_is_never_thrown_away(db):
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(f["teamer"].id): "false"})
    async with await _client() as ac:
        r = await ac.patch(f"/api/participants/{p['id']}",
                           json={"custom_fields": {str(f["team"].id): "Kitchen"}}, headers=headers)
    assert r.json()["custom_fields"][str(f["team"].id)] == "Kitchen"


# ─── 19-26: saving rules and order ────────────────────────────────────

async def _api(db):
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    return ev, f, headers, f"/api/events/{ev.id}/custom-fields"


async def test_19_a_new_field_goes_to_the_end(db):
    ev, f, headers, base = await _api(db)
    async with await _client() as ac:
        r = await ac.post(f"{base}/", json={"label": "Allergies", "field_type": "text"}, headers=headers)
        assert r.status_code == 201, r.text
        listed = (await ac.get(f"{base}/", headers=headers)).json()
    assert listed[-1]["label"] == "Allergies"


async def test_20_rules_that_cannot_stand_are_refused(db):
    ev, f, headers, base = await _api(db)
    invalid = "errors.custom_fields.condition_invalid"
    cases = [
        (R(C(f["team"].id, "one_of", ["x"])), invalid),               # text source, dropdown op
        (R(C(f["role"].id, "one_of", ["Pilot"])), "errors.custom_fields.condition_option_in_use"),
        (R(C("date_of_birth", "age_under", 0)), invalid),
        (R(C("gender", "one_of", ["other"])), invalid),
        (R(C(uuid.uuid4(), "one_of", ["true"])), invalid),
        (R(C(f["teamer"].id, "one_of", [])), invalid),
        (R(C(f["note"].id, "is_filled")), invalid),                    # info is no source
        (R(C(f["team"].id, "gt", "abc")), invalid),
        (R(C("phone", "contains", "")), invalid),
        ({"match": "some", "conditions": [C("phone", "is_empty")]}, invalid),
        (R(), invalid),
    ]
    async with await _client() as ac:
        for rule, key in cases:
            r = await ac.post(f"{base}/", json={"label": f"X{uuid.uuid4().hex[:4]}", "field_type": "text",
                                                "show_if": rule}, headers=headers)
            assert r.status_code == 409, (rule, r.text)
            assert r.json()["detail"]["key"] == key, rule
        # A rule may not point at a field further down.
        r = await ac.patch(f"{base}/{f['teamer'].id}",
                           json={"show_if": R(C(f["role"].id, "one_of", ["Cook"]))}, headers=headers)
        assert r.status_code == 409
        assert r.json()["detail"]["key"] == "errors.custom_fields.condition_order"
        listed = (await ac.get(f"{base}/", headers=headers)).json()
    assert {c["label"] for c in listed} == {c.label for c in f.values()}, "nothing refused was saved"
    assert next(c for c in listed if c["label"] == "Teamer")["show_if"] is None


async def test_21_a_rule_is_saved_normalised(db):
    ev, f, headers, base = await _api(db)
    rule = R(C("phone", "contains", "  +49 "), C("date_of_birth", "age_at_least", 16),
             C(f["role"].id, "not_one_of", ["Cook", "Cook"]), match="any")
    async with await _client() as ac:
        r = await ac.post(f"{base}/", json={"label": "Y", "field_type": "text", "show_if": rule}, headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["show_if"] == R(C("phone", "contains", "+49"), C("date_of_birth", "age_at_least", 16),
                                    C(f["role"].id, "not_one_of", ["Cook"]), match="any")


async def test_22_reorder_saves_and_refuses_a_move_above_a_source(db):
    ev, f, headers, base = await _api(db)
    ids = [str(f[k].id) for k in ("teamer", "team", "note", "welcome", "role", "shift", "emergency")]
    async with await _client() as ac:
        r = await ac.post(f"{base}/reorder", json={"field_ids": [ids[1], ids[0]] + ids[2:]}, headers=headers)
        assert r.status_code == 409
        assert r.json()["detail"]["key"] == "errors.custom_fields.condition_order"
        good = [ids[4], ids[5], ids[0], ids[1], ids[2], ids[3], ids[6]]
        r = await ac.post(f"{base}/reorder", json={"field_ids": good}, headers=headers)
        assert r.status_code == 200, r.text
        listed = (await ac.get(f"{base}/", headers=headers)).json()
        assert [c["id"] for c in listed] == good
        r = await ac.post(f"{base}/reorder", json={"field_ids": good[:-1]}, headers=headers)
        assert r.status_code == 422


async def test_23_a_field_with_dependants_cannot_be_deleted(db):
    ev, f, headers, base = await _api(db)
    async with await _client() as ac:
        r = await ac.delete(f"{base}/{f['teamer'].id}", headers=headers)
        assert r.status_code == 409
        assert r.json()["detail"]["key"] == "errors.custom_fields.has_dependants"
        assert (await ac.delete(f"{base}/{f['team'].id}", headers=headers)).status_code == 204
        assert (await ac.delete(f"{base}/{f['teamer'].id}", headers=headers)).status_code == 204


async def test_24_an_answered_field_and_an_info_text_with_marks_can_be_deleted(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth=UNDER_18, custom_fields={str(f["emergency"].id): "0171 234567"})
    async with await _client() as ac:
        assert (await ac.delete(f"{base}/{f['note'].id}", headers=headers)).status_code == 204
        assert (await ac.delete(f"{base}/{f['emergency'].id}", headers=headers)).status_code == 204
    assert await _values(db, p["id"]) == {}


async def test_25_info_text_and_text_format_are_kept_in_options(db):
    ev, f, headers, base = await _api(db)
    async with await _client() as ac:
        r = await ac.post(f"{base}/", json={"label": "Note", "field_type": "info", "is_required": True,
                                            "info_text": "See [the form](https://example.org/a.pdf)"},
                          headers=headers)
        body = r.json()
        assert body["is_required"] is False
        assert body["options"] == {"text": "See [the form](https://example.org/a.pdf)"}
        r = await ac.patch(f"{base}/{body['id']}", json={"label": "Note 2"}, headers=headers)
        assert r.json()["options"]["text"].startswith("See")

        r = await ac.post(f"{base}/", json={"label": "Member no.", "field_type": "text", "text_format": "digits"},
                          headers=headers)
        assert r.json()["options"] == {"format": "digits"}
        fid = r.json()["id"]
        r = await ac.patch(f"{base}/{fid}", json={"label": "Member number"}, headers=headers)
        assert r.json()["options"] == {"format": "digits"}, "leaving text_format out keeps it"
        r = await ac.patch(f"{base}/{fid}", json={"text_format": None}, headers=headers)
        assert r.json()["options"] is None
        r = await ac.post(f"{base}/", json={"label": "Z", "field_type": "text", "text_format": "postcode"},
                          headers=headers)
        assert r.status_code == 422


async def test_26_changing_a_rule_recomputes_the_marks(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth="2012-01-01")   # 14
    assert (await _values(db, p["id"])).get(str(f["note"].id)) == "true"
    async with await _client() as ac:
        r = await ac.patch(f"{base}/{f['note'].id}",
                           json={"show_if": R(C("date_of_birth", "age_under", 14))}, headers=headers)
        assert r.status_code == 200
    assert str(f["note"].id) not in await _values(db, p["id"])


# ─── 27-28: start date, type change ───────────────────────────────────

async def test_27_moving_the_start_date_moves_the_marks(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.patch(f"/api/events/{ev.id}", json={"start_date": "2026-06-05"}, headers=headers)
        assert r.status_code == 200, r.text
    assert str(f["note"].id) not in await _values(db, p["id"])


async def test_28_an_info_text_turned_into_a_question_loses_its_marks(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.patch(f"{base}/{f['note'].id}", json={"field_type": "text"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["options"] is None
    assert str(f["note"].id) not in await _values(db, p["id"])


# ─── 29-32: CSV import ────────────────────────────────────────────────

def _csv(rows: list[dict]) -> bytes:
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return out.getvalue().encode()


async def test_29_import_asks_for_a_required_answer_only_when_it_applies(db):
    from app.services.batch_register_service import parse_csv
    ev, f = await _teamer_event(db)
    base = {"first_name": "A", "last_name": "B", "gdpr_consent": "true"}
    content = _csv([
        {**base, "email": "no@x.org", "Teamer": "no", "Which team": ""},
        {**base, "email": "yes@x.org", "Teamer": "yes", "Which team": ""},
    ])
    no_row, yes_row = (await parse_csv(content, ev.id, db))["rows"]
    assert no_row["valid"], no_row["errors"]
    assert "missing_required_custom:Which team" in yes_row["errors"]


async def test_30_import_checks_a_text_format(db):
    from app.services.batch_register_service import parse_csv
    ev, f = await _teamer_event(db)
    content = _csv([{"first_name": "A", "last_name": "B", "email": "a@x.org", "gdpr_consent": "true",
                     "Emergency number": "ask mum"}])
    row = (await parse_csv(content, ev.id, db))["rows"][0]
    assert "invalid_format:Emergency number" in row["errors"]


async def test_31_an_info_column_is_ignored_not_turned_into_a_new_field(db):
    from app.services.batch_register_service import parse_csv
    ev, f = await _teamer_event(db)
    content = _csv([{"first_name": "A", "last_name": "B", "email": "a@x.org", "gdpr_consent": "true",
                     "Parental consent": "true", "Date of Birth": "02.06.2008"}])
    result = await parse_csv(content, ev.id, db)
    assert result["new_custom_fields"] == []
    assert str(f["note"].id) not in result["rows"][0]["data"].get("custom_fields", {})


async def test_32_the_template_has_no_column_for_an_info_text(db):
    from app.services.batch_register_service import generate_template
    ev, f = await _teamer_event(db)
    header = generate_template(list(f.values())).lstrip("﻿").splitlines()[0]
    assert f"cf:{f['note'].id}" not in header
    assert f"cf:{f['welcome'].id}" not in header
    assert f"cf:{f['team'].id}" in header


# ─── 33-36: copy, form file, CSV export ───────────────────────────────

async def test_33_copying_an_event_points_rules_at_the_copies(db):
    from app.services.event_service import duplicate_event_config
    ev, f = await _teamer_event(db)
    f["role"].show_in_form = False
    f["shift"].show_if = R(C(f["role"].id, "one_of", ["Cook"]), C("gender", "one_of", ["male"]), match="any")
    dest = await make_event(db, name="Copy")
    await duplicate_event_config(db, ev.id, dest.id, CopyOptions())
    await db.flush()
    copies = {c.label: c for c in (await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == dest.id)
    )).scalars().all()}
    assert copies["Which team"].show_if == R(C(copies["Teamer"].id, "one_of", ["true"]))
    assert copies["Parental consent"].show_if == R(C("date_of_birth", "age_under", 18))
    assert copies["Kitchen shift"].show_if == R(C(copies["Role"].id, "one_of", ["Cook"]),
                                                C("gender", "one_of", ["male"]), match="any")
    assert copies["Role"].show_in_form is False
    assert copies["Emergency number"].options == {"format": "phone"}


async def test_34_form_file_carries_rules_by_label(db):
    from app.services.registration_form_io import export_registration_form, import_registration_form
    ev, f = await _teamer_event(db)
    payload = await export_registration_form(db, ev.id)
    team = next(c for c in payload["custom_fields"] if c["label"] == "Which team")
    assert team["show_if"] == {"match": "all", "conditions": [
        {"source_label": "Teamer", "op": "one_of", "value": ["true"]}]}

    dest = await make_event(db, name="Dest")
    db.add(_cf(dest, "Already here", "text", 0))
    await db.flush()
    result = await import_registration_form(db, dest.id, payload)
    assert result["dropped_rules"] == 0
    got = {c.label: c for c in (await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == dest.id)
    )).scalars().all()}
    assert got["Which team"].show_if == R(C(got["Teamer"].id, "one_of", ["true"]))
    assert got["Parental consent"].show_if == R(C("date_of_birth", "age_under", 18))
    order = [c.label for c in sorted(got.values(), key=lambda c: c.sort_order)]
    assert order[0] == "Already here" and order.index("Teamer") < order.index("Which team")

    # A rule naming a field that is not in the file is dropped and counted.
    other = await make_event(db, name="Other")
    result = await import_registration_form(db, other.id, {"kind": payload["kind"], "custom_fields": [team]})
    assert result["dropped_rules"] == 1


async def test_35_people_csv_has_a_column_only_for_a_conditional_info_text(db):
    ev, f, headers, base = await _api(db)
    await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.get(f"/api/events/{ev.id}/export/participants.csv", headers=headers)
    assert r.status_code == 200, r.text
    header = next(csv.reader(io.StringIO(r.text.lstrip("﻿"))))
    assert "Parental consent" in header
    assert "Welcome" not in header


async def test_36_participant_still_comes_back_whole(db):
    ev = await make_event(db)
    await db.commit()
    p = await _register(ev.id)
    row = (await db.execute(select(Participant).where(Participant.id == uuid.UUID(p["id"])))).scalar_one()
    assert row.first_name == "Ana" and p["custom_fields"] == {}
