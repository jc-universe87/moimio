"""Allocation unit — a single slot within a category (Room A, Group 1, etc.)."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AllocationUnit(Base):
    __tablename__ = "allocation_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("allocation_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)  # v0.74: required; "uncapped" concept removed
    gender_restriction: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "male", "female", or null
    # v1.0.1e: optional single-mark restriction. When set, only participants
    # carrying this mark may be placed in the unit (the mark twin of
    # gender_restriction). FK SET NULL so deleting the mark quietly lifts the
    # restriction rather than orphaning it.
    mark_restriction: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mark_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # v1.0.1e: "keep as-is" flag. When true the unit is frozen on re-allocate —
    # its occupants stay, it receives no new placements, and clear/commit skip
    # it. Defaults false so existing units are untouched.
    is_kept: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("AllocationCategory", back_populates="units")
    allocations = relationship("Allocation", back_populates="unit", cascade="all, delete-orphan", lazy="selectin")
