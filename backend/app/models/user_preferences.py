"""UserPreferences — per-user display settings (language, date format, timezone)."""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        # v1.0.4zd (USER-1): CASCADE. A preferences row is theirs alone and
        # has no meaning without them. It had no ON DELETE clause, so the
        # default NO ACTION applied, and it is what made deleting any user
        # who had ever opened the settings panel fail with a raw 500.
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    date_format: Mapped[str] = mapped_column(
        String(20), default="DD/MM/YYYY", nullable=False
    )  # See VALID_DATE_FORMATS in api/user_preferences.py for full list.
    # String(20) accommodates the widest preset ("YYYY년 MM월 DD일", 13 chars).
    timezone: Mapped[str] = mapped_column(
        String(50), default="Europe/London", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserPreferences user={self.user_id} lang={self.language}>"
