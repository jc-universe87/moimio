"""v50b baseline — frozen v50b schema snapshot.

Revision ID: 50b00000_baseline
Revises:
Create Date: 2026-04-16 (initial) / 2026-04-19 (rewrite to use snapshot)

This baseline creates the schema as it was at v0.50b — exactly. Every
subsequent migration in this chain (50c3a00000, 50e1d00000, …) is an
additive delta on top of this frozen state, and reproduces the v0.50t→
v0.51→v0.52 schema evolution step by step.

History of this file
────────────────────
v0.50b through v0.51.1 the upgrade() body was
    Base.metadata.create_all(bind=bind)
using the current app.core.database.Base. Because `Base.metadata` tracks
the *current* models (not the v50b snapshot), `create_all` produced the
LATEST schema every time it ran. Subsequent ADD COLUMN migrations then
crashed with DuplicateColumnError on fresh installs — the columns they
were adding had already been created by the baseline.

v0.52 fixes this by introducing a frozen v50b model snapshot under
app._alembic_snapshots.v50b. That package has its own isolated
DeclarativeBase, so its metadata contains ONLY the v50b tables as they
existed at v0.50b (18 tables, including staff_groups which was later
removed in 50e1d00000, and WITHOUT the `confirmed` column on
allocation_categories which was added in 50c3a00000).

Fresh-install flow now:
  1. Baseline → frozen v50b schema (18 tables, v50b columns)
  2. 50c3a00000 → add `confirmed` to allocation_categories
  3. 50e1d00000 → drop staff_groups, add permissions JSON column
  4. 50f00000 / 50f20000 → marks audit columns
  5. 50i00000 → add is_archived to events
  6. 50j00000 → remove EVENT_ADMIN user role
  7. 50q00000 → enum label case migration (no-op on fresh)
  → Schema matches app.core.database.Base.metadata at v0.52.

Existing-install flow (your DB is already at head):
  Alembic sees alembic_version already == '50q00000', does nothing.
  Baseline is not re-run. No schema touch.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "50b00000_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the v50b schema from the frozen snapshot.

    Deferred import: we only need the snapshot Base when this migration
    actually runs. Keeping it inside upgrade() avoids top-level import
    churn and means the snapshot package is never touched on existing
    installs (where this migration is already marked applied).
    """
    from app._alembic_snapshots.v50b import Base as V50bBase
    bind = op.get_bind()
    V50bBase.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop everything the baseline created. Symmetric with upgrade()."""
    from app._alembic_snapshots.v50b import Base as V50bBase
    bind = op.get_bind()
    V50bBase.metadata.drop_all(bind=bind)
