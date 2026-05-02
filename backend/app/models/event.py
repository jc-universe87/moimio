"""Event model."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import String, Text, Date, DateTime, Boolean, Enum as SAEnum, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # IANA timezone name, e.g. 'Europe/London'. Used for sub-state timing
    # decisions (v50c+). Stored even when unused to keep the data right.
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="UTC"
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[EventStatus] = mapped_column(
        # v0.50q: see note on UserRole — same pattern, lowercase labels.
        SAEnum(
            EventStatus, name="event_status", create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=EventStatus.DRAFT,
    )
    # Setup hub gate flags (§3 gate rules).
    # Organiser must explicitly confirm each required card before the
    # "Open registration" gate unlocks. Edits silently unconfirm (behaviour
    # (a) from v50b design discussion — mirrors §6.2.6 pattern).
    details_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    registration_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    # v0.50i: archive flag. Orthogonal to `status` — an event can be
    # archived regardless of its registration state. Archived events are
    # read-only to everyone except Super Admin (enforced by the
    # require_event_writable dependency on mutation routes).
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    settings: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=lambda: {
            "published_notes_writers": ["event_admin"],
            "allow_team_leader_notes": False,
            "allow_checkin_staff_notes": False,
            "require_email_confirmation": False,
        }
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    participants = relationship("Participant", back_populates="event", lazy="selectin")
    field_configs = relationship("EventFieldConfig", back_populates="event", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Event {self.name} ({self.status.value})>"
