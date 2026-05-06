from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db_session
from models import Room
from schemas import RoomCreate, RoomRead, RoomUpdate

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
def list_rooms(session: Session = Depends(get_db_session)) -> list[Room]:
    return session.execute(select(Room).order_by(Room.name.asc())).scalars().all()


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, session: Session = Depends(get_db_session)) -> Room:
    room = Room(name=payload.name)
    session.add(room)
    _commit_or_raise_conflict(session, duplicate_message="Room name already exists.")
    session.refresh(room)
    return room


@router.put("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: uuid.UUID,
    payload: RoomUpdate,
    session: Session = Depends(get_db_session),
) -> Room:
    room = session.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")

    room.name = payload.name
    _commit_or_raise_conflict(session, duplicate_message="Room name already exists.")
    session.refresh(room)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Response:
    room = session.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")

    session.delete(room)
    _commit_or_raise_conflict(
        session,
        duplicate_message="Room is still in use by one or more containers.",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _commit_or_raise_conflict(session: Session, duplicate_message: str) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=duplicate_message) from exc
