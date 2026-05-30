"""add cnpj to users

Revision ID: 0013_add_user_cnpj
Revises: 0012_add_asaas_event_logs
Create Date: 2026-05-28 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_add_user_cnpj"
down_revision = "0012_add_asaas_event_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("cnpj", sa.String(length=18), nullable=True))
    op.create_unique_constraint("uq_users_cnpj", "users", ["cnpj"])


def downgrade() -> None:
    op.drop_constraint("uq_users_cnpj", "users", type_="unique")
    op.drop_column("users", "cnpj")
