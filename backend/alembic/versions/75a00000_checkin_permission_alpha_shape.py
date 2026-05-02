"""checkin permission α-shape — promote flat string to {access, pre_event}

Revision ID: 75a00000
Revises: 74a00000
Create Date: 2026-04-30

v1.0-pre #10: pre-event check-in access requires a sub-flag alongside the
checkin access value. The cleanest representation is a nested object on
the existing `permissions` column. This migration converts every
EventUserAssignment row's `checkin` key from its flat-string shape
to the new object shape, defaulting `pre_event` to False (preserving
legacy behaviour — pre-event access is opt-in).

Before:  permissions = {"checkin": "write", ...}
After:   permissions = {"checkin": {"access": "write", "pre_event": false}, ...}

A null/missing checkin key is left untouched (no access at all is the
same in both shapes).

Down-migration: collapses the object back to its `access` string. Loses
the pre_event flag; that's expected for a downgrade.

Note on the column type: `EventUserAssignment.permissions` is declared
as JSON (not JSONB). The migration casts to ::jsonb for the surgical
helpers (jsonb_set, jsonb_typeof, jsonb_build_object), then casts back
to ::json on assignment so the column type stays as declared.
"""

from alembic import op
import sqlalchemy as sa


revision = "75a00000"
down_revision = "74a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent: the WHERE clause restricts to rows where checkin is
    # still a JSON string (the legacy shape). Running again is a no-op
    # once every row has been promoted to the object shape.
    op.execute(
        """
        UPDATE event_user_assignments
        SET permissions = jsonb_set(
            permissions::jsonb,
            '{checkin}',
            jsonb_build_object(
                'access', permissions::jsonb -> 'checkin',
                'pre_event', false
            ),
            true
        )::json
        WHERE jsonb_typeof(permissions::jsonb -> 'checkin') = 'string'
        """
    )


def downgrade() -> None:
    # Collapse {access, pre_event} object back to a flat string. Loses
    # pre_event flag (no representation in the old shape).
    op.execute(
        """
        UPDATE event_user_assignments
        SET permissions = jsonb_set(
            permissions::jsonb,
            '{checkin}',
            permissions::jsonb -> 'checkin' -> 'access',
            true
        )::json
        WHERE jsonb_typeof(permissions::jsonb -> 'checkin') = 'object'
        """
    )
