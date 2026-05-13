"""Add many-to-many container tags support.

Revision ID: 0005_container_tags
Revises: 0004_print_sheets
Create Date: 2026-05-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_container_tags"
down_revision = "0004_print_sheets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "container_tags",
        sa.Column("container_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["container_id"], ["containers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("container_id", "label_id"),
    )
    op.create_index("ix_container_tags_label_id", "container_tags", ["label_id"], unique=False)
    op.execute(
        """
        INSERT INTO container_tags (container_id, label_id)
        SELECT id, label_id
        FROM containers
        WHERE label_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_container_tags_label_id", table_name="container_tags")
    op.drop_table("container_tags")
