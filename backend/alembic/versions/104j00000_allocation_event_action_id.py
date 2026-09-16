"""v1.0.4j — allocation_events.action_id: groups the rows one action wrote.

Revision ID: 104j00000
Revises: 104i00000
Create Date: 2026-09-15

From v1.0.4j, excluding a participant from a group type also removes
them from every unit they hold in it. One exclude action therefore
writes several history rows: one `exclude` plus one `unassign` per unit
vacated. The table has a single unit_id and unit_name_snapshot per row,
so these cannot merge into one stored row without losing which units
were vacated. They are collapsed on screen instead (v1.0.4k), and that
needs a shared marker.

Design:

  - Plain UUID, nullable, no FK, no index. There is no actions table
    to reference, a handful of rows share each value, and nothing
    queries on it yet. Revisit the index when the read path exists.

  - Not a timestamp fallback. occurred_at uses clock_timestamp(), a
    per-statement wall clock, chosen so rows written in one transaction
    get DISTINCT timestamps and order correctly. Rows from one action
    are therefore guaranteed not to share a timestamp; this column is
    the only grouping mechanism.

  - No backfill. Existing rows keep NULL, which readers must treat as
    "ungrouped, render individually".

Downgrade: drop the column. Nothing else references it.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "104j00000"
down_revision = "104i00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "allocation_events",
        sa.Column("action_id", UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("allocation_events", "action_id")
