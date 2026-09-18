"""v1.0.4u — moving a whole workspace, and the two reference lists.

Until this release `app.cli.export_all` wrote an archive nothing could read
back. A customer leaving unzipped it and uploaded every event through the
Backup page one at a time, each arriving renamed. `app.cli.import_all` does
the whole archive in one go, through the same per-event restore, so every
rule v1.0.4m to v1.0.4t pinned applies here unchanged.

The rules these tests pin, from the release brief:

  - The export carries `team.json` and `webhooks.json`, always, empty or
    not, and every event file is still there.
  - No secret reaches the archive: no password hash, no reset token, no
    webhook signing secret.
  - Webhooks: the customer's own endpoints only, never the hosting
    service's.
  - Names: own names on an instance with no events, " (Restored)" when
    adding to one that has some.
  - One event that cannot be read costs that event, not the archive.
  - A trial run writes nothing at all.
  - `--as` names an existing Super Admin, or nothing is written.
  - A single-event backup is refused, and sent to the Backup page.
  - Nothing is applied from the two lists: no account, no role, no webhook.
  - A restored event is whole — the same restore as the rest of the series.

`_build` is imported from test_v1_0_4o_round_trip.py, as
test_v1_0_4o_damaged_files.py does, so the whole-archive path is proved
against the same maximal event the per-event round trip uses.
"""

import io
import json
import uuid
import zipfile

import pytest
from sqlalchemy import func, select

from app.cli import export_all, import_all
from app.cli.import_all import (
    ArchiveRefused,
    read_archive,
    restore_archive,
    workspace_is_empty,
)
from app.models.allocation import Allocation
from app.models.allocation_event import AllocationEvent
from app.models.checkin_value import CheckInValue
from app.models.event import Event
from app.models.event_assignment import EventUserAssignment
from app.models.note import Note
from app.models.outbound_webhook import (
    OutboundWebhookEndpoint,
    WebhookEndpointManagedBy,
)
from app.models.user import User, UserRole
from app.services.backup_service import export_event_zip

from tests.conftest import make_event, make_participant
from tests.test_v1_0_4o_round_trip import _build

pytestmark = pytest.mark.asyncio


# Distinctive markers: if any of these three reaches the archive, test 2
# finds it. Each is a value no other column in the fixture holds.
HASH_MARKER = "$2b$12$LEAKED.PASSWORD.HASH.MARKER.v1041u.canary......."
TOKEN_MARKER = "LEAKED-RESET-TOKEN-MARKER-v1041u"
SECRET_MARKER = "LEAKED-WEBHOOK-SECRET-MARKER-v1041u"


# ─── fixtures ─────────────────────────────────────────────────────────

async def _admin(db, email: str = "leaver@test.local") -> User:
    u = User(
        email=email,
        hashed_password=HASH_MARKER,
        full_name="The Leaver",
        role=UserRole.SUPER_ADMIN,
        can_manage_users=True,
        can_create_events=True,
        password_reset_token=TOKEN_MARKER,
    )
    db.add(u)
    await db.flush()
    return u


async def _staff(db, email: str = "helper@test.local") -> User:
    u = User(
        email=email,
        hashed_password="$2b$12$staff.placeholder.hash.for.fixtures.only..",
        full_name="The Helper",
        role=UserRole.STAFF,
        can_create_events=True,
    )
    db.add(u)
    await db.flush()
    return u


async def _endpoint(db, name, url, managed_by, *, secret=SECRET_MARKER,
                    event_types=None, is_active=True) -> OutboundWebhookEndpoint:
    e = OutboundWebhookEndpoint(
        name=name,
        url=url,
        secret=secret,
        event_types=event_types if event_types is not None else ["*"],
        managed_by=managed_by,
        is_active=is_active,
    )
    db.add(e)
    await db.flush()
    return e


