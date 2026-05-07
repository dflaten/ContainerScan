"""Upgrade container codes from four characters to dashed five-character format.

Revision ID: 0002_container_code_dash_format
Revises: 0001_initial_schema
Create Date: 2026-05-06 20:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_container_code_dash_format"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert existing codes such as `AB12` into `AB-12` and widen the column."""
    bind = op.get_bind()
    current_code_length = bind.execute(
        sa.text(
            """
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'containers' AND column_name = 'code';
            """
        )
    ).scalar_one()

    op.execute("ALTER TABLE containers DROP CONSTRAINT IF EXISTS ck_containers_code_format;")

    if current_code_length == 5:
        op.execute(
            """
            ALTER TABLE containers
            ADD CONSTRAINT ck_containers_code_format
            CHECK (code ~ '^[A-Z0-9]{2}-[A-Z0-9]{2}$');
            """
        )
        return

    _drop_code_dependent_database_objects()

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

    _create_code_dependent_database_objects()
    _refresh_search_vector()

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
    _drop_code_dependent_database_objects()

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

    _create_code_dependent_database_objects()
    _refresh_search_vector()

    op.execute(
        """
        ALTER TABLE containers
        ADD CONSTRAINT ck_containers_code_format
        CHECK (code ~ '^[A-Z0-9]{4}$');
        """
    )


def _drop_code_dependent_database_objects() -> None:
    """Drop triggers and functions that depend on the `containers.code` column definition."""
    op.execute("DROP TRIGGER IF EXISTS trg_containers_immutable_code ON containers;")
    op.execute("DROP TRIGGER IF EXISTS trg_containers_search_vector ON containers;")
    op.execute("DROP FUNCTION IF EXISTS prevent_container_code_update();")
    op.execute("DROP FUNCTION IF EXISTS containers_search_vector_update();")


def _create_code_dependent_database_objects() -> None:
    """Recreate triggers and functions dropped around code-column type changes."""
    op.execute(
        """
        CREATE FUNCTION containers_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(NEW.code, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.name, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE FUNCTION prevent_container_code_update() RETURNS trigger AS $$
        BEGIN
            IF NEW.code IS DISTINCT FROM OLD.code THEN
                RAISE EXCEPTION 'container code is immutable once created';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_containers_search_vector
        BEFORE INSERT OR UPDATE OF code, name, description
        ON containers
        FOR EACH ROW
        EXECUTE FUNCTION containers_search_vector_update();
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_containers_immutable_code
        BEFORE UPDATE OF code ON containers
        FOR EACH ROW
        EXECUTE FUNCTION prevent_container_code_update();
        """
    )


def _refresh_search_vector() -> None:
    """Backfill the `search_vector` after code-format rewrites."""
    op.execute(
        """
        UPDATE containers
        SET search_vector =
            setweight(to_tsvector('simple', coalesce(code, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(name, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C');
        """
    )
