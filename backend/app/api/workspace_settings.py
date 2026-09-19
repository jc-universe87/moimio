"""Workspace settings (LEGAL-1): the installation-wide values an admin sets
from the screen.

Three routes.

  GET /api/workspace/public
      No auth. What the public registration form needs and nothing more:
      today, the organisation's privacy notice URL, or null.

  GET /api/admin/workspace/settings
  PUT /api/admin/workspace/settings
      Super admin only, the same gate as the rest of /api/admin/workspace.
      PUT rejects anything that is not an absolute http(s) URL with a
      translatable key, so the form can say what is wrong rather than
      saving nothing and saying nothing (FORM-2's table of silent forms is
      long enough).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.workspace_settings_service import (
    InvalidPrivacyNoticeUrl,
    get_privacy_notice_url,
    set_privacy_notice_url,
)

router = APIRouter(tags=["workspace_settings"])


class WorkspacePublicResponse(BaseModel):
    privacy_notice_url: str | None = None


class WorkspaceSettingsResponse(BaseModel):
    privacy_notice_url: str | None = None


class WorkspaceSettingsUpdate(BaseModel):
    # Optional so a client that sends only the fields it changed keeps
    # working when a second setting arrives. Today there is one.
    privacy_notice_url: str | None = None


def _require_super_admin(current_user: User) -> None:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"key": "errors.workspace.super_admin_only"},
        )


@router.get("/api/workspace/public", response_model=WorkspacePublicResponse)
async def get_workspace_public(db: AsyncSession = Depends(get_db)) -> WorkspacePublicResponse:
    """What the registration form shows a stranger. No auth."""
    return WorkspacePublicResponse(privacy_notice_url=await get_privacy_notice_url(db))


@router.get("/api/admin/workspace/settings", response_model=WorkspaceSettingsResponse)
async def get_workspace_settings_admin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceSettingsResponse:
    _require_super_admin(current_user)
    return WorkspaceSettingsResponse(privacy_notice_url=await get_privacy_notice_url(db))


@router.put("/api/admin/workspace/settings", response_model=WorkspaceSettingsResponse)
async def update_workspace_settings(
    body: WorkspaceSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceSettingsResponse:
    _require_super_admin(current_user)
    try:
        row = await set_privacy_notice_url(db, body.privacy_notice_url)
    except InvalidPrivacyNoticeUrl:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "key": "errors.workspace.privacy_url_invalid",
                "fields": {"privacy_notice_url": "errors.workspace.privacy_url_invalid"},
            },
        )
    await db.commit()
    return WorkspaceSettingsResponse(privacy_notice_url=row.privacy_notice_url)
