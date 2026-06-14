"""Participant service — registration, CRUD, group codes, check-in, confirmation."""

import re
import uuid
import secrets
import random
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Participant, RegistrationStatus
from app.models.preference_request import ParticipantPreferenceRequest
from app.models.custom_field import CustomFieldValue
from app.schemas.participant import ParticipantRegister, ParticipantUpdate
from app.models.event import Event
from app.core.config import get_settings
from app.services.webhook_service import queue_event


# ─── v1.0-pre: collision-safe group-code allocation ─────────────────────────
# Background: the registration form lets participants type a "group code" so
# families/friend-groups end up clustered together by the allocation engine.
# The previous logic took whatever they typed verbatim — which meant two
# unrelated Smith families both typing "SMITH" would collide into one
# 8-person mega-cluster. The fix: only treat a typed value as a *complete*
# code if it has the SURNAME-NNN shape (a stem, a dash, a numeric suffix).
# A bare stem ("SMITH") is treated as the start of a new cluster — we
# allocate a unique suffix within the event scope before saving.
#
# Auto-generated codes (when the registrant leaves the field blank) also
# go through the same uniqueness check.

_COMPLETE_CODE_RE = re.compile(r'^[A-Z0-9]+-\d+$')


def _is_complete_code(code: str) -> bool:
    """A complete group code is `STEM-NNN` — uppercase alnum stem,
    dash, one or more digits. Anything else is a stem-only input
    that needs a unique suffix appended."""
    return bool(_COMPLETE_CODE_RE.match(code))


def _stem_from(text: str) -> str:
    """Normalise a free-text input into a stem suitable for STEM-NNN.
    Uppercase, strip whitespace, keep alnum only, truncate to 8."""
    cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
    return cleaned[:8] or 'GROUP'


async def _allocate_unique_group_code(
    db: AsyncSession, event_id: uuid.UUID, stem: str
) -> str:
    """Return a STEM-NNN code that doesn't collide with any existing
    group_code in this event. Tries random 3-digit suffixes (100–999)
    a handful of times; if all happen to collide, falls back to a
    4-digit suffix (1000–9999) and ultimately a 5-digit one. The
    fallback ladder makes total exhaustion practically impossible."""
    for digits in (3, 4, 5):
        lo, hi = 10 ** (digits - 1), 10 ** digits - 1
        # 8 attempts at 3-digit gives < 1% collision chance for an event
        # with up to ~80 same-stem clusters; the rare miss falls through.
        for _attempt in range(8):
            candidate = f"{stem}-{random.randint(lo, hi)}"
            existing = await db.execute(
                select(Participant.id).where(
                    Participant.event_id == event_id,
                    Participant.group_code == candidate,
                ).limit(1)
            )
            if existing.scalar_one_or_none() is None:
                return candidate
    # Effectively unreachable for any realistic event size, but surface
    # cleanly rather than hanging in an infinite loop if it ever happens.
    raise RuntimeError(f"Could not allocate unique group_code for stem={stem!r}")


async def _resolve_group_code(
    db: AsyncSession,
    event_id: uuid.UUID,
    submitted: str | None,
    last_name: str,
) -> str:
    """Decide what to save as the participant's group_code.

    Three input cases:
      1. Submitted complete code (`SMITH-742`) → take verbatim. Joining
         an existing cluster, or starting a new one whose code happens
         to be self-chosen. Either way, no collision check — the
         registrant is making an explicit "use this code" choice.
      2. Submitted stem only (`SMITH`) → allocate a unique suffix.
         Treats the input as "I'm a Smith starting a Smith cluster";
         the second unrelated Smith family gets a different suffix.
      3. Nothing submitted → derive stem from last_name, allocate a
         unique suffix.
    """
    if submitted and submitted.strip():
        cleaned = submitted.strip().upper()
        if _is_complete_code(cleaned):
            return cleaned
        # Stem only — treat as start of a new cluster.
        return await _allocate_unique_group_code(db, event_id, _stem_from(cleaned))
    return await _allocate_unique_group_code(db, event_id, _stem_from(last_name))


