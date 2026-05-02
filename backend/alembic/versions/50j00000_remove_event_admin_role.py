"""v0.50j — remove EVENT_ADMIN from user_role enum + add users.can_create_events.

Revision ID: 50j00000
Revises: 50i00000
Create Date: 2026-04-18

v0.50j-2: original fix for enum case-sensitivity. SAEnum used Python member
NAMES (uppercase), so the actual Postgres labels were 'SUPER_ADMIN',
'EVENT_ADMIN', 'STAFF'. This migration's raw SQL used those uppercase
literals.

v0.50q: models now declare `values_callable=lambda e: [m.value for m in e]`
on SAEnum, which makes SQLAlchemy use Python VALUES (lowercase) as Postgres
labels going forward. Fresh installs created with v0.50q+ models get
'super_admin' / 'staff' as the actual labels — no UPPERCASE.

This migration runs in TWO distinct contexts now:

  (A) Legacy upgrade path: database has UPPERCASE labels from the original
      50b baseline run + 50j creating 'SUPER_ADMIN', 'EVENT_ADMIN', 'STAFF'.
      When this migration runs (after 50i), it still sees UPPERCASE labels.
      It rebuilds the enum to keep only SUPER_ADMIN + STAFF. Then the
      later 50q migration renames both to lowercase.

  (B) Fresh install path (post-v0.50q): 50b baseline uses v0.50q models,
      creating the enum with just 'super_admin' + 'staff' (lowercase, no
      EVENT_ADMIN ever existed). When this migration runs, there is no
      EVENT_ADMIN variant at all — only super_admin/staff in lowercase.
      The migration must still run cleanly: add can_create_events column
      (already there from baseline), backfill for super_admin, and skip
      the EVENT_ADMIN reassignment / enum rebuild entirely.

The helper `_user_role_label` below looks up which casing of a given
conceptual label ('super_admin', 'event_admin', 'staff') is actually
present in the user_role enum, and returns the correct string — letting
the migration's SQL use the right literal regardless of which path we're on.

Scope (case A — pre-v0.50j DB, UPPERCASE enum):
  1. Add `users.can_create_events`.
  2. Backfill TRUE for EVENT_ADMIN + SUPER_ADMIN.
  3. Grant explicit per-event admin assignments to EVENT_ADMIN creators.
  4. Reassign EVENT_ADMIN users to STAFF.
  5. Rebuild the user_role ENUM without EVENT_ADMIN.

Scope (case B — fresh v0.50q install, lowercase enum, no EVENT_ADMIN):
  1. Skip column add (already there from baseline).
  2. Backfill TRUE for super_admin.
  3. Skip EVENT_ADMIN cleanup entirely — there's nothing to clean.

EventUserAssignment.role is a String column (not an ENUM), so per-event
'event_admin' role labels there remain lowercase and untouched.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "50j00000"
down_revision = "50i00000"
branch_labels = None
depends_on = None


def _enum_has_value(conn, enum_name: str, value: str) -> bool:
    """Return True iff the given Postgres ENUM type has `value` as a label."""
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname = :enum_name
              AND e.enumlabel = :value
            LIMIT 1
            """
        ),
        {"enum_name": enum_name, "value": value},
    ).first()
    return result is not None


def _user_role_label(conn, conceptual: str) -> str | None:
    """Return the actual Postgres label for a conceptual user_role value.

    Looks for both lowercase (v0.50q+) and UPPERCASE (legacy) forms and
    returns whichever currently exists in the enum. Returns None if
    neither exists (e.g. asking for EVENT_ADMIN on a fresh install).

    Used so this migration's raw SQL can quote the right literal
    regardless of which casing convention the database was created under.
    """
    lower = conceptual.lower()
    upper = conceptual.upper()
    if _enum_has_value(conn, "user_role", lower):
        return lower
    if _enum_has_value(conn, "user_role", upper):
        return upper
    return None


