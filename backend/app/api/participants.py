"""Participant routes — public registration and admin management."""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.email import send_confirmation_email, send_registration_receipt
from app.core.urls import get_app_base_url
from app.models.user import User, UserRole
from app.models.participant import RegistrationStatus
from app.models.custom_field import CustomFieldDefinition
from app.schemas.participant import (
    ParticipantRegister, ParticipantUpdate, ParticipantResponse,
    GroupCodeUpdate, CheckInRequest,
)
from app.services.participant_service import (
    register_participant, get_participant_by_id, list_participants,
    update_participant, update_group_code, check_in_participant,
    soft_delete_participant, confirm_participant, maybe_signal_over_cap,
)
from app.services.event_service import get_event_by_id
from app.api.deps import get_current_user, require_role, ensure_event_writable, ensure_event_admin
from app.services.permissions import get_event_permissions, has_read, has_write

logger = get_logger(__name__)

router = APIRouter(tags=["participants"])


# ─── Public registration (no auth) ───

@router.post(
    "/api/events/{event_id}/register",
    response_model=ParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def public_register(
    request: Request,
    event_id: uuid.UUID,
    data: ParticipantRegister,
    db: AsyncSession = Depends(get_db),
):
    """Public registration form submission. No authentication required."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})

    # v0.50i: archived events reject new registrations regardless of
    # their open/closed status. No user context here, so we can't defer
    # to ensure_event_writable (which has a Super Admin bypass). For
    # public registration there's no bypass — archived means closed.
    if event.is_archived:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"key": "errors.event.archived"},
        )

    if event.status.value != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.event.registration_closed"},
        )

    if not data.gdpr_consent:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"key": "errors.participant.gdpr_required"},
        )

    # Check if event requires email confirmation
    event_settings = event.settings or {}
    require_confirmation = event_settings.get("require_email_confirmation", False)

    participant = await register_participant(
        db, event_id, data, require_confirmation=require_confirmation
    )
    logger.info(
        "participant_registered",
        event_id=str(event_id),
        participant_id=str(participant.id),
        confirmation_required=require_confirmation,
    )

    # v1.0.0y: signal once if this registration pushed the active roster
    # past the configured participant cap. No-op when no cap is set.
    await maybe_signal_over_cap(db, event_id)

    # Send email (non-blocking — log failures but don't fail registration)
    lang = data.preferred_language or 'en'
    if require_confirmation and participant.confirmation_token:
        # v0.61b-2: derive the public base URL from the incoming request
        # (Caddy's forwarded headers). Gives the right link for any
        # domain the request came in on — self-hosters on their own
        # domain, multi-domain SaaS, LAN-IP deploys all work unchanged.
        base = get_app_base_url(request)
        confirmation_url = f"{base}/confirm/{participant.confirmation_token}"
        send_confirmation_email(
            to_email=data.email,
            first_name=data.first_name,
            event_name=event.name,
            confirmation_url=confirmation_url,
            lang=lang,
        )
    else:
        send_registration_receipt(
            to_email=data.email,
            first_name=data.first_name,
            event_name=event.name,
            group_code=participant.group_code,
            lang=lang,
        )

    return participant


@router.get("/api/participants/confirm/{token}")
async def confirm_registration(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — process an email confirmation link.

    v0.70d-2b-1 (R7): returns a structured response so the frontend can
    render three honest states instead of silently treating stale tokens
    as success:

      ``{"state": "fresh",   "status": "confirmed"}``  — just confirmed.
      ``{"state": "already", "status": "confirmed"}``  — was already
                                                          confirmed; no-op
                                                          idempotent visit.
      ``{"state": "invalid"}`` — token doesn't match, is stale, or the
                                  participant is cancelled. HTTP 404.

    The receipt email is only sent on 'fresh' — sending it on every
    re-visit would spam users who clicked an old link or bookmarked the
    page. On 'already' the user is calmly told they're set; on 'invalid'
    the UI suggests re-registering or contacting the organiser.
    """
    participant, state = await confirm_participant(db, token)

    if state == "invalid":
        # Keep the 404 status code so crawlers / monitoring tools see
        # a failure, while the structured body gives the frontend
        # enough detail to render the right copy.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"state": "invalid"},
        )

    if state == "fresh":
        logger.info("participant_confirmed", participant_id=str(participant.id))
        # Send confirmed receipt using the participant's stored language.
        # Only on the fresh branch — re-visits never re-send.
        event = await get_event_by_id(db, participant.event_id)
        if event:
            send_registration_receipt(
                to_email=participant.email,
                first_name=participant.first_name,
                event_name=event.name,
                group_code=participant.group_code,
                lang=getattr(participant, 'preferred_language', 'en') or 'en',
            )
    else:  # state == "already"
        logger.info(
            "participant_confirm_revisit",
            participant_id=str(participant.id),
        )

    return {"state": state, "status": "confirmed"}


