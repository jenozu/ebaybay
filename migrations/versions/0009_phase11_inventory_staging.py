"""phase 11 inventory-item staging state

Revision ID: 0009_phase11_inventory
Revises: 0008_phase10_media
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_phase11_inventory"
down_revision = "0008_phase10_media"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("ebay_inventory_status", sa.String(length=32), nullable=False, server_default="NOT_STAGED"))
        batch.add_column(sa.Column("ebay_inventory_error", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("ebay_inventory_payload_fingerprint", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("ebay_inventory_staged_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table("listings") as batch:
        for column in ("ebay_inventory_staged_at", "ebay_inventory_payload_fingerprint", "ebay_inventory_error", "ebay_inventory_status"):
            batch.drop_column(column)
