"""add trial fields to user

Revision ID: 0008_add_user_trial_fields
Revises: 0007_add_user_cpf_whatsapp
Create Date: 2026-01-08 23:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0008_add_user_trial_fields"
down_revision = "0007_add_user_cpf_whatsapp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("trial_plan", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("trial_original_plan", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("trial_ack_start", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("trial_ack_end", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("users", "trial_ack_start", server_default=None)
    op.alter_column("users", "trial_ack_end", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "trial_ack_end")
    op.drop_column("users", "trial_ack_start")
    op.drop_column("users", "trial_ends_at")
    op.drop_column("users", "trial_started_at")
    op.drop_column("users", "trial_original_plan")
    op.drop_column("users", "trial_plan")
