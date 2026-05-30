"""add asaas event logs

Revision ID: 0012_add_asaas_event_logs
Revises: 0011_add_checkout_lists
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_add_asaas_event_logs"
down_revision = "0011_add_checkout_lists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asaas_event_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asaas_event_logs_id"), "asaas_event_logs", ["id"], unique=False)
    op.create_index(op.f("ix_asaas_event_logs_event_id"), "asaas_event_logs", ["event_id"], unique=True)
    op.create_index(op.f("ix_asaas_event_logs_event_type"), "asaas_event_logs", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_asaas_event_logs_event_type"), table_name="asaas_event_logs")
    op.drop_index(op.f("ix_asaas_event_logs_event_id"), table_name="asaas_event_logs")
    op.drop_index(op.f("ix_asaas_event_logs_id"), table_name="asaas_event_logs")
    op.drop_table("asaas_event_logs")
