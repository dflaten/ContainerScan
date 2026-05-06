from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Container


def test_container_room_and_label_relationships_are_required() -> None:
    room_id = Container.__table__.c.room_id
    label_id = Container.__table__.c.label_id

    assert room_id.nullable is False
    assert label_id.nullable is False

    room_fk = next(iter(room_id.foreign_keys))
    label_fk = next(iter(label_id.foreign_keys))

    assert room_fk.ondelete == "RESTRICT"
    assert label_fk.ondelete == "RESTRICT"


def test_initial_migration_enforces_immutable_container_codes() -> None:
    migration = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0001_initial_schema.py"
    migration_text = migration.read_text()

    assert "prevent_container_code_update" in migration_text
    assert "container code is immutable once created" in migration_text
