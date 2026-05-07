from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db_session
from models import Container, Image
from schemas import ImageRead, ImageUpdate
from utils.image_storage import delete_stored_image, save_upload_to_storage


router = APIRouter(tags=["images"])


@router.post("/api/containers/{container_id}/images", response_model=list[ImageRead], status_code=status.HTTP_201_CREATED)
async def upload_container_images_endpoint(
    container_id: uuid.UUID,
    request: Request,
    session: Session = Depends(get_db_session),
) -> list[Image]:
    """Parse a multipart upload request and store container images."""
    form = await request.form()
    images = form.getlist("images")
    captions = form.getlist("captions")
    return await upload_container_images(container_id, session=session, images=images, captions=captions)


async def upload_container_images(
    container_id: uuid.UUID,
    session: Session,
    images: list[UploadFile],
    captions: list[str] | None,
) -> list[Image]:
    """Upload one or more images for a container.

    The first image ever added to a container becomes its primary exterior photo.
    Additional images are treated as secondary contents photos unless explicitly
    promoted later through image metadata updates.
    """
    container = session.get(Container, container_id)
    if container is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found.")
    if any(not isinstance(image, UploadFile) for image in images):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image upload payload.")
    if not images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one image is required.")

    normalized_captions = _normalize_captions(captions, len(images))
    next_sort_order = max((image.sort_order for image in container.images), default=-1) + 1
    settings = get_settings()
    created_images: list[Image] = []
    stored_filenames: list[str] = []

    try:
        for index, upload in enumerate(images):
            filename = await save_upload_to_storage(upload, settings.image_storage_path)
            stored_filenames.append(filename)

            image = Image(
                id=uuid.uuid4(),
                container_id=container.id,
                filename=filename,
                is_primary=not container.images and index == 0,
                caption=normalized_captions[index],
                sort_order=next_sort_order + index,
            )
            session.add(image)
            created_images.append(image)

        session.commit()
    except HTTPException:
        session.rollback()
        for filename in stored_filenames:
            delete_stored_image(filename, settings.image_storage_path)
        raise
    except IntegrityError as exc:
        session.rollback()
        for filename in stored_filenames:
            delete_stored_image(filename, settings.image_storage_path)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to save uploaded images.",
        ) from exc

    for image in created_images:
        session.refresh(image)
    return created_images


@router.put("/api/images/{image_id}", response_model=ImageRead)
def update_image(
    image_id: uuid.UUID,
    payload: ImageUpdate,
    session: Session = Depends(get_db_session),
) -> Image:
    """Update mutable image metadata fields."""
    image = _get_image_or_404(session, image_id)
    if payload.is_primary:
        _clear_primary_flag(image.container.images, keep_id=image.id)
    elif payload.is_primary is False and image.is_primary and len(image.container.images) > 1:
        replacement = _find_next_primary_candidate(image.container.images, excluding_id=image.id)
        if replacement is not None:
            replacement.is_primary = True
    image.is_primary = image.is_primary if payload.is_primary is None else payload.is_primary
    image.caption = payload.caption
    image.sort_order = payload.sort_order

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update image metadata.",
        ) from exc

    session.refresh(image)
    return image


@router.delete("/api/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(image_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Response:
    """Delete one stored image and its metadata record."""
    image = _get_image_or_404(session, image_id)
    filename = image.filename
    settings = get_settings()
    replacement = None
    if image.is_primary:
        replacement = _find_next_primary_candidate(image.container.images, excluding_id=image.id)

    try:
        session.delete(image)
        if replacement is not None:
            replacement.is_primary = True
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to delete image.",
        ) from exc

    delete_stored_image(filename, settings.image_storage_path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_image_or_404(session: Session, image_id: uuid.UUID) -> Image:
    """Load an image by identifier or raise a 404 error."""
    image = session.get(Image, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")
    return image


def _normalize_captions(captions: list[str] | None, expected_count: int) -> list[str | None]:
    """Normalize optional upload captions to match the image count."""
    if captions is None:
        return [None] * expected_count
    if len(captions) != expected_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caption count must match the number of uploaded images.",
        )
    return [caption.strip() or None for caption in captions]


def _clear_primary_flag(images: list[Image], *, keep_id: uuid.UUID) -> None:
    """Clear the primary-image flag from sibling images."""
    for image in images:
        image.is_primary = image.id == keep_id


def _find_next_primary_candidate(images: list[Image], *, excluding_id: uuid.UUID) -> Image | None:
    """Pick the next best primary image from remaining container images."""
    remaining = [image for image in images if image.id != excluding_id]
    if not remaining:
        return None
    return min(remaining, key=lambda image: (image.sort_order, image.uploaded_at, str(image.id)))
