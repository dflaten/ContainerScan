"""Add single container colour selection.

Revision ID: 0006_container_colour
Revises: 0005_container_tags
Create Date: 2026-05-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_container_colour"
down_revision = "0005_container_tags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "containers",
        sa.Column("colour", sa.String(length=7), nullable=True, server_default="#3B82F6"),
    )
    op.execute(
        """
        UPDATE containers
        SET colour = COALESCE(labels.colour, '#3B82F6')
        FROM labels
        WHERE containers.label_id = labels.id
        """
    )
    op.execute("UPDATE containers SET colour = '#3B82F6' WHERE colour IS NULL")
    op.alter_column("containers", "colour", nullable=False, server_default="#3B82F6")


def downgrade() -> None:
    op.drop_column("containers", "colour")
