"""Allocation category — organiser-defined grouping type per event."""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AllocationCategory(Base):
    __tablename__ = "allocation_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    item_label: Mapped[str | None] = mapped_column(String(50), nullable=True)  # singular: "Room", "Group", "Session"
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False, default="exclusive")  # "exclusive" or "overlapping"
    has_capacity: Mapped[bool] = mapped_column(Boolean, default=False)
    # v0.74 DEPRECATED: engine reads unit-level gender_restriction directly.
    # Column kept for backward compatibility; will be dropped in v1.0 cut.
    has_gender_restriction: Mapped[bool] = mapped_column(Boolean, default=False)
    # v0.74: when True, group_code clusters claim their entire allocated unit
    # — no other participants can be placed there even if there's leftover
    # capacity. Default False preserves pre-v0.74 behaviour (clusters share
    # units with non-cluster participants).
    exclusive_group_codes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    # v50c-3: allocation lifecycle — Confirmed when the organiser has locked
    # the allocations for this category. Any edit to an allocation in a
    # confirmed category silently flips this back to False (§12.3 re-open rule).
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
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
