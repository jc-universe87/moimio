"""outbound webhook subsystem (v1.0.0g)

Revision ID: 100g00000
Revises: 85a00000
Create Date: 2026-05-12

v1.0.0g: generic outbound webhook subsystem. Two new tables:

  - `outbound_webhook_endpoints`: registered receivers. Admin-created via
    the new Webhooks admin section OR auto-registered at startup if the
    SaaS env vars (MOIMIO_WEBHOOK_URL + MOIMIO_WEBHOOK_SECRET) are set.

  - `outbound_webhook_deliveries`: append-only log of every delivery
    attempt. Pruned daily by a scheduled job; retention is configurable
    via WEBHOOK_DELIVERY_RETENTION_DAYS (default 30).

No existing data is touched. Self-hosters who don't use webhooks will
have two empty tables added; no behavioural change unless they configure
an endpoint or the SaaS env vars are present at boot.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "100g00000"
down_revision = "85a00000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── outbound_webhook_endpoints ────────────────────────────────
    op.create_table(
        "outbound_webhook_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.String(255), nullable=False),
        sa.Column("event_types", sa.JSON(), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "active", "degraded", "disabled",
                name="webhook_endpoint_state",
                create_constraint=True,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "consecutive_failures",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "managed_by",
            sa.Enum(
                "user", "saas",
                name="webhook_endpoint_managed_by",
                create_constraint=True,
            ),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ─── outbound_webhook_deliveries ───────────────────────────────
    op.create_table(
        "outbound_webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "endpoint_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "outbound_webhook_endpoints.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "success", "failed", "exhausted",
                name="webhook_delivery_status",
                create_constraint=True,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.String(2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Indexes (named explicitly so downgrade can drop them cleanly).
    op.create_index(
        "ix_outbound_webhook_deliveries_endpoint_id",
        "outbound_webhook_deliveries",
        ["endpoint_id"],
    )
    op.create_index(
        "ix_outbound_webhook_deliveries_event_id",
        "outbound_webhook_deliveries",
        ["event_id"],
    )
    op.create_index(
        "ix_outbound_webhook_deliveries_event_type",
        "outbound_webhook_deliveries",
        ["event_type"],
    )
    op.create_index(
        "ix_outbound_webhook_deliveries_status",
        "outbound_webhook_deliveries",
        ["status"],
    )
    op.create_index(
        "ix_outbound_webhook_deliveries_next_attempt_at",
        "outbound_webhook_deliveries",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_outbound_webhook_deliveries_next_attempt_at",
        table_name="outbound_webhook_deliveries",
    )
    op.drop_index(
        "ix_outbound_webhook_deliveries_status",
        table_name="outbound_webhook_deliveries",
    )
    op.drop_index(
        "ix_outbound_webhook_deliveries_event_type",
        table_name="outbound_webhook_deliveries",
    )
    op.drop_index(
        "ix_outbound_webhook_deliveries_event_id",
        table_name="outbound_webhook_deliveries",
    )
    op.drop_index(
        "ix_outbound_webhook_deliveries_endpoint_id",
        table_name="outbound_webhook_deliveries",
    )
    op.drop_table("outbound_webhook_deliveries")
    op.drop_table("outbound_webhook_endpoints")
    # Drop the enums explicitly — Postgres doesn't auto-drop them.
    sa.Enum(name="webhook_delivery_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="webhook_endpoint_managed_by").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="webhook_endpoint_state").drop(op.get_bind(), checkfirst=True)
