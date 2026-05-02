"""User model — organising team accounts (not participants)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum as SAEnum, DateTime, Boolean, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .._base import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    EVENT_ADMIN = "event_admin"
    STAFF = "staff"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
        default=UserRole.EVENT_ADMIN,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Delegation: event_admin granted user-management rights by super_admin
    can_manage_users: Mapped[bool] = mapped_column(Boolean, default=False)
    password_reset_token: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
