"""v0.50i — events.is_archived column.

Revision ID: 50i00000
Revises: 50f20000
Create Date: 2026-04-18

Adds `is_archived` boolean column to events (default False). Archived
events are hidden from the default list view, rendered read-only across
the admin UI, and reject mutations at the backend via the
`require_event_writable` dependency. Super Admin bypasses all of this.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "50i00000"
down_revision = "50f20000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("events", "is_archived")
