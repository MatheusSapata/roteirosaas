"""add preserve_categories em site_import_jobs (manter as categorias do site importado)

Revision ID: 0019_site_import_categories
Revises: 0018_add_site_import_jobs
Create Date: 2026-11-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_site_import_categories"
down_revision = "0018_add_site_import_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("site_import_jobs", sa.Column("preserve_categories", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("site_import_jobs", "preserve_categories")
