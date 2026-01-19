"""Add Stripe fields to subscriptions"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_add_stripe_fields"
down_revision = "0001_full_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("provider", sa.String(length=50), nullable=False, server_default="stripe"))
    op.add_column("subscriptions", sa.Column("stripe_customer_id", sa.String(length=120), nullable=True))
    op.add_column("subscriptions", sa.Column("stripe_subscription_id", sa.String(length=120), nullable=True))
    op.add_column("subscriptions", sa.Column("stripe_price_id", sa.String(length=120), nullable=True))
    op.create_index("ix_subscriptions_stripe_subscription_id", "subscriptions", ["stripe_subscription_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_subscriptions_stripe_subscription_id", table_name="subscriptions")
    op.drop_column("subscriptions", "stripe_price_id")
    op.drop_column("subscriptions", "stripe_subscription_id")
    op.drop_column("subscriptions", "stripe_customer_id")
    op.drop_column("subscriptions", "provider")
