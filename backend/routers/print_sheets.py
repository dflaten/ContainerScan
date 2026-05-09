from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from database import get_db_session
from models import Container, PrintSheet, PrintSheetItem
from schemas import DraftPrintLabelRead, DraftPrintSheetRead, FullSheetCreate, PrintSheetRead
from utils.qr_labels import render_qr_code_png
from utils.code_generator import generate_unique_container_code, is_valid_container_code


router = APIRouter(prefix="/api/print-sheets", tags=["print-sheets"])

FULL_SHEET_LABEL_COUNT = 6


@router.get("/{print_sheet_id}", response_model=PrintSheetRead)
def get_print_sheet(print_sheet_id: uuid.UUID, session: Session = Depends(get_db_session)) -> PrintSheet:
    """Load one saved print sheet with its ordered containers."""
    return _get_print_sheet_or_404(session, print_sheet_id)


@router.post("/drafts/full-sheet", response_model=DraftPrintSheetRead)
def preview_full_sheet_draft(session: Session = Depends(get_db_session)) -> DraftPrintSheetRead:
    """Generate one non-persisted page of provisional labels for preview."""
    draft_codes: list[str] = []

    while len(draft_codes) < FULL_SHEET_LABEL_COUNT:
        candidate = generate_unique_container_code(session)
        if candidate in draft_codes:
            continue
        draft_codes.append(candidate)

    return DraftPrintSheetRead(
        containers=[
            DraftPrintLabelRead(id=uuid.uuid4(), code=code, name=f"Container {code}")
            for code in draft_codes
        ]
    )


@router.post("/generated/full-sheet", response_model=PrintSheetRead, status_code=status.HTTP_201_CREATED)
def create_full_sheet(payload: FullSheetCreate, session: Session = Depends(get_db_session)) -> PrintSheet:
    """Create one saved sheet and brand-new placeholder containers from a previewed full sheet draft."""
    if len(payload.drafts) != FULL_SHEET_LABEL_COUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exactly {FULL_SHEET_LABEL_COUNT} draft labels are required to create one full sheet.",
        )

    invalid_codes = [draft.code for draft in payload.drafts if not is_valid_container_code(draft.code)]
    if invalid_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more draft codes are invalid.")

    draft_codes = [draft.code for draft in payload.drafts]
    existing_codes = session.execute(select(Container.code).where(Container.code.in_(draft_codes))).scalars().all()
    if existing_codes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more previewed labels are no longer available. Generate a fresh preview and try again.",
        )

    print_sheet = PrintSheet()
    session.add(print_sheet)
    session.flush()

    try:
        for index, draft in enumerate(payload.drafts):
            container = Container(
                id=draft.id,
                code=draft.code,
                name=f"Container {draft.code}",
                description="",
                room_id=None,
                label_id=None,
            )
            session.add(container)
            session.flush()
            session.add(
                PrintSheetItem(
                    print_sheet_id=print_sheet.id,
                    container_id=container.id,
                    sort_order=index,
                )
            )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more previewed labels are no longer available. Generate a fresh preview and try again.",
        ) from exc

    return _get_print_sheet_or_404(session, print_sheet.id)


@router.get("/drafts/qr-code/{draft_id}")
def view_draft_qr_code(draft_id: uuid.UUID, code: str) -> Response:
    """Render one inline draft QR code for a non-persisted full-sheet preview."""
    normalized_code = code.strip().upper()
    if not is_valid_container_code(normalized_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft code is invalid.")

    png_bytes = render_qr_code_png(container_id=draft_id)
    return Response(content=png_bytes, media_type="image/png")


def _get_print_sheet_or_404(session: Session, print_sheet_id: uuid.UUID) -> PrintSheet:
    """Load a saved print sheet or raise a 404 error."""
    statement = (
        select(PrintSheet)
        .options(selectinload(PrintSheet.items).selectinload(PrintSheetItem.container))
        .where(PrintSheet.id == print_sheet_id)
    )
    print_sheet = session.execute(statement).scalar_one_or_none()
    if print_sheet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print sheet not found.")
    return print_sheet
