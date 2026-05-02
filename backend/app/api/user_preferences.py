"""User preferences routes — language, date format, timezone."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/auth/me/preferences", tags=["auth"])


class PreferencesResponse(BaseModel):
    language: str
    date_format: str
    timezone: str

    model_config = {"from_attributes": True}


class PreferencesUpdate(BaseModel):
    language: str | None = None
    date_format: str | None = None
    timezone: str | None = None


VALID_DATE_FORMATS = ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]
VALID_LANGUAGES = ["en", "de", "ko", "es", "pt-BR", "fr"]


@router.get("/", response_model=PreferencesResponse)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's display preferences."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        # Create defaults
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)
    return prefs


@router.patch("/", response_model=PreferencesResponse)
async def update_preferences(
    data: PreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's display preferences."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)

    update_data = data.model_dump(exclude_unset=True)

    if "date_format" in update_data and update_data["date_format"] not in VALID_DATE_FORMATS:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail={"key": "errors.user_preferences.invalid_date_format", "params": {"values": ", ".join(VALID_DATE_FORMATS)}})

    if "language" in update_data and update_data["language"] not in VALID_LANGUAGES:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail={"key": "errors.user_preferences.invalid_language", "params": {"values": ", ".join(VALID_LANGUAGES)}})

    for key, value in update_data.items():
        setattr(prefs, key, value)
    db.add(prefs)
    await db.flush()
    await db.refresh(prefs)
    return prefs
