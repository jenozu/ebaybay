"""phase 12 unpublished Offer staging state

Revision ID: 0010_phase12_offer
Revises: 0009_phase11_inventory
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_phase12_offer"
down_revision = "0009_phase11_inventory"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("ebay_offer_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("ebay_offer_status", sa.String(length=32), nullable=False, server_default="NOT_STAGED"))
        batch.add_column(sa.Column("ebay_offer_error", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("ebay_offer_payload_fingerprint", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("ebay_offer_staged_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table("listings") as batch:
        for column in ("ebay_offer_staged_at", "ebay_offer_payload_fingerprint", "ebay_offer_error", "ebay_offer_status", "ebay_offer_id"):
            batch.drop_column(column)