async def register_participant(
    db: AsyncSession, event_id: uuid.UUID, data: ParticipantRegister,
    require_confirmation: bool = False,
) -> Participant:
    """Public registration — creates participant and saves custom field values."""
    token = secrets.token_urlsafe(48) if require_confirmation else None
    status = RegistrationStatus.PENDING if require_confirmation else RegistrationStatus.CONFIRMED

    # v1.0-pre: collision-safe group code. See _resolve_group_code above.
    # The final value is set on the participant before save and before
    # any confirmation/receipt email is sent — emails always reflect the
    # corrected code (e.g. SMITH → SMITH-742).
    group_code = await _resolve_group_code(
        db, event_id, data.group_code, data.last_name
    )

    # Assign sequential participant number for this event
    result_num = await db.execute(
        select(sa_func.max(Participant.participant_number)).where(
            Participant.event_id == event_id
        )
    )
    max_num = result_num.scalar() or 0
    participant_number = max_num + 1

    participant = Participant(
        event_id=event_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        gender=data.gender,
        date_of_birth=data.date_of_birth,
        phone=data.phone,
        address=data.address,
        country=data.country,
        church_organisation=data.church_organisation,
        message=data.message,
        group_code=group_code,
        group_code_categories=getattr(data, 'group_code_categories', None),
        participant_number=participant_number,
        gdpr_consent=data.gdpr_consent,
        registration_status=status,
        confirmation_token=token,
        preferred_language=getattr(data, 'preferred_language', None) or 'en',
    )
    db.add(participant)
    await db.flush()

    if data.custom_fields:
        for field_id_str, value in data.custom_fields.items():
            try:
                field_id = uuid.UUID(field_id_str)
            except ValueError:
                continue
            cfv = CustomFieldValue(
                participant_id=participant.id,
                field_id=field_id,
                value=value,
            )
            db.add(cfv)
        await db.flush()

    # Save preference requests if any
    pref_requests = getattr(data, 'preference_requests', None) or []
    for pref in pref_requests:
        if not pref.get('preferred_name') and not pref.get('preferred_participant_number'):
            continue  # skip empty entries
        pr = ParticipantPreferenceRequest(
            event_id=event_id,
            participant_id=participant.id,
            preferred_participant_number=pref.get('preferred_participant_number'),
            preferred_name=pref.get('preferred_name'),
            preferred_details=pref.get('preferred_details'),
            category_scope=pref.get('category_scope', 'all'),
        )
        db.add(pr)
    if pref_requests:
        await db.flush()

    await db.refresh(participant)
    return participant


