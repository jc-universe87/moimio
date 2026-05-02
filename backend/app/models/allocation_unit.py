"""Allocation unit — a single slot within a category (Room A, Group 1, etc.)."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, func
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
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("AllocationCategory", back_populates="units")
    allocations = relationship("Allocation", back_populates="unit", cascade="all, delete-orphan", lazy="selectin")
