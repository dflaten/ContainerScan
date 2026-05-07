from __future__ import annotations

from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.code_generator import create_candidate_code, generate_unique_container_code, is_valid_container_code


class StubSession:
    """Minimal session stub for exercising code generation lookups."""

    def __init__(self, existing_codes: set[str]) -> None:
        """Store the set of pre-existing codes used by the tests.

        Args:
            existing_codes: Codes that should be treated as already persisted.
        """
        self.existing_codes = existing_codes

    def scalar(self, statement: object) -> str | None:
        """Simulate the scalar lookup used by the generator.

        Args:
            statement: SQLAlchemy statement containing the candidate code.

        Returns:
            str | None: The colliding code when present, otherwise `None`.
        """
        compiled = statement.compile()
        candidate = compiled.params["code_1"]
        return candidate if candidate in self.existing_codes else None


def test_create_candidate_code_uses_expected_format() -> None:
    """Verify that generated candidate codes always match the required format."""
    candidate = create_candidate_code(random.Random(7))

    assert is_valid_container_code(candidate)


def test_generate_unique_container_code_retries_until_non_collision() -> None:
    """Verify that code generation skips colliding candidates until one is unique."""
    session = StubSession({"AB-12", "ZX-90"})
    candidates = iter(["AB-12", "ZX-90", "LM-34"])

    def candidate_factory(_: random.Random | None) -> str:
        return next(candidates)

    code = generate_unique_container_code(session, candidate_factory=candidate_factory)

    assert code == "LM-34"


def test_generate_unique_container_code_rejects_invalid_factory_output() -> None:
    """Verify that invalid candidate factory output is rejected immediately."""
    session = StubSession(set())

    def candidate_factory(_: random.Random | None) -> str:
        return "bad"

    try:
        generate_unique_container_code(session, candidate_factory=candidate_factory)
    except ValueError as exc:
        assert "invalid container code" in str(exc).lower()
    else:
        raise AssertionError("Expected invalid generated codes to raise ValueError")


def test_generate_unique_container_code_raises_after_collision_limit() -> None:
    """Verify that repeated collisions eventually raise a runtime error."""
    session = StubSession({"AB-12"})

    def candidate_factory(_: random.Random | None) -> str:
        return "AB-12"

    try:
        generate_unique_container_code(session, candidate_factory=candidate_factory, max_attempts=3)
    except RuntimeError as exc:
        assert "unique container code" in str(exc).lower()
    else:
        raise AssertionError("Expected repeated collisions to raise RuntimeError")


def test_is_valid_container_code_accepts_only_dashed_uppercase_alphanumeric_values() -> None:
    """Verify the validator accepts only canonical dashed uppercase codes."""
    valid_codes = {"AB-12", "Z9-X0", "00-00"}
    invalid_codes = {"ab-12", "ABC-1", "A1B2", "A_-2", ""}

    assert all(is_valid_container_code(code) for code in valid_codes)
    assert all(not is_valid_container_code(code) for code in invalid_codes)
