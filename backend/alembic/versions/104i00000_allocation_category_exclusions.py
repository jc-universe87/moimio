"""v1.0.4i — allocation_category_exclusions: keep a participant out of a group type.

Revision ID: 104i00000
Revises: 104a00000
Create Date: 2026-09-13

One row per (group type, participant) pair the organiser has excluded.
An excluded participant is one the allocation engine must not place in
that group type. This release adds the table, the model, the service
functions and the endpoints only; the engine does not yet read it and
nothing changes on screen.

Design:

  - Both FKs CASCADE. An exclusion is meaningless without either side:
    when the group type goes, so do its exclusions; when a participant
    is deleted (GDPR erasure included) their exclusion rows go with
    them. There is nothing to preserve here, unlike allocation_events.

  - UNIQUE (allocation_category_id, participant_id). A participant is
    either excluded from a group type or not; a second row would say
    nothing new.

  - Index on allocation_category_id alone: the read pattern is "who is
    excluded from this group type", both for the board and for the
    engine pre-filter that follows in a later release. There is no
    index on participant_id by itself, so the cascade fired by a
    participant delete scans this table. It holds a handful of rows
    per event, so that is cheap; add the index if that ever changes.

  - created_by nullable, no FK. Who excluded the participant is also
    written to allocation_events (event_type exclude/include), which
    is the audit surface. This column is a convenience that must not
    block user deletion.

Downgrade: drop the table. Nothing else references it.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "104i00000"
down_revision = "104a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "allocation_category_exclusions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "allocation_category_id",
            UUID(as_uuid=True),
            sa.ForeignKey("allocation_categories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint(
            "allocation_category_id", "participant_id",
            name="uq_category_exclusion_category_participant",
        ),
    )

    op.create_index(
        "ix_allocation_category_exclusions_allocation_category_id",
        "allocation_category_exclusions",
        ["allocation_category_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_allocation_category_exclusions_allocation_category_id",
        table_name="allocation_category_exclusions",
    )
    op.drop_table("allocation_category_exclusions")
