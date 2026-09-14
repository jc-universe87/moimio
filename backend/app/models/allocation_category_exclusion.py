"""Allocation category exclusion — a participant the engine must keep out of one group type.

v1.0.4i: one row per (group type, participant) pair the organiser has
excluded. Both FKs cascade: an exclusion has no meaning once either side
is gone. `created_by` is a plain nullable UUID, not an FK, so deleting a
user never blocks; the audit surface for who did it is allocation_events
(event_type exclude / include).
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AllocationCategoryExclusion(Base):
    __tablename__ = "allocation_category_exclusions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    allocation_category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("allocation_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("allocation_category_id", "participant_id", name="uq_category_exclusion_category_participant"),
    )
