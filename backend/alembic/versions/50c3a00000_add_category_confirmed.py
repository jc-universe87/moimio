"""v50c-3a — add confirmed column to allocation_categories.

Revision ID: 50c3a00000
Revises: 50b00000_baseline
Create Date: 2026-04-16

Per §12.3 allocation lifecycle. Each category tracks whether the organiser
has confirmed its allocation. Default False — existing rows migrate as
"In Progress", which is the correct interpretation for data that pre-dates
the feature.

This migration is non-destructive: ADD COLUMN with a server default, so
existing rows are filled and no data is lost.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "50c3a00000"
down_revision = "50b00000_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "allocation_categories",
        sa.Column(
            "confirmed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("allocation_categories", "confirmed")
