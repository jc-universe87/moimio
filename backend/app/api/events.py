"""Event routes — CRUD and field config management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.models.event_assignment import EventUserAssignment
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse,
    FieldConfigItem, FieldConfigResponse,
)
from app.services.event_service import (
    create_event, get_event_by_id, list_events, update_event,
    get_field_configs, update_field_configs,
)
from app.api.deps import get_current_user, require_role, ensure_event_writable, require_can_create_events, require_event_admin_dep

logger = get_logger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])


# ─── Public endpoints (no auth) ───

@router.get("/{event_id}/public", response_model=EventResponse)
async def get_event_public(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public event info for the registration form. No auth required."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    return event


@router.get("/{event_id}/fields/public", response_model=list[FieldConfigResponse])
async def get_event_fields_public(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Public field config for the registration form. No auth required."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    configs = await get_field_configs(db, event_id)
    return configs


# ─── Authenticated endpoints ───


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_new_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_can_create_events()),
):
    """Create a new event. Super Admin or Staff with can_create_events flag.

    v0.51: when `data.copy_from_event_id` is set, the caller must have
    access to the source event (Super Admin always; staff via assignment).
    The actual config copy is done server-side in create_event → duplicate_event_config.
    """
    if data.copy_from_event_id is not None:
        await _require_source_access(db, data.copy_from_event_id, current_user)
    event = await create_event(db, data, created_by=current_user.id)
    logger.info(
        "event_created",
        event_id=str(event.id),
        name=event.name,
        created_by=str(current_user.id),
        copied_from=str(data.copy_from_event_id) if data.copy_from_event_id else None,
    )
    return event


async def _require_source_access(
    db: AsyncSession, source_event_id: uuid.UUID, current_user: User,
) -> None:
    """Verify caller can read the source event. Super Admin always; staff
    need an EventUserAssignment row. Raises 403/404 as appropriate."""
    source = await get_event_by_id(db, source_event_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.source_not_found"})
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    res = await db.execute(
        select(EventUserAssignment.id)
        .where(
            EventUserAssignment.event_id == source_event_id,
            EventUserAssignment.user_id == current_user.id,
        )
    )
    if res.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"key": "errors.event.no_source_access"},
        )


@router.get("/{event_id}/duplicate/counts")
async def get_duplicate_counts(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Config-table counts for the duplicate preview page. v0.51.

    Returns the number of rows that would be copied if the caller
    duplicated this event: marks, registration form fields, custom
    fields, allocation categories, staff assignments.
    """
    await _require_source_access(db, event_id, current_user)
    from app.services.event_service import duplicate_counts
    return await duplicate_counts(db, event_id)


@router.get("/", response_model=list[EventResponse])
async def get_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List events visible to the current user.

    v50c-3c-2c: staff (including event admins) see only events they are
    assigned to via EventUserAssignment. Super admins see all.

    v0.50h: each event includes `participant_count` and `checked_in_count`
    for the redesigned list's at-a-glance metric column. Computed in two
    GROUP BY queries rather than per-event subqueries to keep the list
    endpoint snappy even with many events. Cancelled and soft-deleted
    participants are excluded from both counts.
    """
    from app.models.participant import Participant, RegistrationStatus
    from sqlalchemy import func

    events = await list_events(db)
    if current_user.role != UserRole.SUPER_ADMIN:
        # Staff + event admins — scope to their assigned events.
        assign_q = await db.execute(
            select(EventUserAssignment.event_id)
            .where(EventUserAssignment.user_id == current_user.id)
        )
        assigned_ids = {row[0] for row in assign_q.all()}
        events = [e for e in events if e.id in assigned_ids]

    if not events:
        return []

    event_ids = [e.id for e in events]

    # Single GROUP BY for participant counts across all listed events.
    count_q = await db.execute(
        select(
            Participant.event_id,
            func.count(Participant.id).label("total"),
            func.count(Participant.id).filter(Participant.checked_in == True).label("checked_in"),
        )
        .where(
            Participant.event_id.in_(event_ids),
            Participant.deleted_at.is_(None),
            Participant.registration_status != RegistrationStatus.CANCELLED,
        )
        .group_by(Participant.event_id)
    )
    counts_by_event: dict = {row[0]: (row[1], row[2]) for row in count_q.all()}

    # Serialise each event with its counts. Events without rows in the
    # count table (none registered yet) get zero rather than None.
    out = []
    for e in events:
        total, checked_in = counts_by_event.get(e.id, (0, 0))
        r = EventResponse.model_validate(e).model_copy(update={
            "participant_count": total,
            "checked_in_count": checked_in,
        })
        out.append(r)
    return out


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get event by ID."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def patch_event(
    event_id: uuid.UUID,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Update an event. Event Admin only."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    event = await update_event(db, event, data)
    logger.info("event_updated", event_id=str(event.id), updated_by=str(current_user.id))
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_route(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """Hard-delete an event and everything that belongs to it.

    v0.50g-2: Super Admin only. Destructive, irreversible. The frontend
    UI layers a type-to-confirm dialog and recommends a backup download
    before triggering this.

    v1.0.0h-1: also emits an `event.deleted` webhook (handled inside
    the `delete_event` service in the same DB transaction). The
    decision of whether a deletion warrants a refund is a SaaS-side
    billing rule, not a CE rule — CE simply tells SaaS the event
    was deleted and lets SaaS apply its own timing policy.
    """
    from app.services.event_service import delete_event
    ok = await delete_event(db, event_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    logger.info("event_deleted", event_id=str(event_id), deleted_by=str(current_user.id))
    return None


# ─── Archive / unarchive (v0.50i) ─────────────────────────────────────
#
# Super Admin only. Archived events are read-only to EVERYONE (Super
# Admin too — enforced by ensure_event_writable on mutation routes),
# and are hidden from the default events-list groupings in the UI.
# Editing an archived event requires unarchive → edit → re-archive.

@router.post("/{event_id}/archive", response_model=EventResponse)
async def archive_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """Archive an event. Super Admin only. Reversible via /unarchive."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    event.is_archived = True
    await db.flush()
    await db.refresh(event)
    logger.info("event_archived", event_id=str(event_id), by=str(current_user.id))
    return event


