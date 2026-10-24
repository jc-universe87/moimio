"""v1.0.7 — conditional registration fields and info texts.

A custom field may be shown only when an earlier answer matches ("Teamer" is
Yes, or the person is under 18 on the event's start date). An `info` field is
the organiser's text; when it has a rule, the people it applied to carry an
"applies" mark that check-in and People can show.

  1-4    the rule itself: age, yes/no, select, chains
  5-9    public registration: hidden answers dropped, marks set, unknown ids
  10-12  People edits: a changed date of birth moves the mark, marks are
         never typed in, answers are never thrown away
  13-19  saving rules and order: the API refuses what cannot stand
  20-21  start date moves, type changes
  22-24  CSV import and template
  25-27  copy, form export/import, People CSV export
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
from app.services.field_conditions import age_on, evaluate
from tests.conftest import make_event, make_user

pytestmark = pytest.mark.asyncio

UNDER_18 = "2008-06-02"   # 17 on the fixture event's start, 2026-06-01
TURNS_18 = "2008-06-01"   # 18 on that very day


# ─── helpers ──────────────────────────────────────────────────────────

def _cf(event, label, field_type, order, **kw):
    return CustomFieldDefinition(
        id=uuid.uuid4(), event_id=event.id, label=label, field_type=field_type,
        sort_order=order, **kw,
    )


async def _teamer_event(db):
    """Teamer (yes/no) → Which team (text, required); a consent note for
    under-18s; a role select → Kitchen shift."""
    ev = await make_event(db, name="Camp")
    teamer = _cf(ev, "Teamer", "boolean", 0)
    team = _cf(ev, "Which team", "text", 1, is_required=True,
               show_if={"source": str(teamer.id), "any_of": ["true"]})
    note = _cf(ev, "Parental consent", "info", 2,
               options={"text": "Bring the signed form."},
               show_if={"source": "date_of_birth", "age_under": 18})
    welcome = _cf(ev, "Welcome", "info", 3, options={"text": "Hello"})
    role = _cf(ev, "Role", "select", 4, options={"choices": ["Cook", "Driver", "Other"]})
    shift = _cf(ev, "Kitchen shift", "text", 5,
                show_if={"source": str(role.id), "any_of": ["Cook"]})
    db.add_all([teamer, team, note, welcome, role, shift])
    await db.flush()
    return ev, dict(teamer=teamer, team=team, note=note, welcome=welcome, role=role, shift=shift)


async def _client():
    return AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test")


async def _admin_headers(db):
    user = await make_user(db, email=f"a-{uuid.uuid4().hex[:6]}@test.local")
    return {"Authorization": f"Bearer {create_access_token(str(user.id), user.role.value)}"}


async def _register(event_id, **body):
    payload = {"first_name": "Ana", "last_name": "Test",
               "email": f"{uuid.uuid4().hex[:8]}@example.com", "gdpr_consent": True, **body}
    async with await _client() as ac:
        r = await ac.post(f"/api/events/{event_id}/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


async def _values(db, participant_id) -> dict[str, str]:
    rows = (await db.execute(
        select(CustomFieldValue).where(CustomFieldValue.participant_id == uuid.UUID(str(participant_id)))
    )).scalars().all()
    return {str(r.field_id): r.value for r in rows}


# ─── 1-4: the rule ────────────────────────────────────────────────────

async def test_1_age_is_counted_on_the_day():
    assert age_on(date(2008, 6, 1), date(2026, 6, 1)) == 18
    assert age_on(date(2008, 6, 2), date(2026, 6, 1)) == 17
    assert age_on(date(2008, 2, 29), date(2026, 2, 28)) == 17


async def test_2_yes_no_rule_accepts_the_import_spellings(db):
    ev, f = await _teamer_event(db)
    defs = list(f.values())
    for raw in ("true", "yes", "1"):
        kept, _ = evaluate(defs, {str(f["teamer"].id): raw, str(f["team"].id): "Kitchen"}, None, date(2026, 6, 1))
        assert str(f["team"].id) in kept, raw
    kept, _ = evaluate(defs, {str(f["teamer"].id): "false", str(f["team"].id): "Kitchen"}, None, date(2026, 6, 1))
    assert str(f["team"].id) not in kept


async def test_3_select_rule_matches_only_the_ticked_options(db):
    ev, f = await _teamer_event(db)
    defs = list(f.values())
    shift = str(f["shift"].id)
    kept, _ = evaluate(defs, {str(f["role"].id): "Cook", shift: "Early"}, None, date(2026, 6, 1))
    assert kept.get(shift) == "Early"
    kept, _ = evaluate(defs, {str(f["role"].id): "Driver", shift: "Early"}, None, date(2026, 6, 1))
    assert shift not in kept


async def test_4_a_field_behind_a_hidden_field_is_hidden_too(db):
    ev = await make_event(db)
    a = _cf(ev, "A", "boolean", 0)
    b = _cf(ev, "B", "select", 1, options={"choices": ["x", "y"]},
            show_if={"source": str(a.id), "any_of": ["true"]})
    c = _cf(ev, "C", "text", 2, show_if={"source": str(b.id), "any_of": ["x"]})
    # A is No, so B was never shown; a stale B answer must not open C.
    kept, _ = evaluate([a, b, c], {str(a.id): "false", str(b.id): "x", str(c.id): "c"}, None, date.today())
    assert kept == {str(a.id): "false"}


# ─── 5-9: public registration ─────────────────────────────────────────

async def test_5_an_answer_to_a_hidden_field_is_not_stored(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={
        str(f["teamer"].id): "false", str(f["team"].id): "Kitchen",
    })
    assert await _values(db, p["id"]) == {str(f["teamer"].id): "false"}


async def test_6_an_answer_to_a_shown_field_is_stored(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={
        str(f["teamer"].id): "true", str(f["team"].id): "Kitchen",
    })
    vals = await _values(db, p["id"])
    assert vals[str(f["team"].id)] == "Kitchen"


async def test_7_under_18_on_the_start_date_gets_the_mark(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    minor = await _register(ev.id, date_of_birth=UNDER_18)
    adult = await _register(ev.id, date_of_birth=TURNS_18)
    nodob = await _register(ev.id)
    assert (await _values(db, minor["id"])).get(str(f["note"].id)) == "true"
    assert str(f["note"].id) not in await _values(db, adult["id"])
    assert str(f["note"].id) not in await _values(db, nodob["id"])
    # The response carries it, so the screen that called can show it.
    assert minor["custom_fields"].get(str(f["note"].id)) == "true"


async def test_8_an_info_text_without_a_rule_stores_nothing(db):
    ev, f = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(f["welcome"].id): "typed anyway"})
    assert str(f["welcome"].id) not in await _values(db, p["id"])


async def test_9_a_field_of_another_event_is_not_stored(db):
    ev, f = await _teamer_event(db)
    other, g = await _teamer_event(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(g["teamer"].id): "true"})
    assert await _values(db, p["id"]) == {}


# ─── 10-12: People edits ──────────────────────────────────────────────

async def test_10_editing_the_date_of_birth_moves_the_mark(db):
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


async def test_11_a_mark_cannot_be_typed_in(db):
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    p = await _register(ev.id, date_of_birth="1990-01-01")
    async with await _client() as ac:
        r = await ac.patch(f"/api/participants/{p['id']}",
                           json={"custom_fields": {str(f["note"].id): "true"}}, headers=headers)
    assert r.status_code == 200
    assert str(f["note"].id) not in await _values(db, p["id"])


async def test_12_an_organisers_answer_is_never_thrown_away(db):
    """Teamer No, then the organiser fills in a team by hand: People keeps
    it. The rule governs the form, not what an organiser records."""
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    p = await _register(ev.id, custom_fields={str(f["teamer"].id): "false"})
    async with await _client() as ac:
        r = await ac.patch(f"/api/participants/{p['id']}",
                           json={"custom_fields": {str(f["team"].id): "Kitchen"}}, headers=headers)
    assert r.json()["custom_fields"][str(f["team"].id)] == "Kitchen"


# ─── 13-19: saving rules and order ────────────────────────────────────

async def _api(db):
    ev, f = await _teamer_event(db)
    headers = await _admin_headers(db)
    await db.commit()
    return ev, f, headers, f"/api/events/{ev.id}/custom-fields"


async def test_13_a_new_field_goes_to_the_end(db):
    ev, f, headers, base = await _api(db)
    async with await _client() as ac:
        r = await ac.post(f"{base}/", json={"label": "Allergies", "field_type": "text"}, headers=headers)
        assert r.status_code == 201, r.text
        listed = (await ac.get(f"{base}/", headers=headers)).json()
    assert listed[-1]["label"] == "Allergies"


async def test_14_rules_that_cannot_stand_are_refused(db):
    ev, f, headers, base = await _api(db)
    cases = [
        ({"source": str(f["team"].id), "any_of": ["x"]}, "errors.custom_fields.condition_invalid"),   # text source
        ({"source": str(f["role"].id), "any_of": ["Pilot"]}, "errors.custom_fields.condition_option_in_use"),
        ({"source": "date_of_birth", "age_under": 0}, "errors.custom_fields.condition_invalid"),
        ({"source": str(uuid.uuid4()), "any_of": ["true"]}, "errors.custom_fields.condition_invalid"),
        ({"source": str(f["teamer"].id), "any_of": []}, "errors.custom_fields.condition_invalid"),
    ]
    async with await _client() as ac:
        for rule, key in cases:
            r = await ac.post(f"{base}/", json={"label": f"X{uuid.uuid4().hex[:4]}", "field_type": "text",
                                                "show_if": rule}, headers=headers)
            assert r.status_code == 409, (rule, r.text)
            assert r.json()["detail"]["key"] == key, rule
        # A rule may not point at a field further down.
        r = await ac.patch(f"{base}/{f['teamer'].id}",
                           json={"show_if": {"source": str(f["role"].id), "any_of": ["Cook"]}}, headers=headers)
        assert r.status_code == 409
        assert r.json()["detail"]["key"] == "errors.custom_fields.condition_order"
        listed = (await ac.get(f"{base}/", headers=headers)).json()
    assert {c["label"] for c in listed} == {c.label for c in f.values()}, "nothing refused was saved"
    assert next(c for c in listed if c["label"] == "Teamer")["show_if"] is None


async def test_15_reorder_saves_and_refuses_a_move_above_the_source(db):
    ev, f, headers, base = await _api(db)
    ids = [str(f[k].id) for k in ("teamer", "team", "note", "welcome", "role", "shift")]
    async with await _client() as ac:
        bad = [ids[1], ids[0]] + ids[2:]
        r = await ac.post(f"{base}/reorder", json={"field_ids": bad}, headers=headers)
        assert r.status_code == 409
        assert r.json()["detail"]["key"] == "errors.custom_fields.condition_order"
        good = [ids[4], ids[5], ids[0], ids[1], ids[2], ids[3]]
        r = await ac.post(f"{base}/reorder", json={"field_ids": good}, headers=headers)
        assert r.status_code == 200, r.text
        listed = (await ac.get(f"{base}/", headers=headers)).json()
        assert [c["id"] for c in listed] == good
        r = await ac.post(f"{base}/reorder", json={"field_ids": good[:-1]}, headers=headers)
        assert r.status_code == 422


async def test_16_a_field_with_dependants_cannot_be_deleted(db):
    ev, f, headers, base = await _api(db)
    async with await _client() as ac:
        r = await ac.delete(f"{base}/{f['teamer'].id}", headers=headers)
        assert r.status_code == 409
        assert r.json()["detail"]["key"] == "errors.custom_fields.has_dependants"
        assert (await ac.delete(f"{base}/{f['team'].id}", headers=headers)).status_code == 204
        assert (await ac.delete(f"{base}/{f['teamer'].id}", headers=headers)).status_code == 204


async def test_17_an_info_text_with_marks_can_be_deleted(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.delete(f"{base}/{f['note'].id}", headers=headers)
    assert r.status_code == 204, r.text
    assert str(f["note"].id) not in await _values(db, p["id"])


async def test_18_an_info_text_is_never_required_and_keeps_its_text(db):
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


async def test_19_changing_a_rule_recomputes_the_marks(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth="2012-01-01")   # 14
    assert (await _values(db, p["id"])).get(str(f["note"].id)) == "true"
    async with await _client() as ac:
        r = await ac.patch(f"{base}/{f['note'].id}",
                           json={"show_if": {"source": "date_of_birth", "age_under": 14}}, headers=headers)
        assert r.status_code == 200
    assert str(f["note"].id) not in await _values(db, p["id"])


# ─── 20-21: start date, type change ───────────────────────────────────

async def test_20_moving_the_start_date_moves_the_marks(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.patch(f"/api/events/{ev.id}", json={"start_date": "2026-06-05"}, headers=headers)
        assert r.status_code == 200, r.text
    assert str(f["note"].id) not in await _values(db, p["id"])


async def test_21_an_info_text_turned_into_a_question_loses_its_marks(db):
    ev, f, headers, base = await _api(db)
    p = await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.patch(f"{base}/{f['note'].id}", json={"field_type": "text"}, headers=headers)
        assert r.status_code == 200
        assert r.json()["options"] is None
    assert str(f["note"].id) not in await _values(db, p["id"])


# ─── 22-24: CSV import ────────────────────────────────────────────────

def _csv(rows: list[dict]) -> bytes:
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    return out.getvalue().encode()


async def test_22_import_asks_for_a_required_answer_only_when_it_applies(db):
    from app.services.batch_register_service import parse_csv
    ev, f = await _teamer_event(db)
    base = {"first_name": "A", "last_name": "B", "gdpr_consent": "true"}
    content = _csv([
        {**base, "email": "no@x.org", "Teamer": "no", "Which team": ""},
        {**base, "email": "yes@x.org", "Teamer": "yes", "Which team": ""},
    ])
    result = await parse_csv(content, ev.id, db)
    no_row, yes_row = result["rows"]
    assert no_row["valid"], no_row["errors"]
    assert not yes_row["valid"]
    assert "missing_required_custom:Which team" in yes_row["errors"]


async def test_23_an_info_column_is_ignored_not_turned_into_a_new_field(db):
    from app.services.batch_register_service import parse_csv
    ev, f = await _teamer_event(db)
    content = _csv([{"first_name": "A", "last_name": "B", "email": "a@x.org", "gdpr_consent": "true",
                     "Parental consent": "true", "Date of Birth": "02.06.2008"}])
    result = await parse_csv(content, ev.id, db)
    assert result["new_custom_fields"] == []
    assert str(f["note"].id) not in result["rows"][0]["data"].get("custom_fields", {})


async def test_24_the_template_has_no_column_for_an_info_text(db):
    from app.services.batch_register_service import generate_template
    ev, f = await _teamer_event(db)
    header = generate_template(list(f.values())).lstrip("﻿").splitlines()[0]
    assert f"cf:{f['note'].id}" not in header
    assert f"cf:{f['welcome'].id}" not in header
    assert f"cf:{f['team'].id}" in header


# ─── 25-27: copy, form file, CSV export ───────────────────────────────

async def test_25_copying_an_event_points_rules_at_the_copies(db):
    from app.services.event_service import duplicate_event_config
    ev, f = await _teamer_event(db)
    f["role"].show_in_form = False
    dest = await make_event(db, name="Copy")
    await duplicate_event_config(db, ev.id, dest.id, CopyOptions())
    await db.flush()
    copies = {c.label: c for c in (await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == dest.id)
    )).scalars().all()}
    assert copies["Which team"].show_if == {"source": str(copies["Teamer"].id), "any_of": ["true"]}
    assert copies["Parental consent"].show_if == {"source": "date_of_birth", "age_under": 18}
    assert copies["Role"].show_in_form is False


async def test_26_form_file_carries_rules_by_label(db):
    from app.services.registration_form_io import export_registration_form, import_registration_form
    ev, f = await _teamer_event(db)
    payload = await export_registration_form(db, ev.id)
    team = next(c for c in payload["custom_fields"] if c["label"] == "Which team")
    assert team["show_if"] == {"source_label": "Teamer", "any_of": ["true"]}

    dest = await make_event(db, name="Dest")
    db.add(_cf(dest, "Already here", "text", 0))
    await db.flush()
    result = await import_registration_form(db, dest.id, payload)
    assert result["dropped_rules"] == 0
    got = {c.label: c for c in (await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == dest.id)
    )).scalars().all()}
    assert got["Which team"].show_if == {"source": str(got["Teamer"].id), "any_of": ["true"]}
    order = [c.label for c in sorted(got.values(), key=lambda c: c.sort_order)]
    assert order[0] == "Already here" and order.index("Teamer") < order.index("Which team")

    # A rule naming a field that is not in the file is dropped, not guessed.
    lonely = {"kind": payload["kind"], "custom_fields": [team]}
    other = await make_event(db, name="Other")
    result = await import_registration_form(db, other.id, lonely)
    assert result["dropped_rules"] == 1


async def test_27_people_csv_has_a_column_only_for_a_conditional_info_text(db):
    ev, f, headers, base = await _api(db)
    await _register(ev.id, date_of_birth=UNDER_18)
    async with await _client() as ac:
        r = await ac.get(f"/api/events/{ev.id}/export/participants.csv", headers=headers)
    assert r.status_code == 200, r.text
    header = next(csv.reader(io.StringIO(r.text.lstrip("﻿"))))
    assert "Parental consent" in header
    assert "Welcome" not in header


async def test_28_participant_still_comes_back_whole(db):
    """The new step sits inside registration; a person with no custom
    fields at all registers exactly as before."""
    ev = await make_event(db)
    await db.commit()
    p = await _register(ev.id)
    row = (await db.execute(select(Participant).where(Participant.id == uuid.UUID(p["id"])))).scalar_one()
    assert row.first_name == "Ana" and p["custom_fields"] == {}
