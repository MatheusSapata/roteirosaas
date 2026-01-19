"""Add created_at to users

Revision ID: 0006_add_user_created_at
Revises: 0005_add_subscription_preapproval
Create Date: 2025-12-14
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "0006_add_user_created_at"
down_revision = "0003_add_pixels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "created_at")
