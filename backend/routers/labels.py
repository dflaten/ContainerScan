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
    """List all labels sorted by name.

    Args:
        session: Active database session injected by FastAPI.

    Returns:
        list[Label]: All persisted labels in ascending name order.
    """
    return session.execute(select(Label).order_by(Label.name.asc())).scalars().all()


@router.post("", response_model=LabelRead, status_code=status.HTTP_201_CREATED)
def create_label(payload: LabelCreate, session: Session = Depends(get_db_session)) -> Label:
    """Create a new label.

    Args:
        payload: Validated label creation request.
        session: Active database session injected by FastAPI.

    Returns:
        Label: The newly created label record.
    """
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
    """Update an existing label.

    Args:
        label_id: Identifier of the label to update.
        payload: Validated label update request.
        session: Active database session injected by FastAPI.

    Returns:
        Label: The updated label record.

    Raises:
        HTTPException: If the label does not exist.
    """
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
    """Delete a label when it is no longer referenced.

    Args:
        label_id: Identifier of the label to delete.
        session: Active database session injected by FastAPI.

    Returns:
        Response: Empty `204 No Content` response on success.

    Raises:
        HTTPException: If the label does not exist.
    """
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
    """Commit the current transaction or convert integrity errors to HTTP conflicts.

    Args:
        session: Active database session to commit.
        conflict_message: Error detail to return on integrity conflicts.

    Raises:
        HTTPException: If the commit fails because of an integrity error.
    """
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_message) from exc
