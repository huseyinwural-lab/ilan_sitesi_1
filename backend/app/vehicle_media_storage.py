import io
import os
import uuid
import imghdr
from pathlib import Path
from typing import Dict, Any, Optional

from PIL import Image


BASE_DIR = Path("/data/listing_media")
MIN_WIDTH = 800
MIN_HEIGHT = 600
DEFAULT_WEB_MAX_WIDTH = 1800
DEFAULT_THUMB_MAX_WIDTH = 520


def _safe_ext(original: str) -> str:
    ext = Path(original or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    return ext


def _render_resize(source: Image.Image, max_width: int) -> Image.Image:
    if source.width <= max_width:
        return source.copy()
    ratio = max_width / float(source.width)
    new_height = max(1, int(source.height * ratio))
    return source.resize((max_width, new_height), Image.Resampling.LANCZOS)


def _load_logo_image(logo_file_path: Optional[str]) -> Optional[Image.Image]:
    if not logo_file_path:
        return None
    logo_path = Path(logo_file_path)
    if not logo_path.exists() or not logo_path.is_file():
        return None
    if logo_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return None
    with Image.open(logo_path) as logo:
        return logo.convert("RGBA")


def _apply_watermark(
    image: Image.Image,
    *,
    logo: Optional[Image.Image],
    enabled: bool,
    position: str,
    opacity: float,
) -> Image.Image:
    if not enabled or logo is None:
        return image

    base = image.convert("RGBA")
    logo_copy = logo.copy().convert("RGBA")

    target_logo_width = max(64, int(base.width * 0.2))
    if logo_copy.width > target_logo_width:
        ratio = target_logo_width / float(logo_copy.width)
        new_height = max(1, int(logo_copy.height * ratio))
        logo_copy = logo_copy.resize((target_logo_width, new_height), Image.Resampling.LANCZOS)

    alpha = logo_copy.getchannel("A")
    alpha = alpha.point(lambda p: int(p * max(0.0, min(1.0, opacity))))
    logo_copy.putalpha(alpha)

    margin = max(12, int(base.width * 0.02))
    if position == "bottom_left":
        x = margin
        y = base.height - logo_copy.height - margin
    elif position == "top_right":
        x = base.width - logo_copy.width - margin
        y = margin
    elif position == "top_left":
        x = margin
        y = margin
    elif position == "center":
        x = int((base.width - logo_copy.width) / 2)
        y = int((base.height - logo_copy.height) / 2)
    else:
        x = base.width - logo_copy.width - margin
        y = base.height - logo_copy.height - margin

    base.alpha_composite(logo_copy, (max(0, x), max(0, y)))
    return base.convert("RGB")


def store_image(
    country: str,
    listing_id: str,
    file_bytes: bytes,
    original_name: str,
    *,
    watermark_config: Optional[Dict[str, Any]] = None,
    watermark_logo_path: Optional[str] = None,
) -> Dict[str, Any]:
    listing_dir = BASE_DIR / country / listing_id
    private_dir = listing_dir / "private"
    public_dir = listing_dir / "public"
    private_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    original_ext = _safe_ext(original_name)
    original_filename = f"{uuid.uuid4().hex}{original_ext}"
    original_path = private_dir / original_filename
    original_path.write_bytes(file_bytes)

    kind = imghdr.what(original_path)
    if kind not in {"jpeg", "png", "webp"}:
        original_path.unlink(missing_ok=True)
        raise ValueError("Invalid image format")

    with Image.open(io.BytesIO(file_bytes)) as source:
        source_rgb = source.convert("RGB")
        width, height = source_rgb.size

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        original_path.unlink(missing_ok=True)
        raise ValueError("Image resolution too small")

    cfg = watermark_config or {}
    web_max_width = int(cfg.get("web_max_width") or DEFAULT_WEB_MAX_WIDTH)
    thumb_max_width = int(cfg.get("thumb_max_width") or DEFAULT_THUMB_MAX_WIDTH)
    enabled = bool(cfg.get("enabled", True))
    position = str(cfg.get("position") or "bottom_right").strip().lower()
    opacity = float(cfg.get("opacity") if cfg.get("opacity") is not None else 0.35)

    logo = _load_logo_image(watermark_logo_path)

    with Image.open(io.BytesIO(file_bytes)) as source:
        source_rgb = source.convert("RGB")

        web_render = _render_resize(source_rgb, max(600, web_max_width))
        web_render = _apply_watermark(
            web_render,
            logo=logo,
            enabled=enabled,
            position=position,
            opacity=opacity,
        )

        thumb_render = _render_resize(source_rgb, max(240, thumb_max_width))
        thumb_render = _apply_watermark(
            thumb_render,
            logo=logo,
            enabled=enabled,
            position=position,
            opacity=opacity,
        )

    public_web_file = f"{uuid.uuid4().hex}_web.webp"
    public_thumb_file = f"{uuid.uuid4().hex}_thumb.webp"
    public_web_path = public_dir / public_web_file
    public_thumb_path = public_dir / public_thumb_file

    web_render.save(public_web_path, format="WEBP", quality=82, method=6)
    thumb_render.save(public_thumb_path, format="WEBP", quality=78, method=6)

    original_size = max(1, original_path.stat().st_size)
    web_size = max(1, public_web_path.stat().st_size)
    thumb_size = max(1, public_thumb_path.stat().st_size)
    reduction_ratio = round(((original_size - web_size) / original_size) * 100, 2)

    return {
        "file": public_web_file,
        "thumbnail_file": public_thumb_file,
        "original_file": original_filename,
        "width": web_render.width,
        "height": web_render.height,
        "thumb_width": thumb_render.width,
        "thumb_height": thumb_render.height,
        "original_size": int(original_size),
        "public_size": int(web_size),
        "thumbnail_size": int(thumb_size),
        "reduction_ratio": reduction_ratio,
    }


def resolve_public_media_path(listing_id: str, file: str) -> Path:
    if file != os.path.basename(file):
        raise FileNotFoundError()

    for country_dir in BASE_DIR.iterdir():
        if not country_dir.is_dir():
            continue

        modern_path = country_dir / listing_id / "public" / file
        if modern_path.exists() and modern_path.is_file():
            return modern_path

        legacy_path = country_dir / listing_id / file
        if legacy_path.exists() and legacy_path.is_file():
            return legacy_path

    raise FileNotFoundError()
