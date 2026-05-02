"""Data export service — admin-on-behalf participant data export. v0.73.

Builds a single self-contained JSON dictionary covering everything Moimio
holds about one participant. Used by the v0.73 endpoint to support
GDPR Article 20 (right to data portability) on an admin-on-behalf basis.

Scope decisions (locked in design discussion before v0.73 landed):

  * Event metadata is included as a self-describing wrapper (id, name,
    start_date, end_date, location, description, timezone) so the export
    is interpretable on its own. Organisational event data — field
    configs, allocation categories, units that the participant is NOT
    placed in — does NOT belong in the participant's export.

  * Audit history is coarsened. The `actor_user_id` column on
    allocation_events identifies which admin made each move; that's the
    controller's metadata, not the data subject's data. Dropped from
    the export. The participant sees what happened and when, not who
    did it.

  * Foreign keys are resolved to human-readable names. Marks become
    {name, colour}; allocations become {unit_name, category_name};
    check-in values become {field_name, checked}. The export is for
    the data subject, who has no database access — opaque UUIDs alone
    would not satisfy "structured, commonly used and machine-readable"
    in any practical sense.

  * Soft-deleted participants ARE exportable. Unlike most participant
    queries elsewhere in the codebase (which filter
    `deleted_at IS NULL`), this service does not. The DSAR use case
    explicitly covers the post-soft-delete window — a participant
    invoking right-to-access *after* having asked to be removed is
    exactly the case where the export must still work, until hard
    purge. Hard-purged records are unreachable by definition; this
    service does not bring them back.

The function is async and runs as one coordinated SELECT pass per
table. No N+1 traps. Read-only — never modifies state. If the
participant does not exist in the given event, raises a
MoimioAppError that the endpoint surfaces as HTTP 404.

Returned dict shape (top-level keys, in this order):

    {
      "export_metadata": {...},        # what/when/version
      "event": {...},                  # 7 identifying fields
      "participant": {...},            # base record minus token + soft-delete-only fields
      "custom_fields": [...],          # [{label, field_type, value}, ...]
      "marks": [...],                  # [{name, colour, assigned_at}, ...]
      "preference_requests": [...],    # [{preferred_*, resolved, ...}, ...]
      "allocations": [...],            # [{unit_name, category_name, created_at}, ...]
      "allocation_history": [...],     # coarsened audit trail
      "notes": [...],                  # only notable_type='participant', is_published=true
      "checkin_values": [...],         # [{field_name, checked, ...}, ...]
    }

The "notes" slice deserves a callout: only PUBLISHED notes whose
notable_type is 'participant' AND notable_id matches this participant
are included. Internal/draft admin notes (is_published=False) are NOT
the data subject's data — they're the controller's working notes.
Event-level notes and allocation-level notes are similarly excluded.
"""

import uuid
from datetime import datetime, date, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import MoimioAppError
from app.models.allocation import Allocation
from app.models.allocation_category import AllocationCategory
from app.models.allocation_event import AllocationEvent
from app.models.allocation_unit import AllocationUnit
from app.models.checkin_field import CheckInField
from app.models.checkin_value import CheckInValue
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.event import Event
from app.models.mark import MarkAssignment, MarkDefinition
from app.models.note import Note
from app.models.participant import Participant
from app.models.preference_request import ParticipantPreferenceRequest


# Service version. Bumps when the export shape changes in a way that
# downstream consumers (data subject's tools, future self-service flows)
# would need to know about. Kept separate from the app/backend version
# because the export contract is its own thing.
EXPORT_SCHEMA_VERSION = "1.0"


def _iso(value):
    """Format datetime/date as ISO string; pass through None and others."""
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


