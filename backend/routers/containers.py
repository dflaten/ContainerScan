from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from database import get_db_session
from models import Container, Label, Room
from schemas import ContainerCreate, ContainerRead, ContainerUpdate
from utils.code_generator import generate_unique_container_code

router = APIRouter(prefix="/api/containers", tags=["containers"])


@router.get("", response_model=list[ContainerRead])
def list_containers(session: Session = Depends(get_db_session)) -> list[Container]:
    """List all containers with image metadata preloaded.

    Args:
        session: Active database session injected by FastAPI.

    Returns:
        list[Container]: Containers ordered from newest to oldest.
    """
    statement = (
        select(Container)
        .options(selectinload(Container.images))
        .order_by(Container.created_at.desc(), Container.code.asc())
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
    _ensure_room_and_label_exist(session, room_id=payload.room_id, label_id=payload.label_id)

    container = Container(
        code=generate_unique_container_code(session),
        name=payload.name,
        description=payload.description,
        room_id=payload.room_id,
        label_id=payload.label_id,
    )
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
    statement = select(Container).options(selectinload(Container.images)).where(Container.code == code.upper())
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
    _ensure_room_and_label_exist(session, room_id=payload.room_id, label_id=payload.label_id)

    container.name = payload.name
    container.description = payload.description
    container.room_id = payload.room_id
    container.label_id = payload.label_id

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
    session.delete(container)
    _commit_or_raise_conflict(session)
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
    statement = select(Container).options(selectinload(Container.images)).where(Container.id == container_id)
    container = session.execute(statement).scalar_one_or_none()
    if container is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found.")
    return container


def _ensure_room_and_label_exist(session: Session, *, room_id: uuid.UUID, label_id: uuid.UUID) -> None:
    """Validate that referenced room and label records exist.

    Args:
        session: Active database session to query.
        room_id: Identifier of the required room.
        label_id: Identifier of the required label.

    Raises:
        HTTPException: If either referenced record does not exist.
    """
    if session.get(Room, room_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
    if session.get(Label, label_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found.")


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
