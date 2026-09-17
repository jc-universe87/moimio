"""ParticipantPreferenceRequest — who a participant wants to be grouped with."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


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

    # RETIRED in v1.0.4r, and unread from that release on.
    #
    # "all", or a JSON array of group type ids. Nothing ever enforced it: it
    # appeared nowhere in the engine or the allocation service, the
    # registration page never rendered a selector for it, and the one screen
    # that displayed a list value showed raw ids. Every row takes the default
    # from here on.
    #
    # The column stays for one release for rollback safety and is dropped
    # after v1.0.5 (see BACKLOG ARCH-5).
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
