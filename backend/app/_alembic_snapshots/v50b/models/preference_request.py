"""ParticipantPreferenceRequest — who a participant wants to be grouped with."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .._base import Base


class ParticipantPreferenceRequest(Base):
    __tablename__ = "participant_preference_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False, index=True
    )

    # Who they want to be with
    preferred_participant_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True  # if target is already registered
    )
    preferred_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_details: Mapped[str | None] = mapped_column(
        Text, nullable=True  # DOB, hometown, church — for manual organiser matching
    )

    # Scope: "all" or JSON array of category UUIDs
    category_scope: Mapped[dict | list | None] = mapped_column(
        JSONB, nullable=True, default=lambda: "all"
    )

    # Resolution
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    participant = relationship("Participant", foreign_keys=[participant_id])
