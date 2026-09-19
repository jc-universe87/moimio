"""The one-row `workspace_settings` table (LEGAL-1).

Two readers and one writer. The public registration form reads the privacy
notice URL without authentication; the workspace settings page reads and
writes it as a super admin. Validation of the URL lives here, so the API
layer and any future caller reject the same things.
"""

from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace_settings import SINGLETON_ID, WorkspaceSettings

# The longest URL the field accepts. Generous for a real notice page,
# small enough that nothing can be parked in the column.
PRIVACY_NOTICE_URL_MAX_LEN = 2048


class InvalidPrivacyNoticeUrl(ValueError):
    """The value is not an absolute http(s) URL."""


def normalise_privacy_notice_url(raw: str | None) -> str | None:
    """Return the URL to store, or None for "unset".

    Blank and whitespace-only mean unset, so clearing the box clears the
    setting. Anything else must be an absolute URL with an http or https
    scheme and a host: `example.org/privacy` is rejected rather than
    guessed at, because a link the form renders must not point somewhere
    the admin did not type.
    """
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    if len(value) > PRIVACY_NOTICE_URL_MAX_LEN:
        raise InvalidPrivacyNoticeUrl("too long")
    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise InvalidPrivacyNoticeUrl(str(exc)) from exc
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise InvalidPrivacyNoticeUrl("not an absolute http(s) URL")
    # A host has to have something in it besides credentials or a port.
    if not parts.hostname:
        raise InvalidPrivacyNoticeUrl("no host")
    return value


async def get_workspace_settings(db: AsyncSession) -> WorkspaceSettings | None:
    """The row, or None if nothing has ever been saved."""
    return await db.get(WorkspaceSettings, SINGLETON_ID)


async def get_privacy_notice_url(db: AsyncSession) -> str | None:
    row = await get_workspace_settings(db)
    return row.privacy_notice_url if row else None


async def set_privacy_notice_url(db: AsyncSession, raw: str | None) -> WorkspaceSettings:
    """Validate, then store. Raises InvalidPrivacyNoticeUrl; commits nothing,
    the caller owns the transaction."""
    value = normalise_privacy_notice_url(raw)
    row = await get_workspace_settings(db)
    if row is None:
        row = WorkspaceSettings(id=SINGLETON_ID)
        db.add(row)
    row.privacy_notice_url = value
    await db.flush()
    return row
