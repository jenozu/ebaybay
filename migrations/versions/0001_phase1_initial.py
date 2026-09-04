"""phase 1 initial schema

Revision ID: 0001_phase1
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_phase1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("ebay_connections", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("environment", sa.String(length=32), nullable=False), sa.Column("marketplace_id", sa.String(length=32), nullable=False), sa.Column("account_label", sa.String(length=128), nullable=True), sa.Column("token_path", sa.String(length=255), nullable=False), sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("listings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sku", sa.String(length=64), nullable=False), sa.Column("title", sa.String(length=255), nullable=True), sa.Column("seller_notes", sa.Text(), nullable=True), sa.Column("condition", sa.String(length=64), nullable=True), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("final_price", sa.Numeric(10, 2), nullable=True), sa.Column("status", sa.String(length=32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("sku"))
    op.create_index("ix_listings_sku", "listings", ["sku"], unique=True)
    op.create_index("ix_listings_status", "listings", ["status"], unique=False)
    op.create_table("listing_images", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False), sa.Column("filename", sa.String(length=255), nullable=False), sa.Column("original_filename", sa.String(length=255), nullable=False), sa.Column("mime_type", sa.String(length=128), nullable=False), sa.Column("size_bytes", sa.Integer(), nullable=False), sa.Column("sort_order", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_listing_images_listing_id", "listing_images", ["listing_id"], unique=False)
    op.create_table("listing_aspects", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(length=128), nullable=False), sa.Column("value", sa.String(length=255), nullable=True), sa.Column("required", sa.Boolean(), nullable=False))
    op.create_index("ix_listing_aspects_listing_id", "listing_aspects", ["listing_id"], unique=False)
    op.create_table("comparable_listings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False), sa.Column("ebay_item_id", sa.String(length=64), nullable=True), sa.Column("title", sa.String(length=255), nullable=True), sa.Column("price", sa.Numeric(10, 2), nullable=True), sa.Column("currency", sa.String(length=8), nullable=True), sa.Column("url", sa.Text(), nullable=True), sa.Column("similarity_score", sa.Float(), nullable=True))
    op.create_index("ix_comparable_listings_listing_id", "comparable_listings", ["listing_id"], unique=False)


def downgrade():
    op.drop_index("ix_comparable_listings_listing_id", table_name="comparable_listings")
    op.drop_table("comparable_listings")
    op.drop_index("ix_listing_aspects_listing_id", table_name="listing_aspects")
    op.drop_table("listing_aspects")
    op.drop_index("ix_listing_images_listing_id", table_name="listing_images")
    op.drop_table("listing_images")
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_sku", table_name="listings")
    op.drop_table("listings")
    op.drop_table("ebay_connections")
