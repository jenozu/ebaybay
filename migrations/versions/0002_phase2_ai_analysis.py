"""phase 2 ai product analysis

Revision ID: 0002_phase2_ai
Revises: 0001_phase1
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_phase2_ai"
down_revision = "0001_phase1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("product_name", sa.String(length=255), nullable=True))
        batch.add_column(sa.Column("brand", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("model_number", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("mpn", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("gtin", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("ai_condition_suggestion", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("ai_condition_confidence", sa.Float(), nullable=True))
        batch.add_column(sa.Column("ai_overall_confidence", sa.Float(), nullable=True))
        batch.add_column(sa.Column("ai_visible_observations", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("ai_visible_text", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("ai_search_terms", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("ai_detected_attributes", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("ai_uncertain_fields", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("ai_last_analyzed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("raw_json", sa.Text(), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("parsed_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_analyses_listing_id", "ai_analyses", ["listing_id"], unique=False)


def downgrade():
    op.drop_index("ix_ai_analyses_listing_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")
    with op.batch_alter_table("listings") as batch:
        batch.drop_column("ai_last_analyzed_at")
        batch.drop_column("ai_uncertain_fields")
        batch.drop_column("ai_detected_attributes")
        batch.drop_column("ai_search_terms")
        batch.drop_column("ai_visible_text")
        batch.drop_column("ai_visible_observations")
        batch.drop_column("ai_overall_confidence")
        batch.drop_column("ai_condition_confidence")
        batch.drop_column("ai_condition_suggestion")
        batch.drop_column("gtin")
        batch.drop_column("mpn")
        batch.drop_column("model_number")
        batch.drop_column("brand")
        batch.drop_column("product_name")
