from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Table, Text, Column, func, text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

container_tags_table = Table(
    "container_tags",
    Base.metadata,
    Column("container_id", UUID(as_uuid=True), ForeignKey("containers.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", UUID(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_container_tags_label_id", "label_id"),
)


class Room(Base):
    """Database model for a physical storage location."""

    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    containers: Mapped[list["Container"]] = relationship(back_populates="room")


class Label(Base):
    """Database model for a user-defined colour label."""

    __tablename__ = "labels"
    __table_args__ = (
        CheckConstraint(r"colour ~ '^#[0-9A-Fa-f]{6}$'", name="ck_labels_colour_hex"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    colour: Mapped[str] = mapped_column(String(7), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    primary_containers: Mapped[list["Container"]] = relationship(back_populates="label")
    tagged_containers: Mapped[list["Container"]] = relationship(
        secondary=container_tags_table,
        back_populates="tags",
    )


class Container(Base):
    """Database model for a stored container and its metadata."""

    __tablename__ = "containers"
    __table_args__ = (
        CheckConstraint(r"code ~ '^[A-Z0-9]{2}-[A-Z0-9]{2}$'", name="ck_containers_code_format"),
        Index("ix_containers_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_containers_room_id", "room_id"),
        Index("ix_containers_label_id", "label_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(CHAR(5), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    colour: Mapped[str] = mapped_column(String(7), nullable=False, server_default=text("'#3B82F6'"))
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="RESTRICT"),
        nullable=True,
    )
    label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        nullable=False,
        server_default=text("''::tsvector"),
    )

    room: Mapped[Room | None] = relationship(back_populates="containers")
    label: Mapped[Label | None] = relationship(back_populates="primary_containers")
    tags: Mapped[list[Label]] = relationship(
        secondary=container_tags_table,
        back_populates="tagged_containers",
        order_by="Label.name",
    )
    images: Mapped[list["Image"]] = relationship(
        back_populates="container",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Image.sort_order",
    )
    print_sheet_items: Mapped[list["PrintSheetItem"]] = relationship(back_populates="container")

    @property
    def tag_ids(self) -> list[uuid.UUID]:
        """Expose ordered tag identifiers for API serialization."""
        return [tag.id for tag in self.tags]


class Image(Base):
    """Database model for an image attached to a container."""

    __tablename__ = "images"
    __table_args__ = (
        Index("ix_images_container_id", "container_id"),
        Index("ix_images_container_sort_order", "container_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("containers.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    container: Mapped[Container] = relationship(back_populates="images")

    @property
    def url(self) -> str:
        """Return the relative URL used to serve this stored image."""
        return f"/images/{self.filename}"


class PrintSheet(Base):
    """Database model for a saved printable sheet of container labels."""

    __tablename__ = "print_sheets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items: Mapped[list["PrintSheetItem"]] = relationship(
        back_populates="print_sheet",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PrintSheetItem.sort_order",
    )

    @property
    def containers(self) -> list[Container]:
        """Expose ordered containers for API serialization and print previews."""
        return [item.container for item in self.items]


class PrintSheetItem(Base):
    """Join model preserving container order within one saved print sheet."""

    __tablename__ = "print_sheet_items"
    __table_args__ = (
        Index("ix_print_sheet_items_print_sheet_id", "print_sheet_id"),
        Index("ix_print_sheet_items_container_id", "container_id"),
        Index("ix_print_sheet_items_sheet_sort_order", "print_sheet_id", "sort_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    print_sheet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("print_sheets.id", ondelete="CASCADE"),
        nullable=False,
    )
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("containers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    print_sheet: Mapped[PrintSheet] = relationship(back_populates="items")
    container: Mapped[Container] = relationship(back_populates="print_sheet_items")
