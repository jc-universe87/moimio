"""v1.0.4zd — every remaining reference to a deleted user.

Revision ID: 104zd0000
Revises: 104zb0000
Create Date: 2026-09-18

USER-1, reopened. v1.0.4zb fixed `notes.author_id` and closed the entry on
that evidence; the account is held by five more references. Deleting an
established user still failed with a raw 500:

    ERROR:  update or delete on table "users" violates foreign key
            constraint "user_preferences_user_id_fkey" on table
            "user_preferences"

`user_preferences` is the only reference that BLOCKS. It is also the worst
one to have missed: a preferences row is written the moment somebody sets
their language, date format or time zone, so "an established user" is
precisely "a user who has opened the settings panel once". With that row
gone first, even the heaviest account in the workspace — 12 notes, 8 events,
4230 history rows, 154 mark assignments — deletes cleanly, because every
other foreign key is already SET NULL or CASCADE.

Three changes, under the rule settled in the v1.0.4zd brief: what is theirs
alone goes with them, what is a record of what happened is kept with the
person shown as removed, and a grant of access is deleted.

  1. user_preferences.user_id -> ON DELETE CASCADE.
     Theirs alone. A preferences row has no meaning without its user, so
     the database removes it rather than the code sweeping it: there is
     nothing for a reader to see happen.

  2. events.created_by -> nullable, with a REAL foreign key, ON DELETE SET
     NULL. A record of what happened, so it is kept. It had no foreign key
     at all, so it never blocked a delete — it just went on pointing at an
     id that no longer existed. `SetupHub.jsx:394-396` compares it to the
     current user for a permission test, where a dangling id silently
     matches nobody.

  3. allocation_category_exclusions.created_by -> a REAL foreign key, ON
     DELETE SET NULL. Same rot, already nullable, and read nowhere at all
     (written at allocation_service.py:388 and never loaded).

CONSEQUENCE WORTH NAMING. Giving events.created_by a real key breaks a
stand-in restore has relied on: backup_service.py wrote
`created_by=actor_user_id or new_event_id`, using the EVENT's own id as a
placeholder user id, safe only because nothing checked it. That becomes a
violation here, so restore now writes None — the truthful answer anyway,
since nobody on the receiving instance created that event.

Safe on existing data, verified before this was written rather than assumed:
a foreign key cannot be added over values absent from the parent. On the
session-86 database, 8 events with 0 dangling creators, and 71 exclusions
with 0 dangling created_by. No cleanup step and no NOT VALID: a self-hoster
whose data IS dangling should see this fail loudly on the constraint, not
have rows silently altered underneath them.

DOWNGRADE. Restores all three constraints. Before reinstating
events.created_by NOT NULL it has to do something about events whose creator
has since been deleted and is therefore null, and there is no honest value to
put back — inventing a creator is the same lie D3 rejected for note
authorship. It DELETES those events. That is a far heavier cost than
v1.0.4zb's downgrade, which dropped a few authorless notes: an event takes
its participants and allocations with it. TAKE A DUMP BEFORE DOWNGRADING
PAST THIS REVISION.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "104zd0000"
down_revision = "104zb0000"
branch_labels = None
depends_on = None

_PREFS_FK = "user_preferences_user_id_fkey"
_EVENTS_FK = "events_created_by_fkey"
_EXCL_FK = "allocation_category_exclusions_created_by_fkey"


def upgrade() -> None:
    # 1. Theirs alone — goes with them.
    op.drop_constraint(_PREFS_FK, "user_preferences", type_="foreignkey")
    op.create_foreign_key(
        _PREFS_FK, "user_preferences", "users", ["user_id"], ["id"],
        ondelete="CASCADE",
    )

    # 2. A record — kept, with nobody named.
    op.alter_column(
        "events", "created_by",
        existing_type=UUID(as_uuid=True), nullable=True,
    )
    op.create_foreign_key(
        _EVENTS_FK, "events", "users", ["created_by"], ["id"],
        ondelete="SET NULL",
    )

    # 3. Same, on the exclusion row.
    op.create_foreign_key(
        _EXCL_FK, "allocation_category_exclusions", "users",
        ["created_by"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(_EXCL_FK, "allocation_category_exclusions", type_="foreignkey")
    op.drop_constraint(_EVENTS_FK, "events", type_="foreignkey")
    # See the docstring. There is no honest creator to restore, and NOT NULL
    # cannot hold with these rows present. This is the expensive line.
    op.execute("DELETE FROM events WHERE created_by IS NULL")
    op.alter_column(
        "events", "created_by",
        existing_type=UUID(as_uuid=True), nullable=False,
    )
    op.drop_constraint(_PREFS_FK, "user_preferences", type_="foreignkey")
    op.create_foreign_key(
        _PREFS_FK, "user_preferences", "users", ["user_id"], ["id"],
    )
