from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Container, Image, Label, Room
from routers.scan import get_scan_container, render_scan_view


@dataclass
class FakeResult:
    """Simple query-result wrapper used by scan router unit tests."""

    items: list[object]

    def scalar_one_or_none(self) -> object | None:
        """Return exactly one item or `None`."""
        if not self.items:
            return None
        if len(self.items) > 1:
            raise AssertionError("Expected at most one item.")
        return self.items[0]


@dataclass
class FakeSession:
    """In-memory session stub for scan router tests."""

    containers: dict[uuid.UUID, Container] = field(default_factory=dict)

    def execute(self, statement: object) -> FakeResult:
        """Simulate single-container `SELECT` queries."""
        entity = statement.column_descriptions[0]["entity"]
        if entity is not Container:
            raise AssertionError(f"Unexpected entity: {entity!r}")

        items = list(self.containers.values())
        for criterion in statement._where_criteria:
            if not hasattr(criterion, "left") or not hasattr(criterion, "right"):
                continue
            column_name = criterion.left.name
            value = criterion.right.value
            items = [item for item in items if getattr(item, column_name) == value]
        return FakeResult(items)


def _build_room(*, name: str) -> Room:
    return Room(id=uuid.uuid4(), name=name, created_at=datetime.now(timezone.utc))


def _build_label(*, name: str, colour: str) -> Label:
    return Label(id=uuid.uuid4(), name=name, colour=colour, created_at=datetime.now(timezone.utc))


def _build_image(*, container_id: uuid.UUID, sort_order: int, caption: str | None = None) -> Image:
    return Image(
        id=uuid.uuid4(),
        container_id=container_id,
        filename=f"{container_id}-{sort_order}.jpg",
        uploaded_at=datetime.now(timezone.utc),
        is_primary=sort_order == 0,
        caption=caption,
        sort_order=sort_order,
    )


def _build_container(
    *,
    code: str,
    name: str,
    description: str,
    room: Room,
    label: Label,
    colour: str = "#3B82F6",
) -> Container:
    now = datetime.now(timezone.utc)
    return Container(
        id=uuid.uuid4(),
        code=code,
        name=name,
        description=description,
        colour=colour,
        room_id=room.id,
        label_id=label.id,
        created_at=now,
        updated_at=now,
        room=room,
        label=label,
        images=[],
    )


def test_get_scan_container_returns_read_only_container_data() -> None:
    """Verify public scan data includes room, label, and image metadata."""
    room = _build_room(name="Garage")
    label = _build_label(name="Tools", colour="#AABBCC")
    container = _build_container(
        code="AA-11",
        name="Hardware Bin",
        description="screws bolts nails",
        room=room,
        label=label,
    )
    image = _build_image(container_id=container.id, sort_order=0, caption="Front view")
    container.images = [image]
    session = FakeSession(containers={container.id: container})

    result = get_scan_container(container.id, session)

    assert result.id == container.id
    assert result.room.name == "Garage"
    assert result.label.colour == "#AABBCC"
    assert result.colour == "#3B82F6"
    assert result.images[0].url == f"/images/{image.filename}"


def test_render_scan_view_returns_mobile_friendly_read_only_html() -> None:
    """Verify the public scan route renders a minimal read-only HTML page."""
    room = _build_room(name="Attic")
    label = _build_label(name="Seasonal", colour="#112233")
    container = _build_container(
        code="BC-23",
        name="Holiday Lights",
        description="LED strings and extension cords",
        room=room,
        label=label,
        colour="#EF4444",
    )
    image = _build_image(container_id=container.id, sort_order=0, caption="Primary exterior")
    container.images = [image]
    session = FakeSession(containers={container.id: container})

    response = render_scan_view(container.id, session)
    html = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "width=device-width, initial-scale=1" in html
    assert "Read-only scan view" in html
    assert "Holiday Lights" in html
    assert "Attic" in html
    assert "Seasonal" in html
    assert "#EF4444" in html
    assert image.url in html
    assert "Primary exterior" in html


def test_render_scan_view_handles_not_yet_documented_containers() -> None:
    """Verify scan HTML uses placeholder metadata for incomplete containers."""
    now = datetime.now(timezone.utc)
    container = Container(
        id=uuid.uuid4(),
        code="LM-44",
        name="Container LM-44",
        description="",
        colour="#3B82F6",
        room_id=None,
        label_id=None,
        created_at=now,
        updated_at=now,
        room=None,
        label=None,
        images=[],
    )
    session = FakeSession(containers={container.id: container})

    response = render_scan_view(container.id, session)
    html = response.body.decode("utf-8")

    assert response.status_code == 200
    assert "Unassigned Room" in html
    assert "Untagged" in html
    assert "This container has not been documented yet." in html


def test_scan_routes_raise_not_found_for_missing_container() -> None:
    """Verify missing scan resources return a 404-style error."""
    session = FakeSession()

    try:
        get_scan_container(uuid.uuid4(), session)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Container not found."
    else:
        raise AssertionError("Expected missing scan lookup to raise HTTPException")

    try:
        render_scan_view(uuid.uuid4(), session)
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "Container not found."
    else:
        raise AssertionError("Expected missing scan view to raise HTTPException")
