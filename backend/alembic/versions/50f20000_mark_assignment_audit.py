"""v0.50f-2 — marks assignment audit (assigned_by_user_id on mark_assignments).

Revision ID: 50f20000
Revises: 50f00000
Create Date: 2026-04-18

Adds a nullable `assigned_by_user_id` column to mark_assignments so we
can attribute who assigned a mark to a participant. The MarkAssignModal
surfaces this as "Assigned by Alice, 3 days ago" under each currently
assigned mark.

Nullable because pre-v0.50f-2 assignments have no known assigner. ON
DELETE SET NULL so the assignment survives user deletion, losing only
the attribution.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "50f20000"
down_revision = "50f00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mark_assignments",
        sa.Column(
            "assigned_by_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("mark_assignments", "assigned_by_user_id")
