"""v0.50q — Rename enum labels from UPPERCASE to lowercase.

Revision ID: 50q00000
Revises: 50j00000
Create Date: 2026-04-19

Context
-------
Three Postgres enum types in this database — `user_role`, `event_status`,
and `registration_status` — were originally created with UPPERCASE labels
(`SUPER_ADMIN`, `STAFF`, `DRAFT`, `OPEN`, …) because SQLAlchemy's default
`SAEnum(MyEnum)` uses each member's **name** as the label. The Python
enum **values** are lowercase strings, so there was a persistent mismatch:
app code handles lowercase (via the ORM's automatic name↔value translation),
but every migration touching an enum column had to remember to use
UPPERCASE literals in raw SQL. This mismatch bit us three times during
the v0.50j arc (event admin role removal).

Fix
---
In v0.50q the models declare `values_callable=lambda e: [m.value for m in e]`
on each SAEnum column. That makes SQLAlchemy generate Postgres labels from
the Python **values** (lowercase) going forward — fresh installs get
lowercase labels out of the box.

This migration renames existing UPPERCASE labels to lowercase on
already-deployed databases via `ALTER TYPE ... RENAME VALUE`, which:
  - Is atomic per statement
  - Does NOT touch row data (enum labels are resolved by OID internally,
    so existing rows continue to refer to the same values under their new
    label spelling)
  - Is idempotent-unsafe: running it a second time errors with
    "enum value ... does not exist". Hence the defensive check below.

Safety
------
- Fresh installs: 50b baseline's `create_all()` now uses the v0.50q models
  → enum labels created as lowercase → this migration finds no UPPERCASE
  labels to rename → skips all branches silently.
- Existing installs (UPPERCASE labels): this migration finds them, renames.
- Partial state (mixed — shouldn't happen but defensive): each rename is
  guarded independently.

Downgrade
---------
Reverse each rename. Same safety properties, same idempotence guard.
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "50q00000"
down_revision = "50j00000"
branch_labels = None
depends_on = None


# ( (enum_type_name, [(upper, lower), ...]), ... )
# Keep this table in sync with the Python enums in app.models.
# The ordering matters only for the log output — renames are independent.
ENUMS_TO_RENAME: list[tuple[str, list[tuple[str, str]]]] = [
    ("user_role", [
        ("SUPER_ADMIN", "super_admin"),
        ("STAFF",       "staff"),
    ]),
    ("event_status", [
        ("DRAFT",    "draft"),
        ("OPEN",     "open"),
        ("CLOSED",   "closed"),
        ("ARCHIVED", "archived"),
    ]),
    ("registration_status", [
        ("PENDING",   "pending"),
        ("CONFIRMED", "confirmed"),
        ("CANCELLED", "cancelled"),
    ]),
]


def _current_labels(conn, enum_type: str) -> set[str]:
    """Return the set of labels currently defined for a Postgres enum type."""
    rows = conn.execute(
        text(f"SELECT unnest(enum_range(NULL::{enum_type}))::text AS label")
    ).fetchall()
    return {r[0] for r in rows}


def _safe_label(label: str) -> str:
    """Guard against anything that's not a plain ASCII enum-label identifier.

    ALTER TYPE ... RENAME VALUE does NOT accept bound parameters — the
    literals must be inline in the SQL string. Our labels come from the
    hardcoded ENUMS_TO_RENAME table (not user input), but we still
    defensively validate to avoid any chance of an injection vector if
    this helper is ever reused.
    """
    import re
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", label):
        raise ValueError(f"Refusing to use label {label!r} in raw SQL")
    return label


def upgrade() -> None:
    conn = op.get_bind()
    for enum_type, pairs in ENUMS_TO_RENAME:
        # Validate the enum type name too.
        _safe_label(enum_type)
        labels = _current_labels(conn, enum_type)
        for upper, lower in pairs:
            if upper in labels and lower not in labels:
                # ALTER TYPE ... RENAME VALUE requires inline SQL literals
                # — it's a DDL statement and Postgres doesn't allow bound
                # parameters here. Labels are validated by _safe_label;
                # single quotes are safe because the regex excludes them.
                safe_old = _safe_label(upper)
                safe_new = _safe_label(lower)
                conn.execute(text(
                    f"ALTER TYPE {enum_type} RENAME VALUE '{safe_old}' TO '{safe_new}'"
                ))
            # Silent skip for: (a) already-lowercase on fresh install,
            # (b) already-renamed on re-run, (c) partial state where
            # both variants somehow exist (leave things alone, require
            # manual intervention rather than making it worse).


def downgrade() -> None:
    conn = op.get_bind()
    # Reverse direction: lowercase → UPPERCASE, iterate enums in reverse order
    for enum_type, pairs in reversed(ENUMS_TO_RENAME):
        _safe_label(enum_type)
        labels = _current_labels(conn, enum_type)
        for upper, lower in pairs:
            if lower in labels and upper not in labels:
                safe_old = _safe_label(lower)
                safe_new = _safe_label(upper)
                conn.execute(text(
                    f"ALTER TYPE {enum_type} RENAME VALUE '{safe_old}' TO '{safe_new}'"
                ))
