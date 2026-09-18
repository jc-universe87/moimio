"""
Export every event in this workspace to a single ZIP archive.

Usage (inside the backend container):
    python -m app.cli.export_all --out /path/to/moimio-export.zip

The whole-workspace counterpart to the per-event "backup.zip" download in
the app. A self-hoster can use it for a complete off-box backup or for
migrating a workspace; it is also how the hosted control plane fulfils a
data-export request before a workspace is paused.

The archive contains:
    manifest.json            — exported_at, event count, and the list of
                               events (id, name, archived flag)
    events/<event_id>.zip    — each event's full backup, exactly as the
                               in-app `backup.zip?mode=full` download
                               produces it (manifest.json, event.json,
                               participants.csv, and the allocation / marks
                               / preferences / custom-field / notes JSON)
    team.json                — v1.0.4u. The organising team, for reference:
                               each account's name, email, system role and
                               permission flags, plus its per-event roles
                               keyed by the event ids in the manifest.
    webhooks.json            — v1.0.4u. The customer's own outbound webhook
                               endpoints, for reference: name, address,
                               subscribed event types, active flag.

Both reference lists are always present, empty or not, and neither is ever
part of a per-event backup: an event admin can download one of those, and
the team and the webhooks belong to the whole instance. Nothing restores
them. `app.cli.import_all` reads the events and never reads these two
files, because a permission must never come from a file.

Never in either list: password hashes, password-reset tokens, webhook
signing secrets, and endpoints the hosting service manages for itself.

Every note is included, private ones too: this is the organisation's own
copy of its own data. Every event is included, archived ones too — a complete export must not
silently drop archived data. Exits 0 on success, non-zero on any failure
(so an automated caller can tell a real export from a failed one).
"""

import argparse
import asyncio
import io
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.event import Event
from app.models.event_assignment import EventUserAssignment
from app.models.outbound_webhook import (
    OutboundWebhookEndpoint,
    WebhookEndpointManagedBy,
)
from app.models.user import User
from app.services.backup_service import ALL_PRIVATE_NOTES, export_event_zip

# v1.0.4u: the one sentence both reference lists carry, so a customer
# opening either file knows what it is before reading a single row.
REFERENCE_NOTE = (
    "For reference only. Restoring this archive never applies this list: "
    "no account is created, no role is granted, no webhook is registered."
)


async def build_team_list(db: AsyncSession) -> dict:
    """The organising team, as a reference list.

    Name, email, system role and the two system permission flags per
    account, plus the per-event roles from `event_user_assignments` keyed
    by event id — the same ids the manifest lists, so the two files read
    together.

    Deliberately absent: `hashed_password`, `password_reset_token` and
    `password_reset_expires`. A password is not somebody's data to take
    with them to another server; it is a credential for this one.
    """
    result = await db.execute(select(User).order_by(User.created_at))
    users = list(result.scalars().all())

    result = await db.execute(select(EventUserAssignment))
    assignments = list(result.scalars().all())
    by_user: dict[str, list[dict]] = {}
    for a in assignments:
        by_user.setdefault(str(a.user_id), []).append(
            {
                "event_id": str(a.event_id),
                "role": a.role,
                "permissions": a.permissions or {},
            }
        )

    return {
        "note": REFERENCE_NOTE,
        "user_count": len(users),
        "users": [
            {
                "user_id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "is_active": bool(u.is_active),
                "can_manage_users": bool(u.can_manage_users),
                "can_create_events": bool(u.can_create_events),
                "event_roles": sorted(
                    by_user.get(str(u.id), []),
                    key=lambda r: r["event_id"],
                ),
            }
            for u in users
        ],
    }


async def build_webhook_list(db: AsyncSession) -> dict:
    """The customer's own outbound webhook endpoints, as a reference list.

    Only `managed_by == "user"` endpoints: the ones an admin created on the
    Webhooks page. The hosting service's own endpoints are infrastructure of
    the instance the customer is leaving, not the customer's data, and
    listing their addresses would hand out the control plane's map.

    Deliberately absent: `secret`. It is a live signing key, and a customer
    re-entering it on their own server is the point at which they decide
    what their new instance may sign.
    """
    result = await db.execute(
        select(OutboundWebhookEndpoint)
        .where(
            OutboundWebhookEndpoint.managed_by == WebhookEndpointManagedBy.USER
        )
        .order_by(OutboundWebhookEndpoint.created_at)
    )
    endpoints = list(result.scalars().all())

    return {
        "note": REFERENCE_NOTE,
        "endpoint_count": len(endpoints),
        "endpoints": [
            {
                "name": e.name,
                "url": e.url,
                "event_types": list(e.event_types or []),
                "is_active": bool(e.is_active),
            }
            for e in endpoints
        ],
    }


async def build_archive(db: AsyncSession) -> bytes:
    """Build the whole-workspace export archive and return its bytes.

    Reuses `export_event_zip(mode="full")` per event, so this command
    never duplicates the per-event backup logic — it only enumerates and
    wraps. Kept separate from I/O so it can be unit-tested directly.
    """
    result = await db.execute(select(Event).order_by(Event.created_at))
    events = list(result.scalars().all())

    buf = io.BytesIO()
    manifest_events = []
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for event in events:
            # v1.0.4s: every private note goes in. This is the leaving
            # export: the organisation's own copy of its own data, produced
            # from a shell that already has full database access. Holding
            # somebody's private notes back here would mean handing a
            # customer an incomplete copy of what they are owed.
            event_bytes = await export_event_zip(
                event.id, db, mode="full", private_notes=ALL_PRIVATE_NOTES)
            zf.writestr(f"events/{event.id}.zip", event_bytes)
            manifest_events.append(
                {
                    "event_id": str(event.id),
                    "name": event.name,
                    "archived": bool(event.is_archived),
                }
            )

        manifest = {
            "generator": "app.cli.export_all",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "event_count": len(events),
            "events": manifest_events,
        }
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )

        # v1.0.4u: the two reference lists. Always written, empty or not,
        # so a customer never has to wonder whether an absent file means
        # "none" or "this export is older than the feature".
        zf.writestr(
            "team.json",
            json.dumps(await build_team_list(db), indent=2, ensure_ascii=False),
        )
        zf.writestr(
            "webhooks.json",
            json.dumps(await build_webhook_list(db), indent=2, ensure_ascii=False),
        )

    return buf.getvalue()


async def main_async(out_path: str) -> int:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    async with async_session_factory() as db:
        data = await build_archive(db)
    out.write_bytes(data)
    print(f"Exported workspace to {out} ({len(data)} bytes).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="app.cli.export_all",
        description="Export every event in this workspace to one ZIP archive.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="path to write the archive to (e.g. /tmp/moimio-export.zip)",
    )
    args = parser.parse_args(argv)

    try:
        return asyncio.run(main_async(args.out))
    except Exception as exc:  # any failure must be a non-zero exit
        print(f"export failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
