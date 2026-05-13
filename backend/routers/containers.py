from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from config import get_settings
from database import get_db_session
from models import Container, Label, Room
from schemas import ContainerCreate, ContainerRead, ContainerUpdate
from utils.code_generator import generate_unique_container_code
from utils.image_storage import delete_stored_image
from utils.qr_labels import render_qr_code_png, render_qr_label_png

router = APIRouter(prefix="/api/containers", tags=["containers"])


@router.get("", response_model=list[ContainerRead])
def list_containers(
    session: Session = Depends(get_db_session),
    search: str | None = None,
    room_id: uuid.UUID | None = None,
    tag_id: uuid.UUID | None = None,
    label_id: uuid.UUID | None = None,
    code: str | None = None,
) -> list[Container]:
    """List all containers with image metadata preloaded.

    Args:
        search: Optional full-text search string for code, name, and description.
        room_id: Optional room filter.
        tag_id: Optional tag filter.
        label_id: Deprecated single-label filter alias.
        code: Optional exact container code filter.
        session: Active database session injected by FastAPI.

    Returns:
        list[Container]: Containers ordered from newest to oldest after filters are applied.
    """
    normalized_search = _normalize_optional_text(search)
    normalized_code = _normalize_optional_code(code)
    statement = _build_container_list_statement(
        search=normalized_search,
        room_id=room_id,
        tag_id=tag_id or label_id,
        code=normalized_code,
    )
    return session.execute(statement).scalars().all()


@router.post("", response_model=ContainerRead, status_code=status.HTTP_201_CREATED)
def create_container(payload: ContainerCreate, session: Session = Depends(get_db_session)) -> Container:
    """Create a new container with a generated immutable code.

    Args:
        payload: Validated container creation request.
        session: Active database session injected by FastAPI.

    Returns:
        Container: The newly created container record.
    """
    _ensure_room_and_tags_exist(session, room_id=payload.room_id, tag_ids=payload.tag_ids)
    code = generate_unique_container_code(session)
    primary_tag_id = payload.tag_ids[0] if payload.tag_ids else None

    container = Container(
        code=code,
        name=payload.name or f"Container {code}",
        description=payload.description,
        colour=payload.colour,
        room_id=payload.room_id,
        label_id=primary_tag_id,
    )
    if payload.tag_ids:
        container.tags = [session.get(Label, tag_id) for tag_id in payload.tag_ids]
    session.add(container)
    _commit_or_raise_conflict(session)
    session.refresh(container)
    return container


