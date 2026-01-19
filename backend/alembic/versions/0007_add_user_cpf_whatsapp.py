"""add cpf and whatsapp to users

Revision ID: 0007_add_user_cpf_whatsapp
Revises: 0006_add_user_created_at
Create Date: 2025-12-16 22:40:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_add_user_cpf_whatsapp"
down_revision = "0006_add_user_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
  op.add_column("users", sa.Column("cpf", sa.String(length=14), nullable=True))
  op.add_column("users", sa.Column("whatsapp", sa.String(length=20), nullable=True))
  op.create_unique_constraint("uq_users_cpf", "users", ["cpf"])


def downgrade() -> None:
  op.drop_constraint("uq_users_cpf", "users", type_="unique")
  op.drop_column("users", "whatsapp")
  op.drop_column("users", "cpf")
