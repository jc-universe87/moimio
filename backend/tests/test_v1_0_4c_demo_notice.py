"""v1.0.4c: /api/capabilities carries the demo-notice flag and inbox URL.

Same shape as the account_url tests: off/empty by default (a self-hoster
never sees a "demonstration workspace" banner), reflects the environment
when set (the SaaS sets both for demo tenants via env_render.py).
"""

import pytest

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_capabilities_demo_notice_off_by_default(client, monkeypatch):
    monkeypatch.delenv("FEATURE_DEMO_NOTICE", raising=False)
    monkeypatch.delenv("MOIMIO_DEMO_MAIL_URL", raising=False)
    get_settings.cache_clear()
    try:
        resp = await client.get("/api/capabilities")
    finally:
        get_settings.cache_clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo_notice"] is False
    assert body["demo_mail_url"] == ""


@pytest.mark.asyncio
async def test_capabilities_demo_notice_reflects_env(client, monkeypatch):
    monkeypatch.setenv("FEATURE_DEMO_NOTICE", "true")
    monkeypatch.setenv("MOIMIO_DEMO_MAIL_URL", "https://demo.moimio.app/mail/")
    get_settings.cache_clear()
    try:
        resp = await client.get("/api/capabilities")
    finally:
        get_settings.cache_clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo_notice"] is True
    assert body["demo_mail_url"] == "https://demo.moimio.app/mail/"


@pytest.mark.asyncio
async def test_capabilities_demo_notice_without_url(client, monkeypatch):
    """Flag on, URL blank: the notice shows with "/mail/" as plain text."""
    monkeypatch.setenv("FEATURE_DEMO_NOTICE", "true")
    monkeypatch.delenv("MOIMIO_DEMO_MAIL_URL", raising=False)
    get_settings.cache_clear()
    try:
        resp = await client.get("/api/capabilities")
    finally:
        get_settings.cache_clear()
    body = resp.json()
    assert body["demo_notice"] is True
    assert body["demo_mail_url"] == ""
