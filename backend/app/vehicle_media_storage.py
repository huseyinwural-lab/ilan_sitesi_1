import os
import uuid
import imghdr
from pathlib import Path
from typing import Tuple

from PIL import Image


BASE_DIR = Path("/data/listing_media")


def _safe_filename(original: str) -> str:
    # keep extension if present
    ext = Path(original).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    return f"{uuid.uuid4().hex}{ext}"


def _content_type_ok(content_type: str | None) -> bool:
    if not content_type:
        return False
    return content_type.startswith("image/")


def store_image(country: str, listing_id: str, file_bytes: bytes, original_name: str) -> Tuple[str, int, int]:
    target_dir = BASE_DIR / country / listing_id
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = _safe_filename(original_name)
    path = target_dir / filename

    path.write_bytes(file_bytes)

    # Validate image format
    kind = imghdr.what(path)
    if kind not in {"jpeg", "png", "webp"}:
        path.unlink(missing_ok=True)
        raise ValueError("Invalid image format")

    with Image.open(path) as img:
        width, height = img.size

    if width < 800 or height < 600:
        path.unlink(missing_ok=True)
        raise ValueError("Image resolution too small")

    return filename, width, height


def resolve_public_media_path(listing_id: str, file: str) -> Path:
    # Path traversal protection: file must be basename
    if file != os.path.basename(file):
        raise FileNotFoundError()

    # Search in all countries for listing_id (simple v1)
    for country_dir in BASE_DIR.iterdir():
        if not country_dir.is_dir():
            continue
        p = country_dir / listing_id / file
        if p.exists() and p.is_file():
            return p

    raise FileNotFoundError()
