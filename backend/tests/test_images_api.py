from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sys
from tempfile import SpooledTemporaryFile
from tempfile import TemporaryDirectory
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Container, Image, Label, Room
from routers.images import delete_image, update_image, upload_container_images
from schemas import ImageUpdate
from utils.image_storage import build_safe_image_filename, delete_stored_image, save_upload_to_storage


@dataclass
class FakeSession:
    """In-memory session stub for image router tests."""

    containers: dict[uuid.UUID, Container] = field(default_factory=dict)
    images: dict[uuid.UUID, Image] = field(default_factory=dict)
    pending_additions: list[Image] = field(default_factory=list)
    pending_delete: object | None = None
    rollbacks: int = 0

    def get(self, model: type[object], identifier: uuid.UUID) -> object | None:
        """Look up a container or image by identifier."""
        if model is Container:
            return self.containers.get(identifier)
        if model is Image:
            return self.images.get(identifier)
        raise AssertionError(f"Unexpected model: {model!r}")

    def add(self, instance: object) -> None:
        """Stage an image for insertion on commit."""
        if not isinstance(instance, Image):
            raise AssertionError(f"Unexpected instance: {instance!r}")
        self.pending_additions.append(instance)

    def commit(self) -> None:
        """Apply staged inserts or deletes."""
        if isinstance(self.pending_delete, Image):
            image = self.pending_delete
            self.images.pop(image.id, None)
            container = self.containers.get(image.container_id)
            if container is not None:
                container.images = [item for item in container.images if item.id != image.id]
        else:
            for image in self.pending_additions:
                if image.id in self.images:
                    raise IntegrityError("statement", {}, Exception("constraint violation"))
                self.images[image.id] = image
                container = self.containers[image.container_id]
                container.images.append(image)
            self.pending_additions.clear()

        self.pending_delete = None

    def refresh(self, _: object) -> None:
        """Mirror SQLAlchemy refresh as a no-op."""
        return None

    def delete(self, instance: object) -> None:
        """Stage one image for deletion."""
        self.pending_delete = instance

    def rollback(self) -> None:
        """Clear staged work and track rollback calls."""
        self.pending_additions.clear()
        self.pending_delete = None
        self.rollbacks += 1


def _build_room(*, name: str) -> Room:
    return Room(id=uuid.uuid4(), name=name, created_at=datetime.now(timezone.utc))


def _build_label(*, name: str, colour: str) -> Label:
    return Label(id=uuid.uuid4(), name=name, colour=colour, created_at=datetime.now(timezone.utc))


def _build_container(*, code: str, room_id: uuid.UUID, label_id: uuid.UUID) -> Container:
    now = datetime.now(timezone.utc)
    return Container(
        id=uuid.uuid4(),
        code=code,
        name="Bin",
        description="",
        room_id=room_id,
        label_id=label_id,
        created_at=now,
        updated_at=now,
        images=[],
    )


def _build_image(*, container_id: uuid.UUID, sort_order: int, caption: str | None = None) -> Image:
    return Image(
        id=uuid.uuid4(),
        container_id=container_id,
        filename=f"{uuid.uuid4().hex}.jpg",
        uploaded_at=datetime.now(timezone.utc),
        is_primary=sort_order == 0,
        caption=caption,
        sort_order=sort_order,
    )


def _build_upload(filename: str, content_type: str, payload: bytes) -> UploadFile:
    file = SpooledTemporaryFile()
    file.write(payload)
    file.seek(0)
    return UploadFile(file=file, filename=filename, headers={"content-type": content_type})


def test_save_upload_to_storage_uses_safe_generated_filenames() -> None:
    """Verify uploaded files are stored with server-generated safe names."""
    with TemporaryDirectory() as temp_dir:
        upload = _build_upload("../../../garage-tools.png", "image/png", b"png-bytes")
        filename = asyncio.run(save_upload_to_storage(upload, temp_dir))

        assert filename.endswith(".png")
        assert "/" not in filename
        assert ".." not in filename
        stored_bytes = (Path(temp_dir) / filename).read_bytes()
        assert stored_bytes == b"png-bytes"


def test_build_safe_image_filename_rejects_unsupported_types() -> None:
    """Verify unsupported uploads are rejected before storage."""
    upload = _build_upload("notes.txt", "text/plain", b"not-an-image")

    try:
        build_safe_image_filename(upload)
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Unsupported image type" in exc.detail
    else:
        raise AssertionError("Expected unsupported upload type to raise HTTPException")


