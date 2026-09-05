"""phase 8 encrypted eBay OAuth connection

Revision ID: 0006_phase8_oauth
Revises: 0005_phase6_writer
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_phase8_oauth"
down_revision = "0005_phase6_writer"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("ebay_connections") as batch:
        batch.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default="DISCONNECTED"))
        batch.add_column(sa.Column("encrypted_access_token", sa.Text(), nullable=True))
        batch.add_column(sa.Column("encrypted_refresh_token", sa.Text(), nullable=True))
        batch.add_column(sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("last_error_code", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("legacy_imported_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_index("ix_ebay_connections_status", ["status"])


def downgrade():
    with op.batch_alter_table("ebay_connections") as batch:
        batch.drop_index("ix_ebay_connections_status")
        for column in ("legacy_imported_at", "last_error_code", "disconnected_at", "refresh_token_expires_at", "access_token_expires_at", "encrypted_refresh_token", "encrypted_access_token", "status"):
            batch.drop_column(column)
