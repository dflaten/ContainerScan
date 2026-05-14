from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from database import SessionLocal
from models import Color, Container, Label, Room


@dataclass(frozen=True)
class SeedContainer:
    code: str
    name: str
    description: str
    room_name: str
    label_name: str


ROOM_NAMES = [
    "Basement",
    "Garage",
]

LABELS = [
    "Holiday",
    "Archive",
    "Electronics",
]

COLORS = [
    ("Blue", "#3B82F6"),
    ("Yellow", "#FACC15"),
    ("Red", "#EF4444"),
    ("Green", "#22C55E"),
]

CONTAINERS = [
    SeedContainer(
        code="HN-01",
        name="Holiday Lights",
        description="Extension cords, warm white string lights, and outdoor timer plugs.",
        room_name="Garage",
        label_name="Holiday",
    ),
    SeedContainer(
        code="AR-02",
        name="Tax Archive 2023",
        description="Receipts, signed returns, and scanned backup media for the 2023 filing year.",
        room_name="Basement",
        label_name="Archive",
    ),
    SeedContainer(
        code="EL-03",
        name="Camera Gear",
        description="Mirrorless body, two prime lenses, spare batteries, chargers, and SD cards.",
        room_name="Basement",
        label_name="Electronics",
    ),
    SeedContainer(
        code="AR-04",
        name="House Manuals",
        description="Appliance manuals, paint codes, spare keys, and contractor warranty paperwork.",
        room_name="Garage",
        label_name="Archive",
    ),
]


def get_or_create_room(session, name: str) -> tuple[Room, bool]:
    room = session.execute(select(Room).where(Room.name == name)).scalar_one_or_none()
    if room is not None:
        return room, False

    room = Room(name=name)
    session.add(room)
    session.flush()
    return room, True


def get_or_create_label(session, name: str) -> tuple[Label, bool]:
    label = session.execute(select(Label).where(Label.name == name)).scalar_one_or_none()
    if label is not None:
        return label, False

    label = Label(name=name)
    session.add(label)
    session.flush()
    return label, True


def get_or_create_color(session, name: str, value: str) -> tuple[Color, bool]:
    color = session.execute(select(Color).where(Color.name == name)).scalar_one_or_none()
    if color is not None:
        if color.value != value:
            color.value = value
            session.flush()
        return color, False

    color = Color(name=name, value=value)
    session.add(color)
    session.flush()
    return color, True


def get_or_create_container(
    session,
    *,
    code: str,
    name: str,
    description: str,
    room_id,
    label_id,
) -> bool:
    container = session.execute(select(Container).where(Container.code == code)).scalar_one_or_none()
    if container is not None:
        return False

    session.add(
        Container(
            code=code,
            name=name,
            description=description,
            room_id=room_id,
            label_id=label_id,
        )
    )
    session.flush()
    return True


def main() -> int:
    created_rooms = 0
    created_labels = 0
    created_colors = 0
    created_containers = 0

    with SessionLocal() as session:
        room_by_name: dict[str, Room] = {}
        label_by_name: dict[str, Label] = {}

        for room_name in ROOM_NAMES:
            room, created = get_or_create_room(session, room_name)
            room_by_name[room_name] = room
            created_rooms += int(created)

        for color_name, color_value in COLORS:
            _, created = get_or_create_color(session, color_name, color_value)
            created_colors += int(created)

        for label_name in LABELS:
            label, created = get_or_create_label(session, label_name)
            label_by_name[label_name] = label
            created_labels += int(created)

        for container_seed in CONTAINERS:
            created = get_or_create_container(
                session,
                code=container_seed.code,
                name=container_seed.name,
                description=container_seed.description,
                room_id=room_by_name[container_seed.room_name].id,
                label_id=label_by_name[container_seed.label_name].id,
            )
            created_containers += int(created)

        session.commit()

    print("Seed complete.")
    print(f"Rooms created: {created_rooms}")
    print(f"Colors created: {created_colors}")
    print(f"Labels created: {created_labels}")
    print(f"Containers created: {created_containers}")
    print(f"Total sample containers ensured: {len(CONTAINERS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
