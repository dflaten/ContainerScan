from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys
from unittest.mock import patch
import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Container, Image, Label, Room
from routers.containers import (
    create_container,
    delete_container,
    download_container_qr_label,
    get_container,
    get_container_by_code,
    list_containers,
    update_container,
)
from schemas import ContainerCreate, ContainerUpdate
from utils.qr_labels import build_scan_url


@dataclass
class FakeResult:
    """Simple query-result wrapper used by container router unit tests."""

    items: list[object]

    def scalars(self) -> FakeResult:
        """Return self to mimic SQLAlchemy's scalar result API.

        Returns:
            FakeResult: The current fake result object.
        """
        return self

    def all(self) -> list[object]:
        """Return all stored result items.

        Returns:
            list[object]: The items captured for this fake query result.
        """
        return self.items

    def scalar_one_or_none(self) -> object | None:
        """Return exactly one item or `None`.

        Returns:
            object | None: The single matching item, if present.
        """
        if not self.items:
            return None
        if len(self.items) > 1:
            raise AssertionError("Expected at most one item.")
        return self.items[0]


@dataclass
class FakeSession:
    """In-memory session stub for container router tests."""

    rooms: dict[uuid.UUID, Room] = field(default_factory=dict)
    labels: dict[uuid.UUID, Label] = field(default_factory=dict)
    containers: dict[uuid.UUID, Container] = field(default_factory=dict)
    images: dict[uuid.UUID, Image] = field(default_factory=dict)
    pending_add: object | None = None
    pending_delete: object | None = None
    rollbacks: int = 0

    def execute(self, statement: object) -> FakeResult:
        """Simulate simple `SELECT` queries for containers.

        Args:
            statement: SQLAlchemy statement to evaluate.

        Returns:
            FakeResult: Fake scalar result rows matching the statement.
        """
        entity = statement.column_descriptions[0]["entity"]
        filters = statement.get_execution_options().get("containerscan_filters", {})
        where_criteria = list(statement._where_criteria)

        if entity is Container:
            items = list(self.containers.values())
            if filters.get("search") is not None:
                items = [
                    item for item in items if _container_matches_search(item, filters["search"])
                ]
            if filters.get("room_id") is not None:
                items = [item for item in items if item.room_id == filters["room_id"]]
            if filters.get("label_id") is not None:
                items = [item for item in items if item.label_id == filters["label_id"]]
            if filters.get("code") is not None:
                items = [item for item in items if item.code == filters["code"]]
            for criterion in where_criteria:
                if not hasattr(criterion, "left") or not hasattr(criterion, "right"):
                    continue
                column_name = criterion.left.name
                value = criterion.right.value
                items = [item for item in items if getattr(item, column_name) == value]
            items.sort(key=lambda item: (item.created_at, item.code), reverse=True)
            return FakeResult(items)

        raise AssertionError(f"Unexpected entity: {entity!r}")

    def add(self, instance: object) -> None:
        """Stage one object for insertion on the next commit.

        Args:
            instance: ORM instance to store when committed.
        """
        self.pending_add = instance

    def get(self, model: type[object], identifier: uuid.UUID) -> object | None:
        """Look up a room, label, or container by identifier.

        Args:
            model: ORM type being requested.
            identifier: Resource identifier to resolve.

        Returns:
            object | None: The matching resource, if present.
        """
        if model is Room:
            return self.rooms.get(identifier)
        if model is Label:
            return self.labels.get(identifier)
        if model is Container:
            return self.containers.get(identifier)
        raise AssertionError(f"Unexpected model: {model!r}")

    def commit(self) -> None:
        """Apply staged changes and enforce fake integrity constraints."""
        if isinstance(self.pending_add, Container):
            self._store_container(self.pending_add)
        elif isinstance(self.pending_delete, Container):
            self._delete_container(self.pending_delete)
        else:
            self._validate_current_state()

        self.pending_add = None
        self.pending_delete = None

    def refresh(self, _: object) -> None:
        """Mirror SQLAlchemy's refresh API as a no-op for tests.

        Returns:
            None: Always returns `None`.
        """
        return None

    def delete(self, instance: object) -> None:
        """Stage one object for deletion on the next commit.

        Args:
            instance: ORM instance to remove when committed.
        """
        self.pending_delete = instance

    def rollback(self) -> None:
        """Clear staged changes and increment the rollback counter."""
        self.pending_add = None
        self.pending_delete = None
        self.rollbacks += 1

    def _store_container(self, container: Container) -> None:
        """Persist a container in the in-memory store.

        Args:
            container: Container instance to store.
        """
        if any(existing.code == container.code and existing.id != container.id for existing in self.containers.values()):
            raise _integrity_error()
        self.containers[container.id] = container

    def _delete_container(self, container: Container) -> None:
        """Delete a container and any related image records.

        Args:
            container: Container instance to delete.
        """
        self.containers.pop(container.id, None)
        image_ids = [
            image_id for image_id, image in self.images.items() if image.container_id == container.id
        ]
        for image_id in image_ids:
            self.images.pop(image_id, None)

    def _validate_current_state(self) -> None:
        """Ensure fake uniqueness constraints still hold after updates."""
        codes = [container.code for container in self.containers.values()]
        if len(codes) != len(set(codes)):
            raise _integrity_error()


