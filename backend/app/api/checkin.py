"""Check-in routes — manage check-in desk fields and values."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.models.checkin_field import CheckInField
from app.models.checkin_value import CheckInValue
from app.api.deps import get_current_user, ensure_event_writable, require_event_admin_dep
from app.services.permissions import get_event_permissions, has_write

logger = get_logger(__name__)
router = APIRouter(tags=["checkin"])


class CheckInFieldCreate(BaseModel):
    field_name: str
    sort_order: int = 0


class CheckInToggle(BaseModel):
    participant_id: uuid.UUID
    field_id: uuid.UUID
    checked: bool


# ─── Fields ───

@router.get("/api/events/{event_id}/checkin-fields/")
async def list_checkin_fields(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CheckInField)
        .where(CheckInField.event_id == event_id)
        .order_by(CheckInField.sort_order, CheckInField.created_at)
    )
    fields = list(result.scalars().all())
    return [
        {"id": f.id, "event_id": f.event_id, "field_name": f.field_name, "sort_order": f.sort_order}
        for f in fields
    ]


@router.post("/api/events/{event_id}/checkin-fields/", status_code=201)
async def create_checkin_field(
    event_id: uuid.UUID,
    data: CheckInFieldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    field = CheckInField(event_id=event_id, field_name=data.field_name, sort_order=data.sort_order)
    db.add(field)
    await db.flush()
    await db.refresh(field)
    return {"id": field.id, "event_id": field.event_id, "field_name": field.field_name, "sort_order": field.sort_order}


@router.delete("/api/events/{event_id}/checkin-fields/{field_id}", status_code=204)
async def delete_checkin_field(
    event_id: uuid.UUID,
    field_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    await ensure_event_writable(db, event_id, current_user)
    result = await db.execute(select(CheckInField).where(CheckInField.id == field_id, CheckInField.event_id == event_id))
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(status_code=404, detail={"key": "errors.checkin.field_not_found"})
    # Delete associated values first
    await db.execute(delete(CheckInValue).where(CheckInValue.field_id == field_id))
    await db.delete(field)
    await db.flush()


# ─── Values ───

@router.get("/api/events/{event_id}/checkin-values/")
async def get_checkin_values(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CheckInValue).where(CheckInValue.event_id == event_id)
    )
    values = list(result.scalars().all())
    # Return as { "participant_id:field_id": checked }
    out = {}
    for v in values:
        key = f"{v.participant_id}:{v.field_id}"
        out[key] = v.checked
    return out


@router.post("/api/events/{event_id}/checkin-values/")
async def toggle_checkin_value(
    event_id: uuid.UUID,
    data: CheckInToggle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_event_writable(db, event_id, current_user)
    # v0.50e-1a: staff with any check-in permission can tick off columns.
    # Read-only access has been removed in this simplified model.
    if current_user.role == UserRole.STAFF:
        perms = await get_event_permissions(db, current_user, event_id)
        if perms is None or not has_write(perms, "checkin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.checkin.permission_required"})
    result = await db.execute(
        select(CheckInValue).where(
            CheckInValue.participant_id == data.participant_id,
            CheckInValue.field_id == data.field_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.checked = data.checked
    else:
        val = CheckInValue(
            event_id=event_id,
            participant_id=data.participant_id,
            field_id=data.field_id,
            checked=data.checked,
        )
        db.add(val)
    await db.flush()
    # v1.0-pre #8: broadcast tick-field changes for live cross-device sync.
    try:
        from app.core.pubsub import broker
        await broker.publish(
            f"checkin:{event_id}",
            {
                "type": "checkin_value_changed",
                "participant_id": str(data.participant_id),
                "field_id": str(data.field_id),
                "checked": bool(data.checked),
            },
        )
    except Exception:
        # Best-effort; DB write already succeeded.
        pass
    return {"participant_id": str(data.participant_id), "field_id": str(data.field_id), "checked": data.checked}
