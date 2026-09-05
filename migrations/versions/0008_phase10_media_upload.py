"""phase 10 eBay Media image resources

Revision ID: 0008_phase10_media
Revises: 0007_phase9_defaults
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_phase10_media"
down_revision = "0007_phase9_defaults"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listing_images") as batch:
        batch.add_column(sa.Column("ebay_image_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("ebay_image_url", sa.Text(), nullable=True))
        batch.add_column(sa.Column("ebay_upload_status", sa.String(length=32), nullable=False, server_default="PENDING"))
        batch.add_column(sa.Column("ebay_upload_error", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("ebay_upload_fingerprint", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("ebay_uploaded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table("listing_images") as batch:
        for column in ("ebay_uploaded_at", "ebay_upload_fingerprint", "ebay_upload_error", "ebay_upload_status", "ebay_image_url", "ebay_image_id"):
            batch.drop_column(column)