async def confirm_participant(
    db: AsyncSession, token: str
) -> tuple[Participant | None, str]:
    """Process a confirmation-token click. Returns (participant, state).

    v0.70d-2b-1 (R7): the old version cleared the token on first use and
    returned None for both "never valid" and "already used". The frontend
    silently rendered stale-token hits as "success", which was dishonest
    UX. Now returns one of three states so callers can tell them apart:

      ``('fresh')``     — token matched a PENDING participant; status
                          flipped to CONFIRMED. First legitimate visit.
      ``('already')``   — token matched a CONFIRMED participant. Idempotent
                          re-visit (user clicked an old email, bookmark,
                          etc.). No action taken; safe to show a calm
                          "already confirmed" message.
      ``('invalid')``   — no match. Token is bad, stale-and-replaced (the
                          participant re-registered generating a new token),
                          or the participant is cancelled / soft-deleted.
                          Frontend renders the honest "this link is no
                          longer valid" state.

    The token is intentionally NOT cleared on confirmation anymore — keeping
    it lets the idempotent re-visit land on 'already' instead of falling
    through to 'invalid'. The token is a one-way credential with no action
    side-effects beyond confirmation, so leaving it set is safe; any
    re-click is a no-op.
    """
    result = await db.execute(
        select(Participant).where(
            Participant.confirmation_token == token,
            Participant.deleted_at.is_(None),
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        # Token either never existed, or was associated with a
        # soft-deleted participant, or was overwritten when the same
        # email re-registered. Caller sees 'invalid'.
        return None, "invalid"

    if participant.registration_status == RegistrationStatus.CANCELLED:
        # Cancelled participants shouldn't re-confirm via email — an
        # admin deliberately flipped them to cancelled. Treat as invalid
        # from the public link's POV; the participant can contact the
        # organiser if they want to re-register.
        return None, "invalid"

    if participant.registration_status == RegistrationStatus.CONFIRMED:
        # Idempotent re-visit. Return the participant so the caller can
        # still reference them (e.g. for logging), but flag 'already' so
        # they don't trigger another confirmation email.
        return participant, "already"

    # Status is PENDING — legitimate first confirmation.
    participant.registration_status = RegistrationStatus.CONFIRMED
    db.add(participant)
    await db.flush()
    await db.refresh(participant)
    return participant, "fresh"


async def get_participant_by_id(db: AsyncSession, participant_id: uuid.UUID) -> Participant | None:
    result = await db.execute(
        select(Participant).where(
            Participant.id == participant_id,
            Participant.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_participants(
    db: AsyncSession, event_id: uuid.UUID
) -> list[Participant]:
    result = await db.execute(
        select(Participant).where(
            Participant.event_id == event_id,
            Participant.deleted_at.is_(None),
        ).order_by(Participant.created_at.desc())
    )
    return list(result.scalars().all())


async def update_participant(
    db: AsyncSession, participant: Participant, data: ParticipantUpdate
) -> Participant:
    update_data = data.model_dump(exclude_unset=True)
    if "registration_status" in update_data:
        update_data["registration_status"] = RegistrationStatus(
            update_data["registration_status"]
        )
    # v0.87 #14: custom_fields is a *computed property* on Participant
    # backed by the CustomFieldValue relationship — `setattr` would fail
    # silently. Pull it out of update_data and upsert per-id below.
    incoming_cfs: dict | None = update_data.pop("custom_fields", None)

    for key, value in update_data.items():
        setattr(participant, key, value)

    if incoming_cfs is not None:
        # Upsert each custom_field value: replace if exists, insert if new.
        # Existing keys NOT in incoming_cfs are left alone — this is a
        # PATCH-style merge, not a full replacement. Empty strings or
        # null clear the value (delete the row) so admins can blank a
        # field cleanly.
        # v0.89 #14 fix: deletes need to flush before refresh, otherwise
        # the cached `custom_field_values` selectin relationship still
        # contains the doomed rows. Order: deletes first → flush →
        # upserts → flush → expire the relationship → refresh.
        existing_q = await db.execute(
            select(CustomFieldValue).where(
                CustomFieldValue.participant_id == participant.id,
            )
        )
        existing_by_field_id: dict[str, CustomFieldValue] = {
            str(cfv.field_id): cfv for cfv in existing_q.scalars().all()
        }
        # Pass 1: deletions (so they flush before the upsert pass adds rows
        # that could otherwise collide on (participant_id, field_id) if
        # there's a uniqueness constraint).
        any_deletes = False
        for field_id_str, raw_value in incoming_cfs.items():
            try:
                uuid.UUID(field_id_str)  # validate
            except (ValueError, TypeError):
                continue
            value_clean = (raw_value or "").strip() if isinstance(raw_value, str) else raw_value
            if value_clean == "" or value_clean is None:
                existing = existing_by_field_id.get(field_id_str)
                if existing is not None:
                    await db.delete(existing)
                    any_deletes = True
        if any_deletes:
            await db.flush()
        # Pass 2: upserts (only non-empty values).
        for field_id_str, raw_value in incoming_cfs.items():
            try:
                field_id = uuid.UUID(field_id_str)
            except (ValueError, TypeError):
                continue
            value_clean = (raw_value or "").strip() if isinstance(raw_value, str) else raw_value
            if value_clean == "" or value_clean is None:
                continue  # already handled in pass 1
            existing = existing_by_field_id.get(field_id_str)
            if existing is not None and field_id_str in {
                # Skip rows we just deleted — though `existing` would still
                # be in the dict, deletion has flushed so the row is gone.
                # In practice, a single key can't be both deleted and
                # upserted in the same batch (the value is one-or-the-other),
                # so this branch is just defensive.
            }:
                continue
            if existing is not None:
                existing.value = str(value_clean)
            else:
                cfv = CustomFieldValue(
                    participant_id=participant.id,
                    field_id=field_id,
                    value=str(value_clean),
                )
                db.add(cfv)
        await db.flush()
        # Force SQLAlchemy to re-load custom_field_values on the next
        # access — without this, the selectin-loaded relationship still
        # holds the pre-mutation list (including the just-deleted rows).
        await db.refresh(participant, attribute_names=["custom_field_values"])

    db.add(participant)
    await db.flush()
    await db.refresh(participant)
    return participant


async def update_group_code(
    db: AsyncSession, participant: Participant, new_code: str, categories: list | None = None
) -> Participant:
    participant.group_code = new_code
    participant.group_code_categories = categories
    db.add(participant)
    await db.flush()
    await db.refresh(participant)
    return participant


async def check_in_participant(
    db: AsyncSession, participant: Participant, checked_in: bool
) -> Participant:
    participant.checked_in = checked_in
    participant.checked_in_at = (
        datetime.now(timezone.utc) if checked_in else None
    )
    db.add(participant)
    await db.flush()
    await db.refresh(participant)
    return participant


async def soft_delete_participant(
    db: AsyncSession, participant: Participant
) -> Participant:
    participant.deleted_at = datetime.now(timezone.utc)
    db.add(participant)
    await db.flush()
    await db.refresh(participant)
    return participant


# ─── Over-cap signalling (v1.0.0y) ───────────────────────────────────


def _round_up_to_band(n: int, step: int = 50) -> int:
    """Round n UP to the next multiple of `step`. We report this coarse
    band instead of an exact headcount."""
    return ((n + step - 1) // step) * step


async def maybe_signal_over_cap(
    db: AsyncSession, event_id: uuid.UUID
) -> bool:
    """Emit `event.over_cap` ONCE if this event's active roster has crossed
    the configured participant cap.

    Active roster = confirmed + pending, excluding removed (deleted_at set).
    No-op when:
      - no cap is configured (MOIMIO_PARTICIPANT_CAP unset) — self-hosters;
      - the event has already signalled (over_cap_signalled is true);
      - the event is missing, or the count is at/under the cap.

    The exact count never leaves CE: only an approximate band (rounded up to
    the next 50) plus the cap travels in the webhook. Queued in the caller's
    transaction (queue_event only inserts a PENDING row); the request commit
    ships it alongside the participant change. Never blocks anything — purely
    a signal. Returns True iff a signal was emitted.
    """
    cap = get_settings().moimio_participant_cap
    if not cap:
        return False

    event = await db.get(Event, event_id)
    if event is None or event.over_cap_signalled:
        return False

    count = (
        await db.execute(
            select(sa_func.count())
            .select_from(Participant)
            .where(
                Participant.event_id == event_id,
                Participant.registration_status.in_(
                    [RegistrationStatus.PENDING, RegistrationStatus.CONFIRMED]
                ),
                Participant.deleted_at.is_(None),
            )
        )
    ).scalar_one()

    if count <= cap:
        return False

    event.over_cap_signalled = True
    db.add(event)
    await queue_event(
        db,
        event_type="event.over_cap",
        data={
            "event_id": str(event_id),
            "participant_estimate": _round_up_to_band(count),
            "cap": cap,
        },
    )
    return True
