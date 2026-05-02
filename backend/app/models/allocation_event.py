"""Allocation event — append-only audit log for participant ↔ unit changes.

v0.60a introduces an immutable record of every assign/unassign emitted by
the two write paths (manual via allocation_service, bulk via
engine_service). Purpose:

  - Organiser-facing timeline: "Alice moved from Room A to Room B at 14:32"
  - Per-participant history surfaced in InsightPanel (planned v0.60c)
  - Carrier for engine reasoning (planned v0.60d, via the `meta` JSONB)

Design (see HANDOVER_v0.60.md §v0.60a for full rationale):

  - **Append-only** at the application layer. No service writes UPDATE or
    DELETE against this table. Fresh rows only.

  - **GDPR-compatible via FK nullification.** `participant_id`,
    `actor_user_id`, `unit_id`, `category_id` all use `ON DELETE SET NULL`
    so that right-to-erasure on the referenced subject cascades to null
    without rewriting audit rows. The structural record survives.

  - **Snapshotted unit + category names.** `unit_name_snapshot` and
    `category_name_snapshot` capture the human-readable names at event
    time. This ensures history reads stay truthful after renames
    ("Room A" → "Lobby") and survives unit/category deletion. Names are
    non-PII so snapshotting is GDPR-neutral.

  - **No participant name snapshot.** Participant names ARE PII; keeping
    a snapshot would require a scrub job on erasure. Instead, reads join
    to `participants` and render "[removed participant]" when the FK is
    NULL. The operational cost: you can't distinguish multiple erased
    participants in old log entries. Accepted tradeoff for a church
    retreat platform where audit forensics across deleted subjects is a
    vanishing use case.

  - **`event_id` CASCADES.** When an entire event is hard-deleted, its
    audit trail goes with it. No orphan audit events referring to a
    non-existent event.

  - **`meta` JSONB nullable.** Reserved for engine reasoning payloads
    shipping in v0.60d ("placed by preference match with X", "balanced
    by gender after 3 attempts", etc). v0.60a leaves it null.

Why not a Postgres enum for `event_type` / `source`?
  We want to add new source labels without migrations (e.g. future
  batch-import paths). String columns with Python-side enums give
  type safety in the app without locking the DB.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ─── Python-side enums (string constants, not SAEnum) ─────────────────
#
# Exposed as module constants so callers import by name and type-checkers
# catch typos. Stored as plain TEXT in the DB so we can add values
# without migrations.

class AllocationEventType:
    ASSIGN = "assign"
    UNASSIGN = "unassign"

    ALL = frozenset({ASSIGN, UNASSIGN})


class AllocationEventSource:
    # Manual organiser action via allocation_service.assign/unassign.
    MANUAL = "manual"

    # Silent cascade inside assign_participant for exclusive categories —
    # when assigning a participant to an exclusive category unit, any
    # existing allocation in other units of the same category is
    # deleted. Those deletions emit an unassign event with this source.
    MANUAL_CASCADE = "manual_cascade"

    # Manual "Clear category" button — clear_category_allocations called
    # from the API endpoint (not from commit_proposal).
    CLEAR_CATEGORY = "clear_category"

    # Engine commit — commit_proposal writes a batch of assignments,
    # preceded by a clear of existing allocations in the category. Both
    # the cleared unassigns and the new assigns carry this source.
    ENGINE_COMMIT = "engine_commit"

    # v0.70d-2a-2: participant's registration_status flipped to
    # 'cancelled'. Their allocations across ALL categories are
    # auto-removed and each emits an unassign event with this source —
    # so the audit trail distinguishes cleanups driven by withdrawal
    # from organiser-initiated unassigns. Cancelled participants stay
    # visible in PeopleTable with a cancelled status pill; they just
    # no longer occupy a spot anywhere.
    PARTICIPANT_CANCELLED = "participant_cancelled"

    ALL = frozenset({MANUAL, MANUAL_CASCADE, CLEAR_CATEGORY, ENGINE_COMMIT, PARTICIPANT_CANCELLED})


# ─── ORM model ────────────────────────────────────────────────────────

class AllocationEvent(Base):
    """Immutable audit row for a single assign or unassign action."""

    __tablename__ = "allocation_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The event (retreat/session) this happened in. CASCADE: if the
    # whole event is deleted, its audit trail goes too.
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The participant being moved. SET NULL on delete: erasure
    # cascades. Read-side renders "[removed participant]" when null.
    participant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("participants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # The unit the participant was assigned to / unassigned from.
    # SET NULL on delete — we still have unit_name_snapshot for display.
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("allocation_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # The category the unit belonged to, snapshotted so category-level
    # timelines remain queryable even after unit deletion. SET NULL
    # because a category may be deleted entirely.
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("allocation_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Who did it. Null for events where attribution isn't known (e.g.
    # future system-triggered commits, or after user deletion).
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # "assign" | "unassign". See AllocationEventType.
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Origin of the event. See AllocationEventSource.
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    # Human-readable name snapshots — preserve display even after rename
    # or deletion of the referenced unit/category. Non-PII, GDPR-neutral.
    # Unit name is required because every event necessarily involves a
    # unit at the time it fires; category name follows from the unit.
    unit_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    category_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)

    # Reserved for engine reasoning (v0.60d+). Examples:
    #   {"reason": "preference_match", "matched_with": ["<uuid>"]}
    #   {"reason": "gender_balance", "attempts": 3}
    #   {"reason": "fill_order"}
    # Left null by v0.60a write paths.
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # When the event fired. Server default = clock_timestamp() (per-
    # statement wall-clock) rather than now() (= transaction_timestamp,
    # which returns an identical value for every row inserted in the
    # same transaction). Multiple events emitted within a single service
    # call — e.g. the paired unassign+assign of a move within an
    # exclusive category — need distinct timestamps so the timeline
    # orders them correctly. Indexed for timeline-ordered reads.
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.clock_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        # Primary read pattern: "timeline for this event, newest first".
        Index(
            "ix_allocation_events_event_occurred",
            "event_id",
            "occurred_at",
        ),
        # Secondary: "history for this participant in this event".
        Index(
            "ix_allocation_events_event_participant",
            "event_id",
            "participant_id",
        ),
    )
