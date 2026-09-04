"""Tests for v1.0.4a — outbound webhooks refuse private/internal targets.

Three layers:
1. The policy function itself, with a fake resolver so nothing touches
   DNS.
2. The admin API: create and update return 422 with the i18n key.
3. Delivery: a user-managed endpoint whose name now resolves privately
   is recorded as failed without a request being made; a SaaS-managed
   endpoint on the private network is delivered as before.
"""

import ipaddress

import httpx
import pytest

from app.api.deps import get_current_user
from app.main import app as fastapi_app
from app.models.outbound_webhook import (
    OutboundWebhookEndpoint,
    WebhookDeliveryStatus,
    WebhookEndpointManagedBy,
    WebhookEndpointState,
)
from app.models.user import User, UserRole
from app.services import webhook_service
from app.services import webhook_url_policy as policy
from app.services.webhook_url_policy import (
    WebhookUrlRejected,
    check_webhook_url,
    is_forbidden_address,
)



# ─── Helpers ────────────────────────────────────────────────────────────

PUBLIC_V4 = ipaddress.ip_address("93.184.216.34")
PUBLIC_V6 = ipaddress.ip_address("2606:2800:220:1:248:1893:25c8:1946")


def _fake_resolver(table: dict[str, list[str]]):
    def resolve(host: str):
        return [ipaddress.ip_address(a) for a in table.get(host, [])]
    return resolve


def _super_admin() -> User:
    return User(
        email="super@test.local",
        hashed_password="$2b$12$test.hash.placeholder.for.test.fixtures.only....",
        full_name="Test Super",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    )


# ─── 1. Policy ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("addr", [
    "10.20.30.40", "10.255.255.255",          # RFC 1918
    "172.16.0.1", "172.31.255.254",
    "192.168.4.24",
    "127.0.0.1", "127.8.8.8",              # loopback
    "169.254.169.254", "169.254.1.1",      # link-local incl. cloud metadata
    "100.64.0.1", "100.127.255.254",       # CGNAT / Tailscale
    "0.0.0.0", "0.1.2.3",
    "224.0.0.1", "240.0.0.1",              # multicast, reserved
    "::1", "::", "fc00::1", "fd12::1",     # IPv6 loopback, unspecified, ULA
    "fe80::1", "ff02::1",                  # IPv6 link-local, multicast
    "::ffff:10.20.30.40", "::ffff:127.0.0.1", # IPv4-mapped
])
def test_forbidden_addresses(addr):
    assert is_forbidden_address(ipaddress.ip_address(addr))


@pytest.mark.parametrize("addr", ["93.184.216.34", "8.8.8.8", "1.1.1.1", str(PUBLIC_V6)])
def test_public_addresses_allowed(addr):
    assert not is_forbidden_address(ipaddress.ip_address(addr))


@pytest.mark.parametrize("url", [
    "http://10.20.30.40:8000/webhooks/ce",
    "http://127.0.0.1:2019/config/",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]:8000/",
    "http://[::ffff:10.20.30.40]/",
    "http://localhost/hook",
    "http://LOCALHOST:8080/hook",
    "http://db.localhost/hook",
    "http://100.100.1.1/",
])
def test_literal_private_targets_rejected(url):
    with pytest.raises(WebhookUrlRejected):
        check_webhook_url(url, allow_private=False)


@pytest.mark.parametrize("url", ["ftp://example.com/x", "file:///etc/passwd", "gopher://x"])
def test_non_http_schemes_rejected_even_when_private_allowed(url):
    with pytest.raises(WebhookUrlRejected) as exc:
        check_webhook_url(url, allow_private=True)
    assert exc.value.reason == "scheme"


def test_hostname_resolving_privately_rejected(monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver({"evil.example": ["10.20.30.40"]}))
    with pytest.raises(WebhookUrlRejected) as exc:
        check_webhook_url("https://evil.example/hook", allow_private=False)
    assert exc.value.reason == "private"


def test_hostname_with_one_private_answer_among_public_rejected(monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver(
        {"mixed.example": ["93.184.216.34", "192.168.1.1"]}
    ))
    with pytest.raises(WebhookUrlRejected):
        check_webhook_url("https://mixed.example/hook", allow_private=False)


def test_public_hostname_allowed(monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver(
        {"hooks.example": ["93.184.216.34", str(PUBLIC_V6)]}
    ))
    check_webhook_url("https://hooks.example/hook", allow_private=False)


def test_unresolvable_hostname_allowed(monkeypatch):
    """Cannot reach anything; delivery fails on its own and is logged."""
    monkeypatch.setattr(policy, "_resolve", _fake_resolver({}))
    check_webhook_url("https://not-yet-live.example/hook", allow_private=False)


def test_allow_private_switch_permits_private_targets():
    check_webhook_url("http://192.168.1.50:5678/webhook", allow_private=True)
    check_webhook_url("http://localhost:5678/webhook", allow_private=True)