@router.post("/{event_id}/unarchive", response_model=EventResponse)
async def unarchive_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
):
    """Unarchive an event, restoring normal read-write access. Super Admin only."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    event.is_archived = False
    await db.flush()
    await db.refresh(event)
    logger.info("event_unarchived", event_id=str(event_id), by=str(current_user.id))
    return event


# ─── Setup hub confirm / unconfirm ───
#
# These wrap the confirmed flags with a cleaner API. The frontend Setup hub
# calls these when the user taps "Save & close" or edits a confirmed card.

@router.post("/{event_id}/setup/confirm/{card}", response_model=EventResponse)
async def confirm_setup_card(
    event_id: uuid.UUID,
    card: str,  # 'details' | 'registration'
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Mark a Setup-hub card as confirmed by the organiser."""
    if card not in ("details", "registration"):
        raise HTTPException(status_code=400, detail={"key": "errors.event.unknown_card"})
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    # Build patch with ONLY the relevant flag. Passing None for the other
    # field would end up writing NULL to a NOT NULL column because Pydantic
    # treats explicit None as "set" for model_dump(exclude_unset=True).
    field = "details_confirmed" if card == "details" else "registration_confirmed"
    patch = EventUpdate(**{field: True})
    event = await update_event(db, event, patch)
    logger.info("setup_card_confirmed", event_id=str(event_id), card=card, by=str(current_user.id))
    return event


@router.post("/{event_id}/setup/unconfirm/{card}", response_model=EventResponse)
async def unconfirm_setup_card(
    event_id: uuid.UUID,
    card: str,  # 'details' | 'registration'
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Roll a Setup-hub card back to unconfirmed (undo the tick)."""
    if card not in ("details", "registration"):
        raise HTTPException(status_code=400, detail={"key": "errors.event.unknown_card"})
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    field = "details_confirmed" if card == "details" else "registration_confirmed"
    patch = EventUpdate(**{field: False})
    event = await update_event(db, event, patch)
    logger.info("setup_card_unconfirmed", event_id=str(event_id), card=card, by=str(current_user.id))
    return event


# ─── Open registration (gated) ───
#
# Spec §3 gate rules: Details AND Registration must be confirmed before
# registration can be opened. This endpoint enforces the gate server-side;
# the Setup hub UI enforces it client-side too, but the server has final say.
#
# NOTE: The generic PATCH /events/{id} path remains un-gated in v50b-1 for
# backward compatibility with the v45 EventDetailPage which calls PATCH to
# change status. v50b-2 (Setup hub landing) will migrate to these dedicated
# endpoints and the PATCH path can then enforce the gate too.

@router.post("/{event_id}/registration/open", response_model=EventResponse)
async def open_registration(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Open registration for this event. Gated on both confirmed flags."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    if not (event.details_confirmed and event.registration_confirmed):
        raise HTTPException(
            status_code=409,
            detail={"key": "errors.event.cards_not_confirmed"},
        )
    event = await update_event(db, event, EventUpdate(status="open"))
    logger.info("registration_opened", event_id=str(event_id), by=str(current_user.id))
    return event


@router.post("/{event_id}/registration/close", response_model=EventResponse)
async def close_registration(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Close registration for this event."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    event = await update_event(db, event, EventUpdate(status="closed"))
    logger.info("registration_closed", event_id=str(event_id), by=str(current_user.id))
    return event


# ─── Field Configs ───

@router.get("/{event_id}/fields", response_model=list[FieldConfigResponse])
async def get_event_fields(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Get registration form field configuration for an event."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    configs = await get_field_configs(db, event_id)
    return configs


@router.put("/{event_id}/fields", response_model=list[FieldConfigResponse])
async def set_event_fields(
    event_id: uuid.UUID,
    configs: list[FieldConfigItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Set registration form field configuration. Event Admin only."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    await ensure_event_writable(db, event_id, current_user)
    updated = await update_field_configs(db, event_id, configs)
    logger.info("field_configs_updated", event_id=str(event_id), updated_by=str(current_user.id))
    return updated


# ─── Email ───

@router.post("/{event_id}/test-email")
async def send_test_email(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_event_admin_dep()),
):
    """Send a test email to the current admin user to verify SMTP config.

    v0.61b: delegates HTML rendering to app.core.email.render_smtp_test_email
    so the test email uses the same shell (dark-mode safe, mobile-responsive,
    plain-text alt) as every other transactional email we send.
    """
    from app.core.email import send_email, render_smtp_test_email
    from app.core.config import get_settings
    settings = get_settings()

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail={"key": "errors.event.not_found"})

    if not settings.smtp_enabled:
        raise HTTPException(status_code=400, detail={"key": "errors.smtp.not_configured"})

    event_settings = event.settings or {}
    from_name = event_settings.get("email_from_name", settings.smtp_from_name)
    reply_to = event_settings.get("email_reply_to", "")

    subject, html, text = render_smtp_test_email(
        event_name=event.name,
        from_name=from_name,
        reply_to=reply_to,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
    )

    success = send_email(current_user.email, subject, html, text)
    if success:
        return {"detail": f"Test email sent to {current_user.email}"}
    else:
        raise HTTPException(status_code=500, detail={"key": "errors.smtp.test_failed"})