async def export_participant_data(
    db: AsyncSession,
    event_id: uuid.UUID,
    participant_id: uuid.UUID,
) -> dict:
    """Aggregate every Moimio table touching one participant into one dict.

    Read-only. One SELECT per table. FKs resolved to names where the
    name is meaningful to the data subject. Audit history coarsened to
    drop actor_user_id.

    Raises MoimioAppError(404) if the participant does not exist in this
    event (covers both "no such participant" and "wrong event_id" with
    a single error — we don't leak whether the participant exists in
    some other event the caller doesn't have access to).
    """
    # 1. Participant — also serves as the existence check.
    p_row = await db.execute(
        select(Participant).where(
            Participant.id == participant_id,
            Participant.event_id == event_id,
        )
    )
    participant = p_row.scalar_one_or_none()
    if participant is None:
        raise MoimioAppError("errors.participant.not_found", status_code=404)

    # 2. Event metadata wrapper (self-describing). Per the locked
    #    decision, only the 7 identifying fields — not field_config,
    #    not allocation categories the participant is NOT in.
    e_row = await db.execute(select(Event).where(Event.id == event_id))
    event = e_row.scalar_one_or_none()
    # If the event row is missing (event hard-deleted but participant
    # still here), we surface a degraded slice rather than 404 — the
    # participant's own data is still legitimate to export.
    event_slice = {
        "id": str(event.id) if event else str(event_id),
        "name": event.name if event else None,
        "description": event.description if event else None,
        "location": event.location if event else None,
        "timezone": event.timezone if event else None,
        "start_date": _iso(event.start_date) if event else None,
        "end_date": _iso(event.end_date) if event else None,
    }

    # 3. Custom fields — join values to their definitions for label/type.
    cf_rows = await db.execute(
        select(CustomFieldValue, CustomFieldDefinition)
        .join(
            CustomFieldDefinition,
            CustomFieldValue.field_id == CustomFieldDefinition.id,
        )
        .where(CustomFieldValue.participant_id == participant_id)
        .order_by(CustomFieldDefinition.sort_order)
    )
    custom_fields = []
    for value, definition in cf_rows.all():
        custom_fields.append({
            "label": definition.label,
            "field_type": definition.field_type,
            "value": value.value,
        })

    # 4. Marks — resolve mark_id to {name, colour}. Sorted by assignment
    #    time so the order matches the participant's actual experience.
    mark_rows = await db.execute(
        select(MarkAssignment, MarkDefinition)
        .join(MarkDefinition, MarkAssignment.mark_id == MarkDefinition.id)
        .where(MarkAssignment.participant_id == participant_id)
        .order_by(MarkAssignment.created_at)
    )
    marks = []
    for assignment, definition in mark_rows.all():
        marks.append({
            "name": definition.name,
            "colour": definition.colour,
            "assigned_at": _iso(assignment.created_at),
        })

    # 5. Preference requests — both directions:
    #    (a) requests this participant MADE, and
    #    (b) requests OTHERS made naming this participant by number.
    #    Both are arguably "their" data under Article 20.
    pref_rows = await db.execute(
        select(ParticipantPreferenceRequest)
        .where(
            ParticipantPreferenceRequest.event_id == event_id,
            ParticipantPreferenceRequest.participant_id == participant_id,
        )
        .order_by(ParticipantPreferenceRequest.created_at)
    )
    preference_requests_made = []
    for pref in pref_rows.scalars().all():
        preference_requests_made.append({
            "direction": "made_by_this_participant",
            "preferred_participant_number": pref.preferred_participant_number,
            "preferred_name": pref.preferred_name,
            "preferred_details": pref.preferred_details,
            "category_scope": pref.category_scope,
            "resolved": pref.resolved,
            "resolved_note": pref.resolved_note,
            "created_at": _iso(pref.created_at),
        })

    # The "received" direction needs the participant's own number to
    # match against preferred_participant_number on other rows.
    preference_requests_received = []
    if participant.participant_number is not None:
        recv_rows = await db.execute(
            select(ParticipantPreferenceRequest)
            .where(
                ParticipantPreferenceRequest.event_id == event_id,
                ParticipantPreferenceRequest.preferred_participant_number
                    == participant.participant_number,
                # Exclude self-referential rows (would already appear
                # in the "made" slice above).
                ParticipantPreferenceRequest.participant_id != participant_id,
            )
            .order_by(ParticipantPreferenceRequest.created_at)
        )
        for pref in recv_rows.scalars().all():
            preference_requests_received.append({
                "direction": "received_naming_this_participant",
                "preferred_participant_number": pref.preferred_participant_number,
                "preferred_name": pref.preferred_name,
                "preferred_details": pref.preferred_details,
                "category_scope": pref.category_scope,
                "resolved": pref.resolved,
                "resolved_note": pref.resolved_note,
                "created_at": _iso(pref.created_at),
            })

    preference_requests = preference_requests_made + preference_requests_received

    # 6. Current allocations — resolve unit_id to {unit_name, category_name}.
    alloc_rows = await db.execute(
        select(Allocation, AllocationUnit, AllocationCategory)
        .join(AllocationUnit, Allocation.unit_id == AllocationUnit.id)
        .join(
            AllocationCategory,
            AllocationUnit.category_id == AllocationCategory.id,
        )
        .where(
            Allocation.event_id == event_id,
            Allocation.participant_id == participant_id,
        )
        .order_by(AllocationCategory.sort_order, AllocationUnit.sort_order)
    )
    allocations = []
    for alloc, unit, category in alloc_rows.all():
        allocations.append({
            "category_name": category.name,
            "unit_name": unit.name,
            "created_at": _iso(alloc.created_at),
            "updated_at": _iso(alloc.updated_at),
        })

    # 7. Allocation history (coarsened audit trail). Drop actor_user_id
    #    per the locked decision. Use the snapshotted unit/category
    #    names from the audit row itself, not a current join — the
    #    snapshot is the historically-correct view.
    history_rows = await db.execute(
        select(AllocationEvent)
        .where(
            AllocationEvent.event_id == event_id,
            AllocationEvent.participant_id == participant_id,
        )
        .order_by(AllocationEvent.occurred_at)
    )
    allocation_history = []
    for h in history_rows.scalars().all():
        allocation_history.append({
            "event_type": h.event_type,
            "source": h.source,
            "unit_name": h.unit_name_snapshot,
            "category_name": h.category_name_snapshot,
            "meta": h.meta,
            "occurred_at": _iso(h.occurred_at),
        })

    # 8. Notes addressed to this participant. Only published notes
    #    targeting notable_type='participant' with notable_id=participant_id.
    #    Draft/internal admin notes (is_published=False) are the
    #    controller's working notes, not the data subject's data.
    note_rows = await db.execute(
        select(Note)
        .where(
            Note.notable_type == "participant",
            Note.notable_id == participant_id,
            Note.is_published.is_(True),
        )
        .order_by(Note.created_at)
    )
    notes = []
    for n in note_rows.scalars().all():
        notes.append({
            "content": n.content,
            "created_at": _iso(n.created_at),
            "updated_at": _iso(n.updated_at),
        })

    # 9. Check-in values — resolve field_id to field_name.
    cv_rows = await db.execute(
        select(CheckInValue, CheckInField)
        .join(CheckInField, CheckInValue.field_id == CheckInField.id)
        .where(
            CheckInValue.event_id == event_id,
            CheckInValue.participant_id == participant_id,
        )
        .order_by(CheckInField.sort_order)
    )
    checkin_values = []
    for value, field in cv_rows.all():
        checkin_values.append({
            "field_name": field.field_name,
            "checked": value.checked,
            "created_at": _iso(value.created_at),
            "updated_at": _iso(value.updated_at),
        })

    # 10. Participant base slice. Excludes:
    #     - confirmation_token (security-sensitive, no data-subject value)
    #
    # Includes deleted_at when present — for soft-deleted records the
    # timestamp is "the moment the participant asked to be removed,"
    # which is legitimately the data subject's data and useful context
    # in their export. None for non-soft-deleted records.
    participant_slice = {
        "id": str(participant.id),
        "participant_number": participant.participant_number,
        "first_name": participant.first_name,
        "last_name": participant.last_name,
        "email": participant.email,
        "gender": participant.gender,
        "date_of_birth": _iso(participant.date_of_birth),
        "phone": participant.phone,
        "address": participant.address,
        "country": participant.country,
        "church_organisation": participant.church_organisation,
        "message": participant.message,
        "group_code": participant.group_code,
        "group_code_categories": participant.group_code_categories,
        "override_group_room": participant.override_group_room,
        "registration_status": (
            participant.registration_status.value
            if hasattr(participant.registration_status, "value")
            else participant.registration_status
        ),
        "gdpr_consent": participant.gdpr_consent,
        "checked_in": participant.checked_in,
        "checked_in_at": _iso(participant.checked_in_at),
        "preferred_language": participant.preferred_language,
        "created_at": _iso(participant.created_at),
        "updated_at": _iso(participant.updated_at),
        "deleted_at": _iso(participant.deleted_at),
    }

    return {
        "export_metadata": {
            "schema_version": EXPORT_SCHEMA_VERSION,
            "exported_at": _iso(datetime.now(timezone.utc)),
            "kind": "admin_on_behalf_participant_export",
            "notes": (
                "Generated by Moimio's admin-on-behalf data export. "
                "Audit history is coarsened: the identity of admins "
                "who performed allocation moves is not included. "
                "Internal admin draft notes are not included; only "
                "published notes addressed to this participant are."
            ),
        },
        "event": event_slice,
        "participant": participant_slice,
        "custom_fields": custom_fields,
        "marks": marks,
        "preference_requests": preference_requests,
        "allocations": allocations,
        "allocation_history": allocation_history,
        "notes": notes,
        "checkin_values": checkin_values,
    }
