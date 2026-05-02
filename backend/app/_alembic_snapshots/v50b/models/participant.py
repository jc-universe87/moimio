"""Participant model — registered attendees of events."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Text, Boolean, DateTime, Date, ForeignKey,
    Enum as SAEnum, func, Integer,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .._base import Base


class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )

    # ─── Required fields ───
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # ─── Fixed optional fields (organiser toggles) ───
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    church_organisation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ─── Participant free text ───
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ─── Group system ───
    group_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    group_code_categories: Mapped[list | None] = mapped_column(
        JSONB, nullable=True  # NULL = all categories; [uuid_str, ...] = specific
    )
    override_group_room: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # ─── Participant number (event-scoped sequential) ───
    participant_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )

    # ─── Registration & check-in ───
    registration_status: Mapped[RegistrationStatus] = mapped_column(
        SAEnum(RegistrationStatus, name="registration_status", create_constraint=True),
        nullable=False,
        default=RegistrationStatus.PENDING,
    )
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmation_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    checked_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ─── Language preference (for emails) ───
    preferred_language: Mapped[str] = mapped_column(String(10), nullable=False, default='en')

    # ─── GDPR soft delete ───
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ─── Timestamps ───
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ─── Relationships ───
    event = relationship("Event", back_populates="participants")
    custom_field_values = relationship(
        "CustomFieldValue", back_populates="participant", lazy="selectin"
    )

    @property
    def custom_fields(self) -> dict:
        """Return custom field values as {str(field_id): value} for API responses."""
        return {
            str(cfv.field_id): cfv.value
            for cfv in (self.custom_field_values or [])
            if cfv.value is not None
        }

    def __repr__(self) -> str:
        return f"<Participant {self.first_name} {self.last_name} ({self.registration_status.value})>"
