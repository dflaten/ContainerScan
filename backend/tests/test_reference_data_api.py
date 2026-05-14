from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Label, Room
from routers.labels import create_tag, delete_tag, list_tags, update_tag
from routers.rooms import create_room, delete_room, list_rooms, update_room
from schemas import RoomCreate, RoomUpdate, TagCreate, TagUpdate


@dataclass
class FakeResult:
    """Simple query-result wrapper used by router unit tests."""

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


@dataclass
class FakeSession:
    """In-memory session stub for room and label router tests."""

    rooms: dict[uuid.UUID, Room] = field(default_factory=dict)
    labels: dict[uuid.UUID, Label] = field(default_factory=dict)
    protected_room_ids: set[uuid.UUID] = field(default_factory=set)
    protected_label_ids: set[uuid.UUID] = field(default_factory=set)
    pending_add: object | None = None
    pending_delete: object | None = None
    rollbacks: int = 0

    def execute(self, statement: object) -> FakeResult:
        """Simulate simple ordered `SELECT` queries for rooms and labels.

        Args:
            statement: SQLAlchemy statement to evaluate.

        Returns:
            FakeResult: Fake scalar result rows matching the statement.
        """
        entity = statement.column_descriptions[0]["entity"]
        if entity is Room:
            return FakeResult(sorted(self.rooms.values(), key=lambda room: room.name))
        if entity is Label:
            return FakeResult(sorted(self.labels.values(), key=lambda label: label.name))
        raise AssertionError(f"Unexpected entity: {entity!r}")

    def add(self, instance: object) -> None:
        """Stage one object for insertion on the next commit.

        Args:
            instance: ORM instance to store when committed.
        """
        self.pending_add = instance

    def get(self, model: type[object], identifier: uuid.UUID) -> object | None:
        """Look up a room or label by identifier.

        Args:
            model: ORM type being requested.
            identifier: Resource identifier to resolve.

        Returns:
            object | None: The matching resource, if present.
        """
        store = self.rooms if model is Room else self.labels
        return store.get(identifier)

    def commit(self) -> None:
        """Apply staged changes and enforce fake integrity constraints."""
        if isinstance(self.pending_add, Room):
            self._store_room(self.pending_add)
        elif isinstance(self.pending_add, Label):
            self._store_label(self.pending_add)
        elif isinstance(self.pending_delete, Room):
            self._delete_room(self.pending_delete)
        elif isinstance(self.pending_delete, Label):
            self._delete_label(self.pending_delete)
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

    def _store_room(self, room: Room) -> None:
        """Persist a room in the in-memory store.

        Args:
            room: Room instance to store.
        """
        if any(existing.name == room.name and existing.id != room.id for existing in self.rooms.values()):
            raise _integrity_error()
        self.rooms[room.id] = room

    def _store_label(self, label: Label) -> None:
        """Persist a label in the in-memory store.

        Args:
            label: Label instance to store.
        """
        if any(existing.name == label.name and existing.id != label.id for existing in self.labels.values()):
            raise _integrity_error()
        self.labels[label.id] = label

    def _delete_room(self, room: Room) -> None:
        """Delete a room unless it is marked as protected.

        Args:
            room: Room instance to delete.
        """
        if room.id in self.protected_room_ids:
            raise _integrity_error()
        self.rooms.pop(room.id, None)

    def _delete_label(self, label: Label) -> None:
        """Delete a label unless it is marked as protected.

        Args:
            label: Label instance to delete.
        """
        if label.id in self.protected_label_ids:
            raise _integrity_error()
        self.labels.pop(label.id, None)

    def _validate_current_state(self) -> None:
        """Ensure fake uniqueness constraints still hold after updates."""
        room_names = [room.name for room in self.rooms.values()]
        if len(room_names) != len(set(room_names)):
            raise _integrity_error()

        label_names = [label.name for label in self.labels.values()]
        if len(label_names) != len(set(label_names)):
            raise _integrity_error()


def _integrity_error() -> IntegrityError:
    """Construct a generic integrity error for fake-session tests.

    Returns:
        IntegrityError: Constraint-style error used by router tests.
    """
    return IntegrityError("statement", {}, Exception("constraint violation"))


def _build_room(*, name: str) -> Room:
    """Build a room fixture object for unit tests.

    Args:
        name: Room name to assign.

    Returns:
        Room: Unsaved room instance.
    """
    return Room(id=uuid.uuid4(), name=name, created_at=datetime.now(timezone.utc))


def _build_label(*, name: str, colour: str | None = None) -> Label:
    """Build a label fixture object for unit tests.

    Args:
        name: Label name to assign.
    Returns:
        Label: Unsaved label instance.
    """
    return Label(
        id=uuid.uuid4(),
        name=name,
        created_at=datetime.now(timezone.utc),
    )


def test_room_crud_endpoints_cover_happy_path_and_conflicts() -> None:
    """Verify room CRUD behavior, validation, and conflict handling."""
    existing_room = _build_room(name="Attic")
    protected_room = _build_room(name="Garage")
    session = FakeSession(
        rooms={existing_room.id: existing_room, protected_room.id: protected_room},
        protected_room_ids={protected_room.id},
    )

    rooms = list_rooms(session)
    assert [item.name for item in rooms] == ["Attic", "Garage"]

    created_room = create_room(RoomCreate(name="  Pantry  "), session)
    assert created_room.name == "Pantry"

    try:
        create_room(RoomCreate(name="Attic"), session)
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "Room name already exists."
    else:
        raise AssertionError("Expected duplicate room name to raise HTTPException")

    updated_room = update_room(existing_room.id, RoomUpdate(name="Office"), session)
    assert updated_room.name == "Office"

    try:
        update_room(uuid.uuid4(), RoomUpdate(name="Den"), session)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("Expected missing room update to raise HTTPException")

    try:
        delete_room(protected_room.id, session)
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "Room is still in use by one or more containers."
    else:
        raise AssertionError("Expected protected room delete to raise HTTPException")

    delete_response = delete_room(existing_room.id, session)
    assert delete_response.status_code == 204
    assert existing_room.id not in session.rooms


def test_tag_crud_endpoints_cover_happy_path_and_conflicts() -> None:
    """Verify tag CRUD behavior, validation, and conflict handling."""
    existing_label = _build_label(name="Seasonal", colour="#3B82F6")
    protected_label = _build_label(name="Tools", colour="#22C55E")
    session = FakeSession(
        labels={existing_label.id: existing_label, protected_label.id: protected_label},
        protected_label_ids={protected_label.id},
    )

    tags = list_tags(session)
    assert [item.name for item in tags] == ["Seasonal", "Tools"]

    created_tag = create_tag(TagCreate(name=" Fragile "), session)
    assert created_tag.name == "Fragile"

    try:
        create_tag(TagCreate(name="Seasonal"), session)
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "Tag name already exists."
    else:
        raise AssertionError("Expected duplicate tag name to raise HTTPException")

    updated_tag = update_tag(
        existing_label.id,
        TagUpdate(name="Holiday"),
        session,
    )
    assert updated_tag.name == "Holiday"

    try:
        TagCreate(name="   ")
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected invalid tag validation to fail")

    try:
        delete_tag(uuid.uuid4(), session)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("Expected missing tag delete to raise HTTPException")

    try:
        delete_tag(protected_label.id, session)
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "Tag is still in use by one or more containers."
    else:
        raise AssertionError("Expected protected tag delete to raise HTTPException")

    delete_response = delete_tag(existing_label.id, session)
    assert delete_response.status_code == 204
    assert existing_label.id not in session.labels