async def _two_event_workspace(db) -> dict:
    """Two events, an admin, a staff member with a per-event role, and one
    endpoint of each kind."""
    admin = await _admin(db)
    staff = await _staff(db)
    ev1 = await make_event(db, name="Spring Retreat")
    await make_participant(db, ev1.id, first_name="Alice")
    ev2 = await make_event(db, name="Autumn Conference")
    await make_participant(db, ev2.id, first_name="Bob")
    db.add(EventUserAssignment(
        event_id=ev1.id, user_id=staff.id, role="staff",
        permissions={"people": "read", "checkin": "write"},
    ))
    mine = await _endpoint(
        db, "Our Slack", "https://hooks.example.org/ours",
        WebhookEndpointManagedBy.USER, event_types=["event.created"],
    )
    theirs = await _endpoint(
        db, "SaaS billing", "https://control-plane.invalid/hook",
        WebhookEndpointManagedBy.SAAS,
    )
    await db.flush()
    return {"admin": admin, "staff": staff, "ev1": ev1, "ev2": ev2,
            "mine": mine, "theirs": theirs}


def _members(content: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def _rezip(members: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, raw in members.items():
            zf.writestr(name, raw)
    return out.getvalue()


def _every_byte(content: bytes) -> bytes:
    """Every byte the archive holds, decompressed, nested archives opened.

    Searching the archive's own bytes alone would prove nothing: the
    members are deflated, so a leaked secret would not appear as itself.
    """
    blob = bytearray(content)
    for name, raw in _members(content).items():
        blob += raw
        if name.endswith(".zip"):
            for inner in _members(raw).values():
                blob += inner
    return bytes(blob)


async def _counts(db) -> dict[str, int]:
    async def n(model):
        return (await db.execute(
            select(func.count()).select_from(model))).scalar() or 0
    return {
        "events": await n(Event),
        "users": await n(User),
        "assignments": await n(EventUserAssignment),
        "endpoints": await n(OutboundWebhookEndpoint),
        "allocation_events": await n(AllocationEvent),
    }


# ─── 1. the export carries both lists ─────────────────────────────────

async def test_export_carries_both_reference_lists(db):
    w = await _two_event_workspace(db)

    data = await export_all.build_archive(db)
    names = set(_members(data))

    assert "team.json" in names
    assert "webhooks.json" in names
    assert "manifest.json" in names
    # Every event file is still there: the lists join the archive, they do
    # not displace anything.
    assert f"events/{w['ev1'].id}.zip" in names
    assert f"events/{w['ev2'].id}.zip" in names

    team = json.loads(_members(data)["team.json"])
    assert team["note"]
    by_email = {u["email"]: u for u in team["users"]}
    assert "leaver@test.local" in by_email
    assert by_email["leaver@test.local"]["role"] == "super_admin"
    assert by_email["leaver@test.local"]["can_manage_users"] is True

    helper = by_email["helper@test.local"]
    assert helper["role"] == "staff"
    # The per-event role, keyed by an event id the manifest already lists.
    assert helper["event_roles"] == [{
        "event_id": str(w["ev1"].id),
        "role": "staff",
        "permissions": {"people": "read", "checkin": "write"},
    }]
    manifest_ids = {e["event_id"] for e in json.loads(
        _members(data)["manifest.json"])["events"]}
    assert helper["event_roles"][0]["event_id"] in manifest_ids


async def test_both_lists_are_present_when_empty(db):
    # No users at all beyond what an event needs, no endpoints: both files
    # still exist, so an absent file never has to be interpreted.
    data = await export_all.build_archive(db)
    members = _members(data)
    assert json.loads(members["team.json"])["users"] == []
    assert json.loads(members["webhooks.json"])["endpoints"] == []
    assert json.loads(members["webhooks.json"])["endpoint_count"] == 0


# ─── 2. no secret anywhere in the archive ─────────────────────────────

async def test_no_secret_is_anywhere_in_the_archive(db):
    await _two_event_workspace(db)

    blob = _every_byte(await export_all.build_archive(db))

    assert HASH_MARKER.encode() not in blob, "a password hash reached the archive"
    assert TOKEN_MARKER.encode() not in blob, "a reset token reached the archive"
    assert SECRET_MARKER.encode() not in blob, "a webhook secret reached the archive"
    # The columns themselves are absent, not merely emptied.
    team = json.loads(_members(await export_all.build_archive(db))["team.json"])
    for user in team["users"]:
        assert "hashed_password" not in user
        assert "password_reset_token" not in user
        assert "password_reset_expires" not in user


# ─── 3. webhooks: the customer's own only ─────────────────────────────

async def test_webhook_list_carries_the_customers_own_only(db):
    await _two_event_workspace(db)

    hooks = json.loads(_members(await export_all.build_archive(db))["webhooks.json"])

    assert hooks["endpoint_count"] == 1
    listed = hooks["endpoints"][0]
    assert listed == {
        "name": "Our Slack",
        "url": "https://hooks.example.org/ours",
        "event_types": ["event.created"],
        "is_active": True,
    }
    # The hosting service's own endpoint is not the customer's data.
    assert "control-plane.invalid" not in json.dumps(hooks)


async def test_webhook_list_is_empty_when_there_are_none(db):
    await make_event(db, name="Quiet Workspace")
    hooks = json.loads(_members(await export_all.build_archive(db))["webhooks.json"])
    assert hooks["endpoints"] == []


# ─── 4. names ─────────────────────────────────────────────────────────

async def test_restore_keeps_names_on_a_fresh_instance(db):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)

    summary = await restore_archive(
        data, db, w["admin"].id, suffix_name=False, dry_run=False)

    assert summary["failed"] == []
    assert len(summary["restored"]) == 2
    assert {r["new_event_name"] for r in summary["restored"]} == {
        "Spring Retreat", "Autumn Conference"}


async def test_restore_adds_the_suffix_when_told_to(db):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)

    summary = await restore_archive(
        data, db, w["admin"].id, suffix_name=True, dry_run=False)

    assert summary["failed"] == []
    assert {r["new_event_name"] for r in summary["restored"]} == {
        "Spring Retreat (Restored)", "Autumn Conference (Restored)"}


