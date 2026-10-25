"""custom_field show_if column

Revision ID: 107a00000
Revises: 106a00000
Create Date: 2026-10-24

Conditional registration fields: a custom field may be shown on the form
only when an earlier answer matches ("Teamer" is Yes, or the person is
under 18). The rule is a small JSON object on the field; the shapes are
documented in app/services/field_conditions.py.

The same release adds the `info` field type (text from the organiser that
nobody fills in). That needs no schema change: `field_type` is a string and
the text lives in the existing `options` JSON.

Safe on existing data: a nullable column with no default, so every
existing field reads as "always shown", which is what it is today.
Downgrade drops the rules; the fields themselves stay, always shown.
"""

from alembic import op
import sqlalchemy as sa


revision = "107a00000"
down_revision = "106a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "custom_field_definitions",
        sa.Column("show_if", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("custom_field_definitions", "show_if")
