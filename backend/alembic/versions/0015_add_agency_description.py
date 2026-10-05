"""add description to agencies

Revision ID: 0015_add_agency_description
Revises: 0014_add_checkout_tracking
Create Date: 2026-10-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_add_agency_description"
down_revision = "0014_add_checkout_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agencies", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("agencies", "description")
