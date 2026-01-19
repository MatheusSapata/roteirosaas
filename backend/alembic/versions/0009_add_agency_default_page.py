"""add default page relationship to agencies"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0009_add_agency_default_page"
down_revision = "0008_add_user_trial_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agencies", sa.Column("default_page_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "agencies_default_page_id_fkey", "agencies", "pages", ["default_page_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("agencies_default_page_id_fkey", "agencies", type_="foreignkey")
    op.drop_column("agencies", "default_page_id")
