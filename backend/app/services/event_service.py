"""Event service — CRUD and field config management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventStatus
from app.models.event_field_config import EventFieldConfig
from app.models.user import UserRole
from app.models.user_preferences import UserPreferences
from app.schemas.event import EventCreate, EventUpdate, FieldConfigItem
from app.services.allocation_service import create_default_categories
from app.services.webhook_service import queue_event

# Default optional fields that can be toggled per event
DEFAULT_FIELD_CONFIGS = [
    "gender", "date_of_birth", "phone", "address", "country", "church_organisation",
]

# Which EventUpdate fields, if changed, should silently un-confirm which gate.
# Implements behaviour (a) from v50b design: any edit to a confirmed Setup
# card rolls its confirmed flag back to false so the organiser must
# re-confirm. Mirrors §6.2.6 allocation-confirm pattern.
DETAILS_FIELDS = {"name", "description", "location", "timezone", "start_date", "end_date"}
# Registration-related event settings live under `event.settings` and on
# child tables (EventFieldConfig). We unconfirm registration when
# event.settings changes (email config, grouping, style etc.), and the
# field_configs update path unconfirms it separately.


async def create_event(db: AsyncSession, data: EventCreate, created_by: uuid.UUID) -> Event:
    # Inherit timezone from the creating user's preferences, fall back to UTC.
    tz = data.timezone
    if not tz:
        res = await db.execute(
            select(UserPreferences.timezone).where(UserPreferences.user_id == created_by)
        )
        tz = res.scalar_one_or_none() or "UTC"

    event = Event(
        name=data.name,
        description=data.description,
        location=data.location,
        timezone=tz,
        start_date=data.start_date,
        end_date=data.end_date,
        created_by=created_by,
    )
    db.add(event)
    await db.flush()

    # v0.51: branch on copy_from_event_id.
    # - No copy → original behaviour: default field configs + default
    #   allocation categories.
    # - Copy set → skip defaults; copy config from source event via
    #   duplicate_event_config(). Source access was verified by the
    #   route before we got here.
    if data.copy_from_event_id is None:
        # Default field configs (all disabled by default)
        for field_name in DEFAULT_FIELD_CONFIGS:
            config = EventFieldConfig(
                event_id=event.id,
                field_name=field_name,
                is_enabled=False,
                is_required=False,
            )
            db.add(config)
        # Default allocation categories (Rooms + Small Groups)
        await create_default_categories(db, event.id)
    else:
        await duplicate_event_config(
            db, source_event_id=data.copy_from_event_id, dest_event_id=event.id
        )

    # v0.50j: auto-grant the creator a per-event admin assignment so
    # they can actually edit the event they just made. Previously the
    # system-wide EVENT_ADMIN role granted implicit access to every
    # event; that role no longer exists, so access is per-event now.
    # Super Admins don't need an assignment (they bypass the check),
    # but non-super creators must have one or they'd be locked out.
    #
    # v0.51: when duplicating, the creator may already be present
    # (copied from source as a staff assignment). Dedupe by checking
    # before insert to avoid the uq_event_user unique-constraint
    # violation.
    from app.models.user import User as _User
    from app.models.event_assignment import EventUserAssignment as _EUA
    user_res = await db.execute(
        select(_User.role).where(_User.id == created_by)
    )
    creator_role = user_res.scalar_one_or_none()
    if creator_role != UserRole.SUPER_ADMIN:
        existing_res = await db.execute(
            select(_EUA.id)
            .where(_EUA.event_id == event.id, _EUA.user_id == created_by)
        )
        if existing_res.scalar_one_or_none() is None:
            db.add(_EUA(
                event_id=event.id,
                user_id=created_by,
                role="event_admin",
                permissions={},
            ))

    await db.flush()
    await db.refresh(event)

    # v1.0.0h: emit event.created webhook. Same transaction as the
    # event creation — both succeed together or roll back together,
    # so receivers never see an event that didn't actually exist and
    # admins never see an event that wasn't reported. The actual
    # delivery is asynchronous; queue_event only inserts PENDING rows
    # which the scheduler picks up on its next tick. Payload is GDPR-
    # minimal: just the event ID and its creation timestamp. Tenant
    # identity is stamped at the envelope level (see _envelope in
    # webhook_service.py). If no endpoints are configured (typical
    # self-hoster) this is a no-op.
    await queue_event(
        db,
        event_type="event.created",
        data={
            "event_id": str(event.id),
            "created_at": event.created_at.isoformat(),
        },
    )

    return event


async def get_event_by_id(db: AsyncSession, event_id: uuid.UUID) -> Event | None:
    result = await db.execute(select(Event).where(Event.id == event_id))
    return result.scalar_one_or_none()


async def list_events(db: AsyncSession) -> list[Event]:
    result = await db.execute(
        select(Event).where(Event.status != EventStatus.ARCHIVED).order_by(Event.created_at.desc())
    )
    return list(result.scalars().all())


async def update_event(db: AsyncSession, event: Event, data: EventUpdate) -> Event:
    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = EventStatus(update_data["status"])

    # Behaviour (a): un-confirm on edit, but only while in Setup phase.
    # Once past Setup the confirmed flags no longer gate anything, so edits
    # shouldn't disrupt anything. `DRAFT` is Setup.
    in_setup = event.status == EventStatus.DRAFT
    if in_setup:
        touched_details = any(k in update_data for k in DETAILS_FIELDS)
        touched_reg = "settings" in update_data
        # If the caller is explicitly setting details_confirmed or
        # registration_confirmed in this same request (the "Save & close
        # & confirm" flow), respect the explicit value and skip the auto-reset.
        if touched_details and "details_confirmed" not in update_data:
            update_data["details_confirmed"] = False
        if touched_reg and "registration_confirmed" not in update_data:
            update_data["registration_confirmed"] = False

    for key, value in update_data.items():
        setattr(event, key, value)
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def get_field_configs(db: AsyncSession, event_id: uuid.UUID) -> list[EventFieldConfig]:
    result = await db.execute(
        select(EventFieldConfig).where(EventFieldConfig.event_id == event_id)
    )
    return list(result.scalars().all())


async def update_field_configs(
    db: AsyncSession, event_id: uuid.UUID, configs: list[FieldConfigItem]
) -> list[EventFieldConfig]:
    # Field-config edits touch the Registration card's content → unconfirm it
    # (only while Setup). Fetch the event once for that check.
    event = await get_event_by_id(db, event_id)
    if event and event.status == EventStatus.DRAFT and event.registration_confirmed:
        event.registration_confirmed = False
        db.add(event)

    # v0.57b F4 fix: fetch all existing configs in one query and
    # look up by name in Python, instead of one SELECT per item.
    existing_q = await db.execute(
        select(EventFieldConfig).where(EventFieldConfig.event_id == event_id)
    )
    existing_by_name = {c.field_name: c for c in existing_q.scalars().all()}

    for item in configs:
        config = existing_by_name.get(item.field_name)
        if config:
            config.is_enabled = item.is_enabled
            config.is_required = item.is_required
            db.add(config)
        else:
            config = EventFieldConfig(
                event_id=event_id,
                field_name=item.field_name,
                is_enabled=item.is_enabled,
                is_required=item.is_required,
            )
            db.add(config)

    await db.flush()
    return await get_field_configs(db, event_id)


# ─── Delete (v0.50g-2) ────────────────────────────────────────────────────────

async def delete_event(db: AsyncSession, event_id: uuid.UUID) -> bool:
    """Hard-delete an event and everything that belongs to it.

    v0.50g-2: explicit multi-step delete because some FKs lack ON DELETE
    CASCADE (event_field_config, participant, custom_field, preference_request).
    Rather than relying on a schema fix we might not ship today, we walk
    the graph top-down.

    Delete order (children first so their parent FKs don't block us):
      1.  Within participants: notes, mark_assignments, checkin_values,
          allocations, custom_field_values, preference_requests.
          (Those with CASCADE will be handled in step 2; others must
          be explicit.)
      2.  Participants themselves.
      3.  Allocation units, allocation categories.
      4.  Event-scoped config: custom fields (defs), mark definitions,
          check-in field configs, event_field_configs, event_assignments,
          preference requests (at event level), notes at event level.
      5.  The event row.

    Returns True on success, False if not found. Raises on other errors.
    """
    from app.models.participant import Participant
    from app.models.allocation_category import AllocationCategory
    from app.models.allocation import Allocation
    from app.models.allocation_unit import AllocationUnit
    from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
    from app.models.checkin_field import CheckInField
    from app.models.checkin_value import CheckInValue
    from app.models.event_field_config import EventFieldConfig
    from app.models.mark import MarkDefinition, MarkAssignment
    from app.models.event_assignment import EventUserAssignment
    from app.models.preference_request import ParticipantPreferenceRequest
    from app.models.note import Note
    from sqlalchemy import delete as sql_delete

    event = await get_event_by_id(db, event_id)
    if not event:
        return False

    # v1.0.0h-1: emit event.deleted webhook in the same transaction as
    # the cascade. Same atomicity contract as event.created: webhook
    # delivery row and the cascade commit together or roll back
    # together. Tenant identity is stamped at the envelope level (see
    # _envelope in webhook_service.py). Payload is GDPR-minimal: just
    # the event ID and a deletion timestamp. SaaS owns the decision
    # of whether the deletion warrants a refund (e.g. the 24-hour
    # paid-plan policy is a SaaS billing rule, not a CE rule).
    from datetime import datetime, timezone
    await queue_event(
        db,
        event_type="event.deleted",
        data={
            "event_id": str(event_id),
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    # Resolve participant ids up front — we need them for child-of-participant
    # deletes and the participants table itself.
    part_q = await db.execute(
        select(Participant.id).where(Participant.event_id == event_id)
    )
    participant_ids = [row[0] for row in part_q.all()]

    # Resolve category ids similarly for allocation unit cleanup.
    cat_q = await db.execute(
        select(AllocationCategory.id).where(AllocationCategory.event_id == event_id)
    )
    category_ids = [row[0] for row in cat_q.all()]

    # Resolve unit ids so we can sweep notes attached to them.
    unit_ids: list = []
    if category_ids:
        unit_q = await db.execute(
            select(AllocationUnit.id).where(AllocationUnit.category_id.in_(category_ids))
        )
        unit_ids = [row[0] for row in unit_q.all()]

    # ─── Participant-scoped children ────────────────────────────────────
    # Mark assignments and allocations cascade from participant, but we
    # delete explicitly to keep the path deterministic across DBs.
    if participant_ids:
        await db.execute(sql_delete(MarkAssignment).where(MarkAssignment.participant_id.in_(participant_ids)))
        await db.execute(sql_delete(Allocation).where(Allocation.participant_id.in_(participant_ids)))
        await db.execute(sql_delete(CheckInValue).where(CheckInValue.participant_id.in_(participant_ids)))
        await db.execute(sql_delete(CustomFieldValue).where(CustomFieldValue.participant_id.in_(participant_ids)))
        await db.execute(sql_delete(Note).where(Note.notable_type == "participant", Note.notable_id.in_(participant_ids)))
        await db.execute(sql_delete(ParticipantPreferenceRequest).where(ParticipantPreferenceRequest.participant_id.in_(participant_ids)))

    # ─── Participants ───────────────────────────────────────────────────
    await db.execute(sql_delete(Participant).where(Participant.event_id == event_id))

    # ─── Notes attached to allocation units & categories ────────────────
    if unit_ids:
        await db.execute(sql_delete(Note).where(Note.notable_type.in_(["room", "group", "unit"]), Note.notable_id.in_(unit_ids)))
    if category_ids:
        await db.execute(sql_delete(Note).where(Note.notable_type == "category", Note.notable_id.in_(category_ids)))

    # ─── Allocation units + categories ──────────────────────────────────
    if category_ids:
        await db.execute(sql_delete(AllocationUnit).where(AllocationUnit.category_id.in_(category_ids)))
    await db.execute(sql_delete(AllocationCategory).where(AllocationCategory.event_id == event_id))

    # ─── Event-scoped definitions & config ──────────────────────────────
    await db.execute(sql_delete(MarkDefinition).where(MarkDefinition.event_id == event_id))
    await db.execute(sql_delete(CustomFieldDefinition).where(CustomFieldDefinition.event_id == event_id))
    await db.execute(sql_delete(CheckInField).where(CheckInField.event_id == event_id))
    await db.execute(sql_delete(EventFieldConfig).where(EventFieldConfig.event_id == event_id))
    await db.execute(sql_delete(EventUserAssignment).where(EventUserAssignment.event_id == event_id))
    await db.execute(sql_delete(Note).where(Note.notable_type == "event", Note.notable_id == event_id))
    # Any remaining event-scoped preference requests (shouldn't be any
    # after participant cleanup, but harmless to run).
    await db.execute(sql_delete(ParticipantPreferenceRequest).where(ParticipantPreferenceRequest.event_id == event_id))

    # ─── The event itself ───────────────────────────────────────────────
    await db.delete(event)
    await db.flush()
    return True


# ─── v0.51: duplicate event config ───────────────────────────────────────
#
# Copy the "config" tables from a source event to a destination event.
# Caller is responsible for verifying access to the source event and for
# having already created the destination Event row.
#
# Copies: marks, field configs, custom field defs, allocation categories
#         + their units, staff assignments.
# Does NOT copy: participants, allocations, mark assignments,
#         custom field values, check-in fields/values, notes,
#         preference requests, or the Event row itself.
#
# Design note: we chose per-table INSERT ... SELECT in Python rather than
# a single SQL statement so the code reads straightforwardly and any
# future schema additions get caught at import time rather than silently
# skipped by a hand-crafted SELECT column list.
async def duplicate_event_config(
    db: AsyncSession,
    source_event_id: uuid.UUID,
    dest_event_id: uuid.UUID,
) -> None:
    from app.models.mark import MarkDefinition
    from app.models.event_field_config import EventFieldConfig
    from app.models.custom_field import CustomFieldDefinition
    from app.models.allocation_category import AllocationCategory
    from app.models.allocation_unit import AllocationUnit
    from app.models.event_assignment import EventUserAssignment

    # ─── Marks ─────────────────────────────────────────────────────────
    mark_res = await db.execute(
        select(MarkDefinition).where(MarkDefinition.event_id == source_event_id)
    )
    for m in mark_res.scalars().all():
        db.add(MarkDefinition(
            event_id=dest_event_id,
            name=m.name,
            colour=m.colour,
            visible_in=list(m.visible_in or []),
            created_by_user_id=m.created_by_user_id,
        ))

    # ─── Event field configs (registration form schema) ─────────────────
    fc_res = await db.execute(
        select(EventFieldConfig).where(EventFieldConfig.event_id == source_event_id)
    )
    for fc in fc_res.scalars().all():
        db.add(EventFieldConfig(
            event_id=dest_event_id,
            field_name=fc.field_name,
            is_enabled=fc.is_enabled,
            is_required=fc.is_required,
        ))

    # ─── Custom field definitions ──────────────────────────────────────
    cf_res = await db.execute(
        select(CustomFieldDefinition).where(CustomFieldDefinition.event_id == source_event_id)
    )
    for cf in cf_res.scalars().all():
        db.add(CustomFieldDefinition(
            event_id=dest_event_id,
            label=cf.label,
            field_type=cf.field_type,
            options=cf.options,
            is_required=cf.is_required,
            sort_order=cf.sort_order,
        ))

    # ─── Allocation categories + units ────────────────────────────────
    # Units FK into categories, so we need the NEW category IDs to
    # rewire them. Keep a source_cat_id → new_cat_id map during copy.
    cat_res = await db.execute(
        select(AllocationCategory).where(AllocationCategory.event_id == source_event_id)
    )
    cat_id_map: dict[uuid.UUID, uuid.UUID] = {}
    for cat in cat_res.scalars().all():
        new_cat = AllocationCategory(
            event_id=dest_event_id,
            name=cat.name,
            item_label=cat.item_label,
            description=cat.description,
            rule_type=cat.rule_type,
            has_capacity=cat.has_capacity,
            has_gender_restriction=cat.has_gender_restriction,
            sort_order=cat.sort_order,
            is_default=cat.is_default,
            # Fresh event starts with no confirmed allocations.
            confirmed=False,
            settings=cat.settings,
        )
        db.add(new_cat)
        await db.flush()  # populate new_cat.id
        cat_id_map[cat.id] = new_cat.id

    if cat_id_map:
        unit_res = await db.execute(
            select(AllocationUnit).where(AllocationUnit.category_id.in_(list(cat_id_map.keys())))
        )
        for u in unit_res.scalars().all():
            # Introspect available columns defensively — AllocationUnit
            # may have fields we don't know about at write time. Use
            # the SQLAlchemy column list as the source of truth.
            payload = {
                col.name: getattr(u, col.name)
                for col in AllocationUnit.__table__.columns
                if col.name not in ("id", "created_at", "updated_at", "category_id")
            }
            payload["category_id"] = cat_id_map[u.category_id]
            db.add(AllocationUnit(**payload))

    # ─── Staff assignments ────────────────────────────────────────────
    # Per Q3: yes, copy staff assignments. Deduped downstream in
    # create_event (creator gets ensured after this call).
    asn_res = await db.execute(
        select(EventUserAssignment).where(EventUserAssignment.event_id == source_event_id)
    )
    for a in asn_res.scalars().all():
        db.add(EventUserAssignment(
            event_id=dest_event_id,
            user_id=a.user_id,
            role=a.role,
            permissions=a.permissions,
        ))

    await db.flush()


async def duplicate_counts(
    db: AsyncSession,
    event_id: uuid.UUID,
) -> dict:
    """Return config-table counts for the duplicate preview page."""
    from sqlalchemy import func
    from app.models.mark import MarkDefinition
    from app.models.event_field_config import EventFieldConfig
    from app.models.custom_field import CustomFieldDefinition
    from app.models.allocation_category import AllocationCategory
    from app.models.event_assignment import EventUserAssignment

    async def _count(model):
        r = await db.execute(
            select(func.count()).select_from(model).where(model.event_id == event_id)
        )
        return int(r.scalar() or 0)

    return {
        "marks": await _count(MarkDefinition),
        "field_configs": await _count(EventFieldConfig),
        "custom_fields": await _count(CustomFieldDefinition),
        "allocation_categories": await _count(AllocationCategory),
        "staff_assignments": await _count(EventUserAssignment),
    }
