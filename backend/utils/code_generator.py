from __future__ import annotations

import random
import re
import string
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Container


CODE_PATTERN = re.compile(r"^[A-Z0-9]{2}-[A-Z0-9]{2}$")
CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_ATTEMPT_LIMIT = 1024


def is_valid_container_code(code: str) -> bool:
    """Check whether a string matches the canonical container code format.

    Args:
        code: Candidate container code to validate.

    Returns:
        bool: `True` when the code matches the expected dashed uppercase format.
    """
    return CODE_PATTERN.fullmatch(code) is not None


def create_candidate_code(rng: random.Random | None = None) -> str:
    """Generate one random candidate container code.

    Args:
        rng: Optional random generator for deterministic testing.

    Returns:
        str: A candidate code in `AA-11` format.
    """
    generator = rng or random
    return "".join(generator.choice(CODE_ALPHABET) for _ in range(2)) + "-" + "".join(
        generator.choice(CODE_ALPHABET) for _ in range(2)
    )


def generate_unique_container_code(
    session: Session,
    *,
    rng: random.Random | None = None,
    candidate_factory: Callable[[random.Random | None], str] = create_candidate_code,
    max_attempts: int = CODE_ATTEMPT_LIMIT,
) -> str:
    """Generate a unique container code not already present in the database.

    Args:
        session: Database session used to check existing codes.
        rng: Optional random generator for deterministic testing.
        candidate_factory: Function used to produce candidate codes.
        max_attempts: Maximum number of candidates to try before failing.

    Returns:
        str: A unique container code in canonical dashed format.

    Raises:
        ValueError: If the candidate factory returns an invalid code.
        RuntimeError: If a unique code cannot be found within `max_attempts`.
    """
    for _ in range(max_attempts):
        candidate = candidate_factory(rng)
        if not is_valid_container_code(candidate):
            raise ValueError(f"Generated invalid container code: {candidate!r}")

        existing_code = session.scalar(select(Container.code).where(Container.code == candidate))
        if existing_code is None:
            return candidate

    raise RuntimeError("Unable to generate a unique container code after repeated collisions")
