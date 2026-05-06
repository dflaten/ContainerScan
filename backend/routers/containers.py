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
    statement = (
        select(Container)
        .options(selectinload(Container.images))
        .order_by(Container.created_at.desc(), Container.code.asc())
    )
    return session.execute(statement).scalars().all()


@router.post("", response_model=ContainerRead, status_code=status.HTTP_201_CREATED)
def create_container(payload: ContainerCreate, session: Session = Depends(get_db_session)) -> Container:
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
    container = _get_container_or_404(session, container_id)
    return container


@router.get("/code/{code}", response_model=ContainerRead)
def get_container_by_code(code: str, session: Session = Depends(get_db_session)) -> Container:
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
    container = _get_container_or_404(session, container_id)
    session.delete(container)
    _commit_or_raise_conflict(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_container_or_404(session: Session, container_id: uuid.UUID) -> Container:
    statement = select(Container).options(selectinload(Container.images)).where(Container.id == container_id)
    container = session.execute(statement).scalar_one_or_none()
    if container is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found.")
    return container


def _ensure_room_and_label_exist(session: Session, *, room_id: uuid.UUID, label_id: uuid.UUID) -> None:
    if session.get(Room, room_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
    if session.get(Label, label_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found.")


def _commit_or_raise_conflict(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Container update could not be completed.",
        ) from exc
