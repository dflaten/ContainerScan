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
    return CODE_PATTERN.fullmatch(code) is not None


def create_candidate_code(rng: random.Random | None = None) -> str:
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
    for _ in range(max_attempts):
        candidate = candidate_factory(rng)
        if not is_valid_container_code(candidate):
            raise ValueError(f"Generated invalid container code: {candidate!r}")

        existing_code = session.scalar(select(Container.code).where(Container.code == candidate))
        if existing_code is None:
            return candidate

    raise RuntimeError("Unable to generate a unique container code after repeated collisions")
