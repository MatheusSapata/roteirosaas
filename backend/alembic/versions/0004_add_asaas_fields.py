"""add asaas columns

Revision ID: 0004_add_asaas_fields
Revises: 0003_add_pixels
Create Date: 2026-02-28 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_add_asaas_fields"
down_revision: Union[str, None] = "0003_add_pixels"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("asaas_customer_id", sa.String(length=120), nullable=True))
    op.add_column("subscriptions", sa.Column("asaas_subscription_id", sa.String(length=120), nullable=True))
    op.add_column("subscriptions", sa.Column("asaas_payment_link_id", sa.String(length=120), nullable=True))
    op.add_column("subscriptions", sa.Column("external_reference", sa.String(length=160), nullable=True))
    op.add_column("subscriptions", sa.Column("billing_cycle", sa.String(length=20), nullable=False, server_default="monthly"))
    op.create_index("ix_subscriptions_asaas_subscription_id", "subscriptions", ["asaas_subscription_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_subscriptions_asaas_subscription_id", table_name="subscriptions")
    op.drop_column("subscriptions", "billing_cycle")
    op.drop_column("subscriptions", "external_reference")
    op.drop_column("subscriptions", "asaas_payment_link_id")
    op.drop_column("subscriptions", "asaas_subscription_id")
    op.drop_column("subscriptions", "asaas_customer_id")