def _integrity_error() -> IntegrityError:
    """Construct a generic integrity error for fake-session tests.

    Returns:
        IntegrityError: Constraint-style error used by router tests.
    """
    return IntegrityError("statement", {}, Exception("constraint violation"))


def _container_matches_search(container: Container, search: str) -> bool:
    """Check whether a fake container matches a full-text-style search string.

    Args:
        container: Container to evaluate.
        search: Search text to match against code, name, and description.

    Returns:
        bool: `True` when all normalized search terms are present.
    """
    terms = re.findall(r"[a-z0-9]+", search.lower())
    haystack = " ".join([container.code, container.name, container.description]).lower()
    return all(term in haystack for term in terms)


def _build_room(*, name: str) -> Room:
    """Build a room fixture object for unit tests.

    Args:
        name: Room name to assign.

    Returns:
        Room: Unsaved room instance.
    """
    return Room(id=uuid.uuid4(), name=name, created_at=datetime.now(timezone.utc))


def _build_label(*, name: str, colour: str) -> Label:
    """Build a label fixture object for unit tests.

    Args:
        name: Label name to assign.
        colour: Hex colour value to assign.

    Returns:
        Label: Unsaved label instance.
    """
    return Label(
        id=uuid.uuid4(),
        name=name,
        colour=colour,
        created_at=datetime.now(timezone.utc),
    )


def _build_container(
    *,
    code: str,
    name: str,
    room_id: uuid.UUID,
    label_id: uuid.UUID,
    created_at: datetime | None = None,
    description: str = "",
) -> Container:
    """Build a container fixture object for unit tests.

    Args:
        code: Container code to assign.
        name: Container name to assign.
        room_id: Related room identifier.
        label_id: Related label identifier.
        created_at: Optional creation timestamp override.
        description: Description text to assign.

    Returns:
        Container: Unsaved container instance.
    """
    timestamp = created_at or datetime.now(timezone.utc)
    return Container(
        id=uuid.uuid4(),
        code=code,
        name=name,
        description=description,
        room_id=room_id,
        label_id=label_id,
        created_at=timestamp,
        updated_at=timestamp,
        room=None,
        label=None,
        images=[],
    )


def _build_image(*, container_id: uuid.UUID, sort_order: int, caption: str | None = None) -> Image:
    """Build an image fixture object for unit tests.

    Args:
        container_id: Parent container identifier.
        sort_order: Ordering value for the image.
        caption: Optional caption text.

    Returns:
        Image: Unsaved image instance.
    """
    return Image(
        id=uuid.uuid4(),
        container_id=container_id,
        filename=f"{container_id}-{sort_order}.jpg",
        uploaded_at=datetime.now(timezone.utc),
        is_primary=sort_order == 0,
        caption=caption,
        sort_order=sort_order,
    )