@router.get("/{container_id}", response_model=ContainerRead)
def get_container(container_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Container:
    """Fetch a single container by UUID.

    Args:
        container_id: Identifier of the container to load.
        session: Active database session injected by FastAPI.

    Returns:
        Container: The matching container record.
    """
    container = _get_container_or_404(session, container_id)
    return container


def _render_container_qr_label_response(
    container_id: uuid.UUID,
    session: Session,
    *,
    as_attachment: bool,
) -> Response:
    """Generate one QR label PNG response in either inline or download mode."""
    container = _get_container_or_404(session, container_id)
    room_name = container.room.name if container.room is not None else "Unassigned Room"
    label_colour = container.colour
    png_bytes = render_qr_label_png(
        container_id=container.id,
        container_code=container.code,
        container_name=container.name,
        room_name=room_name,
        label_colour=label_colour,
    )
    headers = (
        {"Content-Disposition": f'attachment; filename="{container.code}-label.png"'}
        if as_attachment
        else {}
    )
    return Response(content=png_bytes, media_type="image/png", headers=headers)


@router.get("/{container_id}/qr")
def download_container_qr_label(
    container_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> Response:
    """Generate and return a printable QR label PNG as a download."""
    return _render_container_qr_label_response(container_id, session, as_attachment=True)


@router.get("/{container_id}/qr/inline")
def view_container_qr_label(
    container_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> Response:
    """Generate and return a printable QR label PNG for inline image use."""
    return _render_container_qr_label_response(container_id, session, as_attachment=False)


@router.get("/{container_id}/qr-code/inline")
def view_container_qr_code(
    container_id: uuid.UUID,
    session: Session = Depends(get_db_session),
) -> Response:
    """Generate and return only the QR code PNG for sheet preview tiles."""
    container = _get_container_or_404(session, container_id)
    png_bytes = render_qr_code_png(container_id=container.id)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/code/{code}", response_model=ContainerRead)
def get_container_by_code(code: str, session: Session = Depends(get_db_session)) -> Container:
    """Fetch a single container by its human-facing code.

    Args:
        code: Four-character dashed container code such as `AB-12`.
        session: Active database session injected by FastAPI.

    Returns:
        Container: The matching container record.

    Raises:
        HTTPException: If no container exists for the supplied code.
    """
    statement = (
        select(Container)
        .options(selectinload(Container.images), selectinload(Container.tags))
        .where(Container.code == code.upper())
    )
    container = session.execute(statement).scalar_one_or_none()
    if container is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found.")
    return container


@router.put("/{container_id}", response_model=ContainerRead)
def update_container(
    container_id: uuid.UUID,
    payload: ContainerUpdate,
    session: Session = Depends(get_db_session),
) -> Container:
    """Update mutable container fields.

    Args:
        container_id: Identifier of the container to update.
        payload: Validated container update request.
        session: Active database session injected by FastAPI.

    Returns:
        Container: The updated container record.
    """
    container = _get_container_or_404(session, container_id)
    _ensure_room_and_tags_exist(session, room_id=payload.room_id, tag_ids=payload.tag_ids)

    container.name = payload.name
    container.description = payload.description
    container.colour = payload.colour
    container.room_id = payload.room_id
    container.label_id = payload.tag_ids[0] if payload.tag_ids else None
    container.tags = [session.get(Label, tag_id) for tag_id in payload.tag_ids]

    _commit_or_raise_conflict(session)
    session.refresh(container)
    return container


@router.delete("/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_container(container_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Response:
    """Delete a container and its related image records.

    Args:
        container_id: Identifier of the container to delete.
        session: Active database session injected by FastAPI.

    Returns:
        Response: Empty `204 No Content` response on success.
    """
    container = _get_container_or_404(session, container_id)
    image_filenames = [image.filename for image in container.images]
    session.delete(container)
    _commit_or_raise_conflict(session)
    settings = get_settings()
    for filename in image_filenames:
        delete_stored_image(filename, settings.image_storage_path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_container_or_404(session: Session, container_id: uuid.UUID) -> Container:
    """Load a container or raise a 404 error.

    Args:
        session: Active database session to query.
        container_id: Identifier of the container to load.

    Returns:
        Container: The matching container record.

    Raises:
        HTTPException: If the container does not exist.
    """
    statement = (
        select(Container)
        .options(
            selectinload(Container.images),
            selectinload(Container.room),
            selectinload(Container.label),
            selectinload(Container.tags),
        )
        .where(Container.id == container_id)
    )
    container = session.execute(statement).scalar_one_or_none()
    if container is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found.")
    return container


def _build_container_list_statement(
    *,
    search: str | None,
    room_id: uuid.UUID | None,
    tag_id: uuid.UUID | None,
    code: str | None,
):
    """Build the container listing query with optional search and filters.

    Args:
        search: Optional full-text search string for code, name, and description.
        room_id: Optional room filter.
        tag_id: Optional tag filter.
        code: Optional exact container code filter.

    Returns:
        Select: SQLAlchemy select statement configured for the requested filters.
    """
    statement = (
        select(Container)
        .options(selectinload(Container.images), selectinload(Container.tags))
        .order_by(Container.created_at.desc(), Container.code.asc())
    )

    if search is not None:
        english_query = func.plainto_tsquery("english", search)
        simple_query = func.plainto_tsquery("simple", search)
        statement = statement.where(
            or_(
                Container.search_vector.op("@@")(english_query),
                Container.search_vector.op("@@")(simple_query),
            )
        )

    if room_id is not None:
        statement = statement.where(Container.room_id == room_id)

    if tag_id is not None:
        statement = statement.where(Container.tags.any(Label.id == tag_id))

    if code is not None:
        statement = statement.where(Container.code == code)

    return statement.execution_options(
        containerscan_filters={
            "search": search,
            "room_id": room_id,
            "tag_id": tag_id,
            "label_id": tag_id,
            "code": code,
        }
    )


def _ensure_room_and_tags_exist(
    session: Session,
    *,
    room_id: uuid.UUID | None,
    tag_ids: list[uuid.UUID],
) -> None:
    """Validate that referenced room and tag records exist.

    Args:
        session: Active database session to query.
        room_id: Identifier of the required room.
        tag_ids: Identifiers of the required tags.

    Raises:
        HTTPException: If either referenced record does not exist.
    """
    if room_id is not None and session.get(Room, room_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
    for tag_id in tag_ids:
        if session.get(Label, tag_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")


def _normalize_optional_text(value: str | None) -> str | None:
    """Normalize an optional free-text query parameter.

    Args:
        value: Raw query parameter value.

    Returns:
        str | None: Trimmed text or `None` when the value is blank.
    """
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _normalize_optional_code(value: str | None) -> str | None:
    """Normalize an optional container code query parameter.

    Args:
        value: Raw query parameter value.

    Returns:
        str | None: Uppercased code or `None` when the value is blank.
    """
    normalized = _normalize_optional_text(value)
    if normalized is None:
        return None
    return normalized.upper()


def _commit_or_raise_conflict(session: Session) -> None:
    """Commit the current transaction or convert integrity errors to HTTP conflicts.

    Args:
        session: Active database session to commit.

    Raises:
        HTTPException: If the commit fails because of an integrity error.
    """
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Container update could not be completed.",
        ) from exc
