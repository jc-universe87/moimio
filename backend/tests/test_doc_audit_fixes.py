"""Fixes found while checking the manual against the code.

- Sign-ups are rate limited per address (RATE_LIMIT_REGISTRATION).
- Group codes fold accents instead of dropping the letter.
- Re-importing a people export ignores its "Excluded From" column.
- "Access before the event starts" lets staff manage check-in columns.
"""

import uuid

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.rate_limit import SlidingWindowLimiter, client_ip
from app.models.event_assignment import EventUserAssignment
from app.models.user import User, UserRole
from app.services.batch_register_service import _build_row_mapper
from app.services.participant_service import _stem_from
from app.api.checkin import _require_column_manage
from tests.conftest import make_event


# ─── Rate limit ───────────────────────────────────────────────────────

def test_limiter_allows_up_to_the_limit_then_refuses():
    lim = SlidingWindowLimiter(window=60.0)
    assert all(lim.hit("1.2.3.4", 3) for _ in range(3))
    assert lim.hit("1.2.3.4", 3) is False
    # Another address has its own allowance.
    assert lim.hit("5.6.7.8", 3) is True


def test_limiter_zero_means_off():
    lim = SlidingWindowLimiter(window=60.0)
    assert all(lim.hit("1.2.3.4", 0) for _ in range(500))


def test_limiter_forgets_hits_outside_the_window():
    lim = SlidingWindowLimiter(window=0.0)
    assert all(lim.hit("1.2.3.4", 1) for _ in range(5))


def _request(peer: str, real_ip: str | None = None) -> Request:
    headers = [(b"x-real-ip", real_ip.encode())] if real_ip else []
    return Request({"type": "http", "headers": headers, "client": (peer, 1234)})


def test_client_ip_trusts_the_proxy_header_only_from_an_internal_peer():
    # Through the frontend's Caddy (a private Docker address).
    assert client_ip(_request("172.18.0.4", "203.0.113.9")) == "203.0.113.9"
    # Straight at the backend port from the internet: the header is ignored.
    assert client_ip(_request("93.184.216.34", "203.0.113.9")) == "93.184.216.34"
    # No header: the peer itself.
    assert client_ip(_request("172.18.0.4")) == "172.18.0.4"


@pytest.mark.asyncio
async def test_public_register_answers_429_over_the_limit(db, client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "rate_limit_registration", 2)
    body = {"first_name": "A", "last_name": "B", "email": "a@example.org", "gdpr_consent": True}
    url = f"/api/events/{uuid.uuid4()}/register"
    # Unknown event: the first two get as far as the 404, the third is refused first.
    assert (await client.post(url, json=body)).status_code == 404
    assert (await client.post(url, json=body)).status_code == 404
    r = await client.post(url, json=body)
    assert r.status_code == 429
    assert r.json()["detail"]["key"] == "errors.participant.rate_limited"
    assert r.headers["retry-after"] == "60"


# ─── Group code stems ─────────────────────────────────────────────────

@pytest.mark.parametrize("name,stem", [
    ("Müller", "MULLER"),
    ("Krüger", "KRUGER"),
    ("García", "GARCIA"),
    ("Groß", "GROSS"),
    ("Ødegaard", "ODEGAARD"),
    ("Łukasz", "LUKASZ"),
    ("François", "FRANCOIS"),
    ("Zimmermann", "ZIMMERMA"),
    ("O'Brien", "OBRIEN"),
    ("김", "GROUP"),
    ("", "GROUP"),
])
def test_stem_folds_accents(name, stem):
    assert _stem_from(name) == stem


# ─── Import ignores the export's Excluded From column ─────────────────

def test_excluded_from_column_is_not_an_unknown_header():
    mapping, unknown = _build_row_mapper(
        ["First Name", "Last Name", "Email", "Excluded From", "Marks", "Status"], []
    )
    assert "Excluded From" not in unknown
    assert "Excluded From" not in mapping
    assert unknown == []


# ─── Check-in columns and "Access before the event starts" ────────────

async def _staff_on(db, event_id, *, role="staff", permissions=None):
    u = User(
        email=f"staff-{uuid.uuid4().hex[:8]}@test.local",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Staff",
        role=UserRole.STAFF,
    )
    db.add(u)
    await db.flush()
    db.add(EventUserAssignment(event_id=event_id, user_id=u.id, role=role,
                               permissions=permissions or {}))
    await db.flush()
    return u


@pytest.mark.asyncio
async def test_pre_event_staff_may_manage_columns(db):
    ev = await make_event(db)
    u = await _staff_on(db, ev.id, permissions={"checkin": {"access": "write", "pre_event": True}})
    await _require_column_manage(db, u, ev.id)  # no exception


@pytest.mark.asyncio
async def test_event_admin_may_manage_columns(db):
    ev = await make_event(db)
    u = await _staff_on(db, ev.id, role="event_admin")
    await _require_column_manage(db, u, ev.id)


@pytest.mark.asyncio
@pytest.mark.parametrize("permissions", [
    {"checkin": {"access": "write", "pre_event": False}},
    {"checkin": "write"},                       # legacy flat value
    {"people": "write", "organise": "write"},   # no check-in at all
])
async def test_other_staff_may_not_manage_columns(db, permissions):
    ev = await make_event(db)
    u = await _staff_on(db, ev.id, permissions=permissions)
    with pytest.raises(HTTPException) as exc:
        await _require_column_manage(db, u, ev.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_staff_on_another_event_may_not_manage_columns(db):
    ev = await make_event(db)
    other = await make_event(db, name="Other")
    u = await _staff_on(db, other.id, permissions={"checkin": {"access": "write", "pre_event": True}})
    with pytest.raises(HTTPException):
        await _require_column_manage(db, u, ev.id)
