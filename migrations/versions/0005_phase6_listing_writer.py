"""phase 6 listing writer

Revision ID: 0005_phase6_writer
Revises: 0004_phase5_pricing
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_phase6_writer"
down_revision = "0004_phase5_pricing"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("listings") as batch:
        batch.add_column(sa.Column("title_manual", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch.add_column(sa.Column("description_manual", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("condition_description", sa.Text(), nullable=True))
        batch.add_column(sa.Column("condition_description_manual", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("copy_generated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table("listings") as batch:
        for column in ("copy_generated_at", "condition_description_manual", "condition_description", "description_manual", "description", "title_manual"):
            batch.drop_column(column)