# ─── Admin participant management ───

@router.get(
    "/api/events/{event_id}/participants",
    response_model=list[ParticipantResponse],
)
async def get_event_participants(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all participants for an event. Requires at least people:read permission."""
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    # Check permissions for staff.
    # v0.50e-1a: allow either people:read OR any check-in access, since
    # check-in staff legitimately need the participant list to do their
    # job. The UI (CheckInPanel) only exposes name + selected columns
    # they've enabled. Previously: people:read OR checkin:read; now the
    # latter collapses to any checkin perm.
    # v0.70d-3c-8a: also allow organise:read OR reports:read. Allocators
    # genuinely need to know who they're allocating; reports viewers
    # need participant data to read stats. Without this, OrganiseDashboard
    # and ReportsPanel both hard-fail to load for staff with only those
    # perms — even though the surfaces themselves render fine. The
    # frontend continues to gate write actions; this list endpoint is
    # the read-only seed for any participant-aware view.
    if current_user.role == UserRole.STAFF:
        perms = await get_event_permissions(db, current_user, event_id)
        # v0.70d-3c-9: distinguish "no perms at all" from "wrong perm
        # for this surface". A staff user assigned to an event but
        # without any permissions configured yet should see a setup
        # message, not an access-denied error.
        if perms is None or len([k for k, v in perms.items() if v and v != 'none']) == 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.participant.no_event_perms"})
        # v0.70d-3c-9: marks-only / staff-only perms also imply needing
        # the participant list to do their job (mark assignment, staff
        # role admin both reference participant data).
        # v0.70d-3c-11: "staff" is not a recognized view in
        # services/permissions.py and not offered by the
        # EventAssignmentsPanel UI — has_read(perms, "staff") was
        # always returning False. Removed.
        has_any_participant_relevant_perm = (
            has_read(perms, "people")
            or has_read(perms, "checkin")
            or has_read(perms, "organise")
            or has_read(perms, "reports")
            or has_read(perms, "marks")
        )
        if not has_any_participant_relevant_perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.participant.no_list_access"})
    participants = await list_participants(db, event_id)
    return participants


@router.get(
    "/api/participants/{participant_id}",
    response_model=ParticipantResponse,
)
async def get_participant(
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single participant by ID."""
    participant = await get_participant_by_id(db, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.participant.not_found"})
    return participant


@router.patch(
    "/api/participants/{participant_id}",
    response_model=ParticipantResponse,
)
async def patch_participant(
    participant_id: uuid.UUID,
    data: ParticipantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a participant. Event Admin for this event, Super Admin, or staff with people:write."""
    participant = await get_participant_by_id(db, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.participant.not_found"})
    # v0.70d-3c-9: widen from event_admin-only to allow staff with
    # people:write to edit participant data. Editing covers names,
    # email, group_code, custom fields, status changes. Deletion
    # stays event_admin-only on its own endpoint.
    if current_user.role == UserRole.STAFF:
        perms = await get_event_permissions(db, current_user, participant.event_id)
        if perms is None or not has_write(perms, "people"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.participant.no_write_access"})
    else:
        await ensure_event_admin(db, participant.event_id, current_user)
    await ensure_event_writable(db, participant.event_id, current_user)
    participant = await update_participant(db, participant, data)

    # v0.70d-2a-2: auto-remove allocations when participant is
    # cancelled. Was a raw `DELETE FROM allocation WHERE participant_id=?`
    # (added pre-v0.60a), which silently wiped live memberships without
    # touching the append-only allocation_events table — breaking the
    # audit trail's premise that every assign/unassign is recorded.
    # Now routes through `unassign_all_for_participant`, which iterates
    # each allocation, emits an `unassign` event with source
    # `participant_cancelled`, and unconfirms affected categories.
    # Cancelled participants remain visible in PeopleTable with the
    # burgundy cancelled pill; they just no longer occupy a spot.
    if data.registration_status and data.registration_status == "cancelled":
        from app.services.allocation_service import unassign_all_for_participant
        removed = await unassign_all_for_participant(
            db,
            participant_id=participant_id,
            actor_user_id=current_user.id,
        )
        if removed:
            logger.info(
                "allocations_cleared_on_cancel",
                participant_id=str(participant_id),
                allocations_removed=removed,
            )

    logger.info(
        "participant_updated",
        participant_id=str(participant_id),
        updated_by=str(current_user.id),
    )

    # v1.0.0y: a status change (e.g. cancelled → active) can lift the
    # active roster past the cap; signal once if so. No-op otherwise.
    await maybe_signal_over_cap(db, participant.event_id)
    return participant


@router.patch(
    "/api/participants/{participant_id}/group-code",
    response_model=ParticipantResponse,
)
async def reassign_group_code(
    participant_id: uuid.UUID,
    data: GroupCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STAFF)),
):
    """Reassign a participant's group code. Event Admin or Team Leader."""
    participant = await get_participant_by_id(db, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.participant.not_found"})
    await ensure_event_writable(db, participant.event_id, current_user)

    if len(data.group_code) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"key": "errors.participant.group_code_too_short"},
        )

    participant = await update_group_code(db, participant, data.group_code, data.group_code_categories)
    logger.info(
        "group_code_reassigned",
        participant_id=str(participant_id),
        new_code=data.group_code,
        changed_by=str(current_user.id),
    )
    return participant


@router.post(
    "/api/participants/{participant_id}/checkin",
    response_model=ParticipantResponse,
)
async def checkin_participant(
    participant_id: uuid.UUID,
    data: CheckInRequest = CheckInRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STAFF)),
):
    """Mark a participant as checked in. Requires check-in permission for staff."""
    participant = await get_participant_by_id(db, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.participant.not_found"})
    await ensure_event_writable(db, participant.event_id, current_user)
    # v0.50e-1a: staff with any check-in permission can tick people in. The
    # read-only distinction has been removed; any checkin access = full access.
    if current_user.role == UserRole.STAFF:
        perms = await get_event_permissions(db, current_user, participant.event_id)
        if perms is None or not has_write(perms, "checkin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"key": "errors.participant.checkin_required"})
    participant = await check_in_participant(db, participant, data.checked_in)
    logger.info(
        "participant_checkin",
        participant_id=str(participant_id),
        checked_in=data.checked_in,
        by=str(current_user.id),
    )
    # v1.0-pre #8: broadcast to other clients viewing this event's
    # check-in panel so their UI reflects the change without a refresh.
    # Fire-and-forget; failure to publish doesn't fail the request.
    try:
        from app.core.pubsub import broker
        await broker.publish(
            f"checkin:{participant.event_id}",
            {
                "type": "checkin_changed",
                "participant_id": str(participant_id),
                "checked_in": bool(participant.checked_in),
                "checked_in_at": participant.checked_in_at.isoformat() if participant.checked_in_at else None,
                "by_user_id": str(current_user.id),
            },
        )
    except Exception as e:
        # Log but don't fail the request — the DB write succeeded; this
        # is best-effort fan-out.
        logger.warning("checkin_pubsub_publish_failed", error=str(e))
    return participant


@router.delete(
    "/api/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_participant(
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a participant (GDPR). Event Admin for this event, or Super Admin."""
    participant = await get_participant_by_id(db, participant_id)
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.participant.not_found"})
    await ensure_event_admin(db, participant.event_id, current_user)
    await ensure_event_writable(db, participant.event_id, current_user)
    await soft_delete_participant(db, participant)
    logger.info(
        "participant_deleted",
        participant_id=str(participant_id),
        deleted_by=str(current_user.id),
    )


# ─── Resend confirmation email ────────────────────────────────────────────────

@router.post(
    "/api/events/{event_id}/participants/{participant_id}/resend-confirmation",
    status_code=status.HTTP_200_OK,
)
async def resend_confirmation(
    event_id: uuid.UUID,
    participant_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-send a registration email for one participant. Event Admin only.

    Behaviour:
      - If the participant is `pending` and has a confirmation_token: re-send
        the original confirmation email (same template as the initial send).
      - If the participant is `confirmed`: re-send the registration receipt
        (same template as the post-confirmation message), including their
        group code so they can share it.
      - If the participant is `cancelled`: HTTP 409 — refusing to email a
        cancelled participant by accident.

    Returns: { "sent": true, "kind": "confirmation" | "receipt" }.
    """
    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    await ensure_event_admin(db, event_id, current_user)

    participant = await get_participant_by_id(db, participant_id)
    if not participant or participant.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.participant.not_found"})

    if participant.registration_status == RegistrationStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"key": "errors.participant.cancelled_no_resend"},
        )

    if not participant.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"key": "errors.participant.no_email"},
        )

    lang = participant.preferred_language or 'en'

    if participant.registration_status == RegistrationStatus.PENDING and participant.confirmation_token:
        base = get_app_base_url(request)
        confirmation_url = f"{base}/confirm/{participant.confirmation_token}"
        send_confirmation_email(
            to_email=participant.email,
            first_name=participant.first_name,
            event_name=event.name,
            confirmation_url=confirmation_url,
            lang=lang,
        )
        return {"sent": True, "kind": "confirmation"}

    # CONFIRMED (or PENDING without a token — defensive: send the receipt)
    send_registration_receipt(
        to_email=participant.email,
        first_name=participant.first_name,
        event_name=event.name,
        group_code=participant.group_code,
        lang=lang,
    )
    return {"sent": True, "kind": "receipt"}


