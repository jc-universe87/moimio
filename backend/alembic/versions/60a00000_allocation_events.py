"""v0.60a — allocation_events append-only audit table.

Revision ID: 60a00000
Revises: 50q00000
Create Date: 2026-04-22

Creates the `allocation_events` audit table. This is the foundation of the
v0.60 "engine + history" arc: every assign/unassign emitted by the
allocation service (manual path) and the engine service (bulk path) will
write a row here from v0.60a onward.

Design decisions (full context in HANDOVER_v0.60.md §v0.60a):

  - Table is append-only at the app layer; no UPDATE or DELETE from
    application code. GDPR erasure of referenced subjects works via
    FK ON DELETE SET NULL on participant_id, unit_id, category_id,
    actor_user_id. The structural audit row survives; identifying
    references nullify.

  - event_id uses ON DELETE CASCADE. If the parent event is hard-
    deleted, its audit trail goes with it. This mirrors existing
    behaviour for other event-scoped tables (mark_assignments,
    allocations, etc.) and avoids orphaned audit rows referring to a
    non-existent event.

  - unit_name_snapshot / category_name_snapshot are NOT NULL strings.
    Names are non-PII so retaining them survives rename and deletion
    of the unit/category. Participant name is NOT snapshotted (PII —
    would need erasure scrubbing); reads render "[removed participant]"
    when participant_id is NULL.

  - Two indexes: (event_id, occurred_at) for timeline reads,
    (event_id, participant_id) for per-participant history. Both are
    declared in the model's __table_args__; create_all and this
    migration produce the same result.

  - meta is JSONB nullable. Reserved for engine reasoning payloads
    shipping in v0.60d. Leave null from v0.60a write paths.

Downgrade: drop the table. No data dependency elsewhere in v0.60a
(no other tables reference allocation_events).
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = "60a00000"
down_revision = "50q00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "allocation_events",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "event_id",
            UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "unit_id",
            UUID(as_uuid=True),
            sa.ForeignKey("allocation_units.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            UUID(as_uuid=True),
            sa.ForeignKey("allocation_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "actor_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("unit_name_snapshot", sa.String(100), nullable=False),
        sa.Column("category_name_snapshot", sa.String(100), nullable=False),
        sa.Column("meta", JSONB, nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.clock_timestamp(),
            nullable=False,
        ),
    )

    # Timeline read — "most recent changes in this event".
    op.create_index(
        "ix_allocation_events_event_occurred",
        "allocation_events",
        ["event_id", "occurred_at"],
    )

    # Per-participant history — "what happened to this person".
    op.create_index(
        "ix_allocation_events_event_participant",
        "allocation_events",
        ["event_id", "participant_id"],
    )

    # Index on participant_id alone for cross-event lookups and
    # erasure-performance when cascading SET NULL fires.
    op.create_index(
        "ix_allocation_events_participant_id",
        "allocation_events",
        ["participant_id"],
    )

    # Indexes to support ON DELETE SET NULL performance on the other
    # nullable FKs. Postgres doesn't auto-index FK children.
    op.create_index(
        "ix_allocation_events_unit_id",
        "allocation_events",
        ["unit_id"],
    )
    op.create_index(
        "ix_allocation_events_category_id",
        "allocation_events",
        ["category_id"],
    )


def downgrade() -> None:
    # Indexes drop with the table, but be explicit for symmetry and
    # to catch any accidental residue from partial re-runs.
    op.drop_index("ix_allocation_events_category_id", table_name="allocation_events")
    op.drop_index("ix_allocation_events_unit_id", table_name="allocation_events")
    op.drop_index("ix_allocation_events_participant_id", table_name="allocation_events")
    op.drop_index("ix_allocation_events_event_participant", table_name="allocation_events")
    op.drop_index("ix_allocation_events_event_occurred", table_name="allocation_events")
    op.drop_table("allocation_events")
