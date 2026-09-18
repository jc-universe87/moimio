"""
Restore a whole-workspace export produced by `app.cli.export_all`.

Usage (inside the backend container):
    python -m app.cli.import_all --in /path/to/moimio-export.zip \
        --as admin@example.com [--dry-run] [--into-existing]

The counterpart to `app.cli.export_all`. Until v1.0.4u nothing read that
archive back: a customer leaving the hosted service unzipped it themselves
and uploaded every event through the Backup page one at a time, each
arriving renamed. This command does the whole archive in one go.

What it does:
    • Every event in the archive is restored through the same per-event
      restore the Backup page uses (`backup_service.confirm_restore`), with
      the named admin as the actor. Every rule that restore already applies
      applies here unchanged.
    • On an instance with no events of its own, each event keeps its own
      name. On an instance that already has events the command refuses
      unless `--into-existing` is given, and then names get " (Restored)"
      exactly as the Backup page does.
    • One event that cannot be read costs that event, not the archive: its
      work is rolled back and the next event is tried. The summary names
      every event as restored or failed, with the reason.
    • `--dry-run` writes nothing at all: no rows, no files, no side
      effects. It reads the archive, checks each event file can be read,
      and lists what would come back and what each event would be named.
      It always runs, whatever this instance already holds, so looking
      first never needs a flag that says "write".

What it never does:
    • It never reads `team.json` or `webhooks.json`. Those two files are a
      reference list for a person, not input for a machine: this command
      creates no account, grants no role and registers no webhook. A
      permission must never come from a file. Invite the team again and
      re-enter webhook secrets on the receiving instance.

Exits 0 only when every event in the archive was restored, following
`export_all`'s convention (so an automated caller can tell a real restore
from a partial one).
"""

import argparse
import asyncio
import io
import json
import sys
import zipfile
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.exceptions import MoimioAppError
from app.models.event import Event
from app.models.user import UserRole
from app.services.auth_service import get_user_by_email
from app.services.backup_service import confirm_restore, preview_restore


class ArchiveRefused(Exception):
    """The file is not a whole-workspace export, so nothing is attempted."""


def _describe(exc: Exception) -> str:
    """One short line naming why an event could not be restored.

    A `MoimioAppError` carries a translatable key, not a sentence; this is a
    server command whose reader is whoever typed it, so the key and its
    parameters are printed as they are rather than translated.
    """
    if isinstance(exc, MoimioAppError):
        if exc.params:
            return f"{exc.key} ({exc.params})"
        return exc.key
    return f"{type(exc).__name__}: {exc}"


