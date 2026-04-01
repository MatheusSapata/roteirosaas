"""add finance tables and stripe connect columns

Revision ID: 0010_add_finance_tables
Revises: 0009_add_agency_default_page
Create Date: 2026-04-01 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0010_add_finance_tables"
down_revision: Union[str, None] = "0009_add_agency_default_page"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_account_id", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("stripe_onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("stripe_charges_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("stripe_payouts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_users_stripe_account_id", "users", ["stripe_account_id"], unique=False)

    op.create_table(
        "stripe_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stripe_account_id", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("default_currency", sa.String(length=3), nullable=True),
        sa.Column("charges_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payouts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("details_submitted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("stripe_account_id"),
    )
    op.create_index("ix_stripe_accounts_stripe_account_id", "stripe_accounts", ["stripe_account_id"], unique=True)

    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=True),
        sa.Column("page_id", sa.Integer(), nullable=True),
        sa.Column("page_slug", sa.String(length=255), nullable=True),
        sa.Column("section_id", sa.String(length=64), nullable=True),
        sa.Column("price_item_id", sa.String(length=64), nullable=True),
        sa.Column("product_title", sa.String(length=255), nullable=False),
        sa.Column("product_description", sa.String(length=500), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="brl"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("commission_amount", sa.Integer(), nullable=False),
        sa.Column("stripe_application_fee_amount", sa.Integer(), nullable=False),
        sa.Column("net_amount", sa.Integer(), nullable=True),
        sa.Column("stripe_fee_amount", sa.Integer(), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("installments", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("interest_mode", sa.String(length=20), nullable=False, server_default="merchant"),
        sa.Column("max_installments_no_interest", sa.Integer(), nullable=True),
        sa.Column("payment_status", sa.String(length=50), nullable=False, server_default="requires_payment_method"),
        sa.Column("financial_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("payout_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("passenger_status", sa.String(length=50), nullable=False, server_default="not_started"),
        sa.Column("passengers_required", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passenger_form_token", sa.String(length=128), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(length=120), nullable=False),
        sa.Column("stripe_charge_id", sa.String(length=120), nullable=True),
        sa.Column("stripe_balance_transaction_id", sa.String(length=120), nullable=True),
        sa.Column("stripe_destination_account", sa.String(length=120), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("customer_phone", sa.String(length=50), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stripe_payment_intent_id"),
        sa.UniqueConstraint("passenger_form_token"),
    )
    op.create_index("ix_sales_user_id", "sales", ["user_id"], unique=False)
    op.create_index("ix_sales_agency_id", "sales", ["agency_id"], unique=False)
    op.create_index("ix_sales_stripe_payment_intent_id", "sales", ["stripe_payment_intent_id"], unique=True)
    op.create_index("ix_sales_passenger_form_token", "sales", ["passenger_form_token"], unique=True)

    op.create_table(
        "passengers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("cpf", sa.String(length=20), nullable=True),
        sa.Column("birthdate", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("whatsapp", sa.String(length=50), nullable=True),
        sa.Column("boarding_location", sa.String(length=255), nullable=True),
        sa.Column("extras", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_passengers_sale_id", "passengers", ["sale_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_passengers_sale_id", table_name="passengers")
    op.drop_table("passengers")

    op.drop_index("ix_sales_passenger_form_token", table_name="sales")
    op.drop_index("ix_sales_stripe_payment_intent_id", table_name="sales")
    op.drop_index("ix_sales_agency_id", table_name="sales")
    op.drop_index("ix_sales_user_id", table_name="sales")
    op.drop_table("sales")

    op.drop_index("ix_stripe_accounts_stripe_account_id", table_name="stripe_accounts")
    op.drop_table("stripe_accounts")

    op.drop_index("ix_users_stripe_account_id", table_name="users")
    op.drop_column("users", "stripe_payouts_enabled")
    op.drop_column("users", "stripe_charges_enabled")
    op.drop_column("users", "stripe_onboarding_completed")
    op.drop_column("users", "stripe_account_id")
