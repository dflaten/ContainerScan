"""Initial schema for ContainerScan.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-06 17:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("colour", sa.String(length=7), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(r"colour ~ '^#[0-9A-Fa-f]{6}$'", name="ck_labels_colour_hex"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "containers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.CHAR(length=5), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR(), server_default=sa.text("''::tsvector"), nullable=False),
        sa.CheckConstraint(r"code ~ '^[A-Z0-9]{2}-[A-Z0-9]{2}$'", name="ck_containers_code_format"),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_index("ix_containers_label_id", "containers", ["label_id"], unique=False)
    op.create_index("ix_containers_room_id", "containers", ["room_id"], unique=False)
    op.create_index(
        "ix_containers_search_vector",
        "containers",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )

    op.create_table(
        "images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("container_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["container_id"], ["containers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_images_container_id", "images", ["container_id"], unique=False)
    op.create_index(
        "ix_images_container_sort_order",
        "images",
        ["container_id", "sort_order"],
        unique=False,
    )

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
        CREATE FUNCTION set_updated_at_timestamp() RETURNS trigger AS $$
        BEGIN
            NEW.updated_at := now();
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
        CREATE TRIGGER trg_containers_updated_at
        BEFORE UPDATE ON containers
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at_timestamp();
        """
    )

    op.execute(
        """
        UPDATE containers
        SET search_vector =
            setweight(to_tsvector('simple', coalesce(code, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(name, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C');
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_containers_updated_at ON containers;")
    op.execute("DROP TRIGGER IF EXISTS trg_containers_search_vector ON containers;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at_timestamp();")
    op.execute("DROP FUNCTION IF EXISTS containers_search_vector_update();")

    op.drop_index("ix_images_container_sort_order", table_name="images")
    op.drop_index("ix_images_container_id", table_name="images")
    op.drop_table("images")

    op.drop_index("ix_containers_search_vector", table_name="containers")
    op.drop_index("ix_containers_room_id", table_name="containers")
    op.drop_index("ix_containers_label_id", table_name="containers")
    op.drop_table("containers")

    op.drop_table("labels")
    op.drop_table("rooms")
