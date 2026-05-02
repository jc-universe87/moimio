"""Custom field routes — manage organiser-defined registration fields."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.models.custom_field import CustomFieldDefinition
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate, CustomFieldResponse
from app.services.event_service import get_event_by_id
from app.api.deps import get_current_user, ensure_event_writable, require_event_admin_dep

logger = get_logger(__name__)
router = APIRouter(prefix="/api/events/{event_id}/custom-fields", tags=["custom-fields"])


@router.get("/", response_model=list[CustomFieldResponse])
async def list_custom_fields(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})
    result = await db.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
        .order_by(CustomFieldDefinition.sort_order, CustomFieldDefinition.created_at)
    )
    return list(result.scalars().all())


@router.get("/public", response_model=list[CustomFieldResponse])
async def list_custom_fields_public(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for registration form to fetch custom fields.

    v0.85 #16: filtered by show_in_form. Fields auto-created from a CSV
    import (show_in_form=False) are not surfaced on the public form —
    they're meant for People-page display only. Admins can flip the
    flag in the registration setup UI to surface them on the form.
    """
    result = await db.execute(
        select(CustomFieldDefinition)
        .where(
            CustomFieldDefinition.event_id == event_id,
            CustomFieldDefinition.show_in_form == True,  # noqa: E712
        )
        .order_by(CustomFieldDefinition.sort_order, CustomFieldDefinition.created_at)
    )
    return list(result.scalars().all())


@router.post("/", response_model=CustomFieldResponse, status_code=201)
async def create_custom_field(
    event_id: uuid.UUID,
    data: CustomFieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)

    options_json = None
    if data.options and data.field_type == "select":
        options_json = {"choices": data.options}

    field = CustomFieldDefinition(
        event_id=event_id,
        label=data.label,
        field_type=data.field_type,
        options=options_json,
        is_required=data.is_required,
        sort_order=data.sort_order,
        show_in_form=data.show_in_form,
    )
    db.add(field)
    await db.flush()
    await db.refresh(field)
    logger.info("custom_field_created", field_id=str(field.id), label=field.label)
    return field


@router.patch("/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(
    event_id: uuid.UUID,
    field_id: uuid.UUID,
    data: CustomFieldUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(
        select(CustomFieldDefinition).where(
            CustomFieldDefinition.id == field_id,
            CustomFieldDefinition.event_id == event_id,
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail={"key": "errors.custom_fields.not_found"})

    update_data = data.model_dump(exclude_unset=True)
    if "options" in update_data and update_data["options"] is not None:
        update_data["options"] = {"choices": update_data["options"]}
    for key, value in update_data.items():
        setattr(field, key, value)
    db.add(field)
    await db.flush()
    await db.refresh(field)
    return field


@router.delete("/{field_id}", status_code=204)
async def delete_custom_field(
    event_id: uuid.UUID,
    field_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(
        select(CustomFieldDefinition).where(
            CustomFieldDefinition.id == field_id,
            CustomFieldDefinition.event_id == event_id,
        )
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail={"key": "errors.custom_fields.not_found"})
    await db.delete(field)
    await db.flush()
    logger.info("custom_field_deleted", field_id=str(field_id))
