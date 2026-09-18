"""v1.0.4zb — notes.author_id becomes nullable, with ON DELETE SET NULL.

Revision ID: 104zb0000
Revises: 104j00000
Create Date: 2026-09-18

USER-1. `api/users.py` deletes a user with a bare `db.delete(user)` and no
sweep of anything they authored. `notes.author_id` is NOT NULL with a
foreign key to `users.id` carrying no ON DELETE clause, so PostgreSQL's
default NO ACTION applies and deleting anyone who has ever written a note
raises an integrity error that reaches the organiser as a 500. Confirmed
against the deployed schema, not inferred from the model.

Johannes ruled (session 86, D3) against reassigning authorship, because it
would make the record say somebody wrote what they did not. Instead, when a
user is deleted:

  - their UNPUBLISHED notes are deleted, in the same transaction, by
    `api/users.py`. A draft is that person's own working note.
  - their PUBLISHED notes stay, with no author — the same honest answer
    v1.0.4t gives for history written by a departed user.

This revision is what makes the second half possible.

Why deleting the drafts first is load-bearing, not tidying: the visibility
rule is "published, or mine" (`api/notes.py:59` and `:137`). A null author
matches nobody, so a null-author UNPUBLISHED note would be visible to no
one and unreachable forever. Sweeping them means no such row can exist.

Safe on existing data, verified rather than assumed: on the session-86
database, 13 notes, 0 with a null author, 5 published. Widening NOT NULL to
nullable cannot fail on rows that all have values, and no row is rewritten.

Downgrade: deliberately not lossless. It restores the plain foreign key and
NOT NULL, which a row with a null author cannot satisfy — and there is no
honest value to put back, since inventing an author is exactly what D3
rejected. So it DELETES any note whose author is already null first. The
alternative, failing on those rows, would strand an operator half-way with
no way back; losing a handful of authorless notes is the smaller harm and
is at least truthful.
"""

from alembic import op
import sqlalchemy as sa


revision = "104zb0000"
down_revision = "104j00000"
branch_labels = None
depends_on = None

_FK = "notes_author_id_fkey"


def upgrade() -> None:
    op.alter_column(
        "notes", "author_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    # A foreign key's ON DELETE cannot be altered in place; drop and recreate.
    op.drop_constraint(_FK, "notes", type_="foreignkey")
    op.create_foreign_key(
        _FK, "notes", "users", ["author_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    # See the docstring: there is no honest author to restore, so the rows
    # that have none go. Runs BEFORE the NOT NULL is reinstated, or it would
    # fail on exactly those rows.
    op.execute("DELETE FROM notes WHERE author_id IS NULL")
    op.drop_constraint(_FK, "notes", type_="foreignkey")
    op.create_foreign_key(_FK, "notes", "users", ["author_id"], ["id"])
    op.alter_column(
        "notes", "author_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
