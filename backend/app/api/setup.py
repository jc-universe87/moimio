"""Setup routes — first-run wizard."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/status")
async def setup_status(db: AsyncSession = Depends(get_db)):
    """Returns whether first-run setup is needed (no users exist)."""
    result = await db.execute(select(func.count()).select_from(User))
    count = result.scalar()
    return {"needs_setup": count == 0}


class SetupInit(BaseModel):
    email: EmailStr
    full_name: str
    password: str


@router.post("/init", status_code=201)
async def setup_init(data: SetupInit, db: AsyncSession = Depends(get_db)):
    """Create the first super admin. Only works when no users exist."""
    result = await db.execute(select(func.count()).select_from(User))
    if result.scalar() > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.setup.already_completed"})

    if len(data.password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"key": "errors.auth.password_too_short"})

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.SUPER_ADMIN,
        can_manage_users=True,
        can_create_events=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role.value}
