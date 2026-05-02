"""v0.74 — engine spec changes.

Revision ID: 74a00000
Revises: 60a00000
Create Date: 2026-04-28

This migration implements the schema changes required by the v0.74
allocation engine rewrite:

1. ``allocation_units.capacity`` becomes NOT NULL.
   Existing NULL values are filled with a smart default = total
   registered participant count for the parent event (GREATEST 50).
   The "uncapped unit" concept disappears from the data model;
   organisers must set a real number going forward.

2. New column ``mark_definitions.cluster_behaviour`` —
   enum('together', 'split', 'none') default 'none'.
   Drives PASS 2 (together-clusters) and PASS 3 (split-evenly
   distribution) in the new engine. Existing marks default to
   'none' = no clustering effect, preserving pre-v0.74 behaviour.

3. New column ``allocation_categories.exclusive_group_codes`` —
   boolean default false.
   Per-category toggle: when true, group_code clusters claim their
   entire unit (no other participants placed there). Default false
   preserves pre-v0.74 behaviour (clusters share units).

4. ``allocation_categories.has_gender_restriction`` — DEPRECATED.
   Column REMAINS in schema. Engine no longer reads it as of v0.74
   (unit-level ``gender_restriction`` is the source of truth). To be
   dropped in v1.0 cut. This migration adds a comment to the column
   marking it deprecated; it is otherwise unchanged.

Why deprecate-and-ignore for (4) instead of dropping now:
A destructive drop in v0.74 would change behaviour for events that
explicitly had the toggle off but had unit-level gender restrictions
set — those events would suddenly start enforcing gender. Keeping
the column un-read is safer; the v1.0 cut can drop it once we know
no one's relying on its presence.
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "74a00000"
down_revision = "60a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── (1) Backfill allocation_units.capacity NULL → smart default ──
    #
    # For each unit with NULL capacity, set capacity to the count of
    # active participants in the parent event (via category → event_id),
    # with a floor of 50 so events with zero participants at migration
    # time still get a usable default. Active = not soft-deleted.
    #
    # Using a correlated subquery (no temp table needed; runs once at
    # migration time so performance doesn't matter much).
    op.execute(
        """
        UPDATE allocation_units AS u
        SET capacity = GREATEST(
            (
                SELECT COUNT(*)
                FROM participants AS p
                INNER JOIN allocation_categories AS c
                    ON c.id = u.category_id
                WHERE p.event_id = c.event_id
                  AND p.deleted_at IS NULL
            ),
            50
        )
        WHERE u.capacity IS NULL
        """
    )

    # ── (1 cont.) Lock capacity to NOT NULL ──
    op.alter_column(
        "allocation_units",
        "capacity",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # ── (2) mark_definitions.cluster_behaviour ──
    #
    # Enum stored as VARCHAR for portability (Alembic + Postgres ENUM
    # types are workable but more painful for additive changes; the
    # codebase uses string-backed enums elsewhere — see
    # RegistrationStatus, AllocationEventType).
    op.add_column(
        "mark_definitions",
        sa.Column(
            "cluster_behaviour",
            sa.String(length=20),
            nullable=False,
            server_default="none",
        ),
    )

    # ── (3) allocation_categories.exclusive_group_codes ──
    op.add_column(
        "allocation_categories",
        sa.Column(
            "exclusive_group_codes",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # ── (4) Deprecation marker on has_gender_restriction ──
    #
    # Postgres COMMENT ON COLUMN. Pure documentation; doesn't affect
    # behaviour. Helps future-Claude (and any human DB browser) see
    # that the column is no longer in use.
    op.execute(
        """
        COMMENT ON COLUMN allocation_categories.has_gender_restriction
        IS 'DEPRECATED in v0.74; engine reads unit-level gender_restriction directly. To be dropped in v1.0.'
        """
    )


def downgrade() -> None:
    # ── (4) Remove deprecation comment ──
    op.execute(
        "COMMENT ON COLUMN allocation_categories.has_gender_restriction IS NULL"
    )

    # ── (3) Drop exclusive_group_codes ──
    op.drop_column("allocation_categories", "exclusive_group_codes")

    # ── (2) Drop cluster_behaviour ──
    op.drop_column("mark_definitions", "cluster_behaviour")

    # ── (1) Restore capacity nullability ──
    #
    # Note: this does NOT restore the previously-NULL values. The
    # migration's UPDATE in upgrade() lost that information (which
    # rows were NULL before vs which had explicit values). A
    # downgrade leaves all units with the smart-default values.
    # This is acceptable for downgrade — Alembic downgrades are
    # rarely run in production; this is for dev/test recovery.
    op.alter_column(
        "allocation_units",
        "capacity",
        existing_type=sa.Integer(),
        nullable=True,
    )
