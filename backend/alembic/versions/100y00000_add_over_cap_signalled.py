"""add events.over_cap_signalled (v1.0.0y)

Revision ID: 100y00000
Revises: 100g00000
Create Date: 2026-06-14

v1.0.0y: a single boolean flag on `events`, defaulting to false. It records
whether CE has already emitted an `event.over_cap` signal for that event, so
the signal fires exactly once even as more participants keep registering.

No existing data is meaningfully touched — every current event gets `false`
(none have signalled), which is the correct initial state. Self-hosters who
never configure a participant cap (MOIMIO_PARTICIPANT_CAP) never write to this
column; it simply sits at false.
"""

from alembic import op
import sqlalchemy as sa


revision = "100y00000"
down_revision = "100g00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "over_cap_signalled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("events", "over_cap_signalled")
