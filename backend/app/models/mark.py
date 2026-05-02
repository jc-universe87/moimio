"""Participant marks — colour-coded badges assignable to participants per event."""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MarkDefinition(Base):
    """Organiser-defined mark: name, colour, which views it appears in.

    v0.50f: `created_by_user_id` attributes authorship. Nullable so that
    pre-v0.50f marks (created before this column existed) continue to
    work — they're treated as admin-created ("system" marks). ON DELETE
    SET NULL so marks survive user deletion.
    """
    __tablename__ = "mark_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    colour: Mapped[str] = mapped_column(String(20), nullable=False, default="#4682B4")
    # visible_in: list of views e.g. ["allocation", "people", "checkin"]
    visible_in: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # v0.74: drives engine clustering behaviour for participants with
    # this mark. 'together' = engine forms a sub-cluster of these
    # participants in PASS 2 (largest first, smallest fitting unit).
    # 'split' = engine pre-distributes them evenly across eligible
    # units in PASS 3 (anti-cluster). 'none' = no clustering effect
    # (default; matches pre-v0.74 behaviour).
    cluster_behaviour: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none", server_default="none"
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarkAssignment(Base):
    """Assignment of a mark to a participant within an event.

    v0.50f-2: `assigned_by_user_id` attributes who assigned the mark.
    Nullable because pre-v0.50f-2 assignments predate the column.
    Hard delete on unassign — audit only covers current assignments.
    """
    __tablename__ = "mark_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mark_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mark_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
