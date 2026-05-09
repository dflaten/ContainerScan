from __future__ import annotations

from io import BytesIO
import uuid

from config import get_settings


def build_scan_url(container_id: uuid.UUID) -> str:
    """Build the stable LAN URL encoded into a container QR code."""
    base_url = get_settings().public_base_url.rstrip("/")
    return f"{base_url}/scan/{container_id}"


def render_qr_label_png(
    *,
    container_id: uuid.UUID,
    container_code: str,
    container_name: str,
    room_name: str,
    label_colour: str,
) -> bytes:
    """Render one print-ready QR label tile as PNG bytes."""
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    scan_url = build_scan_url(container_id)
    qr_image = qrcode.make(scan_url).convert("RGB")
    qr_image = qr_image.resize((420, 420), Image.Resampling.NEAREST)

    canvas = Image.new("RGB", (900, 560), _normalize_hex_colour(label_colour))
    draw = ImageDraw.Draw(canvas)

    qr_left = 48
    qr_top = 72
    qr_box = (qr_left - 24, qr_top - 24, qr_left + 420 + 24, qr_top + 420 + 24)
    draw.rounded_rectangle(qr_box, radius=24, fill="#FFFFFF")
    canvas.paste(qr_image, (qr_left, qr_top))

    header_font = _load_font(size=86, bold=True)
    title_font = _load_font(size=44, bold=True)
    body_font = _load_font(size=34, bold=False)
    text_fill = _pick_text_colour(label_colour)

    text_left = 560
    header_top = 82
    draw.text((text_left, header_top), container_code, font=header_font, fill=text_fill)

    name_top = 218
    draw.text(
        (text_left, name_top),
        _fit_text(draw, container_name, title_font, max_width=292),
        font=title_font,
        fill=text_fill,
    )

    room_top = 320
    draw.text((text_left, room_top), "Room", font=body_font, fill=text_fill)
    draw.text(
        (text_left, room_top + 44),
        _fit_text(draw, room_name, title_font, max_width=292),
        font=title_font,
        fill=text_fill,
    )

    footer_top = 500
    draw.text((text_left, footer_top), "Scan to view contents", font=body_font, fill=text_fill)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def render_qr_code_png(*, container_id: uuid.UUID, size: int = 420) -> bytes:
    """Render only the QR code itself as PNG bytes for sheet previews."""
    import qrcode
    from PIL import Image

    scan_url = build_scan_url(container_id)
    qr_image = qrcode.make(scan_url).convert("RGB")
    qr_image = qr_image.resize((size, size), Image.Resampling.NEAREST)

    buffer = BytesIO()
    qr_image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _load_font(*, size: int, bold: bool) -> object:
    """Load a bundled TrueType font when available, otherwise fall back."""
    from PIL import ImageFont

    font_names = ["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"]
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _normalize_hex_colour(colour: str) -> str:
    """Normalize a label colour to an uppercase `#RRGGBB` string."""
    normalized = colour.strip().upper()
    if len(normalized) != 7 or not normalized.startswith("#"):
        raise ValueError("Label colour must use #RRGGBB format.")
    hex_digits = normalized[1:]
    if any(char not in "0123456789ABCDEF" for char in hex_digits):
        raise ValueError("Label colour must use #RRGGBB format.")
    return normalized


def _pick_text_colour(colour: str) -> str:
    """Choose black or white text for strong contrast against the label background."""
    normalized = _normalize_hex_colour(colour)
    red = int(normalized[1:3], 16)
    green = int(normalized[3:5], 16)
    blue = int(normalized[5:7], 16)
    luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
    return "#111111" if luminance >= 160 else "#FFFFFF"


def _fit_text(draw: object, text: str, font: object, *, max_width: int) -> str:
    """Trim long text to fit within the available label width."""
    candidate = " ".join(text.split()) or "Unnamed Container"
    if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
        return candidate

    trimmed = candidate
    while len(trimmed) > 1:
        trimmed = trimmed[:-1].rstrip()
        shortened = f"{trimmed}..."
        if draw.textbbox((0, 0), shortened, font=font)[2] <= max_width:
            return shortened
    return "..."
