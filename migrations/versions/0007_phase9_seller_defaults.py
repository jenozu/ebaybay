"""phase 9 seller policy and inventory-location defaults

Revision ID: 0007_phase9_defaults
Revises: 0006_phase8_oauth
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_phase9_defaults"
down_revision = "0006_phase8_oauth"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ebay_connections") as batch:
        batch.add_column(sa.Column("default_payment_policy_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("default_fulfillment_policy_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("default_return_policy_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("default_merchant_location_key", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("seller_defaults_cache", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("seller_defaults_refreshed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table("ebay_connections") as batch:
        for column in ("seller_defaults_refreshed_at", "seller_defaults_cache", "default_merchant_location_key", "default_return_policy_id", "default_fulfillment_policy_id", "default_payment_policy_id"):
            batch.drop_column(column)
