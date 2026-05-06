from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Room(Base):
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

    containers: Mapped[list["Container"]] = relationship(back_populates="label")


class Container(Base):
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
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="SET NULL"),
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
    label: Mapped[Label | None] = relationship(back_populates="containers")
    images: Mapped[list["Image"]] = relationship(
        back_populates="container",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Image.sort_order",
    )


class Image(Base):
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
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    container: Mapped[Container] = relationship(back_populates="images")
