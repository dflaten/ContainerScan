from __future__ import annotations

from pathlib import Path
import uuid

from fastapi import HTTPException, UploadFile, status


_CONTENT_TYPE_TO_EXTENSION = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_ALLOWED_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def ensure_storage_directory(storage_path: str) -> Path:
    """Create the configured image storage directory if needed."""
    directory = Path(storage_path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_safe_image_filename(upload: UploadFile) -> str:
    """Generate a storage filename with a safe server-controlled basename."""
    extension = _resolve_image_extension(upload)
    return f"{uuid.uuid4().hex}{extension}"


async def save_upload_to_storage(upload: UploadFile, storage_path: str) -> str:
    """Validate and persist one uploaded image to disk."""
    directory = ensure_storage_directory(storage_path)
    filename = build_safe_image_filename(upload)
    target_path = directory / filename

    try:
        content = await upload.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image is empty.")
        target_path.write_bytes(content)
    finally:
        await upload.close()

    return filename


def delete_stored_image(filename: str, storage_path: str) -> None:
    """Remove one stored image file if it still exists."""
    target_path = Path(storage_path) / filename
    try:
        target_path.unlink()
    except FileNotFoundError:
        return None


def _resolve_image_extension(upload: UploadFile) -> str:
    """Resolve a normalized file extension from upload metadata."""
    content_type = (upload.content_type or "").lower()
    if content_type in _CONTENT_TYPE_TO_EXTENSION:
        return _CONTENT_TYPE_TO_EXTENSION[content_type]

    original_name = (upload.filename or "").lower()
    suffix = Path(original_name).suffix
    if suffix in _ALLOWED_EXTENSIONS:
        return ".jpg" if suffix == ".jpeg" else suffix

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported image type. Allowed types: GIF, JPEG, PNG, WEBP.",
    )
