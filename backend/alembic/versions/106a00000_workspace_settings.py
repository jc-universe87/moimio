"""LEGAL-1 — the `workspace_settings` table, one row, one setting.

Revision ID: 106a00000
Revises: 104zd0000
Create Date: 2026-09-19

The public registration form shows one fixed consent sentence and no link,
so an organisation has nowhere to put its own privacy notice, which the
hosted Terms (§10) require it to give participants. The setting is decided
to be workspace-wide, not per event.

There is no workspace table to put a column on: an install IS the
workspace, and every installation-wide value so far has been an environment
variable. An environment variable will not do here, because the
organisation's own admin has to be able to set it from the screen, and on a
hosted tenant they cannot touch the environment. So this is a new table
rather than a new column, deliberately shaped as a singleton: `id` is an
integer primary key that the service always writes as 1, and
`get_or_create` is the only way a row comes into being.

Safe on existing data: it creates an empty table and touches nothing else.
A self-hoster does nothing; the backend image runs `alembic upgrade head` on
start. Until an admin saves a URL there is no row, the public endpoint
answers null, and the form is exactly what it was.

Downgrade drops the table, and with it the one URL an admin may have saved.
That is the whole cost.
"""

from alembic import op
import sqlalchemy as sa


revision = "106a00000"
down_revision = "104zd0000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("privacy_notice_url", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("workspace_settings")
