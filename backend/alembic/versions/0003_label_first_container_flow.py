"""Allow containers to be created before room and label assignment.

Revision ID: 0003_label_first_container_flow
Revises: 0002_container_code_dash_format
Create Date: 2026-05-07 08:55:00
"""

from __future__ import annotations

from alembic import op


revision = "0003_label_first_container_flow"
down_revision = "0002_container_code_dash_format"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Relax room and label assignment so QR labels can be generated first."""
    op.execute("ALTER TABLE containers ALTER COLUMN room_id DROP NOT NULL;")
    op.execute("ALTER TABLE containers ALTER COLUMN label_id DROP NOT NULL;")


def downgrade() -> None:
    """Restore mandatory room and label assignment for containers."""
    op.execute("ALTER TABLE containers ALTER COLUMN room_id SET NOT NULL;")
    op.execute("ALTER TABLE containers ALTER COLUMN label_id SET NOT NULL;")
