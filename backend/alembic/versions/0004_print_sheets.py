"""Add persisted print sheet support.

Revision ID: 0004_print_sheets
Revises: 0003_label_first_container_flow
Create Date: 2026-05-08 06:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_print_sheets"
down_revision = "0003_label_first_container_flow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create saved print sheet tables and ordering indexes."""
    op.create_table(
        "print_sheets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "print_sheet_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("print_sheet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("container_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["container_id"], ["containers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["print_sheet_id"], ["print_sheets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_print_sheet_items_print_sheet_id",
        "print_sheet_items",
        ["print_sheet_id"],
        unique=False,
    )
    op.create_index(
        "ix_print_sheet_items_container_id",
        "print_sheet_items",
        ["container_id"],
        unique=False,
    )
    op.create_index(
        "ix_print_sheet_items_sheet_sort_order",
        "print_sheet_items",
        ["print_sheet_id", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    """Drop saved print sheet tables."""
    op.drop_index("ix_print_sheet_items_sheet_sort_order", table_name="print_sheet_items")
    op.drop_index("ix_print_sheet_items_container_id", table_name="print_sheet_items")
    op.drop_index("ix_print_sheet_items_print_sheet_id", table_name="print_sheet_items")
    op.drop_table("print_sheet_items")
    op.drop_table("print_sheets")