def test_default_reads_setting(monkeypatch):
    """With no explicit flag the policy consults the settings object."""
    from app.core import config as cfg
    settings = cfg.get_settings()
    monkeypatch.setattr(settings, "webhook_allow_private_targets", False)
    with pytest.raises(WebhookUrlRejected):
        check_webhook_url("http://10.20.30.40:8000/")
    monkeypatch.setattr(settings, "webhook_allow_private_targets", True)
    check_webhook_url("http://10.20.30.40:8000/")


# ─── 2. Admin API ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_endpoint_private_url_returns_422(client, db, monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver({}))
    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(
            "/api/webhooks/endpoints",
            json={"name": "ssrf", "url": "http://10.20.30.40:8000/webhooks/ce"},
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == {"key": "errors.webhooks.url_not_allowed"}
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_endpoint_public_url_still_works(client, db, monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver(
        {"hooks.example": ["93.184.216.34"]}
    ))
    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.post(
            "/api/webhooks/endpoints",
            json={"name": "ok", "url": "https://hooks.example/h"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["url"] == "https://hooks.example/h"
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_update_endpoint_to_private_url_returns_422(client, db, monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver(
        {"hooks.example": ["93.184.216.34"]}
    ))
    ep = OutboundWebhookEndpoint(
        name="ok", url="https://hooks.example/h", secret="s", event_types=["*"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.commit()
    fastapi_app.dependency_overrides[get_current_user] = _super_admin
    try:
        resp = await client.patch(
            f"/api/webhooks/endpoints/{ep.id}",
            json={"url": "http://169.254.169.254/latest/meta-data/"},
        )
        assert resp.status_code == 422
        assert resp.json()["detail"] == {"key": "errors.webhooks.url_not_allowed"}
    finally:
        fastapi_app.dependency_overrides.pop(get_current_user, None)
    await db.refresh(ep)
    assert ep.url == "https://hooks.example/h"


# ─── 3. Delivery ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delivery_refused_when_user_endpoint_resolves_privately(db, monkeypatch):
    """Passed at creation, re-pointed since: no request is made."""
    monkeypatch.setattr(policy, "_resolve", _fake_resolver(
        {"rebound.example": ["10.20.30.40"]}
    ))
    ep = OutboundWebhookEndpoint(
        name="rebound", url="https://rebound.example/h", secret="s",
        event_types=["*"], managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={"x": 1}
    )
    await db.commit()

    calls: list[httpx.Request] = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, text="ok")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5.0) as client:
        n = await webhook_service.process_pending_deliveries(db, http_client=client)

    assert n == 1
    assert calls == [], "no HTTP request may be made to a refused target"
    await db.refresh(deliveries[0])
    await db.refresh(ep)
    assert deliveries[0].error == "url_not_allowed"
    assert deliveries[0].response_status is None
    assert deliveries[0].status == WebhookDeliveryStatus.PENDING  # normal retry path
    assert ep.consecutive_failures == 1


@pytest.mark.asyncio
async def test_saas_managed_endpoint_on_private_network_still_delivered(db, monkeypatch):
    """The control plane's own receiver is exempt by design."""
    monkeypatch.setattr(policy, "_resolve", _fake_resolver({}))
    ep = OutboundWebhookEndpoint(
        name="saas", url="http://10.20.30.40:8000/webhooks/ce", secret="s",
        event_types=["*"], managed_by=WebhookEndpointManagedBy.SAAS,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={"x": 1}
    )
    await db.commit()

    calls: list[httpx.Request] = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, text="ok")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5.0) as client:
        n = await webhook_service.process_pending_deliveries(db, http_client=client)

    assert n == 1
    assert len(calls) == 1
    assert str(calls[0].url) == "http://10.20.30.40:8000/webhooks/ce"
    await db.refresh(deliveries[0])
    assert deliveries[0].status == WebhookDeliveryStatus.SUCCESS


@pytest.mark.asyncio
async def test_delivery_to_public_user_endpoint_unchanged(db, monkeypatch):
    monkeypatch.setattr(policy, "_resolve", _fake_resolver(
        {"ok.example": ["93.184.216.34"]}
    ))
    ep = OutboundWebhookEndpoint(
        name="ok", url="https://ok.example/h", secret="s", event_types=["*"],
        managed_by=WebhookEndpointManagedBy.USER,
        state=WebhookEndpointState.ACTIVE, is_active=True,
    )
    db.add(ep)
    await db.flush()
    deliveries = await webhook_service.queue_event(
        db, event_type="test.ping", data={"x": 1}
    )
    await db.commit()
    transport = httpx.MockTransport(lambda req: httpx.Response(200, text="ok"))
    async with httpx.AsyncClient(transport=transport, timeout=5.0) as client:
        await webhook_service.process_pending_deliveries(db, http_client=client)
    await db.refresh(deliveries[0])
    assert deliveries[0].status == WebhookDeliveryStatus.SUCCESS