def test_upload_update_and_delete_image_endpoints_manage_metadata_and_files() -> None:
    """Verify image upload, metadata updates, and deletion behavior."""
    room = _build_room(name="Garage")
    label = _build_label(name="Tools", colour="#AABBCC")
    container = _build_container(code="AA-11", room_id=room.id, label_id=label.id)
    existing_image = _build_image(container_id=container.id, sort_order=2, caption="existing")
    container.images = [existing_image]
    session = FakeSession(
        containers={container.id: container},
        images={existing_image.id: existing_image},
    )

    with TemporaryDirectory() as temp_dir:
        import routers.images as images_router

        original_get_settings = images_router.get_settings
        images_router.get_settings = lambda: type("Settings", (), {"image_storage_path": temp_dir})()
        try:
            created = asyncio.run(
                upload_container_images(
                    container.id,
                    session=session,
                    images=[
                        _build_upload("front.jpeg", "image/jpeg", b"front"),
                        _build_upload("side.webp", "image/webp", b"side"),
                    ],
                    captions=[" Front view ", ""],
                )
            )
            assert [image.sort_order for image in created] == [3, 4]
            assert created[0].caption == "Front view"
            assert created[1].caption is None
            assert created[0].is_primary is False
            assert created[0].url.startswith("/images/")
            assert (Path(temp_dir) / created[0].filename).exists()
            assert (Path(temp_dir) / created[1].filename).exists()

            updated = update_image(
                created[0].id,
                ImageUpdate(caption=" Lid open ", sort_order=0, is_primary=True),
                session,
            )
            assert updated.caption == "Lid open"
            assert updated.sort_order == 0
            assert updated.is_primary is True
            assert existing_image.is_primary is False

            response = delete_image(created[1].id, session)
            assert response.status_code == 204
            assert created[1].id not in session.images
            assert not (Path(temp_dir) / created[1].filename).exists()
        finally:
            images_router.get_settings = original_get_settings


def test_upload_container_images_validates_missing_container_and_caption_mismatch() -> None:
    """Verify upload validation errors use HTTP-style responses."""
    session = FakeSession()

    try:
        asyncio.run(
            upload_container_images(
                uuid.uuid4(),
                session=session,
                images=[_build_upload("front.jpg", "image/jpeg", b"front")],
                captions=None,
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Container not found."
    else:
        raise AssertionError("Expected missing container to raise HTTPException")

    room = _build_room(name="Garage")
    label = _build_label(name="Tools", colour="#AABBCC")
    container = _build_container(code="AA-11", room_id=room.id, label_id=label.id)
    session.containers[container.id] = container

    try:
        asyncio.run(
            upload_container_images(
                container.id,
                session=session,
                images=[
                    _build_upload("front.jpg", "image/jpeg", b"front"),
                    _build_upload("side.jpg", "image/jpeg", b"side"),
                ],
                captions=["only one"],
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "Caption count must match the number of uploaded images."
    else:
        raise AssertionError("Expected caption mismatch to raise HTTPException")


def test_first_uploaded_image_becomes_primary_for_a_container() -> None:
    """Verify the first image upload is reserved as the main exterior photo."""
    room = _build_room(name="Garage")
    label = _build_label(name="Tools", colour="#AABBCC")
    container = _build_container(code="AA-11", room_id=room.id, label_id=label.id)
    session = FakeSession(containers={container.id: container})

    with TemporaryDirectory() as temp_dir:
        import routers.images as images_router

        original_get_settings = images_router.get_settings
        images_router.get_settings = lambda: type("Settings", (), {"image_storage_path": temp_dir})()
        try:
            created = asyncio.run(
                upload_container_images(
                    container.id,
                    session=session,
                    images=[_build_upload("outside.jpg", "image/jpeg", b"outside")],
                    captions=[" Outside shelf view "],
                )
            )
        finally:
            images_router.get_settings = original_get_settings

    assert created[0].is_primary is True
    assert created[0].caption == "Outside shelf view"


def test_delete_stored_image_is_idempotent() -> None:
    """Verify deleting a missing storage file is harmless."""
    with TemporaryDirectory() as temp_dir:
        delete_stored_image("missing.jpg", temp_dir)
        assert not any(Path(temp_dir).iterdir())
