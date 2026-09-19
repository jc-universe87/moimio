"""LEGAL-1 — the workspace privacy notice URL.

What has to hold:
  - the public endpoint answers null until an admin saves something, so the
    registration form is exactly what it was on every existing install;
  - a saved URL comes back on the public endpoint;
  - anything that is not an absolute http(s) URL is refused with a key the
    form can translate, and nothing is stored;
  - blank clears the setting;
  - only a super admin may read or write the admin routes.

Auth via `dependency_overrides`, the pattern the other HTTP tests use.
"""
import uuid

import pytest

from app.api.deps import get_current_user
from app.main import app
from app.models.user import User, UserRole
from app.services.workspace_settings_service import (
    InvalidPrivacyNoticeUrl,
    normalise_privacy_notice_url,
)

pytestmark = pytest.mark.asyncio

ADMIN = "/api/admin/workspace/settings"
PUBLIC = "/api/workspace/public"


def _user(role: UserRole) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{role.value}@legal-1.test",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test",
        role=role,
    )


def _as(role: UserRole):
    app.dependency_overrides[get_current_user] = lambda: _user(role)


def _anon():
    app.dependency_overrides.pop(get_current_user, None)


# ── the validator, on its own ──

@pytest.mark.parametrize("raw", [
    "https://example.org/privacy",
    "http://example.org/datenschutz?x=1#top",
    "  https://example.org/privacy  ",
])
def test_absolute_http_urls_are_accepted(raw):
    assert normalise_privacy_notice_url(raw) == raw.strip()


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_blank_means_unset(raw):
    assert normalise_privacy_notice_url(raw) is None


@pytest.mark.parametrize("raw", [
    "example.org/privacy",          # no scheme
    "/privacy",                     # relative
    "ftp://example.org/privacy",    # wrong scheme
    "javascript:alert(1)",          # not a link to a page
    "https://",                     # scheme, no host
    "https:///privacy",             # empty host
    "mailto:someone@example.org",
    "https://" + "a" * 2050,        # over the length cap
])
def test_everything_else_is_refused(raw):
    with pytest.raises(InvalidPrivacyNoticeUrl):
        normalise_privacy_notice_url(raw)


# ── the routes ──

async def test_public_endpoint_is_null_before_anything_is_saved(client, db):
    _anon()
    resp = await client.get(PUBLIC)
    assert resp.status_code == 200
    assert resp.json() == {"privacy_notice_url": None}


async def test_saved_url_reaches_the_public_endpoint(client, db):
    _as(UserRole.SUPER_ADMIN)
    try:
        resp = await client.put(ADMIN, json={"privacy_notice_url": "https://example.org/privacy"})
        assert resp.status_code == 200
        assert resp.json() == {"privacy_notice_url": "https://example.org/privacy"}
    finally:
        _anon()
    resp = await client.get(PUBLIC)
    assert resp.json() == {"privacy_notice_url": "https://example.org/privacy"}


async def test_invalid_url_is_refused_with_a_key_and_stores_nothing(client, db):
    _as(UserRole.SUPER_ADMIN)
    try:
        resp = await client.put(ADMIN, json={"privacy_notice_url": "example.org/privacy"})
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["key"] == "errors.workspace.privacy_url_invalid"
        assert detail["fields"] == {"privacy_notice_url": "errors.workspace.privacy_url_invalid"}
    finally:
        _anon()
    resp = await client.get(PUBLIC)
    assert resp.json() == {"privacy_notice_url": None}


async def test_blank_clears_a_saved_url(client, db):
    _as(UserRole.SUPER_ADMIN)
    try:
        await client.put(ADMIN, json={"privacy_notice_url": "https://example.org/privacy"})
        resp = await client.put(ADMIN, json={"privacy_notice_url": "   "})
        assert resp.status_code == 200
        assert resp.json() == {"privacy_notice_url": None}
    finally:
        _anon()
    resp = await client.get(PUBLIC)
    assert resp.json() == {"privacy_notice_url": None}


async def test_admin_read_returns_what_was_saved(client, db):
    _as(UserRole.SUPER_ADMIN)
    try:
        await client.put(ADMIN, json={"privacy_notice_url": "https://example.org/privacy"})
        resp = await client.get(ADMIN)
        assert resp.status_code == 200
        assert resp.json() == {"privacy_notice_url": "https://example.org/privacy"}
    finally:
        _anon()


async def test_only_a_super_admin_may_read_or_write(client, db):
    _as(UserRole.STAFF)
    try:
        resp = await client.get(ADMIN)
        assert resp.status_code == 403
        assert resp.json()["detail"]["key"] == "errors.workspace.super_admin_only"
        resp = await client.put(ADMIN, json={"privacy_notice_url": "https://example.org/privacy"})
        assert resp.status_code == 403
    finally:
        _anon()


async def test_anonymous_cannot_write(client, db):
    _anon()
    resp = await client.put(ADMIN, json={"privacy_notice_url": "https://example.org/privacy"})
    assert resp.status_code in (401, 403)
