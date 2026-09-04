"""phase 4 taxonomy and item specifics

Revision ID: 0003_phase4_taxonomy
Revises: 0002_phase2_ai
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_phase4_taxonomy"
down_revision = "0002_phase2_ai"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("ebay_category_id", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("ebay_category_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("ebay_category_path", sa.Text(), nullable=True))
        batch.add_column(sa.Column("ebay_category_candidates", sa.JSON(), nullable=False, server_default="[]"))
    with op.batch_alter_table("listing_aspects") as batch:
        batch.add_column(sa.Column("recommended", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("listing_aspects") as batch:
        batch.drop_column("recommended")
    with op.batch_alter_table("listings") as batch:
        batch.drop_column("ebay_category_candidates")
        batch.drop_column("ebay_category_path")
        batch.drop_column("ebay_category_name")
        batch.drop_column("ebay_category_id")
