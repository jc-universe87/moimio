"""v1.0.3 — capacity 0 means "no capacity limit"; retire the two dead flags.

Two things happen here, both data-only. No schema changes.

1. THE PLACEHOLDER CLEAN-UP (the reason this migration exists).

   Before v1.0.3, a group type carried a ``has_capacity`` switch. When it
   was off, the interface hid the capacity box, but the save path still
   wrote a placeholder capacity of **1** to every unit — and the allocation
   engine has enforced unit capacity as a hard limit since v0.74,
   regardless of the switch. Small Groups was created with the switch off
   by default, so a newly created event could allocate exactly one person
   per group and report everybody else as having no space.

   From v1.0.3 a capacity of 0 means "no limit". This migration converts
   the placeholder rows to 0.

   The WHERE clause is deliberately narrow: capacity is exactly 1 AND the
   unit's group type had the capacity switch off. That pair is the
   placeholder's signature — with the switch off, the box was not
   rendered, so the value cannot have been typed by a person.

   NOT touched: a unit sitting at 1 in a group type whose switch was ON.
   That is indistinguishable from a genuine single-bed room, and the
   organiser could see and edit the field, so it is left exactly as it is.

2. THE FLAGS ARE PINNED ON.

   ``has_capacity`` and ``has_gender_restriction`` are no longer read by
   any code path. They are set true everywhere and kept in the table for
   one release, because old backup archives and old layout exports still
   carry them. Pinning them true (rather than dropping the columns) means
   that if a workspace is ever rolled back to 1.0.2c, the older interface
   shows the capacity and gender fields rather than hiding them, which is
   the recoverable direction.

   Rollback warning: 1.0.2c and earlier read a capacity of 0 as room for
   nobody. Downgrading a workspace after units have been saved with no
   capacity limit will leave people unallocated until this migration is
   reversed. ``downgrade()`` reverses the conversion exactly, because 0
   was not a reachable value before this release.
"""

from alembic import op
import sqlalchemy as sa


revision = "103a00000"
down_revision = "101e00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(sa.text("""
        UPDATE allocation_units AS u
        SET capacity = 0
        FROM allocation_categories AS c
        WHERE u.category_id = c.id
          AND u.capacity = 1
          AND c.has_capacity = false
    """))
    print(
        f"[v1.0.3] units released from the hidden capacity-1 placeholder: "
        f"{result.rowcount}"
    )

    conn.execute(sa.text("""
        UPDATE allocation_categories
        SET has_capacity = true, has_gender_restriction = true
        WHERE has_capacity = false OR has_gender_restriction = false
    """))

    conn.execute(sa.text("""
        COMMENT ON COLUMN allocation_units.capacity
        IS 'Maximum occupants. 0 = no capacity limit (v1.0.3).'
    """))
    conn.execute(sa.text("""
        COMMENT ON COLUMN allocation_categories.has_capacity
        IS 'DEPRECATED v1.0.3 — ignored. Capacity is available on every group type.'
    """))
    conn.execute(sa.text("""
        COMMENT ON COLUMN allocation_categories.has_gender_restriction
        IS 'DEPRECATED v0.74, ignored everywhere since v1.0.3.'
    """))


def downgrade() -> None:
    """Reverse the capacity conversion. Exact: 0 was unreachable before v1.0.3.

    The flags are NOT restored to their old values — which of them were off
    is not recorded anywhere, and leaving them on is the safe direction (an
    older interface then shows the fields instead of hiding them).
    """
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        UPDATE allocation_units SET capacity = 1 WHERE capacity = 0
    """))
    print(f"[v1.0.3 downgrade] units returned to capacity 1: {result.rowcount}")
    conn.execute(sa.text(
        "COMMENT ON COLUMN allocation_units.capacity IS NULL"
    ))
