"""Tests for `app.cli.export_all` — the whole-workspace export.

Two layers:
  • `test_export_all_*` integration tests use the real Postgres `db`
    fixture (CE convention; skipped gracefully where Postgres is absent)
    and exercise the full path through `export_event_zip`.
  • `test_build_archive_orchestration` mocks the database and the
    (already CE-tested) `export_event_zip`, so the genuinely-new logic —
    enumeration, ZIP assembly, manifest — is verified without a database.
"""

import io
import json
import zipfile
from datetime import datetime

import pytest

from app.cli import export_all
from tests.conftest import make_event, make_participant

pytestmark = pytest.mark.asyncio


# ── integration (Postgres db fixture) ──

async def test_export_all_bundles_every_event(db):
    ev1 = await make_event(db, name="Spring Retreat")
    await make_participant(db, ev1.id, first_name="Alice")
    ev2 = await make_event(db, name="Autumn Conference")
    await make_participant(db, ev2.id, first_name="Bob")
    await db.flush()

    data = await export_all.build_archive(db)

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert f"events/{ev1.id}.zip" in names
        assert f"events/{ev2.id}.zip" in names

        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["event_count"] == 2
        seen = {e["name"] for e in manifest["events"]}
        assert seen == {"Spring Retreat", "Autumn Conference"}

        # Each embedded per-event zip is itself a valid backup archive.
        inner = zf.read(f"events/{ev1.id}.zip")
        with zipfile.ZipFile(io.BytesIO(inner)) as ezf:
            assert "manifest.json" in ezf.namelist()
            assert "participants.csv" in ezf.namelist()


async def test_export_all_includes_archived_events(db):
    ev = await make_event(db, name="Archived Event")
    ev.is_archived = True
    await db.flush()

    data = await export_all.build_archive(db)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert manifest["event_count"] == 1
    assert manifest["events"][0]["archived"] is True


async def test_export_all_empty_workspace_is_valid(db):
    # No events: still a valid archive with an empty manifest.
    data = await export_all.build_archive(db)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert manifest["event_count"] == 0
    assert manifest["events"] == []


# ── orchestration (no database) ──

class _FakeEvent:
    def __init__(self, eid, name, archived=False):
        self.id = eid
        self.name = name
        self.is_archived = archived


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, _query):
        return _FakeResult(self._rows)


async def test_build_archive_orchestration(monkeypatch):
    """Enumeration + ZIP assembly + manifest, with the DB and the
    per-event backup both faked. Proves the new code without Postgres."""
    rows = [
        _FakeEvent("11111111-1111-1111-1111-111111111111", "Event One"),
        _FakeEvent("22222222-2222-2222-2222-222222222222", "Event Two", archived=True),
    ]

    async def fake_export_event_zip(event_id, db, mode="full"):
        assert mode == "full"
        return f"zip-for-{event_id}".encode()

    monkeypatch.setattr(export_all, "export_event_zip", fake_export_event_zip)

    data = await export_all.build_archive(_FakeDB(rows))

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
        assert names == {
            "manifest.json",
            "events/11111111-1111-1111-1111-111111111111.zip",
            "events/22222222-2222-2222-2222-222222222222.zip",
        }
        assert zf.read("events/11111111-1111-1111-1111-111111111111.zip") == (
            b"zip-for-11111111-1111-1111-1111-111111111111"
        )
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["event_count"] == 2
        assert manifest["generator"] == "app.cli.export_all"
        # exported_at parses as ISO-8601.
        datetime.fromisoformat(manifest["exported_at"])
        archived = {e["name"]: e["archived"] for e in manifest["events"]}
        assert archived == {"Event One": False, "Event Two": True}
