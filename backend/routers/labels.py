from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db_session
from models import Label
from schemas import LabelCreate, LabelRead, LabelUpdate

router = APIRouter(prefix="/api/labels", tags=["labels"])


@router.get("", response_model=list[LabelRead])
def list_labels(session: Session = Depends(get_db_session)) -> list[Label]:
    return session.execute(select(Label).order_by(Label.name.asc())).scalars().all()


@router.post("", response_model=LabelRead, status_code=status.HTTP_201_CREATED)
def create_label(payload: LabelCreate, session: Session = Depends(get_db_session)) -> Label:
    label = Label(name=payload.name, colour=payload.colour)
    session.add(label)
    _commit_or_raise_conflict(session, conflict_message="Label name already exists.")
    session.refresh(label)
    return label


@router.put("/{label_id}", response_model=LabelRead)
def update_label(
    label_id: uuid.UUID,
    payload: LabelUpdate,
    session: Session = Depends(get_db_session),
) -> Label:
    label = session.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found.")

    label.name = payload.name
    label.colour = payload.colour
    _commit_or_raise_conflict(session, conflict_message="Label name already exists.")
    session.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(label_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Response:
    label = session.get(Label, label_id)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found.")

    session.delete(label)
    _commit_or_raise_conflict(
        session,
        conflict_message="Label is still in use by one or more containers.",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _commit_or_raise_conflict(session: Session, conflict_message: str) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_message) from exc
