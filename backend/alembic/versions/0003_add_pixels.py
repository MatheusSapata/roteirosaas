"""add pixels table

Revision ID: 0003_add_pixels
Revises: 0002_add_stripe_fields
Create Date: 2025-12-14 21:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_pixels"
down_revision = "0002_add_stripe_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pixels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("value", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pixels_id"), "pixels", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_pixels_id"), table_name="pixels")
    op.drop_table("pixels")
