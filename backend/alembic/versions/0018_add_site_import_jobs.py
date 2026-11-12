"""add site import jobs (importar o site inteiro pelo assistente de IA)

Revision ID: 0018_add_site_import_jobs
Revises: 0017_add_user_temporary_password
Create Date: 2026-11-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0018_add_site_import_jobs"
down_revision = "0017_add_user_temporary_password"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "site_import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.String(length=2000), nullable=False),
        sa.Column("source_title", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="awaiting_confirmation", nullable=False),
        sa.Column("stage", sa.String(length=20), nullable=True),
        sa.Column("home_stage", sa.String(length=20), nullable=True),
        sa.Column("include_images", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("total_found", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_site_import_jobs_id"), "site_import_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_site_import_jobs_page_id"), "site_import_jobs", ["page_id"], unique=False)
    op.create_index(op.f("ix_site_import_jobs_user_id"), "site_import_jobs", ["user_id"], unique=False)
    op.create_index("ix_site_import_jobs_agency_status", "site_import_jobs", ["agency_id", "status"], unique=False)
    # No máximo uma importação completa rodando por agência.
    op.create_index(
        "uq_site_import_jobs_running_agency",
        "site_import_jobs",
        ["agency_id"],
        unique=True,
        postgresql_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    op.drop_index("uq_site_import_jobs_running_agency", table_name="site_import_jobs")
    op.drop_index("ix_site_import_jobs_agency_status", table_name="site_import_jobs")
    op.drop_index(op.f("ix_site_import_jobs_user_id"), table_name="site_import_jobs")
    op.drop_index(op.f("ix_site_import_jobs_page_id"), table_name="site_import_jobs")
    op.drop_index(op.f("ix_site_import_jobs_id"), table_name="site_import_jobs")
    op.drop_table("site_import_jobs")
