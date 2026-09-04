"""phase 5 active comparables and pricing

Revision ID: 0004_phase5_pricing
Revises: 0003_phase4_taxonomy
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_phase5_pricing"
down_revision = "0003_phase4_taxonomy"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("final_price_manual", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("comparable_low", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("comparable_high", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("comparable_median", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("quick_sale_price", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("recommended_price", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("high_target_price", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("pricing_confidence", sa.String(16), nullable=True))
        batch.add_column(sa.Column("pricing_explanation", sa.Text(), nullable=True))
        batch.add_column(sa.Column("comparables_last_searched_at", sa.DateTime(timezone=True), nullable=True))
    with op.batch_alter_table("comparable_listings") as batch:
        batch.add_column(sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("total_price", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("condition", sa.String(128), nullable=True))
        batch.add_column(sa.Column("category_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("search_query", sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table("comparable_listings") as batch:
        for column in ("search_query", "category_id", "condition", "total_price", "shipping_cost"):
            batch.drop_column(column)
    with op.batch_alter_table("listings") as batch:
        for column in ("comparables_last_searched_at", "pricing_explanation", "pricing_confidence", "high_target_price", "recommended_price", "quick_sale_price", "comparable_median", "comparable_high", "comparable_low", "final_price_manual"):
            batch.drop_column(column)
