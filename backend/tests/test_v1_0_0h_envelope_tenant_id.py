"""Tests for the v1.0.0h envelope changes — tenant_id top-level stamping.

These are pure-function tests: no DB, no HTTP. They drive `_envelope`
directly under different MOIMIO_TENANT_ID environment values and assert
the shape comes out right.
"""

import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.services import webhook_service


def _reset_settings_cache(monkeypatch, **env):
    """Clear get_settings's lru_cache and apply env vars for this test.

    Settings is lru_cached at import time. To test env-driven behaviour
    we need to clear the cache after monkeypatching, so the next call
    to get_settings() rereads.
    """
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()


def test_envelope_omits_tenant_id_when_env_unset(monkeypatch):
    """No MOIMIO_TENANT_ID → no tenant_id key on the envelope at all.

    Self-hosters who never set the env var must see payload shape
    identical to v1.0.0g. The field doesn't appear as an empty string
    or null — it's absent entirely.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    env = webhook_service._envelope(
        event_id=uuid.uuid4(),
        event_type="event.created",
        data={"event_id": "abc"},
        now=datetime(2026, 5, 12, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert "tenant_id" not in env
    # And the rest of the envelope shape is intact
    assert set(env.keys()) == {"event_id", "event_type", "timestamp", "data"}


def test_envelope_includes_tenant_id_when_env_set(monkeypatch):
    """MOIMIO_TENANT_ID=cmi-germany → tenant_id stamped on the envelope."""
    _reset_settings_cache(monkeypatch, MOIMIO_TENANT_ID="cmi-germany")

    env = webhook_service._envelope(
        event_id=uuid.uuid4(),
        event_type="event.created",
        data={"event_id": "abc"},
        now=datetime(2026, 5, 12, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert env["tenant_id"] == "cmi-germany"


def test_envelope_tenant_id_lives_at_top_level_not_in_data(monkeypatch):
    """tenant_id is envelope-level metadata, not part of data.

    Per v1.0.0h design discussion: data describes the resource event,
    envelope describes the delivery itself. tenant_id is routing
    metadata about the delivery — receivers shouldn't have to crack
    open `data` to know which tenant this came from.
    """
    _reset_settings_cache(monkeypatch, MOIMIO_TENANT_ID="ycc-2026")

    env = webhook_service._envelope(
        event_id=uuid.uuid4(),
        event_type="event.cancelled",
        data={"event_id": "abc"},
        now=datetime(2026, 5, 12, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert env["tenant_id"] == "ycc-2026"
    assert "tenant_id" not in env["data"]


def test_envelope_empty_string_tenant_id_treated_as_absent(monkeypatch):
    """MOIMIO_TENANT_ID="" (explicitly empty) → field still omitted.

    An empty-string value is semantically equivalent to "no tenant
    set" — guards against SaaS provisioning that defaults the var to
    empty rather than removing it.
    """
    _reset_settings_cache(monkeypatch, MOIMIO_TENANT_ID="")

    env = webhook_service._envelope(
        event_id=uuid.uuid4(),
        event_type="event.created",
        data={},
        now=datetime(2026, 5, 12, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert "tenant_id" not in env


def test_envelope_stable_shape_v1_0_0g(monkeypatch):
    """Shipped v1.0.0g envelope keys are preserved exactly.

    The handover commitment is "v1.0.0g — keep this shape stable".
    Even with v1.0.0h additions, the four original keys must always
    be present with the same names and types.
    """
    monkeypatch.delenv("MOIMIO_TENANT_ID", raising=False)
    get_settings.cache_clear()

    event_id = uuid.uuid4()
    now = datetime(2026, 5, 12, 10, 0, 0, tzinfo=timezone.utc)
    env = webhook_service._envelope(
        event_id=event_id,
        event_type="event.created",
        data={"event_id": "inner-id"},
        now=now,
    )
    assert env["event_id"] == str(event_id)
    assert env["event_type"] == "event.created"
    assert env["timestamp"] == now.isoformat()
    assert env["data"] == {"event_id": "inner-id"}
