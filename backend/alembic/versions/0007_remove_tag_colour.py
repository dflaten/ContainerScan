"""Remove tag colour from labels.

Revision ID: 0007_remove_tag_colour
Revises: 0006_container_colour
Create Date: 2026-05-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_remove_tag_colour"
down_revision = "0006_container_colour"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_labels_colour_hex", "labels", type_="check")
    op.drop_column("labels", "colour")


def downgrade() -> None:
    op.add_column(
        "labels",
        sa.Column("colour", sa.String(length=7), nullable=True, server_default="#3B82F6"),
    )
    op.execute("UPDATE labels SET colour = '#3B82F6' WHERE colour IS NULL")
    op.alter_column("labels", "colour", nullable=False, server_default=None)
    op.create_check_constraint(
        "ck_labels_colour_hex",
        "labels",
        r"colour ~ '^#[0-9A-Fa-f]{6}$'",
    )
