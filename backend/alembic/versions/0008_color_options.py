"""Add container color options.

Revision ID: 0008_color_options
Revises: 0007_remove_tag_colour
Create Date: 2026-05-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_color_options"
down_revision = "0007_remove_tag_colour"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "colors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=7), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(r"value ~ '^#[0-9A-Fa-f]{6}$'", name="ck_colors_value_hex"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("value"),
    )

    op.execute(
        """
        INSERT INTO colors (id, name, value)
        VALUES
          ('6f0ef5d0-a18e-4b9a-8f65-32d54a0f2f01', 'Blue', '#3B82F6'),
          ('ce2b05bf-8c44-47a2-8895-7147921964f2', 'Yellow', '#FACC15'),
          ('f7d073f9-7460-4dd6-b947-b43afeb38155', 'Red', '#EF4444'),
          ('72f565d5-64d7-4a36-90ea-fe57cfe6da9c', 'Green', '#22C55E')
        """
    )


def downgrade() -> None:
    op.drop_table("colors")
