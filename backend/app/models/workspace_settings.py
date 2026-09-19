"""WorkspaceSettings — the one row of settings that belong to the whole
installation rather than to an event or a user.

A Moimio install IS a workspace: there is no workspace table, and nothing
sits above `events`. Until now every workspace-level value has been an
environment variable, which suits values the operator sets once (feature
flags, SMTP) and does not suit values the organisation's own admin must be
able to change from the screen. This table holds the latter kind. It has
exactly one row, `id = 1`; `get_or_create` in the service is the only
constructor.

First and so far only column: `privacy_notice_url` (LEGAL-1). The link the
public registration form shows after the consent sentence, pointing at the
ORGANISATION's privacy notice, not Pistio's. Nullable, and null means the
form shows nothing extra.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


SINGLETON_ID = 1


class WorkspaceSettings(Base):
    __tablename__ = "workspace_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=SINGLETON_ID)
    privacy_notice_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<WorkspaceSettings privacy_notice_url={self.privacy_notice_url!r}>"