def test_container_crud_endpoints_cover_happy_path_and_fk_validation() -> None:
    """Verify container CRUD behavior, FK validation, and image metadata handling."""
    room = _build_room(name="Garage")
    next_room = _build_room(name="Attic")
    label = _build_label(name="Tools", colour="#AABBCC")
    next_label = _build_label(name="Seasonal", colour="#112233")
    older = datetime.now(timezone.utc) - timedelta(days=1)
    newer = datetime.now(timezone.utc)

    existing_container = _build_container(
        code="AA-11",
        name="Existing Box",
        room_id=room.id,
        label_id=label.id,
        created_at=older,
        description="wrenches and sockets",
    )
    image = _build_image(container_id=existing_container.id, sort_order=0, caption="front")
    existing_container.images = [image]

    newer_container = _build_container(
        code="ZZ-99",
        name="Newer Box",
        room_id=room.id,
        label_id=label.id,
        created_at=newer,
        description="holiday lights",
    )

    session = FakeSession(
        rooms={room.id: room, next_room.id: next_room},
        labels={label.id: label, next_label.id: next_label},
        containers={
            existing_container.id: existing_container,
            newer_container.id: newer_container,
        },
        images={image.id: image},
    )

    containers = list_containers(session)
    assert [item.code for item in containers] == ["ZZ-99", "AA-11"]

    fetched = get_container(existing_container.id, session)
    assert fetched.images[0].caption == "front"

    fetched_by_code = get_container_by_code("aa-11", session)
    assert fetched_by_code.id == existing_container.id

    with patch("routers.containers.generate_unique_container_code", return_value="BC-23"):
        created = create_container(
            ContainerCreate(
                name="  Camping Bin  ",
                description="  tent stakes and lanterns  ",
                room_id=next_room.id,
                label_id=next_label.id,
            ),
            session,
        )

    assert created.code == "BC-23"
    assert created.name == "Camping Bin"
    assert created.description == "tent stakes and lanterns"
    assert session.containers[created.id].room_id == next_room.id

    updated = update_container(
        existing_container.id,
        ContainerUpdate(
            name=" Garage Tools ",
            description=" drills and screws ",
            room_id=next_room.id,
            label_id=next_label.id,
        ),
        session,
    )
    assert updated.name == "Garage Tools"
    assert updated.description == "drills and screws"
    assert updated.room_id == next_room.id
    assert updated.code == "AA-11"

    delete_response = delete_container(existing_container.id, session)
    assert delete_response.status_code == 204
    assert existing_container.id not in session.containers
    assert image.id not in session.images

    try:
        create_container(
            ContainerCreate(
                name="Missing Room",
                description="",
                room_id=uuid.uuid4(),
                label_id=label.id,
            ),
            session,
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Room not found."
    else:
        raise AssertionError("Expected missing room validation to raise HTTPException")

    try:
        update_container(
            newer_container.id,
            ContainerUpdate(
                name="Missing Label",
                description="",
                room_id=room.id,
                label_id=uuid.uuid4(),
            ),
            session,
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Label not found."
    else:
        raise AssertionError("Expected missing label validation to raise HTTPException")


def test_container_endpoints_raise_not_found_for_missing_records() -> None:
    """Verify missing container lookups return 404-style errors."""
    room = _build_room(name="Basement")
    label = _build_label(name="Archive", colour="#334455")
    session = FakeSession(rooms={room.id: room}, labels={label.id: label})

    try:
        get_container(uuid.uuid4(), session)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Container not found."
    else:
        raise AssertionError("Expected missing container detail to raise HTTPException")

    try:
        get_container_by_code("NO-PE", session)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Container not found."
    else:
        raise AssertionError("Expected missing container code lookup to raise HTTPException")

    try:
        delete_container(uuid.uuid4(), session)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Container not found."
    else:
        raise AssertionError("Expected missing container delete to raise HTTPException")


def test_list_containers_supports_search_and_combined_filters() -> None:
    """Verify container listing supports search, code, room, and label filters together."""
    garage = _build_room(name="Garage")
    attic = _build_room(name="Attic")
    tools = _build_label(name="Tools", colour="#AABBCC")
    seasonal = _build_label(name="Seasonal", colour="#112233")
    base_time = datetime.now(timezone.utc)

    hardware = _build_container(
        code="AA-11",
        name="Hardware Bin",
        room_id=garage.id,
        label_id=tools.id,
        created_at=base_time - timedelta(days=2),
        description="screws bolts nails",
    )
    camping = _build_container(
        code="BC-23",
        name="Camping Gear",
        room_id=attic.id,
        label_id=seasonal.id,
        created_at=base_time - timedelta(days=1),
        description="tent stakes lantern",
    )
    holiday = _build_container(
        code="ZX-90",
        name="Holiday Lights",
        room_id=garage.id,
        label_id=seasonal.id,
        created_at=base_time,
        description="christmas lights extension cords",
    )

    session = FakeSession(
        rooms={garage.id: garage, attic.id: attic},
        labels={tools.id: tools, seasonal.id: seasonal},
        containers={
            hardware.id: hardware,
            camping.id: camping,
            holiday.id: holiday,
        },
    )

    assert [item.code for item in list_containers(search="tent", session=session)] == ["BC-23"]
    assert [item.code for item in list_containers(search="zx-90", session=session)] == ["ZX-90"]
    assert [item.code for item in list_containers(room_id=garage.id, session=session)] == ["ZX-90", "AA-11"]
    assert [item.code for item in list_containers(label_id=seasonal.id, session=session)] == ["ZX-90", "BC-23"]
    assert [item.code for item in list_containers(code=" bc-23 ", session=session)] == ["BC-23"]
    assert [
        item.code
        for item in list_containers(
            search="lights",
            room_id=garage.id,
            label_id=seasonal.id,
            code="zx-90",
            session=session,
        )
    ] == ["ZX-90"]
    assert [item.code for item in list_containers(search="   ", code="   ", session=session)] == [
        "ZX-90",
        "BC-23",
        "AA-11",
    ]


def test_download_container_qr_label_returns_png_attachment() -> None:
    """Verify the QR endpoint returns a PNG response with a useful filename."""
    pytest = __import__("pytest")
    pytest.importorskip("qrcode")
    pytest.importorskip("PIL")

    room = _build_room(name="Garage")
    label = _build_label(name="Tools", colour="#AABBCC")
    container = _build_container(
        code="AA-11",
        name="Hardware Bin",
        room_id=room.id,
        label_id=label.id,
        description="screws bolts nails",
    )
    container.room = room
    container.label = label
    session = FakeSession(
        rooms={room.id: room},
        labels={label.id: label},
        containers={container.id: container},
    )

    response = download_container_qr_label(container.id, session)

    assert response.media_type == "image/png"
    assert response.headers["content-disposition"] == 'attachment; filename="AA-11-label.png"'
    assert response.body.startswith(b"\x89PNG\r\n\x1a\n")


def test_download_container_qr_label_passes_expected_metadata_to_renderer() -> None:
    """Verify the QR endpoint encodes stable scan data and container metadata."""
    room = _build_room(name="Attic")
    label = _build_label(name="Seasonal", colour="#112233")
    container = _build_container(
        code="BC-23",
        name="Holiday Lights",
        room_id=room.id,
        label_id=label.id,
        description="led strings",
    )
    container.room = room
    container.label = label
    session = FakeSession(
        rooms={room.id: room},
        labels={label.id: label},
        containers={container.id: container},
    )

    captured: dict[str, object] = {}

    def _fake_render_qr_label_png(**kwargs: object) -> bytes:
        captured.update(kwargs)
        return b"png-bytes"

    with patch("routers.containers.render_qr_label_png", side_effect=_fake_render_qr_label_png):
        response = download_container_qr_label(container.id, session)

    assert response.body == b"png-bytes"
    assert captured == {
        "container_id": container.id,
        "container_code": "BC-23",
        "container_name": "Holiday Lights",
        "room_name": "Attic",
        "label_colour": "#112233",
    }


def test_build_scan_url_uses_public_base_url_without_double_slashes() -> None:
    """Verify scan URLs are built from the configured LAN origin."""
    with patch(
        "utils.qr_labels.get_settings",
        return_value=type("Settings", (), {"public_base_url": "http://containerscan.local/"})(),
    ):
        scan_url = build_scan_url(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    assert scan_url == "http://containerscan.local/scan/12345678-1234-5678-1234-567812345678"
