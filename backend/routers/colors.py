from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db_session
from models import Color
from schemas import ColorCreate, ColorRead, ColorUpdate

router = APIRouter(prefix="/api/colors", tags=["colors"])


@router.get("", response_model=list[ColorRead])
def list_colors(session: Session = Depends(get_db_session)) -> list[Color]:
    """List all color options sorted by name."""
    return session.execute(select(Color).order_by(Color.name.asc())).scalars().all()


@router.post("", response_model=ColorRead, status_code=status.HTTP_201_CREATED)
def create_color(payload: ColorCreate, session: Session = Depends(get_db_session)) -> Color:
    """Create a new color option."""
    color = Color(name=payload.name, value=payload.value)
    session.add(color)
    _commit_or_raise_conflict(session, duplicate_message="Color name or value already exists.")
    session.refresh(color)
    return color


@router.put("/{color_id}", response_model=ColorRead)
def update_color(
    color_id: uuid.UUID,
    payload: ColorUpdate,
    session: Session = Depends(get_db_session),
) -> Color:
    """Update an existing color option."""
    color = session.get(Color, color_id)
    if color is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found.")

    color.name = payload.name
    color.value = payload.value
    _commit_or_raise_conflict(session, duplicate_message="Color name or value already exists.")
    session.refresh(color)
    return color


@router.delete("/{color_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_color(color_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Response:
    """Delete a color option."""
    color = session.get(Color, color_id)
    if color is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found.")

    session.delete(color)
    _commit_or_raise_conflict(session, duplicate_message="Unable to delete the color option.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _commit_or_raise_conflict(session: Session, duplicate_message: str) -> None:
    """Commit the current transaction or convert integrity errors to HTTP conflicts."""
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=duplicate_message) from exc
