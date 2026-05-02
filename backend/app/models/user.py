"""User model — organising team accounts (not participants)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum as SAEnum, DateTime, Boolean, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        # v0.50q: `values_callable` tells SQLAlchemy to use each enum
        # member's .value (lowercase) as the Postgres label, instead of
        # the default (member name — UPPERCASE). Brings DB labels in line
        # with Python values. Paired with migration 50q00000 which renames
        # existing UPPERCASE labels on already-deployed databases.
        SAEnum(
            UserRole, name="user_role", create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=UserRole.STAFF,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # v0.50j: Event Admin is no longer a system-wide role; it lives on
    # EventUserAssignment.role per event. System-level user capabilities
    # are now expressed as two boolean flags granted to Staff users by
    # Super Admin. Super Admin has both implicitly.
    can_manage_users: Mapped[bool] = mapped_column(Boolean, default=False)
    can_create_events: Mapped[bool] = mapped_column(Boolean, default=False)
    password_reset_token: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
