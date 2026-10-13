"""add temporary password flag to users

Revision ID: 0017_add_user_temporary_password
Revises: 0016_add_lesson_help_article
Create Date: 2026-10-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_add_user_temporary_password"
down_revision = "0016_add_lesson_help_article"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("temporary_password", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "temporary_password")
