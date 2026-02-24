import os
import uuid
import io
from PIL import Image
from typing import Tuple

ALLOWED_IMAGE_TYPES = {"png", "jpeg", "jpg", "webp"}
ALLOWED_VECTOR_TYPES = {"svg"}


def _safe_ext(filename: str) -> str:
    if not filename:
        return "png"
    return filename.rsplit('.', 1)[-1].lower()


def store_site_asset(data: bytes, filename: str, folder: str, allow_svg: bool = False) -> Tuple[str, str]:
    ext = _safe_ext(filename)
    if ext in ALLOWED_VECTOR_TYPES:
        if not allow_svg:
            raise ValueError("SVG not allowed")
    elif ext not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Unsupported image type")

    target_dir = os.path.join(os.path.dirname(__file__), "static", "site_assets", folder)
    os.makedirs(target_dir, exist_ok=True)

    asset_id = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(target_dir, asset_id)

    if ext in ALLOWED_VECTOR_TYPES:
        with open(path, "wb") as handle:
            handle.write(data)
    else:
        image = Image.open(io.BytesIO(data))
        image = image.convert("RGBA") if image.mode not in ("RGB", "RGBA") else image
        image.save(path)

    asset_key = f"{folder}/{asset_id}"
    return asset_key, path
