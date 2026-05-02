"""Custom fields — EAV pattern for organiser-defined registration fields."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CustomFieldDefinition(Base):
    """Organiser-defined field: label, type, options. One per event per custom question."""
    __tablename__ = "custom_field_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="text"
    )  # text | number | select | boolean | date
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_required: Mapped[bool] = mapped_column(default=False)
    # v0.85 #16: gates whether this field appears on the PUBLIC registration
    # form. True (default) for fields created via the registration setup
    # UI — they're meant to be filled in by registrants. False for fields
    # auto-created from CSV-import unknown columns — those exist purely
    # to surface admin-managed data on the People page; surfacing them on
    # the public form would be confusing (registrants can't see them yet
    # nor know what to type). Admins can flip the flag in the registration
    # setup UI later if they want it on the form too.
    show_in_form: Mapped[bool] = mapped_column(default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    values = relationship("CustomFieldValue", back_populates="field_definition", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CustomFieldDefinition {self.label} ({self.field_type})>"


class CustomFieldValue(Base):
    """Participant's answer to a custom field. Stored as text, cast by application."""
    __tablename__ = "custom_field_values"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False, index=True
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("custom_field_definitions.id"), nullable=False, index=True
    )
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    participant = relationship("Participant", back_populates="custom_field_values")
    field_definition = relationship("CustomFieldDefinition", back_populates="values")

    def __repr__(self) -> str:
        return f"<CustomFieldValue field={self.field_id} value={self.value}>"