def upgrade() -> None:
    conn = op.get_bind()
    # v0.50q: detect actual label casing; event_admin_exists is True
    # only if the enum still has that conceptual value (in EITHER casing).
    event_admin_label = _user_role_label(conn, "event_admin")
    super_admin_label = _user_role_label(conn, "super_admin")
    event_admin_exists = event_admin_label is not None

    # ─── 1. Add can_create_events column (default False) ────────────────
    col_exists = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'can_create_events'
            LIMIT 1
            """
        )
    ).first()
    if not col_exists:
        op.add_column(
            "users",
            sa.Column(
                "can_create_events",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    # ─── 2. Backfill can_create_events ──────────────────────────────────
    # v0.50q: construct the IN-list from actual labels, not hardcoded.
    # super_admin_label should always be present (every DB has it) but
    # we defend against the weird case where neither variant exists —
    # then there's nothing to backfill and we skip.
    backfill_labels: list[str] = []
    if super_admin_label:
        backfill_labels.append(super_admin_label)
    if event_admin_label:
        backfill_labels.append(event_admin_label)
    if backfill_labels:
        in_list = ", ".join(f"'{lbl}'" for lbl in backfill_labels)
        op.execute(
            f"UPDATE users SET can_create_events = TRUE "
            f"WHERE role::text IN ({in_list})"
        )

    # ─── 3/4/5. EVENT_ADMIN → STAFF reassignment, enum rebuild ──────────
    if not event_admin_exists:
        # Fresh install on v0.50q+ or already-cleaned-up DB. Nothing to
        # reassign or rebuild. The enum already has only {super_admin, staff}
        # (in whatever casing), which matches what we want post-50j.
        return

    # Convert the enum column to text so we can drop and recreate the type.
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT")

    # Grant per-event admin assignments to EVENT_ADMIN users who created
    # events they don't already have an assignment on. Pre-v0.50j the
    # system role implicitly granted access; post-v0.50j it must be
    # materialised explicitly.
    #
    # NOTE: EventUserAssignment.role is a String(20), NOT an enum, and
    # uses the lowercase literal 'event_admin' (matches the rest of the
    # codebase). Don't confuse it with the user_role enum's labels.
    import uuid as _uuid
    rows = conn.execute(
        sa.text(
            """
            SELECT e.id AS event_id, u.id AS user_id
            FROM users u
            JOIN events e ON e.created_by = u.id
            WHERE u.role = :event_admin_label
              AND NOT EXISTS (
                  SELECT 1 FROM event_user_assignments a
                  WHERE a.event_id = e.id AND a.user_id = u.id
              )
            """
        ),
        {"event_admin_label": event_admin_label},
    ).fetchall()
    for row in rows:
        conn.execute(
            sa.text(
                "INSERT INTO event_user_assignments "
                "(id, event_id, user_id, role, permissions, created_at) "
                "VALUES (:id, :event_id, :user_id, 'event_admin', '{}', NOW())"
            ),
            {
                "id": str(_uuid.uuid4()),
                "event_id": str(row.event_id),
                "user_id": str(row.user_id),
            },
        )

    # Reassign EVENT_ADMIN → the staff label (whatever its casing is).
    staff_label = _user_role_label(conn, "staff") or "staff"
    op.execute(
        sa.text("UPDATE users SET role = :staff WHERE role = :event_admin")
        .bindparams(staff=staff_label, event_admin=event_admin_label)
    )

    # Rebuild the enum without EVENT_ADMIN. Use the SAME casing the
    # existing labels were in — 50q will handle the lowercase migration
    # later in the chain on databases that still have UPPERCASE.
    op.execute("DROP TYPE user_role")
    new_super = super_admin_label or "super_admin"
    op.execute(
        f"CREATE TYPE user_role AS ENUM ('{new_super}', '{staff_label}')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role "
        "USING role::user_role"
    )


def downgrade() -> None:
    conn = op.get_bind()
    # Case-aware downgrade: handle both UPPERCASE (legacy) and lowercase
    # (v0.50q+) enum label conventions.
    event_admin_label = _user_role_label(conn, "event_admin")
    if event_admin_label is not None:
        # EVENT_ADMIN still present (shouldn't be in normal downgrade but
        # guard against rerun). Just drop the column.
        op.drop_column("users", "can_create_events")
        return

    super_admin_label = _user_role_label(conn, "super_admin") or "SUPER_ADMIN"
    staff_label = _user_role_label(conn, "staff") or "STAFF"
    # Re-add EVENT_ADMIN using the same casing convention the DB is on.
    # If existing labels are lowercase (v0.50q+ era), re-add as 'event_admin';
    # if UPPERCASE, re-add as 'EVENT_ADMIN'.
    re_add_label = "event_admin" if super_admin_label.islower() else "EVENT_ADMIN"

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT")
    op.execute("DROP TYPE user_role")
    op.execute(
        f"CREATE TYPE user_role AS ENUM "
        f"('{super_admin_label}', '{re_add_label}', '{staff_label}')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role "
        "USING role::user_role"
    )
    op.drop_column("users", "can_create_events")
