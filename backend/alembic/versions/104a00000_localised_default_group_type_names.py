"""v1.0.4 — default group type names follow the reader's language.

Adds two nullable markers to allocation_categories:

    name_key        e.g. 'rooms', 'small_groups'
    item_label_key  e.g. 'room', 'group'

While a marker is set, the interface and the PDF each render that name in
their own language. The moment the organiser types a name of their own the
marker is cleared and the text is theirs for good. A group type the
organiser creates never has a marker at all.

BACKFILL
--------
Existing events should benefit too, not just new ones, so this backfills
the markers onto built-in group types that still carry their original
English names.

The WHERE clause is narrow on purpose. It requires BOTH that the row was
created as a built-in (`is_default`) AND that the text is still exactly
what we shipped. An organiser who renamed Rooms to "Chalets" keeps
"Chalets" and gets no marker, which is correct: that name is theirs.

Name and item label are backfilled independently, because they are edited
independently. Renaming the type to "Dorms" while leaving the item label
as "Room" leaves the label translatable and the name theirs.

DOWNGRADE
---------
Drops both columns. Nothing is lost that cannot be recreated: `name` has
carried the English text all along, so a downgraded workspace simply shows
English default names again, exactly as it did before v1.0.4.
"""

from alembic import op
import sqlalchemy as sa


revision = "104a00000"
down_revision = "103a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("allocation_categories",
                  sa.Column("name_key", sa.String(length=40), nullable=True))
    op.add_column("allocation_categories",
                  sa.Column("item_label_key", sa.String(length=40), nullable=True))

    conn = op.get_bind()
    pairs = [("Rooms", "rooms"), ("Small Groups", "small_groups")]
    total = 0
    for text, key in pairs:
        r = conn.execute(sa.text("""
            UPDATE allocation_categories SET name_key = :key
            WHERE is_default = true AND name = :text AND name_key IS NULL
        """), {"key": key, "text": text})
        total += r.rowcount
    for text, key in [("Room", "room"), ("Group", "group")]:
        r = conn.execute(sa.text("""
            UPDATE allocation_categories SET item_label_key = :key
            WHERE is_default = true AND item_label = :text AND item_label_key IS NULL
        """), {"key": key, "text": text})
        total += r.rowcount

    print(f"[v1.0.4] default group type names now follow the reader's "
          f"language: {total} field(s) marked")


def downgrade() -> None:
    op.drop_column("allocation_categories", "item_label_key")
    op.drop_column("allocation_categories", "name_key")
