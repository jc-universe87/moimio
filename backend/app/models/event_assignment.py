"""Event assignments — per-event role and permissions for users.

v0.50e-1b: StaffGroup removed. Permissions now live directly on the
assignment, giving each user their own per-event permissions map. The
"Copy from [user]" convenience in the UI replaces the shared-group pattern.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, JSON, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EventUserAssignment(Base):
    """Assigns a user to an event with a role and per-user permissions.

    role:
      - "event_admin" — full access, permissions dict ignored
      - "staff"       — honoured by permissions dict

    permissions (staff only, v0.50e-1d final shape):
      people:   "read" | "write" | null
      organise: "read" | "write" | null
      checkin:  "write" | null
      reports:  "read" | null
    """
    __tablename__ = "event_user_assignments"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="staff")  # "event_admin" | "staff"
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
