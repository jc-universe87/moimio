"""Custom field routes — manage organiser-defined registration fields."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.models.custom_field import CustomFieldDefinition
from app.schemas.custom_field import (
    CustomFieldCreate, CustomFieldUpdate, CustomFieldReorder, CustomFieldResponse,
)
from app.services.event_service import get_event_by_id
from app.services.field_conditions import (
    INFO, ConditionError, check_rules, clean_rule, dependants_of, load_defs,
    refresh_event_info_marks,
)
from app.api.deps import get_current_user, ensure_event_writable, require_event_admin_dep

logger = get_logger(__name__)
router = APIRouter(prefix="/api/events/{event_id}/custom-fields", tags=["custom-fields"])


def _refuse(err: ConditionError):
    raise HTTPException(status_code=409, detail={"key": err.key})


def _options_for(field_type: str, choices: list[str] | None, info_text: str | None) -> dict | None:
    if field_type == "select" and choices:
        return {"choices": choices}
    if field_type == INFO:
        return {"text": (info_text or "").strip()}
    return None


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

    defs = await load_defs(db, event_id)
    sort_order = data.sort_order
    if sort_order is None:
        sort_order = max((d.sort_order or 0 for d in defs), default=-1) + 1
    try:
        rule = clean_rule(data.show_if)
    except ConditionError as err:
        _refuse(err)

    field = CustomFieldDefinition(
        event_id=event_id,
        label=data.label,
        field_type=data.field_type,
        options=_options_for(data.field_type, data.options, data.info_text),
        # Nobody fills in an info text, so it can never be required.
        is_required=data.is_required and data.field_type != INFO,
        sort_order=sort_order,
        show_in_form=data.show_in_form,
        show_if=rule,
    )
    db.add(field)
    await db.flush()
    await db.refresh(field)
    try:
        check_rules(await load_defs(db, event_id))
    except ConditionError as err:
        await db.rollback()
        _refuse(err)
    if field.field_type == INFO and rule is not None:
        await refresh_event_info_marks(db, event_id)
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
    info_text = update_data.pop("info_text", None)
    if "options" in update_data and update_data["options"] is not None:
        update_data["options"] = {"choices": update_data["options"]}
    if "show_if" in update_data:
        try:
            update_data["show_if"] = clean_rule(update_data["show_if"])
        except ConditionError as err:
            _refuse(err)
    was_info = field.field_type == INFO
    for key, value in update_data.items():
        setattr(field, key, value)
    if field.field_type == INFO:
        if info_text is not None or not (field.options or {}).get("text"):
            field.options = _options_for(INFO, None, info_text)
        field.is_required = False
    elif was_info:
        # No longer an info text: its text and its "applies" marks go, so a
        # mark never reads as somebody's answer.
        if field.options and "choices" not in field.options:
            field.options = None
        field.values.clear()  # delete-orphan: the rows go on flush
    db.add(field)
    await db.flush()
    await db.refresh(field)
    # A rule may point at this field, or this field's rule may have changed:
    # either way the whole event's rules must still hold.
    try:
        check_rules(await load_defs(db, event_id))
    except ConditionError as err:
        await db.rollback()
        _refuse(err)
    await refresh_event_info_marks(db, event_id)
    return field


@router.post("/reorder", response_model=list[CustomFieldResponse])
async def reorder_custom_fields(
    event_id: uuid.UUID,
    data: CustomFieldReorder,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Save a new field order. Refused when a field would end up above the
    field its rule depends on, so a rule never points further down the form."""
    await ensure_event_writable(db, event_id, current_user)
    defs = await load_defs(db, event_id)
    by_id = {d.id: d for d in defs}
    if len(data.field_ids) != len(by_id) or set(data.field_ids) != set(by_id):
        raise HTTPException(status_code=422, detail={"key": "errors.custom_fields.reorder_mismatch"})
    new_order = [by_id[i] for i in data.field_ids]
    try:
        check_rules(new_order)
    except ConditionError as err:
        _refuse(err)
    for i, d in enumerate(new_order):
        d.sort_order = i
    await db.flush()
    await refresh_event_info_marks(db, event_id)
    return new_order


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
    # v1.0.7: a field another field's rule depends on cannot go first.
    if dependants_of(await load_defs(db, event_id), field.id):
        raise HTTPException(status_code=409, detail={"key": "errors.custom_fields.has_dependants"})
    await db.delete(field)
    await db.flush()
    logger.info("custom_field_deleted", field_id=str(field_id))
