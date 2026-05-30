"""add checkout tracking tables

Revision ID: 0014_add_checkout_tracking
Revises: 0013_add_user_cnpj
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0014_add_checkout_tracking"
down_revision = "0013_add_user_cnpj"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkout_leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("offer_key", sa.String(length=120), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("customer_document", sa.String(length=32), nullable=False),
        sa.Column("customer_phone", sa.String(length=32), nullable=False),
        sa.Column("customer_zipcode", sa.String(length=16), nullable=False),
        sa.Column("payment_method_selected", sa.String(length=30), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_defined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["checkout_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_checkout_leads_customer_document"), "checkout_leads", ["customer_document"], unique=False)
    op.create_index(op.f("ix_checkout_leads_customer_email"), "checkout_leads", ["customer_email"], unique=False)
    op.create_index(op.f("ix_checkout_leads_id"), "checkout_leads", ["id"], unique=False)
    op.create_index(op.f("ix_checkout_leads_offer_key"), "checkout_leads", ["offer_key"], unique=False)
    op.create_index(op.f("ix_checkout_leads_session_id"), "checkout_leads", ["session_id"], unique=False)
    op.create_index(op.f("ix_checkout_leads_token"), "checkout_leads", ["token"], unique=False)

    op.create_table(
        "checkout_tracking_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("offer_key", sa.String(length=120), nullable=False),
        sa.Column("event_name", sa.String(length=80), nullable=False),
        sa.Column("step", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=True),
        sa.Column("payment_method", sa.String(length=30), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("ip_country", sa.String(length=80), nullable=True),
        sa.Column("ip_region", sa.String(length=120), nullable=True),
        sa.Column("ip_city", sa.String(length=120), nullable=True),
        sa.Column("ip_timezone", sa.String(length=120), nullable=True),
        sa.Column("ip_lat", sa.String(length=30), nullable=True),
        sa.Column("ip_lon", sa.String(length=30), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["checkout_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_checkout_tracking_events_created_at"), "checkout_tracking_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_event_name"), "checkout_tracking_events", ["event_name"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_id"), "checkout_tracking_events", ["id"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_offer_key"), "checkout_tracking_events", ["offer_key"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_payment_method"), "checkout_tracking_events", ["payment_method"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_session_id"), "checkout_tracking_events", ["session_id"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_status"), "checkout_tracking_events", ["status"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_step"), "checkout_tracking_events", ["step"], unique=False)
    op.create_index(op.f("ix_checkout_tracking_events_token"), "checkout_tracking_events", ["token"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_checkout_tracking_events_token"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_step"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_status"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_session_id"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_payment_method"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_offer_key"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_id"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_event_name"), table_name="checkout_tracking_events")
    op.drop_index(op.f("ix_checkout_tracking_events_created_at"), table_name="checkout_tracking_events")
    op.drop_table("checkout_tracking_events")

    op.drop_index(op.f("ix_checkout_leads_token"), table_name="checkout_leads")
    op.drop_index(op.f("ix_checkout_leads_session_id"), table_name="checkout_leads")
    op.drop_index(op.f("ix_checkout_leads_offer_key"), table_name="checkout_leads")
    op.drop_index(op.f("ix_checkout_leads_id"), table_name="checkout_leads")
    op.drop_index(op.f("ix_checkout_leads_customer_email"), table_name="checkout_leads")
    op.drop_index(op.f("ix_checkout_leads_customer_document"), table_name="checkout_leads")
    op.drop_table("checkout_leads")
