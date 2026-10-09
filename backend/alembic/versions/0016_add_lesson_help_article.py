"""add help article link and video date to lessons

Revision ID: 0016_add_lesson_help_article
Revises: 0015_add_agency_description
Create Date: 2026-10-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_add_lesson_help_article"
down_revision = "0015_add_agency_description"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("help_article", sa.String(length=80), nullable=True))
    op.add_column(
        "lessons",
        sa.Column("video_updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.execute("UPDATE lessons SET video_updated_at = COALESCE(updated_at, created_at, now())")


def downgrade() -> None:
    op.drop_column("lessons", "video_updated_at")
    op.drop_column("lessons", "help_article")
