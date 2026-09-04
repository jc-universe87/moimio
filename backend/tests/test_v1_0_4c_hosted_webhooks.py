"""v1.0.4c, item 32: on a hosted instance the webhook API is read-only.

When FEATURE_ACCOUNT_PORTAL is true, every route that would add, change,
delete, rotate, re-enable or test-fire a user-managed endpoint returns
403 errors.webhooks.hosted_managed. Listing and reading stay open. When
the flag is false (a self-hoster) nothing changes.
"""

import pytest

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.main import app as fastapi_app
from app.models.outbound_webhook import (
    OutboundWebhookEndpoint,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.models.user import User, UserRole
from app.services import webhook_url_policy as policy

HOSTED = {"key": "errors.webhooks.hosted_managed"}


def _super_admin() -> User:
    return User(
        email="super@test.local",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Super",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )


async def _user_endpoint(db) -> OutboundWebhookEndpoint:
    ep = OutboundWebhookEndpoint(
        name="theirs", url="https://hooks.example/h", secret="s", event_types=["*"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.commit()
    return ep


@pytest.fixture
def as_super_admin(monkeypatch):
    # hooks.example resolves publicly so the URL policy is not what refuses
    monkeypatch.setattr(policy, "_resolve", lambda host: [])
    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    yield
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def hosted(monkeypatch):
    monkeypatch.setenv("FEATURE_ACCOUNT_PORTAL", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def self_hosted(monkeypatch):
    monkeypatch.delenv("FEATURE_ACCOUNT_PORTAL", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ─── Hosted: every mutation refused, reads open ────────────────────────────

@pytest.mark.asyncio
async def test_hosted_create_refused(client, db, as_super_admin, hosted):
    resp = await client.post(
        "/api/webhooks/endpoints",
        json={"name": "mine", "url": "https://hooks.example/h"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == HOSTED


@pytest.mark.asyncio
async def test_hosted_update_delete_rotate_reenable_test_refused(client, db, as_super_admin, hosted):
    ep = await _user_endpoint(db)
    base = f"/api/webhooks/endpoints/{ep.id}"
    calls = [
        client.patch(base, json={"name": "renamed"}),
        client.delete(base),
        client.post(f"{base}/rotate-secret"),
        client.post(f"{base}/reenable"),
        client.post(f"{base}/test"),
    ]
    for coro in calls:
        resp = await coro
        assert resp.status_code == 403, (resp.request.method, resp.request.url, resp.text)
        assert resp.json()["detail"] == HOSTED
    # nothing was changed or removed
    await db.refresh(ep)
    assert ep.name == "theirs"
    assert ep.is_active is True


@pytest.mark.asyncio
async def test_hosted_list_and_get_still_open(client, db, as_super_admin, hosted):
    ep = await _user_endpoint(db)
    resp = await client.get("/api/webhooks/endpoints")
    assert resp.status_code == 200
    assert [e["id"] for e in resp.json()] == [str(ep.id)]
    resp = await client.get(f"/api/webhooks/endpoints/{ep.id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_hosted_super_admin_check_still_comes_first(client, db, hosted, monkeypatch):
    """A non-super-admin on a hosted instance gets the permissions error,
    not the hosted one: the gate sits behind the existing role check."""
    def _staff() -> User:
        return User(email="s@test.local", hashed_password="x", full_name="S",
                    role=UserRole.STAFF, is_active=True)
    fastapi_app.dependency_overrides[get_current_user] = _staff
    try:
        resp = await client.post("/api/webhooks/endpoints",
                                 json={"name": "x", "url": "https://hooks.example/h"})
        assert resp.status_code == 403
        assert resp.json()["detail"] == {"key": "errors.users.insufficient_permissions"}
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)


# ─── Self-hosted: unchanged ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_self_hosted_create_and_delete_still_work(client, db, as_super_admin, self_hosted):
    resp = await client.post(
        "/api/webhooks/endpoints",
        json={"name": "mine", "url": "https://hooks.example/h"},
    )
    assert resp.status_code == 201, resp.text
    ep_id = resp.json()["id"]
    resp = await client.patch(f"/api/webhooks/endpoints/{ep_id}", json={"name": "renamed"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "renamed"
    resp = await client.delete(f"/api/webhooks/endpoints/{ep_id}")
    assert resp.status_code == 204
