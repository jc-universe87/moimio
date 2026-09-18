"""Note model — private or published, attachable to any entity."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ─── Polymorphic attachment ───
    # notable_type: "participant" | "event" | "room" | "group" | "assignment"
    notable_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    notable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # ─── Content ───
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ─── Author ───
    # v1.0.4zb (USER-1): nullable, with ON DELETE SET NULL. A published note
    # outlives the person who wrote it and shows no author, exactly as
    # v1.0.4t does for history from a departed user; authorship is never
    # reassigned, because that would make the record say somebody wrote what
    # they did not. Unpublished notes are swept before the user row goes
    # (api/users.py), so a null author here always means a PUBLISHED note —
    # which matters, because the visibility rule is "published, or mine" and
    # a null author matches nobody.
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ─── Timestamps ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        visibility = "published" if self.is_published else "private"
        return f"<Note {visibility} on {self.notable_type}:{self.notable_id}>"
