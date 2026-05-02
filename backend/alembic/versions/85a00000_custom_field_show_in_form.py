"""custom_field show_in_form column

Revision ID: 85a00000
Revises: 75a00000
Create Date: 2026-05-01

v0.85 #16: gates a custom field's visibility on the public registration
form. Existing fields default to True (they were created via the
registration setup UI and are meant to be filled in by registrants).
CSV-imported fields default to False (they carry admin-managed data
and shouldn't appear on the public form unless the admin opts them in).
"""

from alembic import op
import sqlalchemy as sa


revision = "85a00000"
down_revision = "75a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NOT NULL with server default so existing rows backfill correctly.
    op.add_column(
        "custom_field_definitions",
        sa.Column(
            "show_in_form",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    # Drop the server default once the column is populated — application-side
    # default takes over for new rows. This matches Moimio's pattern where
    # server_defaults are only for safe back-fills during ALTER TABLE.
    op.alter_column(
        "custom_field_definitions",
        "show_in_form",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("custom_field_definitions", "show_in_form")