# ─── Batch registration ───────────────────────────────────────────────────────

@router.post(
    "/api/events/{event_id}/participants/batch/preview",
    status_code=status.HTTP_200_OK,
)
async def batch_preview(
    event_id: uuid.UUID,
    file: UploadFile = File(...),
    dob_format: str = "eu",  # v1.0.0o: "eu" (default) or "iso" — disambiguates DD.MM.YYYY vs YYYY.MM.DD when both numeric components are ≤ 12. Anything else falls back to "eu".
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV and receive a validation preview — no participants are created.
    Returns per-row errors/warnings and a summary. Event Admin only.
    """
    from app.services.batch_register_service import parse_csv

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    await ensure_event_admin(db, event_id, current_user)

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"key": "errors.batch.csv_only"},
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"key": "errors.batch.empty_file"},
        )

    # v1.0.0o: normalise dob_format. "iso" covers Korean YYYY.MM.DD too
    # (same shape, year-first); only "iso" and "eu" are valid.
    normalised_dob_format = "iso" if dob_format == "iso" else "eu"
    result = await parse_csv(content, event_id, db, dob_format=normalised_dob_format)
    logger.info(
        "batch_preview",
        event_id=str(event_id),
        total=result["summary"]["total"],
        valid=result["summary"]["valid"],
        dob_format=normalised_dob_format,
        by=str(current_user.id),
    )
    return result


@router.post(
    "/api/events/{event_id}/participants/batch/commit",
    status_code=status.HTTP_200_OK,
)
async def batch_commit(
    event_id: uuid.UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Commit a previously previewed batch. Accepts the rows array returned by
    /batch/preview — invalid rows are skipped automatically.
    Event Admin only.
    """
    from app.services.batch_register_service import commit_batch

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    await ensure_event_admin(db, event_id, current_user)
    await ensure_event_writable(db, event_id, current_user)

    rows = payload.get("rows")
    if not rows or not isinstance(rows, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"key": "errors.batch.bad_body"},
        )

    # v0.85 #16: pass through the new-custom-field info from the preview.
    # Frontend sends these alongside `rows` after the admin confirms in
    # the preview ("These columns aren't recognised — create as new
    # custom fields?"). Both default to empty so existing callers (older
    # frontends, scripts) keep working.
    new_custom_fields = payload.get("new_custom_fields") or []
    unknown_values_by_row = payload.get("unknown_values_by_row") or []

    result = await commit_batch(
        rows, event_id, db,
        new_custom_fields=new_custom_fields,
        unknown_values_by_row=unknown_values_by_row,
    )
    logger.info(
        "batch_commit",
        event_id=str(event_id),
        created=result["created"],
        skipped=result["skipped"],
        failed=result["failed"],
        new_custom_fields=len(result.get("created_custom_fields", [])),
        by=str(current_user.id),
    )

    # v1.0.0y: a batch can add many at once and cross the cap in one go;
    # check once after the whole batch (not per row). No-op when no cap.
    await maybe_signal_over_cap(db, event_id)
    return result



