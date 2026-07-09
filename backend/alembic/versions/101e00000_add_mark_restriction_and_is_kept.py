"""add allocation_units.mark_restriction + is_kept (v1.0.1e)

Revision ID: 101e00000
Revises: 100y00000
Create Date: 2026-07-09

v1.0.1e adds two optional room-level controls, both mirroring the shape of the
existing gender_restriction column so nothing new is introduced conceptually:

  - mark_restriction — nullable FK to mark_definitions.id (ON DELETE SET NULL).
    When set, only participants carrying that mark may be placed in the unit.
    SET NULL means deleting a mark quietly lifts any restriction that used it,
    rather than blocking the delete or orphaning the reference.

  - is_kept — a boolean, default false. When true the unit is "kept as-is" and
    left untouched on re-allocate.

No existing data is meaningfully touched: every current unit gets
mark_restriction = NULL (unrestricted, as today) and is_kept = false (not
frozen), which are the correct initial states.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "101e00000"
down_revision = "100y00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "allocation_units",
        sa.Column("mark_restriction", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_allocation_units_mark_restriction",
        "allocation_units",
        "mark_definitions",
        ["mark_restriction"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "allocation_units",
        sa.Column(
            "is_kept",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_allocation_units_mark_restriction",
        "allocation_units",
        type_="foreignkey",
    )
    op.drop_column("allocation_units", "is_kept")
    op.drop_column("allocation_units", "mark_restriction")