# ─── 5. the emptiness check ───────────────────────────────────────────

async def test_workspace_is_empty_reports_correctly(db):
    assert await workspace_is_empty(db) is True

    ev = await make_event(db, name="One Event")
    await db.flush()
    assert await workspace_is_empty(db) is False

    # An archived event still counts: this is not a fresh server.
    ev.is_archived = True
    await db.flush()
    assert await workspace_is_empty(db) is False


# ─── 6. one damaged event does not stop the rest ──────────────────────

async def test_a_damaged_event_costs_that_event_only(db):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)

    members = _members(data)
    members[f"events/{w['ev2'].id}.zip"] = b"this is not a ZIP archive at all"
    damaged = _rezip(members)

    summary = await restore_archive(
        damaged, db, w["admin"].id, suffix_name=True, dry_run=False)

    assert [r["new_event_name"] for r in summary["restored"]] == [
        "Spring Retreat (Restored)"]
    assert len(summary["failed"]) == 1
    failure = summary["failed"][0]
    assert failure["name"] == "Autumn Conference"
    assert failure["reason"], "a failure must say why"

    # Nothing of the failed event is left behind.
    left = (await db.execute(select(func.count()).select_from(Event).where(
        Event.name == "Autumn Conference (Restored)"))).scalar()
    assert left == 0
    survived = (await db.execute(select(func.count()).select_from(Event).where(
        Event.name == "Spring Retreat (Restored)"))).scalar()
    assert survived == 1


# ─── 7. the trial run writes nothing ──────────────────────────────────

async def test_the_trial_run_writes_nothing(db):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)
    await db.commit()

    before = await _counts(db)
    summary = await restore_archive(
        data, db, w["admin"].id, suffix_name=False, dry_run=True)
    after = await _counts(db)

    assert before == after
    assert summary["dry_run"] is True
    assert summary["failed"] == []
    # The summary still lists every event, by its own name.
    assert {r["name"] for r in summary["restored"]} == {
        "Spring Retreat", "Autumn Conference"}
    # Nothing was written, so nothing has a new id.
    assert all("new_event_id" not in r for r in summary["restored"])


# ─── 7b. the trial run always runs (v1.0.4v) ────────────────

async def test_the_trial_run_runs_on_an_instance_with_events(db, tmp_path, capsys):
    """Looking first must never need a flag whose name says "write".

    Until v1.0.4v the non-empty refusal came before the dry-run branch, so
    the safe preview was refused unless it was given --into-existing.
    """
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)
    await db.commit()
    path = tmp_path / "workspace.zip"
    path.write_bytes(data)

    before = await _counts(db)
    # No --into-existing, and this instance already has two events.
    code = await import_all.main_async(
        str(path), "leaver@test.local", True, False)
    await db.rollback()
    out = capsys.readouterr().out

    assert code == 0, "a trial run must not be refused"
    assert await _counts(db) == before, "a trial run must write nothing"
    # It says what a real run would need, and what each event would be called.
    assert "--into-existing" in out
    assert "Spring Retreat (Restored)" in out
    assert "Autumn Conference (Restored)" in out


