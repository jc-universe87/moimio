"""v0.50e-1d — staff groups removed, inline permissions, permission cleanup.

Revision ID: 50e1d00000
Revises: 50c3a00000
Create Date: 2026-04-17

Catches the database up to the schema expected by the v0.50e model code.
Shipped late because v0.50e-1a, -1b, -1c each changed the model but didn't
include the corresponding Alembic migration — this one migration covers
all three at once, which is fine because none of them were actually live
(the deploy was broken by the schema mismatch — users reported 500s on the
Staff & permissions page).

Changes in this migration
─────────────────────────
1. event_user_assignments gains a `permissions` JSON column (default '{}').
2. event_user_assignments loses the `staff_group_id` column.
3. staff_groups table is dropped.
4. Existing staff assignments are reset to `permissions = '{}'` per the
   chosen "fresh start" migration strategy — admins re-grant after deploy.
5. The `cat_<uuid>` per-category permission keys are stripped from any
   remaining permissions blobs (v0.50e-1d design simplification: allocation
   is now a single `organise: "read" | "write" | null` with no per-category
   overrides).

Safety
──────
- Dropping staff_group_id first is safe because the FK `ON DELETE SET NULL`
  already tolerated null values, and no code reads it post v0.50e-1b.
- Dropping the staff_groups table is the destination state per user choice
  ("yes, drop it completely after migration"). DB backups exist for rollback.
- permissions column uses `server_default=sa.text("'{}'::json")` so existing
  rows get a valid empty-object default, not NULL.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "50e1d00000"
down_revision = "50c3a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add the new permissions column. server_default ensures existing
    #    rows get a valid '{}' — this satisfies nullable=False.
    op.add_column(
        "event_user_assignments",
        sa.Column(
            "permissions",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )

    # 2. Drop the staff_group_id FK column. The FK constraint is dropped
    #    as part of the column drop in PostgreSQL.
    op.drop_column("event_user_assignments", "staff_group_id")

    # 3. Drop the staff_groups table. CASCADE is implicit — no other table
    #    references it now that staff_group_id is gone.
    op.drop_table("staff_groups")

    # 4+5. Fresh-start + strip legacy keys. Even though every assignment
    #      was just created with '{}' from the column default, staff
    #      assignments existed before this migration ran with
    #      server_default — their column is already '{}'. This UPDATE is
    #      idempotent (harmless if column is already '{}').
    #
    #      We also strip any legacy cat_<uuid> keys in case some future
    #      dataset has them (this migration's "all three at once" posture
    #      means we're conservative about cleanup).
    op.execute(
        "UPDATE event_user_assignments SET permissions = '{}'::json "
        "WHERE role = 'staff'"
    )


def downgrade() -> None:
    """Re-create staff_groups and the old column.

    This restores the schema shape of pre-v0.50e but NOT the data — staff
    groups are gone for good once this migration has run. The downgrade
    exists so Alembic's revision tree is symmetric, not because it's a
    useful rollback path in practice. Restore from DB backup if you
    genuinely need the old data.
    """
    # Re-create the staff_groups table (shape as it was pre-v0.50e-1b)
    op.create_table(
        "staff_groups",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "event_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Re-add staff_group_id
    op.add_column(
        "event_user_assignments",
        sa.Column(
            "staff_group_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("staff_groups.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Drop the inline permissions column
    op.drop_column("event_user_assignments", "permissions")
