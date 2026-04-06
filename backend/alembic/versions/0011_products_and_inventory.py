"""add products, variations, sale items and inventory control

Revision ID: 0011_products_and_inventory
Revises: 0010_add_finance_tables
Create Date: 2026-04-06 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0011_products_and_inventory"
down_revision: Union[str, None] = "0010_add_finance_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("trip_date", sa.Date(), nullable=True),
        sa.Column("date_is_flexible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("inventory_strategy", sa.String(length=20), nullable=False, server_default="manual"),
        sa.Column("total_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sold_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("allow_oversell", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(op.f("ix_products_public_id"), "products", ["public_id"], unique=True)
    op.create_index(op.f("ix_products_user_id"), "products", ["user_id"], unique=False)

    op.create_table(
        "product_variations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BRL"),
        sa.Column("people_included", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("stock_mode", sa.String(length=20), nullable=False, server_default="shared"),
        sa.Column("total_slots", sa.Integer(), nullable=True),
        sa.Column("available_slots", sa.Integer(), nullable=True),
        sa.Column("reserved_slots", sa.Integer(), nullable=True),
        sa.Column("sold_slots", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(op.f("ix_product_variations_product_id"), "product_variations", ["product_id"], unique=False)

    op.create_table(
        "sale_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_public_id", sa.String(length=36), nullable=True),
        sa.Column("variation_id", sa.Integer(), nullable=True),
        sa.Column("variation_public_id", sa.String(length=36), nullable=True),
        sa.Column("variation_name", sa.String(length=255), nullable=False),
        sa.Column("variation_description", sa.String(length=500), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="BRL"),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_price", sa.Integer(), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("stock_mode", sa.String(length=20), nullable=False, server_default="shared"),
        sa.Column("reserved_from_product", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_from_variant", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variation_id"], ["product_variations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_items_sale_id"), "sale_items", ["sale_id"], unique=False)

    op.create_table(
        "product_inventory_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("variation_id", sa.Integer(), nullable=True),
        sa.Column("sale_id", sa.Integer(), nullable=True),
        sa.Column("sale_item_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("available_before", sa.Integer(), nullable=True),
        sa.Column("available_after", sa.Integer(), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sale_item_id"], ["sale_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["variation_id"], ["product_variations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sale_payment_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_id"),
        sa.UniqueConstraint("token"),
    )

    op.add_column("sales", sa.Column("product_id", sa.Integer(), nullable=True))
    op.add_column("sales", sa.Column("product_public_id", sa.String(length=36), nullable=True))
    op.add_column("sales", sa.Column("channel", sa.String(length=20), nullable=False, server_default="page"))
    op.create_index(op.f("ix_sales_product_id"), "sales", ["product_id"], unique=False)
    op.create_index(op.f("ix_sales_product_public_id"), "sales", ["product_public_id"], unique=False)
    op.create_foreign_key("fk_sales_product_id", "sales", "products", ["product_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_sales_product_id", "sales", type_="foreignkey")
    op.drop_index(op.f("ix_sales_product_public_id"), table_name="sales")
    op.drop_index(op.f("ix_sales_product_id"), table_name="sales")
    op.drop_column("sales", "channel")
    op.drop_column("sales", "product_public_id")
    op.drop_column("sales", "product_id")

    op.drop_table("sale_payment_links")
    op.drop_table("product_inventory_events")
    op.drop_table("sale_items")
    op.drop_table("product_variations")
    op.drop_table("products")
