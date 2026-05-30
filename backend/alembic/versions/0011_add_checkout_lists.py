"""add checkout coupon and checkout config lists

Revision ID: 0011_add_checkout_lists
Revises: 0010_add_checkout_tables
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0011_add_checkout_lists"
down_revision = "0010_add_checkout_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "checkout_settings",
        sa.Column("coupons_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
    )
    op.add_column(
        "checkout_settings",
        sa.Column("checkouts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("checkout_settings", "checkouts_json")
    op.drop_column("checkout_settings", "coupons_json")
