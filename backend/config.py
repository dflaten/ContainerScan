from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime configuration values for the backend service."""

    database_url: str
    image_storage_path: str
    public_base_url: str


def get_settings() -> Settings:
    """Load backend settings from environment variables.

    Returns:
        Settings: The resolved backend configuration with defaults applied.
    """
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://cs_user:cs_pass@db:5432/containerscan",
        ),
        image_storage_path=os.getenv("IMAGE_STORAGE_PATH", "/app/images"),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://containerscan.local"),
    )
