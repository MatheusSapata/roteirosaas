"""add checkout tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0010_add_checkout_tables"
down_revision = "0009_add_agency_default_page"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkout_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("theme_mode", sa.String(length=20), nullable=False, server_default="dark"),
        sa.Column("desktop_image_url", sa.String(length=500), nullable=True),
        sa.Column("mobile_banner_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("offers_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_checkout_settings_id", "checkout_settings", ["id"], unique=False)

    op.create_table(
        "checkout_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("offer_key", sa.String(length=120), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("plan_key", sa.String(length=50), nullable=False, server_default="professional"),
        sa.Column("billing_cycle", sa.String(length=20), nullable=False, server_default="monthly"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("payment_method", sa.String(length=30), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("customer_document", sa.String(length=32), nullable=False),
        sa.Column("customer_phone", sa.String(length=32), nullable=False),
        sa.Column("customer_zipcode", sa.String(length=16), nullable=False),
        sa.Column("coupon_code", sa.String(length=80), nullable=True),
        sa.Column("asaas_customer_id", sa.String(length=120), nullable=True),
        sa.Column("asaas_payment_id", sa.String(length=120), nullable=True),
        sa.Column("pix_copy_paste", sa.Text(), nullable=True),
        sa.Column("pix_qr_code_base64", sa.Text(), nullable=True),
        sa.Column("pix_expiration_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_defined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_checkout_sessions_id", "checkout_sessions", ["id"], unique=False)
    op.create_index("ix_checkout_sessions_token", "checkout_sessions", ["token"], unique=True)
    op.create_index("ix_checkout_sessions_offer_key", "checkout_sessions", ["offer_key"], unique=False)
    op.create_index("ix_checkout_sessions_status", "checkout_sessions", ["status"], unique=False)
    op.create_index("ix_checkout_sessions_customer_email", "checkout_sessions", ["customer_email"], unique=False)
    op.create_index("ix_checkout_sessions_customer_document", "checkout_sessions", ["customer_document"], unique=False)
    op.create_index("ix_checkout_sessions_asaas_customer_id", "checkout_sessions", ["asaas_customer_id"], unique=False)
    op.create_index("ix_checkout_sessions_asaas_payment_id", "checkout_sessions", ["asaas_payment_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_checkout_sessions_asaas_payment_id", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_asaas_customer_id", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_customer_document", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_customer_email", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_status", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_offer_key", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_token", table_name="checkout_sessions")
    op.drop_index("ix_checkout_sessions_id", table_name="checkout_sessions")
    op.drop_table("checkout_sessions")
    op.drop_index("ix_checkout_settings_id", table_name="checkout_settings")
    op.drop_table("checkout_settings")
