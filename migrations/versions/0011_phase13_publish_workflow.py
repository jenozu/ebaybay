"""phase 13 controlled publication state

Revision ID: 0011_phase13_publish
Revises: 0010_phase12_offer
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_phase13_publish"
down_revision = "0010_phase12_offer"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("ebay_listing_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("ebay_listing_url", sa.Text(), nullable=True))
        batch.add_column(sa.Column("ebay_publish_status", sa.String(length=32), nullable=False, server_default="NOT_PUBLISHED"))
        batch.add_column(sa.Column("ebay_publish_error", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("ebay_published_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table("listings") as batch:
        for column in ("ebay_published_at", "ebay_publish_error", "ebay_publish_status", "ebay_listing_url", "ebay_listing_id"):
            batch.drop_column(column)
