from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models import Container


def test_container_room_and_label_relationships_are_optional() -> None:
    """Verify that containers can be created before room or label assignment."""
    room_id = Container.__table__.c.room_id
    label_id = Container.__table__.c.label_id

    assert room_id.nullable is True
    assert label_id.nullable is True

    room_fk = next(iter(room_id.foreign_keys))
    label_fk = next(iter(label_id.foreign_keys))

    assert room_fk.ondelete == "RESTRICT"
    assert label_fk.ondelete == "RESTRICT"


def test_initial_migration_enforces_immutable_container_codes() -> None:
    """Verify the initial migration includes the immutable container code trigger."""
    migration = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0001_initial_schema.py"
    migration_text = migration.read_text()

    assert "prevent_container_code_update" in migration_text
    assert "container code is immutable once created" in migration_text


def test_label_first_migration_relaxes_container_assignment_requirements() -> None:
    """Verify the label-first migration makes room and label assignment optional."""
    migration = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0003_label_first_container_flow.py"
    )
    migration_text = migration.read_text()

    assert "ALTER COLUMN room_id DROP NOT NULL" in migration_text
    assert "ALTER COLUMN label_id DROP NOT NULL" in migration_text
