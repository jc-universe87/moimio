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

Every event is included, archived ones too — a complete export must not
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
from app.services.backup_service import export_event_zip


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
            event_bytes = await export_event_zip(event.id, db, mode="full")
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
