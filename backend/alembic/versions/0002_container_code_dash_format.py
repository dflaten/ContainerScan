"""Upgrade container codes from four characters to dashed five-character format.

Revision ID: 0002_container_code_dash_format
Revises: 0001_initial_schema
Create Date: 2026-05-06 20:45:00
"""

from __future__ import annotations

from alembic import op


revision = "0002_container_code_dash_format"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert existing codes such as `AB12` into `AB-12` and widen the column."""
    op.execute("ALTER TABLE containers DROP CONSTRAINT IF EXISTS ck_containers_code_format;")

    op.execute(
        """
        ALTER TABLE containers
        ALTER COLUMN code TYPE CHAR(5)
        USING CASE
            WHEN btrim(code) ~ '^[A-Z0-9]{4}$' THEN substr(btrim(code), 1, 2) || '-' || substr(btrim(code), 3, 2)
            ELSE btrim(code)
        END;
        """
    )

    op.execute(
        """
        ALTER TABLE containers
        ADD CONSTRAINT ck_containers_code_format
        CHECK (code ~ '^[A-Z0-9]{2}-[A-Z0-9]{2}$');
        """
    )


def downgrade() -> None:
    """Remove the dash from canonical codes and shrink the column back to four characters."""
    op.execute("ALTER TABLE containers DROP CONSTRAINT IF EXISTS ck_containers_code_format;")

    op.execute(
        """
        ALTER TABLE containers
        ALTER COLUMN code TYPE CHAR(4)
        USING CASE
            WHEN btrim(code) ~ '^[A-Z0-9]{2}-[A-Z0-9]{2}$' THEN replace(btrim(code), '-', '')
            ELSE btrim(code)
        END;
        """
    )

    op.execute(
        """
        ALTER TABLE containers
        ADD CONSTRAINT ck_containers_code_format
        CHECK (code ~ '^[A-Z0-9]{4}$');
        """
    )
