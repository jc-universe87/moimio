"""User management routes — list, create, edit, deactivate, delete users."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.api.deps import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/users", tags=["users"])


def can_manage(current_user: User) -> bool:
    # v0.50j: EVENT_ADMIN role no longer exists. User management rights
    # now flow from the can_manage_users flag on any Staff user (Super
    # Admin has implicit access).
    return current_user.role == UserRole.SUPER_ADMIN or current_user.can_manage_users


def require_user_mgmt(current_user: User = Depends(get_current_user)) -> User:
    if not can_manage(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.users.insufficient_permissions"})
    return current_user


def user_out(u: User) -> dict:
    return {
        "id": str(u.id), "email": u.email, "full_name": u.full_name,
        "role": u.role.value, "is_active": u.is_active,
        "can_manage_users": u.can_manage_users,
        "can_create_events": u.can_create_events,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "staff"  # "super_admin" | "staff" (v0.50j: event_admin removed)
    can_manage_users: bool = False
    can_create_events: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    can_manage_users: Optional[bool] = None
    can_create_events: Optional[bool] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_mgmt),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return [user_out(u) for u in result.scalars().all()]


@router.post("/", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_mgmt),
):
    # Only super_admin can create another super_admin
    if data.role == "super_admin" and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"key": "errors.users.super_admin_only_creates_super"})

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"key": "errors.auth.email_taken"})

    if len(data.password) < 8:
        raise HTTPException(status_code=422, detail={"key": "errors.auth.password_too_short"})

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole(data.role),
        can_manage_users=data.can_manage_users,
        can_create_events=data.can_create_events,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("user_created", new_user_id=str(user.id), by=str(current_user.id))
    return user_out(user)


@router.patch("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_mgmt),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail={"key": "errors.auth.user_not_found"})

    # Cannot demote or edit another super_admin unless you are super_admin
    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"key": "errors.users.cannot_edit_super"})

    # Cannot promote to super_admin unless you are super_admin
    if data.role == "super_admin" and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"key": "errors.users.super_admin_only_grants_super"})

    if data.full_name is not None: user.full_name = data.full_name
    if data.role is not None: user.role = UserRole(data.role)
    if data.can_manage_users is not None: user.can_manage_users = data.can_manage_users
    if data.can_create_events is not None: user.can_create_events = data.can_create_events
    if data.is_active is not None: user.is_active = data.is_active

    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user_out(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user_mgmt),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail={"key": "errors.auth.user_not_found"})
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail={"key": "errors.users.cannot_delete_self"})
    if user.role == UserRole.SUPER_ADMIN and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"key": "errors.users.cannot_delete_super"})
    await db.delete(user)
    await db.flush()