async def test_a_real_run_on_an_instance_with_events_is_still_refused(
        db, tmp_path):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)
    await db.commit()
    path = tmp_path / "workspace.zip"
    path.write_bytes(data)

    before = await _counts(db)
    code = await import_all.main_async(
        str(path), "leaver@test.local", False, False)
    await db.rollback()

    assert code == 1
    assert await _counts(db) == before


# ─── 8. the admin check ───────────────────────────────────────────────

async def test_an_unknown_address_is_refused(db, tmp_path):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)
    await db.commit()
    path = tmp_path / "workspace.zip"
    path.write_bytes(data)

    before = await _counts(db)
    code = await import_all.main_async(
        str(path), "nobody@test.local", False, True)
    await db.rollback()

    assert code == 1
    assert await _counts(db) == before


async def test_a_non_super_admin_is_refused(db, tmp_path):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)
    await db.commit()
    path = tmp_path / "workspace.zip"
    path.write_bytes(data)

    before = await _counts(db)
    code = await import_all.main_async(
        str(path), "helper@test.local", False, True)
    await db.rollback()

    assert code == 1
    assert await _counts(db) == before


# ─── 9. a single-event backup is refused ──────────────────────────────

async def test_a_single_event_backup_is_refused(db, tmp_path):
    ev = await make_event(db, name="Just One Event")
    await make_participant(db, ev.id, first_name="Alice")
    await db.flush()
    single = await export_event_zip(ev.id, db, mode="full")
    await db.commit()

    with pytest.raises(ArchiveRefused) as exc:
        read_archive(single)
    assert "Backup page" in str(exc.value)

    path = tmp_path / "one-event.zip"
    path.write_bytes(single)
    before = await _counts(db)
    code = await import_all.main_async(
        str(path), "anyone@test.local", False, True)
    await db.rollback()

    assert code == 1
    assert await _counts(db) == before


# ─── 10. nothing is applied from the two lists ────────────────────────

async def test_nothing_is_applied_from_the_reference_lists(db):
    w = await _two_event_workspace(db)
    data = await export_all.build_archive(db)
    await db.commit()

    before = await _counts(db)
    summary = await restore_archive(
        data, db, w["admin"].id, suffix_name=True, dry_run=False)
    after = await _counts(db)

    assert summary["failed"] == []
    assert after["users"] == before["users"], "restore created an account"
    assert after["assignments"] == before["assignments"], "restore granted a role"
    assert after["endpoints"] == before["endpoints"], "restore created a webhook"
    # It did restore the events, so the counts above are not simply flat.
    assert after["events"] == before["events"] + 2


# ─── 11. a restored event is whole ────────────────────────────────────

async def test_a_restored_event_is_whole(db):
    src = await _build(db, extra_notes=True)
    admin = src["user"]
    data = await export_all.build_archive(db)

    summary = await restore_archive(
        data, db, admin.id, suffix_name=False, dry_run=False)

    assert summary["failed"] == [], summary["failed"]
    assert len(summary["restored"]) == 1
    new_id = uuid.UUID(summary["restored"][0]["new_event_id"])
    assert new_id != src["event"].id

    async def n(model, column):
        return (await db.execute(select(func.count()).select_from(model)
                                 .where(column == new_id))).scalar() or 0

    # The whole series, proved through the whole-archive path: history
    # (v1.0.4t), notes and check-in (v1.0.4s), placements (v1.0.4m onward).
    assert await n(AllocationEvent, AllocationEvent.event_id) > 0, "no history"
    assert await n(CheckInValue, CheckInValue.event_id) > 0, "no check-in"
    assert await n(Allocation, Allocation.event_id) > 0, "no placements"
    # A note names what it is about rather than its event, so the event's
    # own notes are the ones countable by id alone.
    notes = (await db.execute(
        select(func.count()).select_from(Note)
        .where(Note.notable_type == "event", Note.notable_id == new_id)
    )).scalar() or 0
    assert notes > 0, "no notes"