def read_archive(content: bytes) -> tuple[dict, list[str]]:
    """Open a whole-workspace archive and return its manifest and members.

    Raises `ArchiveRefused` for anything that is not one: a file that is not
    a ZIP at all, and — the case worth naming — a single-event backup, which
    belongs on the Backup page and not here.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise ArchiveRefused("that file is not a ZIP archive.")

    with zf:
        names = set(zf.namelist())
        # A per-event backup has `event.json` at the root; a whole-workspace
        # export never does. Say where it belongs instead of failing vaguely.
        if "event.json" in names:
            raise ArchiveRefused(
                "that is a single-event backup, not a whole-workspace "
                "export. Restore it from the Backup page in the app "
                "(Backup ▸ From backup)."
            )
        if "manifest.json" not in names:
            raise ArchiveRefused(
                "that archive has no manifest.json, so it is not a "
                "whole-workspace export."
            )
        try:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ArchiveRefused("that archive's manifest.json cannot be read.")
        if not isinstance(manifest, dict) or "events" not in manifest:
            raise ArchiveRefused(
                "that archive's manifest.json does not list events, so it "
                "is not a whole-workspace export."
            )

        members = sorted(
            n for n in names if n.startswith("events/") and n.endswith(".zip")
        )

    return manifest, members


async def workspace_is_empty(db: AsyncSession) -> bool:
    """Whether this instance holds no events at all.

    Archived events count: an instance with nothing but archived events is
    not a fresh server, and restoring into it is the case `--into-existing`
    exists for.
    """
    result = await db.execute(select(func.count()).select_from(Event))
    return (result.scalar() or 0) == 0


async def restore_archive(
    content: bytes,
    db: AsyncSession,
    actor_user_id,
    *,
    suffix_name: bool,
    dry_run: bool,
) -> dict:
    """Restore every event in a whole-workspace archive.

    Returns a summary naming every event as restored or failed. One event's
    failure is caught, its own work rolled back, and the next event tried:
    `confirm_restore` commits, so an event that raises before its commit
    leaves nothing behind once its transaction is rolled back, and an event
    that already committed is untouched by a later failure.

    With `dry_run` nothing is written: each event file is opened and read
    through `preview_restore`, which parses the backup and returns its
    summary without touching the database.
    """
    manifest, members = read_archive(content)

    # Manifest order first, so the summary reads in the order the export
    # wrote them; anything in the archive the manifest does not mention is
    # still restored, appended at the end. A file is never skipped because
    # the manifest forgot it.
    ordered: list[str] = []
    for entry in manifest.get("events") or []:
        if not isinstance(entry, dict):
            continue
        member = f"events/{entry.get('event_id')}.zip"
        if member in members and member not in ordered:
            ordered.append(member)
    ordered += [m for m in members if m not in ordered]

    named = {
        f"events/{e.get('event_id')}.zip": e.get("name")
        for e in (manifest.get("events") or [])
        if isinstance(e, dict)
    }

    restored: list[dict] = []
    failed: list[dict] = []

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for member in ordered:
            row = {"member": member, "name": named.get(member)}
            try:
                event_bytes = zf.read(member)
                if dry_run:
                    preview = preview_restore(event_bytes)
                    row["name"] = preview.get("event_name") or row["name"]
                    # v1.0.4v: the name this event would end up with, so a
                    # trial run on an instance that already has events shows
                    # the suffix before a real run applies it.
                    base = row["name"] or member
                    row["would_be_named"] = (
                        f"{base} (Restored)" if suffix_name else base
                    )
                    row["counts"] = preview.get("counts", {})
                    restored.append(row)
                    continue
                result = await confirm_restore(
                    event_bytes, db, actor_user_id=actor_user_id,
                    suffix_name=suffix_name,
                )
                row["new_event_id"] = result["new_event_id"]
                row["new_event_name"] = result["new_event_name"]
                row["counts"] = result.get("counts", {})
                restored.append(row)
            except Exception as exc:  # one bad event costs that event only
                if not dry_run:
                    await db.rollback()
                row["reason"] = _describe(exc)
                failed.append(row)

    return {
        "dry_run": dry_run,
        "suffix_name": suffix_name,
        "event_count": len(ordered),
        "restored": restored,
        "failed": failed,
    }


def print_summary(summary: dict) -> None:
    """Every event named, restored or failed, with the reason."""
    verb = "would be restored" if summary["dry_run"] else "restored"
    if summary["dry_run"]:
        print("Trial run: nothing was written.")
    print(
        f"{len(summary['restored'])} of {summary['event_count']} "
        f"event(s) {verb}."
    )
    if summary["dry_run"] and summary["suffix_name"]:
        # suffix_name is set from "this instance already has events", which
        # is the same condition a real run would refuse on.
        print(
            "This instance already has events, so a real run needs "
            "--into-existing, and each event would be named as shown."
        )
    for row in summary["restored"]:
        name = (row.get("new_event_name") or row.get("would_be_named")
                or row.get("name") or row["member"])
        suffix = ""
        if row.get("new_event_id"):
            suffix = f"  → {row['new_event_id']}"
        print(f"  ok      {name}{suffix}")
    for row in summary["failed"]:
        name = row.get("name") or row["member"]
        print(f"  FAILED  {name}: {row['reason']}")
    if summary["failed"]:
        print(f"{len(summary['failed'])} event(s) failed.")


async def main_async(
    in_path: str, as_email: str, dry_run: bool, into_existing: bool
) -> int:
    path = Path(in_path)
    if not path.is_file():
        print(f"import failed: no such file: {path}", file=sys.stderr)
        return 1
    content = path.read_bytes()

    # Refuse the wrong kind of file before opening a session, so a
    # single-event backup never gets as far as touching the database.
    try:
        read_archive(content)
    except ArchiveRefused as exc:
        print(f"import refused: {exc}", file=sys.stderr)
        return 1

    async with async_session_factory() as db:
        user = await get_user_by_email(db, as_email)
        if user is None:
            print(
                f"import refused: no user with the address {as_email} on "
                f"this instance. Nothing was written.",
                file=sys.stderr,
            )
            return 1
        if user.role is not UserRole.SUPER_ADMIN:
            print(
                f"import refused: {as_email} is not a Super Admin on this "
                f"instance. Nothing was written.",
                file=sys.stderr,
            )
            return 1

        empty = await workspace_is_empty(db)
        # v1.0.4v: the refusal guards a REAL run only. A trial run writes
        # nothing, so refusing it made the safe way of looking first need a
        # flag whose name says the opposite. It now always runs, whatever
        # this instance holds, and its summary says what a real run would
        # need and what each event would end up called.
        if not dry_run and not empty and not into_existing:
            print(
                "import refused: this instance already has events. Restoring "
                "on top of them is deliberate, so pass --into-existing to do "
                "it; the restored events will be named \" (Restored)\". "
                "Nothing was written.",
                file=sys.stderr,
            )
            return 1

        # §4.2: own names on a fresh instance, the suffix when adding to an
        # instance that already has events of its own.
        summary = await restore_archive(
            content, db, user.id,
            suffix_name=not empty,
            dry_run=dry_run,
        )

    print_summary(summary)
    return 0 if not summary["failed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="app.cli.import_all",
        description=(
            "Restore every event in a whole-workspace export produced by "
            "app.cli.export_all."
        ),
    )
    parser.add_argument(
        "--in",
        dest="in_path",
        required=True,
        help="path to the archive to read (e.g. /tmp/moimio-export.zip)",
    )
    parser.add_argument(
        "--as",
        dest="as_email",
        required=True,
        help=(
            "email address of an existing Super Admin on this instance; the "
            "restored events are attributed to them"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "write nothing at all; list what would be restored, and what "
            "each event would be named. Always runs, whatever this instance "
            "already holds"
        ),
    )
    parser.add_argument(
        "--into-existing",
        action="store_true",
        help=(
            "allow restoring onto an instance that already has events; "
            "restored names get \" (Restored)\""
        ),
    )
    args = parser.parse_args(argv)

    try:
        return asyncio.run(
            main_async(
                args.in_path, args.as_email, args.dry_run, args.into_existing
            )
        )
    except Exception as exc:  # any failure must be a non-zero exit
        print(f"import failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
