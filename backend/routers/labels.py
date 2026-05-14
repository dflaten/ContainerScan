from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db_session
from models import Label
from schemas import TagCreate, TagRead, TagUpdate

router = APIRouter(tags=["tags"])


@router.get("/api/tags", response_model=list[TagRead])
def list_tags(session: Session = Depends(get_db_session)) -> list[Label]:
    """List all tags sorted by name.

    Args:
        session: Active database session injected by FastAPI.

    Returns:
        list[Label]: All persisted tags in ascending name order.
    """
    return session.execute(select(Label).order_by(Label.name.asc())).scalars().all()


@router.post("/api/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, session: Session = Depends(get_db_session)) -> Label:
    """Create a new tag.

    Args:
        payload: Validated tag creation request.
        session: Active database session injected by FastAPI.

    Returns:
        Label: The newly created tag record.
    """
    label = Label(name=payload.name)
    session.add(label)
    _commit_or_raise_conflict(session, conflict_message="Tag name already exists.")
    session.refresh(label)
    return label


@router.put("/api/tags/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    session: Session = Depends(get_db_session),
) -> Label:
    """Update an existing tag.

    Args:
        tag_id: Identifier of the tag to update.
        payload: Validated tag update request.
        session: Active database session injected by FastAPI.

    Returns:
        Label: The updated tag record.

    Raises:
        HTTPException: If the tag does not exist.
    """
    label = session.get(Label, tag_id)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")

    label.name = payload.name
    _commit_or_raise_conflict(session, conflict_message="Tag name already exists.")
    session.refresh(label)
    return label


@router.delete("/api/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Response:
    """Delete a tag when it is no longer referenced.

    Args:
        tag_id: Identifier of the tag to delete.
        session: Active database session injected by FastAPI.

    Returns:
        Response: Empty `204 No Content` response on success.

    Raises:
        HTTPException: If the tag does not exist.
    """
    label = session.get(Label, tag_id)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")

    session.delete(label)
    _commit_or_raise_conflict(
        session,
        conflict_message="Tag is still in use by one or more containers.",
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
