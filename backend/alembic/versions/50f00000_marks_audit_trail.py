"""v0.50f — marks audit trail (created_by_user_id on mark_definitions).

Revision ID: 50f00000
Revises: 50e1d00000
Create Date: 2026-04-18

Adds a nullable `created_by_user_id` column to mark_definitions so the
marks system can attribute authorship. This enables:
  1. Creator-based ownership (v0.50f): staff with marks:write can only
     edit/delete marks they created; admin can edit/delete any.
  2. Audit trail UI: "Created by Alice" shown in MarksPanel.

Nullable because existing marks predate this column. ON DELETE SET NULL
so that when a user is deleted the mark survives, losing attribution
rather than cascading away.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "50f00000"
down_revision = "50e1d00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mark_definitions",
        sa.Column(
            "created_by_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("mark_definitions", "created_by_user_id")
