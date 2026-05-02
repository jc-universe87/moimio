"""Allocation category — organiser-defined grouping type per event."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .._base import Base


class AllocationCategory(Base):
    __tablename__ = "allocation_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    item_label: Mapped[str | None] = mapped_column(String(50), nullable=True)  # singular: "Room", "Group", "Session"
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False, default="exclusive")  # "exclusive" or "overlapping"
    has_capacity: Mapped[bool] = mapped_column(Boolean, default=False)
    has_gender_restriction: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=lambda: {
            "engine": {
                "use_group_codes": True,
                "group_remaining_by_gender": True,
                "split_oversized_groups": True,
            }
        }
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    units = relationship("AllocationUnit", back_populates="category", cascade="all, delete-orphan", lazy="selectin")
