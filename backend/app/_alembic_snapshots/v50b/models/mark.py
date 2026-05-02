"""Participant marks — colour-coded badges assignable to participants per event."""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .._base import Base


class MarkDefinition(Base):
    """Organiser-defined mark: name, colour, which views it appears in."""
    __tablename__ = "mark_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    colour: Mapped[str] = mapped_column(String(20), nullable=False, default="#4682B4")
    # visible_in: list of views e.g. ["allocation", "people", "checkin"]
    visible_in: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarkAssignment(Base):
    """Assignment of a mark to a participant within an event."""
    __tablename__ = "mark_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mark_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mark_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