@router.get(
    "/api/events/{event_id}/participants/batch/template.csv",
)
async def batch_template(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download a CSV template pre-populated with this event's custom field columns.
    Includes one example row. UTF-8 BOM for Excel compatibility.
    Event Admin only.
    """
    from app.services.batch_register_service import generate_template

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"key": "errors.event.not_found"})
    await ensure_event_admin(db, event_id, current_user)

    result = await db.execute(
        select(CustomFieldDefinition)
        .where(CustomFieldDefinition.event_id == event_id)
        .order_by(CustomFieldDefinition.sort_order)
    )
    custom_fields = list(result.scalars().all())

    csv_content = generate_template(custom_fields)
    safe_name = event.name.replace(" ", "_").replace("/", "-")[:40]

    return StreamingResponse(
        iter([csv_content.encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="moimio_template_{safe_name}.csv"'
        },
    )


@router.get(
    "/api/events/{event_id}/participants/{participant_id}/data-export",
)
async def participant_data_export(
    event_id: uuid.UUID,
    participant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin-on-behalf data export for a single participant.

    Aggregates everything Moimio holds about this participant — base
    record, custom fields, marks, preference requests (both directions),
    current allocations, coarsened audit history, published notes,
    check-in values, and self-describing event metadata — into a single
    JSON download. Supports GDPR Article 20 (right to data portability)
    on an admin-on-behalf basis.

    Soft-deleted participants ARE exportable (see service docstring).
    Hard-purged records return 404.

    Filename: `participant-export-{number}-{YYYY-MM-DD}.json`. When the
    participant has no participant_number assigned, the first 8 chars
    of their UUID stand in. The date stamp is the export date in UTC.

    Event Admin only. Returns 404 if the participant doesn't exist in
    this event (single 404 covers both "no such participant" and
    "wrong event_id" — we don't leak existence in other events).
    """
    from datetime import datetime, timezone
    from app.services.data_export_service import export_participant_data

    event = await get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"key": "errors.event.not_found"},
        )
    await ensure_event_admin(db, event_id, current_user)

    # The service raises MoimioAppError on missing participant; the
    # global exception handler maps it to the right HTTP status with
    # the right i18n key. No need for a try/except here — re-raising
    # would just duplicate the framework's behaviour.
    payload = await export_participant_data(db, event_id, participant_id)

    # Filename construction. Participant number is the human-readable
    # identifier organisers and participants both recognise; UUID
    # fallback covers the rare case where number wasn't assigned (e.g.
    # legacy records pre-numbering, or import races).
    p_number = payload["participant"].get("participant_number")
    p_id_str = payload["participant"]["id"]
    identifier = (
        f"{p_number:03d}" if p_number is not None
        else p_id_str.split("-")[0]
    )
    date_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"participant-export-{identifier}-{date_stamp}.json"

    logger.info(
        "data_export_generated",
        event_id=str(event_id),
        participant_id=str(participant_id),
        by=str(current_user.id),
    )

    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
