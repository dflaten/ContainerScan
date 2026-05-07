from __future__ import annotations

from html import escape
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database import get_db_session
from models import Container
from schemas import ScanContainerRead


router = APIRouter(tags=["scan"])


@router.get("/api/scan/{container_id}", response_model=ScanContainerRead)
def get_scan_container(container_id: uuid.UUID, session: Session = Depends(get_db_session)) -> Container:
    """Return the read-only container data used by public scan views."""
    return _get_scan_container_or_404(session, container_id)


@router.get("/scan/{container_id}", response_class=HTMLResponse)
def render_scan_view(container_id: uuid.UUID, session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Render a minimal mobile-friendly read-only scan page."""
    container = _get_scan_container_or_404(session, container_id)
    room_name = container.room.name if container.room is not None else "Unassigned Room"
    label_name = container.label.name if container.label is not None else "Unlabeled"
    label_colour = container.label.colour if container.label is not None else "#4B5563"
    description = escape(container.description) if container.description else "No description recorded."

    image_markup = "".join(
        (
            '<figure class="photo">'
            f'<img src="{escape(image.url)}" alt="{escape(image.caption or container.name)}" loading="lazy">'
            f"<figcaption>{escape(image.caption or ('Primary photo' if image.is_primary else 'Container image'))}</figcaption>"
            "</figure>"
        )
        for image in container.images
    )
    if not image_markup:
        image_markup = '<p class="empty">No images have been uploaded for this container yet.</p>'

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(container.code)} | ContainerScan</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        background: #f4f1ea;
        color: #172033;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background:
          radial-gradient(circle at top left, rgba(255,255,255,0.82), transparent 38%),
          linear-gradient(180deg, {label_colour} 0, {label_colour} 220px, #f4f1ea 220px);
      }}
      main {{
        width: min(100%, 760px);
        margin: 0 auto;
        padding: 24px 16px 48px;
      }}
      .card {{
        background: rgba(255,255,255,0.92);
        border-radius: 24px;
        padding: 20px;
        box-shadow: 0 18px 40px rgba(23,32,51,0.16);
        backdrop-filter: blur(12px);
      }}
      .code {{
        display: inline-block;
        margin: 0 0 12px;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(23,32,51,0.08);
        font-size: 0.88rem;
        font-weight: 700;
        letter-spacing: 0.12em;
      }}
      h1 {{
        margin: 0;
        font-size: clamp(2rem, 7vw, 3.25rem);
        line-height: 0.95;
      }}
      .meta {{
        margin: 18px 0 0;
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      }}
      .meta div {{
        padding: 14px;
        border-radius: 16px;
        background: rgba(23,32,51,0.05);
      }}
      .meta dt {{
        margin: 0 0 4px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #52607a;
      }}
      .meta dd {{
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
      }}
      .description {{
        margin: 20px 0 0;
        font-size: 1rem;
        line-height: 1.6;
      }}
      .readonly {{
        margin: 20px 0 0;
        font-size: 0.92rem;
        color: #52607a;
      }}
      .gallery {{
        margin: 20px 0 0;
        display: grid;
        gap: 16px;
      }}
      .photo {{
        margin: 0;
        overflow: hidden;
        border-radius: 20px;
        background: #ffffff;
        box-shadow: inset 0 0 0 1px rgba(23,32,51,0.06);
      }}
      .photo img {{
        display: block;
        width: 100%;
        height: auto;
        aspect-ratio: 4 / 3;
        object-fit: cover;
        background: #e8edf5;
      }}
      .photo figcaption {{
        padding: 12px 14px 14px;
        font-size: 0.92rem;
      }}
      .empty {{
        margin: 20px 0 0;
        padding: 18px;
        border-radius: 18px;
        background: rgba(23,32,51,0.05);
        color: #52607a;
      }}
    </style>
  </head>
  <body>
    <main>
      <article class="card">
        <p class="code">{escape(container.code)}</p>
        <h1>{escape(container.name)}</h1>
        <dl class="meta">
          <div>
            <dt>Room</dt>
            <dd>{escape(room_name)}</dd>
          </div>
          <div>
            <dt>Label</dt>
            <dd>{escape(label_name)}</dd>
          </div>
        </dl>
        <p class="description">{description}</p>
        <p class="readonly">Read-only scan view. Admin edits stay in the main management interface.</p>
        <section class="gallery">{image_markup}</section>
      </article>
    </main>
  </body>
</html>
"""
    return HTMLResponse(content=html, status_code=status.HTTP_200_OK)


def _get_scan_container_or_404(session: Session, container_id: uuid.UUID) -> Container:
    """Load one container with related data for public scan views."""
    statement = (
        select(Container)
        .options(
            selectinload(Container.images),
            selectinload(Container.room),
            selectinload(Container.label),
        )
        .where(Container.id == container_id)
    )
    container = session.execute(statement).scalar_one_or_none()
    if container is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Container not found.")
    return container
