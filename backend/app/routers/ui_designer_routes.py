from copy import deepcopy
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import time
from typing import Any, Optional
import uuid
import xml.etree.ElementTree as ET

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.dependencies import PERMISSION_ROLE_MAP, check_named_permission, get_current_user_optional
from app.models.core import AuditLog
from app.models.ui_config import UIConfig
from app.models.ui_logo_asset import UILogoAsset
from app.models.ui_theme import UITheme
from app.models.ui_theme_assignment import UIThemeAssignment
from app.site_media_storage import store_site_asset


router = APIRouter(prefix="/api", tags=["ui_designer"])

ADMIN_UI_DESIGNER_PERMISSION = "ADMIN_UI_DESIGNER"
UI_SEGMENTS = {"corporate", "individual"}
UI_SCOPES = {"system", "tenant", "user"}
UI_CONFIG_TYPES = {"header", "nav", "dashboard"}
UI_CONFIG_STATUSES = {"draft", "published"}
UI_LOGO_MAX_BYTES = 2 * 1024 * 1024
UI_LOGO_ALLOWED_EXTENSIONS = {"png", "svg", "webp"}
UI_LOGO_RATIO_TARGET = 3.0
UI_LOGO_RATIO_TOLERANCE = 0.1
UI_LOGO_RETENTION_DAYS = 7
UI_LOGO_URL_PREFIX = "/api/site/assets/"
DASHBOARD_MIN_KPI_WIDGETS = 1
DASHBOARD_MAX_WIDGETS = 12
LOGO_ERROR_INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
LOGO_ERROR_FILE_TOO_LARGE = "FILE_TOO_LARGE"
LOGO_ERROR_INVALID_ASPECT_RATIO = "INVALID_ASPECT_RATIO"
LOGO_ERROR_INVALID_FILE_CONTENT = "INVALID_FILE_CONTENT"
LOGO_ERROR_STORAGE_PIPELINE = "STORAGE_PIPELINE_ERROR"
PUBLISH_ERROR_MISSING_CONFIG_VERSION = "MISSING_CONFIG_VERSION"
PUBLISH_ERROR_CONFIG_VERSION_CONFLICT = "CONFIG_VERSION_CONFLICT"
PUBLISH_ERROR_CONFIG_HASH_MISMATCH = "CONFIG_HASH_MISMATCH"
PUBLISH_ERROR_LOCKED = "PUBLISH_LOCKED"
ROLLBACK_ERROR_MISSING_REASON = "MISSING_ROLLBACK_REASON"
PUBLISH_ERROR_SCOPE_CONFLICT = "SCOPE_CONFLICT"
PUBLISH_ERROR_MISSING_OWNER_SCOPE = "MISSING_OWNER_SCOPE"
UI_ERROR_FEATURE_DISABLED = "FEATURE_DISABLED"
UI_ERROR_UNAUTHORIZED_SCOPE = "UNAUTHORIZED_SCOPE"
THEME_ERROR_INVALID_SCOPE = "INVALID_THEME_SCOPE"
FEATURE_DISABLE_INDIVIDUAL_HEADER_EDITOR = True
PUBLISH_LOCK_TTL_SECONDS = 8

_PUBLISH_LOCK_REGISTRY: dict[str, dict[str, Any]] = {}
_PUBLISH_LOCK_GUARD = asyncio.Lock()

DEFAULT_CORPORATE_HEADER_CONFIG = {
    "rows": [
        {
            "id": "row1",
            "title": "Row 1",
            "blocks": [
                {"id": "logo", "type": "logo", "label": "Logo", "required": True},
                {"id": "quick_actions", "type": "quick_actions", "label": "Hızlı Aksiyonlar"},
                {"id": "language_switcher", "type": "language_switcher", "label": "Dil"},
            ],
        },
        {
            "id": "row2",
            "title": "Row 2",
            "blocks": [
                {"id": "fixed_blocks", "type": "fixed_blocks", "label": "Sabit Bloklar"},
                {"id": "modules", "type": "modules", "label": "Modüller"},
            ],
        },
        {
            "id": "row3",
            "title": "Row 3",
            "blocks": [
                {"id": "store_filter", "type": "store_filter", "label": "Mağaza Filtresi"},
                {"id": "user_menu", "type": "user_menu", "label": "Kullanıcı Menüsü"},
            ],
        },
    ],
    "logo": {
        "url": None,
        "alt": "Kurumsal Logo",
        "fallback_text": "ANNONCIA",
        "aspect_ratio": "3:1",
    },
}

THEME_COLOR_KEYS = ["primary", "secondary", "accent", "text", "inverse"]
THEME_SPACING_KEYS = ["xs", "sm", "md", "lg", "xl"]
THEME_RADIUS_KEYS = ["sm", "md", "lg"]


def _safe_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _site_assets_base_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "static" / "site_assets"


def _site_assets_storage_health() -> dict[str, Any]:
    base_dir = _site_assets_base_dir()
    base_dir.mkdir(parents=True, exist_ok=True)
    writable = base_dir.exists() and base_dir.is_dir() and base_dir.stat().st_mode is not None
    can_write = False
    try:
        probe = base_dir / ".logo_upload_health"
        with probe.open("w", encoding="utf-8") as handle:
            handle.write("ok")
        probe.unlink(missing_ok=True)
        can_write = True
    except Exception:
        can_write = False

    return {
        "status": "ok" if writable and can_write else "degraded",
        "writable": bool(writable and can_write),
        "base_dir": str(base_dir),
    }


def _logo_upload_http_error(
    *,
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[dict[str, Any]] = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": details or {},
        },
    )


def _asset_key_from_url(value: Optional[str]) -> Optional[str]:
    if not value or not value.startswith(UI_LOGO_URL_PREFIX):
        return None
    raw = value.split(UI_LOGO_URL_PREFIX, 1)[-1]
    key = raw.split("?", 1)[0].strip()
    return key or None


def _asset_path_from_key(asset_key: str) -> Path:
    base_dir = _site_assets_base_dir()
    target = (base_dir / asset_key).resolve()
    if not str(target).startswith(str(base_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid asset path")
    return target


def _extract_file_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _parse_svg_size(data: bytes) -> tuple[float, float]:
    try:
        root = ET.fromstring(data.decode("utf-8", errors="ignore"))
    except ET.ParseError as exc:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_INVALID_FILE_CONTENT,
            message="SVG parse edilemedi",
            details={"expected": "Geçerli SVG XML", "received": "Bozuk veya parse edilemeyen içerik"},
        ) from exc

    view_box = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    if view_box:
        parts = [item for item in view_box.replace(",", " ").split(" ") if item]
        if len(parts) == 4:
            try:
                width = float(parts[2])
                height = float(parts[3])
                if width > 0 and height > 0:
                    return width, height
            except ValueError:
                pass

    def _numeric(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch == ".")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    width = _numeric(root.attrib.get("width"))
    height = _numeric(root.attrib.get("height"))
    if width and height and width > 0 and height > 0:
        return width, height

    raise _logo_upload_http_error(
        code=LOGO_ERROR_INVALID_FILE_CONTENT,
        message="SVG width/height metadata bulunamadı",
        details={"expected": "width/height veya viewBox", "received": "Eksik ölçü metadata"},
    )


def _validate_logo_constraints(data: bytes, filename: str) -> dict[str, Any]:
    ext = _extract_file_extension(filename)
    if ext not in UI_LOGO_ALLOWED_EXTENSIONS:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_INVALID_FILE_TYPE,
            message="Desteklenen formatlar: png/svg/webp",
            details={
                "expected": sorted(UI_LOGO_ALLOWED_EXTENSIONS),
                "received": ext or "unknown",
            },
        )
    if len(data) > UI_LOGO_MAX_BYTES:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_FILE_TOO_LARGE,
            message="Dosya boyutu 2MB sınırını aşıyor",
            details={
                "expected_max_bytes": UI_LOGO_MAX_BYTES,
                "received_bytes": len(data),
            },
        )

    if ext == "svg":
        width, height = _parse_svg_size(data)
    else:
        try:
            with Image.open(BytesIO(data)) as image:
                width, height = image.size
        except Exception as exc:
            raise _logo_upload_http_error(
                code=LOGO_ERROR_INVALID_FILE_CONTENT,
                message="Görsel dosyası okunamadı",
                details={"expected": "Geçerli png/webp", "received": "Bozuk raster içerik"},
            ) from exc

    if not width or not height:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_INVALID_FILE_CONTENT,
            message="Görsel ölçüsü geçersiz",
            details={"expected": "Pozitif width/height", "received": {"width": width, "height": height}},
        )
    ratio = float(width) / float(height)
    min_ratio = UI_LOGO_RATIO_TARGET * (1 - UI_LOGO_RATIO_TOLERANCE)
    max_ratio = UI_LOGO_RATIO_TARGET * (1 + UI_LOGO_RATIO_TOLERANCE)
    if ratio < min_ratio or ratio > max_ratio:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_INVALID_ASPECT_RATIO,
            message=f"Logo aspect ratio 3:1 (±%10) olmalı. Mevcut oran: {ratio:.2f}",
            details={
                "expected": "3:1 ±10%",
                "expected_min_ratio": round(min_ratio, 4),
                "expected_max_ratio": round(max_ratio, 4),
                "received_ratio": round(ratio, 4),
                "width": int(round(width)),
                "height": int(round(height)),
            },
        )

    return {
        "extension": ext,
        "width": int(round(width)),
        "height": int(round(height)),
        "ratio": round(ratio, 4),
    }


def _default_header_config(segment: str) -> dict[str, Any]:
    if segment == "corporate":
        return deepcopy(DEFAULT_CORPORATE_HEADER_CONFIG)
    return {"rows": [], "logo": {"url": None, "fallback_text": "ANNONCIA", "aspect_ratio": "3:1"}}


def _normalize_header_config_data(config_data: dict[str, Any], segment: str) -> dict[str, Any]:
    payload = deepcopy(config_data or {})
    if segment != "corporate":
        payload.setdefault("rows", [])
        payload.setdefault("logo", {"url": None, "fallback_text": "ANNONCIA", "aspect_ratio": "3:1"})
        return payload

    default = _default_header_config("corporate")
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    row_map: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_id = (row.get("id") or "").strip().lower()
        if row_id in {"row1", "row2", "row3"}:
            row_map[row_id] = {
                "id": row_id,
                "title": row.get("title") or row_id.upper(),
                "blocks": row.get("blocks") if isinstance(row.get("blocks"), list) else [],
            }

    normalized_rows = []
    for fallback_row in default["rows"]:
        row_id = fallback_row["id"]
        selected = row_map.get(row_id) or fallback_row
        blocks = []
        for block in selected.get("blocks", []):
            if not isinstance(block, dict):
                continue
            block_type = (block.get("type") or "").strip()
            if not block_type:
                continue
            block_id = (block.get("id") or block_type).strip()
            blocks.append(
                {
                    "id": block_id,
                    "type": block_type,
                    "label": block.get("label") or block_type,
                    "required": bool(block.get("required", False)),
                    "logo_url": block.get("logo_url"),
                }
            )
        normalized_rows.append(
            {
                "id": row_id,
                "title": selected.get("title") or fallback_row.get("title") or row_id.upper(),
                "blocks": blocks,
            }
        )

    logo = payload.get("logo") if isinstance(payload.get("logo"), dict) else {}
    normalized_logo = {
        "url": logo.get("url"),
        "alt": logo.get("alt") or "Kurumsal Logo",
        "fallback_text": logo.get("fallback_text") or "ANNONCIA",
        "aspect_ratio": "3:1",
        "width": logo.get("width"),
        "height": logo.get("height"),
        "ratio": logo.get("ratio"),
    }
    payload["rows"] = normalized_rows
    payload["logo"] = normalized_logo
    return payload


def _validate_corporate_header_guardrails(config_data: dict[str, Any]) -> None:
    rows = config_data.get("rows") if isinstance(config_data.get("rows"), list) else []
    if len(rows) != 3:
        raise HTTPException(status_code=400, detail="Kurumsal header 3 satır içermelidir")

    expected = ["row1", "row2", "row3"]
    row_ids = [str((row or {}).get("id") or "").strip().lower() for row in rows]
    if row_ids != expected:
        raise HTTPException(status_code=400, detail="Satır sırası row1,row2,row3 olmalıdır")

    for row in rows:
        blocks = row.get("blocks") if isinstance(row.get("blocks"), list) else []
        if not blocks:
            raise HTTPException(status_code=400, detail=f"{row.get('id')} en az 1 bileşen içermelidir")

    row1_blocks = rows[0].get("blocks") if isinstance(rows[0].get("blocks"), list) else []
    logo_block = next((block for block in row1_blocks if str(block.get("type") or "") == "logo"), None)
    if not logo_block:
        raise HTTPException(status_code=400, detail="Row1 içinde zorunlu logo bileşeni bulunmalıdır")


def _normalize_dashboard_layout(layout_payload: Any) -> list[dict[str, Any]]:
    if layout_payload is None:
        return []
    if not isinstance(layout_payload, list):
        raise HTTPException(status_code=400, detail="Dashboard layout liste (array) olmalıdır")

    normalized_items: list[dict[str, Any]] = []
    for item in layout_payload:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="Dashboard layout öğeleri object olmalıdır")

        widget_id = str(item.get("widget_id") or item.get("i") or item.get("id") or "").strip()
        if not widget_id:
            raise HTTPException(status_code=400, detail="Dashboard layout öğesinde widget_id zorunludur")

        normalized_item = {**item, "widget_id": widget_id}
        for key in ("x", "y", "w", "h"):
            value = normalized_item.get(key)
            if value is None:
                continue
            try:
                numeric_value = int(value)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail=f"Dashboard layout alanı '{key}' sayı olmalıdır") from exc

            if key in {"x", "y"} and numeric_value < 0:
                raise HTTPException(status_code=400, detail=f"Dashboard layout alanı '{key}' 0 veya daha büyük olmalıdır")
            if key in {"w", "h"} and numeric_value < 1:
                raise HTTPException(status_code=400, detail=f"Dashboard layout alanı '{key}' 1 veya daha büyük olmalıdır")
            normalized_item[key] = numeric_value

        normalized_items.append(normalized_item)
    return normalized_items


def _normalize_dashboard_widgets(widgets_payload: Any) -> list[dict[str, Any]]:
    if widgets_payload is None:
        return []
    if not isinstance(widgets_payload, list):
        raise HTTPException(status_code=400, detail="Dashboard widgets liste (array) olmalıdır")

    normalized_items: list[dict[str, Any]] = []
    for item in widgets_payload:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="Dashboard widget öğeleri object olmalıdır")

        widget_id = str(item.get("widget_id") or item.get("id") or "").strip()
        if not widget_id:
            raise HTTPException(status_code=400, detail="Dashboard widget öğesinde widget_id zorunludur")

        widget_type = str(item.get("widget_type") or item.get("type") or "").strip().lower()
        if not widget_type:
            raise HTTPException(status_code=400, detail="Dashboard widget öğesinde widget_type zorunludur")

        normalized_item = {
            **item,
            "widget_id": widget_id,
            "widget_type": widget_type,
            "enabled": bool(item.get("enabled", True)),
        }
        normalized_items.append(normalized_item)
    return normalized_items


def _extract_dashboard_layout_widgets(
    *,
    layout_payload: Any,
    widgets_payload: Any,
    config_data: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    raw_layout = layout_payload if layout_payload is not None else config_data.get("layout")
    raw_widgets = widgets_payload if widgets_payload is not None else config_data.get("widgets")

    normalized_layout = _normalize_dashboard_layout(raw_layout)
    normalized_widgets = _normalize_dashboard_widgets(raw_widgets)

    next_config_data = deepcopy(config_data)
    next_config_data.pop("layout", None)
    next_config_data.pop("widgets", None)
    return normalized_layout, normalized_widgets, next_config_data


def _validate_dashboard_guardrails(layout: list[dict[str, Any]], widgets: list[dict[str, Any]]) -> None:
    total_widgets = len(widgets)
    if total_widgets > DASHBOARD_MAX_WIDGETS:
        raise HTTPException(status_code=400, detail=f"Dashboard en fazla {DASHBOARD_MAX_WIDGETS} widget içerebilir")

    kpi_count = sum(
        1
        for widget in widgets
        if str(widget.get("widget_type") or "").strip().lower() == "kpi" and widget.get("enabled", True) is not False
    )
    if kpi_count < DASHBOARD_MIN_KPI_WIDGETS:
        raise HTTPException(status_code=400, detail="Dashboard en az 1 KPI widget içermelidir")

    widget_ids = [str(widget.get("widget_id") or "").strip() for widget in widgets]
    if len(widget_ids) != len(set(widget_ids)):
        raise HTTPException(status_code=400, detail="Dashboard widget_id alanları benzersiz olmalıdır")

    layout_widget_ids = [str(item.get("widget_id") or "").strip() for item in layout]
    if len(layout_widget_ids) != len(set(layout_widget_ids)):
        raise HTTPException(status_code=400, detail="Dashboard layout widget_id alanları benzersiz olmalıdır")

    if layout_widget_ids:
        widget_id_set = set(widget_ids)
        layout_id_set = set(layout_widget_ids)

        missing_layout_ids = sorted(widget_id_set - layout_id_set)
        if missing_layout_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Her widget için layout girdisi zorunludur: {', '.join(missing_layout_ids)}",
            )

        unknown_layout_ids = sorted(layout_id_set - widget_id_set)
        if unknown_layout_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Layout içinde tanımsız widget_id bulundu: {', '.join(unknown_layout_ids)}",
            )


def _extract_header_logo_url(config_data: dict[str, Any]) -> Optional[str]:
    logo = config_data.get("logo") if isinstance(config_data.get("logo"), dict) else {}
    logo_url = (logo.get("url") or "").strip()
    if logo_url:
        return logo_url

    rows = config_data.get("rows") if isinstance(config_data.get("rows"), list) else []
    for row in rows:
        if str((row or {}).get("id") or "").strip().lower() != "row1":
            continue
        blocks = row.get("blocks") if isinstance(row.get("blocks"), list) else []
        for block in blocks:
            if str((block or {}).get("type") or "").strip() != "logo":
                continue
            candidate = (block.get("logo_url") or block.get("url") or "").strip()
            if candidate:
                return candidate
    return None


def _apply_header_logo_to_config(config_data: dict[str, Any], logo_url: str, logo_meta: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_header_config_data(config_data, "corporate")
    rows = normalized["rows"]
    row1 = rows[0]
    blocks = row1.get("blocks") or []

    logo_block = None
    for block in blocks:
        if str((block or {}).get("type") or "") == "logo":
            logo_block = block
            break
    if not logo_block:
        logo_block = {"id": "logo", "type": "logo", "label": "Logo", "required": True}
        blocks.insert(0, logo_block)

    logo_block["logo_url"] = logo_url
    logo_block["aspect_ratio"] = "3:1"
    logo_block["width"] = logo_meta.get("width")
    logo_block["height"] = logo_meta.get("height")
    logo_block["ratio"] = logo_meta.get("ratio")

    normalized["logo"] = {
        **(normalized.get("logo") or {}),
        "url": logo_url,
        "aspect_ratio": "3:1",
        "width": logo_meta.get("width"),
        "height": logo_meta.get("height"),
        "ratio": logo_meta.get("ratio"),
        "fallback_text": (normalized.get("logo") or {}).get("fallback_text") or "ANNONCIA",
    }
    return normalized


async def _upsert_logo_asset_row(
    session: AsyncSession,
    *,
    asset_key: str,
    asset_url: str,
    segment: str,
    scope: str,
    scope_id: Optional[str],
    current_user: dict[str, Any],
) -> UILogoAsset:
    existing = (await session.execute(select(UILogoAsset).where(UILogoAsset.asset_key == asset_key).limit(1))).scalar_one_or_none()
    if existing:
        existing.asset_url = asset_url
        existing.segment = segment
        existing.scope = scope
        existing.scope_id = scope_id
        existing.config_type = "header"
        existing.is_deleted = False
        existing.updated_at = datetime.now(timezone.utc)
        return existing

    row = UILogoAsset(
        asset_key=asset_key,
        asset_url=asset_url,
        segment=segment,
        scope=scope,
        scope_id=scope_id,
        config_type="header",
        created_by=_safe_uuid(current_user.get("id")),
        created_by_email=current_user.get("email"),
    )
    session.add(row)
    return row


async def _mark_replaced_logo_if_exists(
    session: AsyncSession,
    *,
    old_logo_url: Optional[str],
    new_asset_key: str,
) -> Optional[UILogoAsset]:
    old_asset_key = _asset_key_from_url(old_logo_url)
    if not old_asset_key or old_asset_key == new_asset_key:
        return None

    now_dt = datetime.now(timezone.utc)
    retention_dt = now_dt + timedelta(days=UI_LOGO_RETENTION_DAYS)
    existing = (await session.execute(select(UILogoAsset).where(UILogoAsset.asset_key == old_asset_key).limit(1))).scalar_one_or_none()
    if not existing:
        existing = UILogoAsset(
            asset_key=old_asset_key,
            asset_url=old_logo_url or f"{UI_LOGO_URL_PREFIX}{old_asset_key}",
            segment="corporate",
            scope="system",
            scope_id=None,
            config_type="header",
        )
        session.add(existing)

    existing.is_replaced = True
    existing.replaced_by_asset_key = new_asset_key
    existing.replaced_at = now_dt
    existing.delete_after = retention_dt
    existing.updated_at = now_dt
    return existing


async def _cleanup_replaced_logo_assets(limit: int = 100) -> dict[str, int]:
    async with AsyncSessionLocal() as cleanup_session:
        now_dt = datetime.now(timezone.utc)
        due_rows = (
            await cleanup_session.execute(
                select(UILogoAsset)
                .where(
                    UILogoAsset.is_replaced.is_(True),
                    UILogoAsset.is_deleted.is_(False),
                    UILogoAsset.delete_after.isnot(None),
                    UILogoAsset.delete_after <= now_dt,
                )
                .order_by(UILogoAsset.delete_after.asc())
                .limit(limit)
            )
        ).scalars().all()

        deleted = 0
        skipped = 0
        for row in due_rows:
            try:
                target_path = _asset_path_from_key(row.asset_key)
                if target_path.exists() and target_path.is_file():
                    target_path.unlink(missing_ok=True)
                row.is_deleted = True
                row.updated_at = now_dt
                deleted += 1
            except Exception:
                skipped += 1

        if due_rows:
            await cleanup_session.commit()

        return {"deleted": deleted, "skipped": skipped}


def _is_hex_color(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    raw = value.strip()
    if len(raw) != 7 or not raw.startswith("#"):
        return False
    return all(ch in "0123456789abcdefABCDEF" for ch in raw[1:])


def _validate_theme_tokens(tokens: dict[str, Any]) -> None:
    if not isinstance(tokens, dict):
        raise HTTPException(status_code=400, detail="Theme tokens object olmalıdır")

    colors = tokens.get("colors")
    if colors is not None:
        if not isinstance(colors, dict):
            raise HTTPException(status_code=400, detail="tokens.colors object olmalıdır")
        for key in THEME_COLOR_KEYS:
            value = colors.get(key)
            if value is None:
                continue
            if not _is_hex_color(value):
                raise HTTPException(status_code=400, detail=f"{key} hex formatında olmalıdır")

    typography = tokens.get("typography")
    if typography is not None:
        if not isinstance(typography, dict):
            raise HTTPException(status_code=400, detail="tokens.typography object olmalıdır")
        base_size = typography.get("base_font_size")
        if base_size is not None:
            try:
                size_int = int(base_size)
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=400, detail="base_font_size sayı olmalıdır") from exc
            if size_int < 12 or size_int > 24:
                raise HTTPException(status_code=400, detail="base_font_size 12-24 aralığında olmalıdır")

    spacing = tokens.get("spacing")
    if spacing is not None:
        if not isinstance(spacing, dict):
            raise HTTPException(status_code=400, detail="tokens.spacing object olmalıdır")
        for key in THEME_SPACING_KEYS:
            value = spacing.get(key)
            if value is None:
                continue
            try:
                spacing_int = int(value)
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=400, detail=f"spacing.{key} sayı olmalıdır") from exc
            if spacing_int < 0 or spacing_int > 64:
                raise HTTPException(status_code=400, detail=f"spacing.{key} 0-64 aralığında olmalıdır")

    radius = tokens.get("radius")
    if radius is not None:
        if not isinstance(radius, dict):
            raise HTTPException(status_code=400, detail="tokens.radius object olmalıdır")
        for key in THEME_RADIUS_KEYS:
            value = radius.get(key)
            if value is None:
                continue
            try:
                radius_int = int(value)
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=400, detail=f"radius.{key} sayı olmalıdır") from exc
            if radius_int < 0 or radius_int > 32:
                raise HTTPException(status_code=400, detail=f"radius.{key} 0-32 aralığında olmalıdır")


class UIConfigSavePayload(BaseModel):
    segment: str = Field(default="individual")
    scope: str = Field(default="system")
    scope_id: Optional[str] = None
    status: str = Field(default="draft")
    config_data: dict = Field(default_factory=dict)
    layout: Optional[list[dict[str, Any]]] = None
    widgets: Optional[list[dict[str, Any]]] = None


class UIConfigPublishPayload(BaseModel):
    segment: str = Field(default="individual")
    scope: str = Field(default="system")
    scope_id: Optional[str] = None
    config_id: Optional[str] = None
    owner_type: Optional[str] = None
    owner_id: Optional[str] = None
    config_version: Optional[int] = None
    resolved_config_hash: Optional[str] = None
    retry_count: int = 0
    require_confirm: bool = False


class UIConfigLegacyPublishPayload(BaseModel):
    owner_type: Optional[str] = None
    owner_id: Optional[str] = None
    config_version: Optional[int] = None
    resolved_config_hash: Optional[str] = None
    retry_count: int = 0


class UIConfigConflictSyncPayload(BaseModel):
    segment: str = Field(default="individual")
    scope: str = Field(default="system")
    scope_id: Optional[str] = None
    previous_version: Optional[int] = None
    retry_count: int = 0


class UIConfigRollbackPayload(BaseModel):
    segment: str = Field(default="individual")
    scope: str = Field(default="system")
    scope_id: Optional[str] = None
    target_config_id: Optional[str] = None
    rollback_reason: Optional[str] = None
    require_confirm: bool = False


class UIThemeCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    tokens: dict = Field(default_factory=dict)
    is_active: bool = False


class UIThemeUpdatePayload(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    tokens: Optional[dict] = None
    is_active: Optional[bool] = None


class UIThemeAssignmentPayload(BaseModel):
    theme_id: str
    scope: str = Field(default="system")
    scope_id: Optional[str] = None


def _normalize_segment(value: str) -> str:
    segment = (value or "individual").strip().lower()
    if segment not in UI_SEGMENTS:
        raise HTTPException(status_code=400, detail="Invalid segment")
    return segment


def _normalize_scope(scope: str, scope_id: Optional[str]) -> tuple[str, Optional[str]]:
    normalized_scope = (scope or "system").strip().lower()
    if normalized_scope not in UI_SCOPES:
        raise HTTPException(status_code=400, detail="Invalid scope")

    normalized_scope_id = (scope_id or "").strip() or None
    if normalized_scope == "system":
        return normalized_scope, None
    if not normalized_scope_id:
        raise HTTPException(status_code=400, detail="scope_id is required for tenant/user scope")
    return normalized_scope, normalized_scope_id


def _normalize_config_type(value: str) -> str:
    config_type = (value or "").strip().lower()
    if config_type not in UI_CONFIG_TYPES:
        raise HTTPException(status_code=400, detail="Invalid config_type")
    return config_type


def _normalize_status(value: str) -> str:
    status = (value or "draft").strip().lower()
    if status not in UI_CONFIG_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    return status


def _ui_http_error(*, code: str, message: str, status_code: int, extras: Optional[dict[str, Any]] = None) -> HTTPException:
    payload = {"code": code, "message": message}
    if extras:
        payload.update(extras)
    return HTTPException(status_code=status_code, detail=payload)


def _assert_header_segment_enabled(config_type: str, segment: str) -> None:
    if FEATURE_DISABLE_INDIVIDUAL_HEADER_EDITOR and config_type == "header" and segment == "individual":
        raise _ui_http_error(
            code=UI_ERROR_FEATURE_DISABLED,
            message="Bireysel header editörü devre dışı",
            status_code=403,
            extras={"feature": "individual_header_editor", "hint": "Header modeli yalnızca global + dealer override olarak sadeleştirildi"},
        )


def _normalize_owner_scope(owner_type: Optional[str], owner_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    normalized_owner_type = (owner_type or "").strip().lower() or None
    normalized_owner_id = (owner_id or "").strip() or None
    return normalized_owner_type, normalized_owner_id


def _expected_owner_scope_for_row(row: UIConfig) -> tuple[str, str]:
    if row.scope == "tenant":
        return "dealer", (row.scope_id or "").strip()
    if row.scope == "system":
        return "global", "global"
    return row.scope, (row.scope_id or row.scope)


def _owner_scope_from_scope(scope: str, scope_id: Optional[str]) -> tuple[str, str]:
    if scope == "tenant":
        return "dealer", (scope_id or "").strip()
    return "global", "global"


def _stable_hash_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _build_ui_publish_snapshot(row: UIConfig) -> dict[str, Any]:
    owner_type, owner_id = _expected_owner_scope_for_row(row)
    effective_config = _effective_config_data(row, row.config_type, row.segment)
    snapshot_source = {
        "config_type": row.config_type,
        "segment": row.segment,
        "scope": row.scope,
        "scope_id": row.scope_id,
        "config_version": row.version,
        "config_data": effective_config,
    }
    if row.config_type == "dashboard":
        snapshot_source["layout"] = effective_config.get("layout", [])
        snapshot_source["widgets"] = effective_config.get("widgets", [])

    return {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "config_version": int(row.version),
        "resolved_config_hash": _stable_hash_payload(snapshot_source),
    }


def _validate_owner_scope_or_raise(row: UIConfig, owner_type: Optional[str], owner_id: Optional[str]) -> None:
    normalized_owner_type, normalized_owner_id = _normalize_owner_scope(owner_type, owner_id)
    if not normalized_owner_type or not normalized_owner_id:
        raise _ui_http_error(
            code=PUBLISH_ERROR_MISSING_OWNER_SCOPE,
            message="owner_type ve owner_id zorunludur",
            status_code=400,
            extras={"hint": "Publish öncesi scope owner bilgisi gönderilmelidir"},
        )


async def _record_publish_attempt_audit(
    session: AsyncSession,
    *,
    current_user: dict[str, Any],
    config_type: str,
    segment: str,
    scope: str,
    scope_id: Optional[str],
    config_id: Optional[str],
    config_version: Optional[int],
    retry_count: int,
    conflict_detected: bool,
    lock_wait_ms: int,
    publish_duration_ms: Optional[int],
    status: str,
    detail_message: str,
    extra: Optional[dict[str, Any]] = None,
    commit_now: bool = False,
) -> None:
    owner_type, owner_id = _owner_scope_from_scope(scope, scope_id)
    metadata = {
        "actor_id": current_user.get("id"),
        "owner_type": owner_type,
        "owner_id": owner_id,
        "segment": segment,
        "scope": scope,
        "scope_id": scope_id,
        "config_version": config_version,
        "retry_count": int(max(0, retry_count or 0)),
        "conflict_detected": bool(conflict_detected),
        "lock_wait_ms": int(max(0, lock_wait_ms or 0)),
        "publish_duration_ms": int(max(0, publish_duration_ms or 0)) if publish_duration_ms is not None else None,
        "status": status,
        "message": detail_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        metadata.update(extra)

    session.add(
        _create_ui_config_audit_log(
            action="ui_config_publish_attempt",
            current_user=current_user,
            config_type=config_type,
            resource_id=config_id or "scope_attempt",
            old_values=None,
            new_values=None,
            metadata_info=metadata,
        )
    )
    if commit_now:
        await session.commit()

    expected_owner_type, expected_owner_id = _expected_owner_scope_for_row(row)
    if normalized_owner_type != expected_owner_type or normalized_owner_id != expected_owner_id:
        raise _ui_http_error(
            code=PUBLISH_ERROR_SCOPE_CONFLICT,
            message="owner scope mismatch",
            status_code=409,
            extras={
                "expected_owner_type": expected_owner_type,
                "expected_owner_id": expected_owner_id,
                "your_owner_type": normalized_owner_type,
                "your_owner_id": normalized_owner_id,
            },
        )


def _scope_clause(scope: str, scope_id: Optional[str]):
    if scope == "system":
        return [UIConfig.scope == "system", or_(UIConfig.scope_id.is_(None), UIConfig.scope_id == "")]
    return [UIConfig.scope == scope, UIConfig.scope_id == scope_id]


def _theme_scope_clause(scope: str, scope_id: Optional[str]):
    if scope == "system":
        return [UIThemeAssignment.scope == "system", or_(UIThemeAssignment.scope_id.is_(None), UIThemeAssignment.scope_id == "")]
    return [UIThemeAssignment.scope == scope, UIThemeAssignment.scope_id == scope_id]


def _flatten_token_paths(payload: Any, prefix: str = "") -> set[str]:
    if not isinstance(payload, dict):
        return set()
    paths: set[str] = set()
    for key, value in payload.items():
        key_name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            paths |= _flatten_token_paths(value, key_name)
        else:
            paths.add(key_name)
    return paths


def _deep_merge_tokens(base_tokens: dict[str, Any], override_tokens: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base_tokens or {})
    for key, value in (override_tokens or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_tokens(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _validate_theme_scope_v2_or_raise(scope: str) -> None:
    if scope not in {"system", "tenant"}:
        raise _ui_http_error(
            code=THEME_ERROR_INVALID_SCOPE,
            message="Theme override sadece system veya tenant scope için desteklenir",
            status_code=400,
            extras={"allowed_scopes": ["system", "tenant"], "received_scope": scope},
        )


def _serialize_ui_config(row: UIConfig) -> dict[str, Any]:
    config_data = deepcopy(row.config_data or {})
    layout_value = row.layout if isinstance(row.layout, list) else []
    widgets_value = row.widgets if isinstance(row.widgets, list) else []

    if row.config_type == "dashboard":
        layout_value, widgets_value, config_data = _extract_dashboard_layout_widgets(
            layout_payload=row.layout,
            widgets_payload=row.widgets,
            config_data=config_data,
        )

    hash_source = {
        "config_type": row.config_type,
        "segment": row.segment,
        "scope": row.scope,
        "scope_id": row.scope_id,
        "config_version": int(row.version),
        "config_data": config_data,
    }
    if row.config_type == "dashboard":
        hash_source["layout"] = layout_value
        hash_source["widgets"] = widgets_value

    return {
        "id": str(row.id),
        "config_type": row.config_type,
        "segment": row.segment,
        "scope": row.scope,
        "scope_id": row.scope_id,
        "status": row.status,
        "version": row.version,
        "config_data": config_data,
        "layout": layout_value,
        "widgets": widgets_value,
        "created_by": str(row.created_by) if row.created_by else None,
        "created_by_email": row.created_by_email,
        "resolved_config_hash": _stable_hash_payload(hash_source),
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _serialize_ui_theme(row: UITheme) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "tokens": row.tokens or {},
        "is_active": bool(row.is_active),
        "created_by": str(row.created_by) if row.created_by else None,
        "created_by_email": row.created_by_email,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _serialize_ui_theme_assignment(row: UIThemeAssignment) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "theme_id": str(row.theme_id),
        "scope": row.scope,
        "scope_id": row.scope_id,
        "assigned_by": str(row.assigned_by) if row.assigned_by else None,
        "assigned_by_email": row.assigned_by_email,
        "deprecated": row.scope == "user",
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _normalize_header_rows_for_diff(config_data: dict[str, Any], segment: str) -> list[dict[str, Any]]:
    normalized = _normalize_header_config_data(config_data or {}, segment)
    rows = normalized.get("rows") if isinstance(normalized.get("rows"), list) else []
    safe_rows: list[dict[str, Any]] = []
    for row in rows:
        blocks = row.get("blocks") if isinstance(row.get("blocks"), list) else []
        safe_rows.append(
            {
                "id": str(row.get("id") or ""),
                "visible": bool(row.get("visible", True)),
                "blocks": [
                    {
                        "id": str(block.get("id") or block.get("type") or ""),
                        "type": str(block.get("type") or ""),
                        "visible": bool(block.get("visible", True)),
                    }
                    for block in blocks
                ],
            }
        )
    return safe_rows


def _compute_ui_config_diff(
    *,
    config_type: str,
    segment: str,
    old_payload: Optional[dict[str, Any]],
    new_payload: Optional[dict[str, Any]],
) -> dict[str, Any]:
    old_payload = old_payload or {"config_data": {}, "layout": [], "widgets": []}
    new_payload = new_payload or {"config_data": {}, "layout": [], "widgets": []}

    if config_type == "dashboard":
        old_widgets = old_payload.get("widgets") if isinstance(old_payload.get("widgets"), list) else []
        new_widgets = new_payload.get("widgets") if isinstance(new_payload.get("widgets"), list) else []
        old_layout = old_payload.get("layout") if isinstance(old_payload.get("layout"), list) else []
        new_layout = new_payload.get("layout") if isinstance(new_payload.get("layout"), list) else []

        old_widget_map = {
            str(item.get("widget_id") or ""): item
            for item in old_widgets
            if isinstance(item, dict) and str(item.get("widget_id") or "").strip()
        }
        new_widget_map = {
            str(item.get("widget_id") or ""): item
            for item in new_widgets
            if isinstance(item, dict) and str(item.get("widget_id") or "").strip()
        }

        old_layout_map = {
            str(item.get("widget_id") or ""): {
                "x": item.get("x"),
                "y": item.get("y"),
                "w": item.get("w"),
                "h": item.get("h"),
            }
            for item in old_layout
            if isinstance(item, dict) and str(item.get("widget_id") or "").strip()
        }
        new_layout_map = {
            str(item.get("widget_id") or ""): {
                "x": item.get("x"),
                "y": item.get("y"),
                "w": item.get("w"),
                "h": item.get("h"),
            }
            for item in new_layout
            if isinstance(item, dict) and str(item.get("widget_id") or "").strip()
        }

        old_ids = set(old_widget_map.keys())
        new_ids = set(new_widget_map.keys())

        added = sorted(new_ids - old_ids)
        removed = sorted(old_ids - new_ids)
        common = sorted(old_ids & new_ids)

        moved: list[dict[str, Any]] = []
        type_changed: list[dict[str, Any]] = []
        for widget_id in common:
            if old_layout_map.get(widget_id) != new_layout_map.get(widget_id):
                moved.append({
                    "widget_id": widget_id,
                    "from": old_layout_map.get(widget_id),
                    "to": new_layout_map.get(widget_id),
                })
            old_type = str((old_widget_map.get(widget_id) or {}).get("widget_type") or "")
            new_type = str((new_widget_map.get(widget_id) or {}).get("widget_type") or "")
            if old_type != new_type:
                type_changed.append({"widget_id": widget_id, "from": old_type, "to": new_type})

        has_changes = bool(added or removed or moved or type_changed)
        return {
            "config_type": config_type,
            "added_widgets": added,
            "removed_widgets": removed,
            "moved_widgets": moved,
            "type_changed_widgets": type_changed,
            "has_changes": has_changes,
            "change_count": len(added) + len(removed) + len(moved) + len(type_changed),
        }

    if config_type == "header":
        old_rows = _normalize_header_rows_for_diff(old_payload.get("config_data") or {}, segment)
        new_rows = _normalize_header_rows_for_diff(new_payload.get("config_data") or {}, segment)

        def _signature_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
            entries: dict[str, dict[str, Any]] = {}
            for row_index, row in enumerate(rows):
                row_id = str(row.get("id") or f"row-{row_index}")
                blocks = row.get("blocks") if isinstance(row.get("blocks"), list) else []
                for block_index, block in enumerate(blocks):
                    block_id = str(block.get("id") or block.get("type") or f"block-{block_index}")
                    key = f"{row_id}:{block_id}"
                    entries[key] = {
                        "row_id": row_id,
                        "index": block_index,
                        "visible": bool(block.get("visible", True)),
                        "type": str(block.get("type") or ""),
                    }
            return entries

        old_map = _signature_map(old_rows)
        new_map = _signature_map(new_rows)
        old_keys = set(old_map.keys())
        new_keys = set(new_map.keys())

        added = sorted(new_keys - old_keys)
        removed = sorted(old_keys - new_keys)
        moved: list[dict[str, Any]] = []
        visibility_changed: list[dict[str, Any]] = []
        for key in sorted(old_keys & new_keys):
            old_entry = old_map[key]
            new_entry = new_map[key]
            if old_entry.get("row_id") != new_entry.get("row_id") or old_entry.get("index") != new_entry.get("index"):
                moved.append({"module": key, "from": old_entry, "to": new_entry})
            if old_entry.get("visible") != new_entry.get("visible"):
                visibility_changed.append({"module": key, "from": old_entry.get("visible"), "to": new_entry.get("visible")})

        has_changes = bool(added or removed or moved or visibility_changed)
        return {
            "config_type": config_type,
            "added_modules": added,
            "removed_modules": removed,
            "moved_modules": moved,
            "visibility_changes": visibility_changed,
            "has_changes": has_changes,
            "change_count": len(added) + len(removed) + len(moved) + len(visibility_changed),
        }

    old_data = old_payload.get("config_data") if isinstance(old_payload.get("config_data"), dict) else {}
    new_data = new_payload.get("config_data") if isinstance(new_payload.get("config_data"), dict) else {}
    has_changes = old_data != new_data
    return {
        "config_type": config_type,
        "has_changes": has_changes,
        "change_count": 1 if has_changes else 0,
    }


def _create_ui_config_audit_log(
    *,
    action: str,
    current_user: dict[str, Any],
    config_type: str,
    resource_id: str,
    old_values: Optional[dict[str, Any]],
    new_values: Optional[dict[str, Any]],
    metadata_info: Optional[dict[str, Any]],
) -> AuditLog:
    return AuditLog(
        user_id=_safe_uuid(current_user.get("id")),
        user_email=current_user.get("email"),
        action=action,
        resource_type=f"ui_config:{config_type}",
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        metadata_info=metadata_info,
    )


def _publish_http_error(
    *,
    code: str,
    message: str,
    status_code: int,
    extras: Optional[dict[str, Any]] = None,
) -> HTTPException:
    payload = {
        "code": code,
        "message": message,
    }
    if extras:
        payload.update(extras)
    return HTTPException(status_code=status_code, detail=payload)


def _publish_scope_key(*, config_type: str, segment: str, scope: str, scope_id: Optional[str]) -> str:
    return f"{config_type}:{segment}:{scope}:{scope_id or 'system'}"


async def _acquire_publish_lock_or_raise(lock_key: str, current_user: dict[str, Any]) -> None:
    now_dt = datetime.now(timezone.utc)
    async with _PUBLISH_LOCK_GUARD:
        existing = _PUBLISH_LOCK_REGISTRY.get(lock_key)
        if existing:
            expires_at = existing.get("expires_at")
            if isinstance(expires_at, datetime) and expires_at > now_dt:
                raise _publish_http_error(
                    code=PUBLISH_ERROR_LOCKED,
                    message="Aynı scope için publish işlemi devam ediyor",
                    status_code=409,
                    extras={
                        "active_lock_until": expires_at.isoformat(),
                        "lock_owner": existing.get("owner_email"),
                        "retry_after_seconds": max(1, int((expires_at - now_dt).total_seconds())),
                    },
                )

        _PUBLISH_LOCK_REGISTRY[lock_key] = {
            "owner_email": current_user.get("email"),
            "acquired_at": now_dt,
            "expires_at": now_dt + timedelta(seconds=PUBLISH_LOCK_TTL_SECONDS),
        }


async def _release_publish_lock(lock_key: str) -> None:
    async with _PUBLISH_LOCK_GUARD:
        _PUBLISH_LOCK_REGISTRY.pop(lock_key, None)


async def _latest_publish_actor(
    session: AsyncSession,
    *,
    config_type: str,
    resource_id: str,
) -> tuple[Optional[str], Optional[str]]:
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.action == "ui_config_publish",
            AuditLog.resource_type == f"ui_config:{config_type}",
            AuditLog.resource_id == resource_id,
        )
        .order_by(desc(AuditLog.created_at))
        .limit(1)
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if not row:
        return None, None
    return row.user_email, row.created_at.isoformat() if row.created_at else None


async def _build_publish_conflict_payload(
    session: AsyncSession,
    *,
    row: UIConfig,
    your_version: Optional[int],
    message: str,
) -> dict[str, Any]:
    latest_published = await _latest_ui_config(
        session,
        config_type=row.config_type,
        segment=row.segment,
        scope=row.scope,
        scope_id=row.scope_id,
        status="published",
    )
    current_version = row.version
    last_published_by = latest_published.created_by_email if latest_published else None
    last_published_at = latest_published.published_at.isoformat() if latest_published and latest_published.published_at else None

    if latest_published:
        actor_email, actor_at = await _latest_publish_actor(
            session,
            config_type=row.config_type,
            resource_id=str(latest_published.id),
        )
        if actor_email:
            last_published_by = actor_email
        if actor_at:
            last_published_at = actor_at
        current_version = max(current_version, latest_published.version)

    return {
        "code": PUBLISH_ERROR_CONFIG_VERSION_CONFLICT,
        "message": message,
        "current_version": current_version,
        "your_version": your_version,
        "last_published_by": last_published_by,
        "last_published_at": last_published_at,
        "hint": "Sayfayı yenileyin ve diff ekranını tekrar kontrol edin",
    }


async def _validate_publish_version_or_raise(
    session: AsyncSession,
    *,
    row: UIConfig,
    config_version: Optional[int],
) -> None:
    if config_version is None:
        raise _publish_http_error(
            code=PUBLISH_ERROR_MISSING_CONFIG_VERSION,
            message="config_version zorunludur",
            status_code=400,
            extras={"hint": "Sayfayı yenileyin ve tekrar deneyin"},
        )

    your_version = int(config_version)
    if your_version != int(row.version):
        conflict = await _build_publish_conflict_payload(
            session,
            row=row,
            your_version=your_version,
            message="config_version güncel değil",
        )
        raise HTTPException(status_code=409, detail=conflict)


def _validate_publish_hash_or_raise(row: UIConfig, resolved_config_hash: Optional[str]) -> None:
    if not resolved_config_hash:
        return
    current_hash = _serialize_ui_config(row).get("resolved_config_hash")
    if current_hash != resolved_config_hash:
        raise _publish_http_error(
            code=PUBLISH_ERROR_CONFIG_HASH_MISMATCH,
            message="Config hash mismatch",
            status_code=409,
            extras={
                "current_hash": current_hash,
                "your_hash": resolved_config_hash,
                "hint": "Latest draft ile diff ekranını yeniden açın",
            },
        )

    if row.status != "draft":
        conflict = await _build_publish_conflict_payload(
            session,
            row=row,
            your_version=your_version,
            message="Bu versiyon artık draft değil; başka bir admin publish etmiş olabilir",
        )
        raise HTTPException(status_code=409, detail=conflict)

    latest_draft = await _latest_ui_config(
        session,
        config_type=row.config_type,
        segment=row.segment,
        scope=row.scope,
        scope_id=row.scope_id,
        status="draft",
    )
    if latest_draft and latest_draft.id != row.id:
        conflict = await _build_publish_conflict_payload(
            session,
            row=latest_draft,
            your_version=your_version,
            message="Daha güncel bir draft versiyonu mevcut",
        )
        raise HTTPException(status_code=409, detail=conflict)


async def _next_ui_config_version(
    session: AsyncSession,
    *,
    config_type: str,
    segment: str,
    scope: str,
    scope_id: Optional[str],
) -> int:
    stmt = select(func.max(UIConfig.version)).where(
        UIConfig.config_type == config_type,
        UIConfig.segment == segment,
        UIConfig.scope == scope,
    )
    if scope == "system":
        stmt = stmt.where(or_(UIConfig.scope_id.is_(None), UIConfig.scope_id == ""))
    else:
        stmt = stmt.where(UIConfig.scope_id == scope_id)
    latest_version = (await session.execute(stmt)).scalar_one_or_none() or 0
    return int(latest_version) + 1


async def _latest_ui_config(
    session: AsyncSession,
    *,
    config_type: str,
    segment: str,
    scope: str,
    scope_id: Optional[str],
    status: Optional[str],
) -> Optional[UIConfig]:
    stmt = (
        select(UIConfig)
        .where(UIConfig.config_type == config_type, UIConfig.segment == segment, *_scope_clause(scope, scope_id))
        .order_by(desc(UIConfig.version), desc(UIConfig.updated_at))
        .limit(1)
    )
    if status:
        stmt = stmt.where(UIConfig.status == status)
    return (await session.execute(stmt)).scalar_one_or_none()


async def _resolve_effective_ui_config(
    session: AsyncSession,
    *,
    config_type: str,
    segment: str,
    tenant_id: Optional[str],
    user_id: Optional[str],
) -> tuple[Optional[UIConfig], str, Optional[str]]:
    chain = [("user", user_id), ("tenant", tenant_id), ("system", None)]
    for scope, scope_id in chain:
        if scope in {"tenant", "user"} and not scope_id:
            continue
        row = await _latest_ui_config(
            session,
            config_type=config_type,
            segment=segment,
            scope=scope,
            scope_id=scope_id,
            status="published",
        )
        if row:
            return row, scope, scope_id
    return None, "default", None


def _effective_config_data(row: Optional[UIConfig], config_type: str, segment: str) -> dict[str, Any]:
    if row and isinstance(row.config_data, dict):
        if config_type == "header":
            return _normalize_header_config_data(row.config_data, segment)
        if config_type == "dashboard":
            layout_value, widgets_value, config_data = _extract_dashboard_layout_widgets(
                layout_payload=row.layout,
                widgets_payload=row.widgets,
                config_data=row.config_data,
            )
            return {
                **config_data,
                "layout": layout_value,
                "widgets": widgets_value,
            }
        return row.config_data
    if config_type == "header":
        return _default_header_config(segment)
    if config_type == "dashboard":
        return {"layout": [], "widgets": []}
    return {}


async def _set_ui_config_scope_to_draft(
    session: AsyncSession,
    *,
    config_type: str,
    segment: str,
    scope: str,
    scope_id: Optional[str],
) -> None:
    stmt = update(UIConfig).where(
        UIConfig.config_type == config_type,
        UIConfig.segment == segment,
        *_scope_clause(scope, scope_id),
        UIConfig.status == "published",
    )
    await session.execute(stmt.values(status="draft", updated_at=datetime.now(timezone.utc)))


def _validate_ui_config_before_publish(row: UIConfig) -> None:
    if row.config_type == "header":
        row.config_data = _normalize_header_config_data(row.config_data or {}, row.segment)
        if row.segment == "corporate":
            _validate_corporate_header_guardrails(row.config_data)
        return

    if row.config_type == "dashboard":
        normalized_layout, normalized_widgets, next_config_data = _extract_dashboard_layout_widgets(
            layout_payload=row.layout,
            widgets_payload=row.widgets,
            config_data=row.config_data if isinstance(row.config_data, dict) else {},
        )
        _validate_dashboard_guardrails(normalized_layout, normalized_widgets)
        row.layout = normalized_layout
        row.widgets = normalized_widgets
        row.config_data = next_config_data


async def _publish_ui_config_row(
    session: AsyncSession,
    *,
    row: UIConfig,
    current_user: dict[str, Any],
    reason: Optional[str] = None,
) -> tuple[UIConfig, dict[str, Any], Optional[dict[str, Any]], dict[str, Any]]:
    _validate_ui_config_before_publish(row)

    previous_published = await _latest_ui_config(
        session,
        config_type=row.config_type,
        segment=row.segment,
        scope=row.scope,
        scope_id=row.scope_id,
        status="published",
    )
    previous_payload = _serialize_ui_config(previous_published) if previous_published else None
    next_payload = _serialize_ui_config(row)

    diff_payload = _compute_ui_config_diff(
        config_type=row.config_type,
        segment=row.segment,
        old_payload=previous_payload,
        new_payload=next_payload,
    )

    await _set_ui_config_scope_to_draft(
        session,
        config_type=row.config_type,
        segment=row.segment,
        scope=row.scope,
        scope_id=row.scope_id,
    )

    now_dt = datetime.now(timezone.utc)
    row.status = "published"
    row.published_at = now_dt
    row.updated_at = now_dt
    snapshot_payload = _build_ui_publish_snapshot(row)

    session.add(
        _create_ui_config_audit_log(
            action="ui_config_publish",
            current_user=current_user,
            config_type=row.config_type,
            resource_id=str(row.id),
            old_values=previous_payload,
            new_values=next_payload,
            metadata_info={
                "segment": row.segment,
                "scope": row.scope,
                "scope_id": row.scope_id,
                "version": row.version,
                "diff": diff_payload,
                "reason": reason or "manual_publish",
                "snapshot": snapshot_payload,
            },
        )
    )

    await session.commit()
    await session.refresh(row)
    return row, diff_payload, previous_payload, snapshot_payload


async def _resolve_effective_theme(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    user_id: Optional[str],
) -> tuple[Optional[UITheme], str, Optional[str], Optional[UIThemeAssignment], dict[str, Any]]:
    del user_id

    global_assignment = (
        await session.execute(
            select(UIThemeAssignment)
            .where(*_theme_scope_clause("system", None))
            .order_by(desc(UIThemeAssignment.updated_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    global_theme = await session.get(UITheme, global_assignment.theme_id) if global_assignment else None
    if global_theme is None:
        global_theme = (
            await session.execute(select(UITheme).where(UITheme.is_active.is_(True)).order_by(desc(UITheme.updated_at)).limit(1))
        ).scalar_one_or_none()

    tenant_assignment = None
    tenant_theme = None
    if tenant_id:
        tenant_assignment = (
            await session.execute(
                select(UIThemeAssignment)
                .where(*_theme_scope_clause("tenant", tenant_id))
                .order_by(desc(UIThemeAssignment.updated_at))
                .limit(1)
            )
        ).scalar_one_or_none()
        tenant_theme = await session.get(UITheme, tenant_assignment.theme_id) if tenant_assignment else None

    if tenant_theme and global_theme:
        resolved_tokens = _deep_merge_tokens(global_theme.tokens or {}, tenant_theme.tokens or {})
        resolution = {
            "mode": "dealer_override_over_global",
            "global_theme_id": str(global_theme.id),
            "dealer_theme_id": str(tenant_theme.id),
            "resolved_config_hash": _stable_hash_payload(resolved_tokens),
        }
        return tenant_theme, "tenant", tenant_id, tenant_assignment, {
            "tokens": resolved_tokens,
            "resolution": resolution,
            "global_theme": global_theme,
            "dealer_theme": tenant_theme,
        }

    if tenant_theme and not global_theme:
        resolution = {
            "mode": "dealer_only_fallback",
            "global_theme_id": None,
            "dealer_theme_id": str(tenant_theme.id),
            "resolved_config_hash": _stable_hash_payload(tenant_theme.tokens or {}),
        }
        return tenant_theme, "tenant", tenant_id, tenant_assignment, {
            "tokens": tenant_theme.tokens or {},
            "resolution": resolution,
            "global_theme": None,
            "dealer_theme": tenant_theme,
        }

    if global_theme:
        resolution = {
            "mode": "global_theme",
            "global_theme_id": str(global_theme.id),
            "dealer_theme_id": None,
            "resolved_config_hash": _stable_hash_payload(global_theme.tokens or {}),
        }
        return global_theme, "system", None, global_assignment, {
            "tokens": global_theme.tokens or {},
            "resolution": resolution,
            "global_theme": global_theme,
            "dealer_theme": None,
        }

    return None, "active_fallback", None, None, {
        "tokens": {},
        "resolution": {
            "mode": "empty",
            "global_theme_id": None,
            "dealer_theme_id": None,
            "resolved_config_hash": _stable_hash_payload({}),
        },
        "global_theme": None,
        "dealer_theme": None,
    }


@router.get("/admin/ui/permissions")
async def get_ui_designer_permissions(current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION))):
    return {
        "permission": ADMIN_UI_DESIGNER_PERMISSION,
        "roles": PERMISSION_ROLE_MAP.get(ADMIN_UI_DESIGNER_PERMISSION, []),
        "enabled": True,
    }


@router.get("/admin/ui/configs/{config_type}")
async def admin_get_ui_config(
    config_type: str,
    segment: str = Query(default="individual"),
    scope: str = Query(default="system"),
    scope_id: Optional[str] = Query(default=None),
    status: str = Query(default="draft"),
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(scope, scope_id)
    normalized_status = _normalize_status(status)

    current = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status=normalized_status,
    )
    versions_stmt = (
        select(UIConfig)
        .where(
            UIConfig.config_type == normalized_type,
            UIConfig.segment == normalized_segment,
            *_scope_clause(normalized_scope, normalized_scope_id),
        )
        .order_by(desc(UIConfig.version), desc(UIConfig.updated_at))
        .limit(100)
    )
    versions = (await session.execute(versions_stmt)).scalars().all()
    current_payload = _serialize_ui_config(current) if current else None
    if current_payload and normalized_type == "header":
        current_payload["config_data"] = _normalize_header_config_data(current_payload.get("config_data") or {}, normalized_segment)

    version_payloads = [_serialize_ui_config(item) for item in versions]
    if normalized_type == "header":
        for item in version_payloads:
            item["config_data"] = _normalize_header_config_data(item.get("config_data") or {}, normalized_segment)

    return {
        "item": current_payload,
        "items": version_payloads,
    }


@router.post("/admin/ui/configs/{config_type}")
async def admin_save_ui_config(
    config_type: str,
    payload: UIConfigSavePayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(payload.segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(payload.scope, payload.scope_id)
    normalized_status = _normalize_status(payload.status)
    normalized_config_data = payload.config_data or {}
    normalized_layout: list[dict[str, Any]] = []
    normalized_widgets: list[dict[str, Any]] = []

    if normalized_type == "header":
        normalized_config_data = _normalize_header_config_data(normalized_config_data, normalized_segment)
        if normalized_segment == "corporate":
            _validate_corporate_header_guardrails(normalized_config_data)
    elif normalized_type == "dashboard":
        normalized_layout, normalized_widgets, normalized_config_data = _extract_dashboard_layout_widgets(
            layout_payload=payload.layout,
            widgets_payload=payload.widgets,
            config_data=normalized_config_data,
        )
        _validate_dashboard_guardrails(normalized_layout, normalized_widgets)

    previous_draft = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="draft",
    )

    next_version = await _next_ui_config_version(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
    )
    now_dt = datetime.now(timezone.utc)

    row = UIConfig(
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status=normalized_status,
        version=next_version,
        config_data=normalized_config_data,
        layout=normalized_layout,
        widgets=normalized_widgets,
        created_by=_safe_uuid(current_user.get("id")),
        created_by_email=current_user.get("email"),
        published_at=now_dt if normalized_status == "published" else None,
    )
    if normalized_status == "published":
        await _set_ui_config_scope_to_draft(
            session,
            config_type=normalized_type,
            segment=normalized_segment,
            scope=normalized_scope,
            scope_id=normalized_scope_id,
        )

    if normalized_status == "draft":
        owner_type, owner_id = _owner_scope_from_scope(normalized_scope, normalized_scope_id)
        session.add(
            _create_ui_config_audit_log(
                action="DRAFT_UPDATED",
                current_user=current_user,
                config_type=normalized_type,
                resource_id=str(row.id),
                old_values=None,
                new_values=None,
                metadata_info={
                    "actor_id": current_user.get("id"),
                    "owner_type": owner_type,
                    "owner_id": owner_id,
                    "previous_version": previous_draft.version if previous_draft else None,
                    "new_version": row.version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        )

    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"ok": True, "item": _serialize_ui_config(row)}


@router.post("/admin/ui/configs/{config_type}/publish/{config_id}", deprecated=True)
async def admin_publish_ui_config(
    config_type: str,
    config_id: str,
    payload: Optional[UIConfigLegacyPublishPayload] = None,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    try:
        config_uuid = uuid.UUID(config_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid config id") from exc

    row = await session.get(UIConfig, config_uuid)
    if not row or row.config_type != normalized_type:
        raise HTTPException(status_code=404, detail="UI config not found")
    _assert_header_segment_enabled(row.config_type, row.segment)

    your_version = payload.config_version if payload else None
    retry_count = int(max(0, (payload.retry_count if payload else 0) or 0))
    try:
        await _validate_publish_version_or_raise(
            session,
            row=row,
            config_version=your_version,
        )
        _validate_publish_hash_or_raise(row, payload.resolved_config_hash if payload else None)
        if row.config_type == "header":
            _validate_owner_scope_or_raise(row, payload.owner_type if payload else None, payload.owner_id if payload else None)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        await _record_publish_attempt_audit(
            session,
            current_user=current_user,
            config_type=row.config_type,
            segment=row.segment,
            scope=row.scope,
            scope_id=row.scope_id,
            config_id=str(row.id),
            config_version=your_version,
            retry_count=retry_count,
            conflict_detected=exc.status_code == 409,
            lock_wait_ms=0,
            publish_duration_ms=None,
            status="validation_error",
            detail_message=detail.get("message") or "Publish validation error",
            extra={"code": detail.get("code")},
            commit_now=True,
        )
        raise

    lock_key = _publish_scope_key(
        config_type=row.config_type,
        segment=row.segment,
        scope=row.scope,
        scope_id=row.scope_id,
    )
    lock_start = time.perf_counter()
    try:
        await _acquire_publish_lock_or_raise(lock_key, current_user)
    except HTTPException as exc:
        lock_wait_ms = int((time.perf_counter() - lock_start) * 1000)
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        await _record_publish_attempt_audit(
            session,
            current_user=current_user,
            config_type=row.config_type,
            segment=row.segment,
            scope=row.scope,
            scope_id=row.scope_id,
            config_id=str(row.id),
            config_version=your_version,
            retry_count=retry_count,
            conflict_detected=True,
            lock_wait_ms=lock_wait_ms,
            publish_duration_ms=None,
            status="locked",
            detail_message=detail.get("message") or "Publish lock active",
            extra={"code": detail.get("code")},
            commit_now=True,
        )
        raise

    lock_wait_ms = int((time.perf_counter() - lock_start) * 1000)
    publish_start = time.perf_counter()
    try:
        published_row, diff_payload, previous_payload, snapshot_payload = await _publish_ui_config_row(
            session,
            row=row,
            current_user=current_user,
            reason="publish_by_config_id_legacy",
        )
    finally:
        await _release_publish_lock(lock_key)

    publish_duration_ms = int((time.perf_counter() - publish_start) * 1000)
    await _record_publish_attempt_audit(
        session,
        current_user=current_user,
        config_type=published_row.config_type,
        segment=published_row.segment,
        scope=published_row.scope,
        scope_id=published_row.scope_id,
        config_id=str(published_row.id),
        config_version=published_row.version,
        retry_count=retry_count,
        conflict_detected=False,
        lock_wait_ms=lock_wait_ms,
        publish_duration_ms=publish_duration_ms,
        status="success",
        detail_message="Publish success",
        extra={"deprecated_endpoint": True},
        commit_now=True,
    )

    return {
        "ok": True,
        "item": _serialize_ui_config(published_row),
        "snapshot": {
            "published_config_id": str(published_row.id),
            "published_version": published_row.version,
            **snapshot_payload,
        },
        "diff": diff_payload,
        "previous": previous_payload,
        "deprecated_endpoint": True,
        "deprecation_note": "Bu endpoint deprecated. Kaldırma planı: P2. Yeni endpoint: /api/admin/ui/configs/{config_type}/publish",
    }


@router.get("/admin/ui/configs/{config_type}/diff")
async def admin_ui_config_diff(
    config_type: str,
    segment: str = Query(default="individual"),
    scope: str = Query(default="system"),
    scope_id: Optional[str] = Query(default=None),
    from_status: str = Query(default="published"),
    to_status: str = Query(default="draft"),
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    del current_user
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(scope, scope_id)
    normalized_from_status = _normalize_status(from_status)
    normalized_to_status = _normalize_status(to_status)

    from_row = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status=normalized_from_status,
    )
    to_row = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status=normalized_to_status,
    )

    from_payload = _serialize_ui_config(from_row) if from_row else None
    to_payload = _serialize_ui_config(to_row) if to_row else None
    diff_payload = _compute_ui_config_diff(
        config_type=normalized_type,
        segment=normalized_segment,
        old_payload=from_payload,
        new_payload=to_payload,
    )

    return {
        "config_type": normalized_type,
        "segment": normalized_segment,
        "scope": normalized_scope,
        "scope_id": normalized_scope_id,
        "from_status": normalized_from_status,
        "to_status": normalized_to_status,
        "from_item": from_payload,
        "to_item": to_payload,
        "diff": diff_payload,
    }


@router.post("/admin/ui/configs/{config_type}/conflict-sync")
async def admin_ui_config_conflict_sync(
    config_type: str,
    payload: UIConfigConflictSyncPayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(payload.segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(payload.scope, payload.scope_id)

    latest_draft = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="draft",
    )
    latest_published = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="published",
    )
    if not latest_draft:
        raise HTTPException(status_code=404, detail="Senkron için draft config bulunamadı")

    from_payload = _serialize_ui_config(latest_published) if latest_published else None
    to_payload = _serialize_ui_config(latest_draft)
    diff_payload = _compute_ui_config_diff(
        config_type=normalized_type,
        segment=normalized_segment,
        old_payload=from_payload,
        new_payload=to_payload,
    )

    owner_type, owner_id = _owner_scope_from_scope(normalized_scope, normalized_scope_id)
    session.add(
        _create_ui_config_audit_log(
            action="DRAFT_SYNCED_AFTER_CONFLICT",
            current_user=current_user,
            config_type=normalized_type,
            resource_id=str(latest_draft.id),
            old_values=None,
            new_values=None,
            metadata_info={
                "actor_id": current_user.get("id"),
                "owner_type": owner_type,
                "owner_id": owner_id,
                "previous_version": payload.previous_version,
                "new_version": latest_draft.version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": int(max(0, payload.retry_count or 0)),
            },
        )
    )
    await session.commit()

    listing = await _ui_config_listing(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="draft",
    )
    return {
        "ok": True,
        "item": listing.get("item"),
        "items": listing.get("items", []),
        "from_item": from_payload,
        "to_item": to_payload,
        "diff": diff_payload,
    }


@router.get("/admin/ui/configs/{config_type}/publish-audits")
async def admin_ui_publish_audits(
    config_type: str,
    segment: str = Query(default="individual"),
    scope: str = Query(default="system"),
    scope_id: Optional[str] = Query(default=None),
    limit: int = Query(default=30, ge=1, le=200),
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    del current_user
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(scope, scope_id)

    stmt = (
        select(AuditLog)
        .where(
            AuditLog.action == "ui_config_publish_attempt",
            AuditLog.resource_type == f"ui_config:{normalized_type}",
        )
        .order_by(desc(AuditLog.created_at))
        .limit(500)
    )
    rows = (await session.execute(stmt)).scalars().all()

    filtered = []
    for row in rows:
        metadata = row.metadata_info or {}
        if metadata.get("segment") != normalized_segment:
            continue
        if metadata.get("scope") != normalized_scope:
            continue
        if normalized_scope == "system":
            if (metadata.get("scope_id") or None) not in {None, ""}:
                continue
        elif metadata.get("scope_id") != normalized_scope_id:
            continue
        filtered.append(row)
        if len(filtered) >= limit:
            break

    items = []
    lock_values: list[int] = []
    publish_values: list[int] = []
    for row in filtered:
        metadata = row.metadata_info or {}
        lock_ms = int(metadata.get("lock_wait_ms") or 0)
        publish_ms = metadata.get("publish_duration_ms")
        if lock_ms >= 0:
            lock_values.append(lock_ms)
        if isinstance(publish_ms, int) and publish_ms >= 0:
            publish_values.append(publish_ms)

        items.append(
            {
                "id": str(row.id),
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "actor_email": row.user_email,
                "status": metadata.get("status"),
                "message": metadata.get("message"),
                "conflict_detected": bool(metadata.get("conflict_detected", False)),
                "retry_count": int(metadata.get("retry_count") or 0),
                "lock_wait_ms": lock_ms,
                "publish_duration_ms": publish_ms,
                "config_version": metadata.get("config_version"),
            }
        )

    telemetry = {
        "avg_lock_wait_ms": round(sum(lock_values) / len(lock_values), 2) if lock_values else 0,
        "max_lock_wait_ms": max(lock_values) if lock_values else 0,
        "avg_publish_duration_ms": round(sum(publish_values) / len(publish_values), 2) if publish_values else 0,
        "max_publish_duration_ms": max(publish_values) if publish_values else 0,
    }

    return {
        "items": items,
        "telemetry": telemetry,
    }


@router.post("/admin/ui/configs/{config_type}/publish")
async def admin_publish_latest_ui_config(
    config_type: str,
    payload: UIConfigPublishPayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(payload.segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(payload.scope, payload.scope_id)

    if not payload.require_confirm:
        raise HTTPException(status_code=400, detail="Publish onayı zorunludur (require_confirm=true)")

    target_row: Optional[UIConfig] = None
    if payload.config_id:
        try:
            config_uuid = uuid.UUID(payload.config_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid config_id") from exc

        row = await session.get(UIConfig, config_uuid)
        if not row or row.config_type != normalized_type:
            raise HTTPException(status_code=404, detail="UI config not found")
        if row.segment != normalized_segment:
            raise HTTPException(status_code=400, detail="config segment uyuşmuyor")
        if row.scope != normalized_scope:
            raise HTTPException(status_code=400, detail="config scope uyuşmuyor")
        if normalized_scope != "system" and row.scope_id != normalized_scope_id:
            raise HTTPException(status_code=400, detail="config scope_id uyuşmuyor")
        if normalized_scope == "system" and (row.scope_id or "") not in {"", None}:
            raise HTTPException(status_code=400, detail="config system scope ile uyumlu değil")
        target_row = row
    else:
        target_row = await _latest_ui_config(
            session,
            config_type=normalized_type,
            segment=normalized_segment,
            scope=normalized_scope,
            scope_id=normalized_scope_id,
            status="draft",
        )

    if not target_row:
        raise HTTPException(status_code=404, detail="Yayınlanacak draft config bulunamadı")

    retry_count = int(max(0, payload.retry_count or 0))
    try:
        await _validate_publish_version_or_raise(
            session,
            row=target_row,
            config_version=payload.config_version,
        )
        _validate_publish_hash_or_raise(target_row, payload.resolved_config_hash)
        if target_row.config_type == "header":
            _validate_owner_scope_or_raise(target_row, payload.owner_type, payload.owner_id)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        await _record_publish_attempt_audit(
            session,
            current_user=current_user,
            config_type=target_row.config_type,
            segment=target_row.segment,
            scope=target_row.scope,
            scope_id=target_row.scope_id,
            config_id=str(target_row.id),
            config_version=payload.config_version,
            retry_count=retry_count,
            conflict_detected=exc.status_code == 409,
            lock_wait_ms=0,
            publish_duration_ms=None,
            status="validation_error",
            detail_message=detail.get("message") or "Publish validation error",
            extra={"code": detail.get("code")},
            commit_now=True,
        )
        raise

    lock_key = _publish_scope_key(
        config_type=target_row.config_type,
        segment=target_row.segment,
        scope=target_row.scope,
        scope_id=target_row.scope_id,
    )
    lock_start = time.perf_counter()
    try:
        await _acquire_publish_lock_or_raise(lock_key, current_user)
    except HTTPException as exc:
        lock_wait_ms = int((time.perf_counter() - lock_start) * 1000)
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        await _record_publish_attempt_audit(
            session,
            current_user=current_user,
            config_type=target_row.config_type,
            segment=target_row.segment,
            scope=target_row.scope,
            scope_id=target_row.scope_id,
            config_id=str(target_row.id),
            config_version=payload.config_version,
            retry_count=retry_count,
            conflict_detected=True,
            lock_wait_ms=lock_wait_ms,
            publish_duration_ms=None,
            status="locked",
            detail_message=detail.get("message") or "Publish lock active",
            extra={"code": detail.get("code")},
            commit_now=True,
        )
        raise

    lock_wait_ms = int((time.perf_counter() - lock_start) * 1000)
    publish_start = time.perf_counter()
    try:
        published_row, diff_payload, previous_payload, snapshot_payload = await _publish_ui_config_row(
            session,
            row=target_row,
            current_user=current_user,
            reason="publish_latest_endpoint",
        )
    finally:
        await _release_publish_lock(lock_key)

    publish_duration_ms = int((time.perf_counter() - publish_start) * 1000)
    await _record_publish_attempt_audit(
        session,
        current_user=current_user,
        config_type=published_row.config_type,
        segment=published_row.segment,
        scope=published_row.scope,
        scope_id=published_row.scope_id,
        config_id=str(published_row.id),
        config_version=published_row.version,
        retry_count=retry_count,
        conflict_detected=False,
        lock_wait_ms=lock_wait_ms,
        publish_duration_ms=publish_duration_ms,
        status="success",
        detail_message="Publish success",
        extra=None,
        commit_now=True,
    )

    return {
        "ok": True,
        "item": _serialize_ui_config(published_row),
        "snapshot": {
            "published_config_id": str(published_row.id),
            "published_version": published_row.version,
            **snapshot_payload,
        },
        "diff": diff_payload,
        "previous": previous_payload,
    }


@router.post("/admin/ui/configs/{config_type}/rollback")
async def admin_rollback_ui_config(
    config_type: str,
    payload: UIConfigRollbackPayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(payload.segment)
    _assert_header_segment_enabled(normalized_type, normalized_segment)
    normalized_scope, normalized_scope_id = _normalize_scope(payload.scope, payload.scope_id)

    if not payload.require_confirm:
        raise HTTPException(status_code=400, detail="Rollback onayı zorunludur (require_confirm=true)")

    rollback_reason = (payload.rollback_reason or "").strip()
    if not rollback_reason:
        raise _publish_http_error(
            code=ROLLBACK_ERROR_MISSING_REASON,
            message="rollback_reason zorunludur",
            status_code=400,
            extras={"hint": "Rollback sebebini girip tekrar deneyin"},
        )

    current_published = await _latest_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="published",
    )
    if not current_published:
        raise HTTPException(status_code=404, detail="Rollback için aktif published config bulunamadı")

    target_row: Optional[UIConfig] = None
    if payload.target_config_id:
        try:
            target_uuid = uuid.UUID(payload.target_config_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid target_config_id") from exc

        row = await session.get(UIConfig, target_uuid)
        if not row or row.config_type != normalized_type:
            raise HTTPException(status_code=404, detail="Rollback target config bulunamadı")
        if row.id == current_published.id:
            raise HTTPException(status_code=400, detail="Rollback target mevcut published ile aynı olamaz")
        if row.segment != normalized_segment or row.scope != normalized_scope:
            raise HTTPException(status_code=400, detail="Rollback target scope/segment uyumsuz")
        if normalized_scope != "system" and row.scope_id != normalized_scope_id:
            raise HTTPException(status_code=400, detail="Rollback target scope_id uyumsuz")
        if normalized_scope == "system" and (row.scope_id or "") not in {"", None}:
            raise HTTPException(status_code=400, detail="Rollback target system scope değil")
        target_row = row
    else:
        target_stmt = (
            select(UIConfig)
            .where(
                UIConfig.config_type == normalized_type,
                UIConfig.segment == normalized_segment,
                *_scope_clause(normalized_scope, normalized_scope_id),
                UIConfig.status == "published",
                UIConfig.id != current_published.id,
            )
            .order_by(desc(UIConfig.version), desc(UIConfig.updated_at))
            .limit(1)
        )
        target_row = (await session.execute(target_stmt)).scalar_one_or_none()

    if not target_row:
        raise HTTPException(status_code=404, detail="Rollback target snapshot bulunamadı")

    _validate_ui_config_before_publish(target_row)

    current_payload = _serialize_ui_config(current_published)
    target_payload = _serialize_ui_config(target_row)
    diff_payload = _compute_ui_config_diff(
        config_type=normalized_type,
        segment=normalized_segment,
        old_payload=current_payload,
        new_payload=target_payload,
    )

    await _set_ui_config_scope_to_draft(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
    )

    now_dt = datetime.now(timezone.utc)
    target_row.status = "published"
    target_row.published_at = now_dt
    target_row.updated_at = now_dt

    session.add(
        _create_ui_config_audit_log(
            action="ui_config_rollback",
            current_user=current_user,
            config_type=normalized_type,
            resource_id=str(target_row.id),
            old_values=current_payload,
            new_values=target_payload,
            metadata_info={
                "segment": normalized_segment,
                "scope": normalized_scope,
                "scope_id": normalized_scope_id,
                "from_config_id": str(current_published.id),
                "to_config_id": str(target_row.id),
                "diff": diff_payload,
                "rollback_reason": rollback_reason,
            },
        )
    )

    await session.commit()
    await session.refresh(target_row)

    return {
        "ok": True,
        "item": _serialize_ui_config(target_row),
        "rolled_back_from": str(current_published.id),
        "rolled_back_to": str(target_row.id),
        "rollback_reason": rollback_reason,
        "diff": diff_payload,
    }


@router.post("/admin/ui/configs/header/logo")
async def admin_upload_header_logo(
    file: UploadFile = File(...),
    segment: str = Form(default="corporate"),
    scope: str = Form(default="system"),
    scope_id: Optional[str] = Form(default=None),
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    normalized_segment = _normalize_segment(segment)
    _assert_header_segment_enabled("header", normalized_segment)
    if normalized_segment != "corporate":
        raise HTTPException(status_code=400, detail="Logo upload bu sprintte sadece corporate segment için açık")
    normalized_scope, normalized_scope_id = _normalize_scope(scope, scope_id)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Dosya boş")

    logo_meta = _validate_logo_constraints(data, file.filename or "")
    storage_health = _site_assets_storage_health()
    if not storage_health.get("writable"):
        raise _logo_upload_http_error(
            code=LOGO_ERROR_STORAGE_PIPELINE,
            message="Storage yazma hattı hazır değil",
            status_code=500,
            details={"storage_health": storage_health},
        )

    try:
        asset_key, _ = store_site_asset(data, file.filename or "logo.webp", folder="ui/logos", allow_svg=True)
    except ValueError as exc:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_INVALID_FILE_TYPE,
            message=str(exc),
            details={"expected": sorted(UI_LOGO_ALLOWED_EXTENSIONS)},
        ) from exc
    except Exception as exc:
        raise _logo_upload_http_error(
            code=LOGO_ERROR_STORAGE_PIPELINE,
            message="Logo dosyası storage pipeline üzerinde yazılamadı",
            status_code=500,
            details={"storage_health": _site_assets_storage_health()},
        ) from exc

    logo_url = f"{UI_LOGO_URL_PREFIX}{asset_key}"

    base_row = await _latest_ui_config(
        session,
        config_type="header",
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="draft",
    )
    if not base_row:
        base_row = await _latest_ui_config(
            session,
            config_type="header",
            segment=normalized_segment,
            scope=normalized_scope,
            scope_id=normalized_scope_id,
            status="published",
        )

    base_config = deepcopy(base_row.config_data) if base_row and isinstance(base_row.config_data, dict) else _default_header_config(normalized_segment)
    old_logo_url = _extract_header_logo_url(base_config)
    next_config = _apply_header_logo_to_config(base_config, logo_url, logo_meta)
    _validate_corporate_header_guardrails(next_config)

    next_version = await _next_ui_config_version(
        session,
        config_type="header",
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
    )
    new_row = UIConfig(
        config_type="header",
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        status="draft",
        version=next_version,
        config_data=next_config,
        created_by=_safe_uuid(current_user.get("id")),
        created_by_email=current_user.get("email"),
        published_at=None,
    )
    session.add(new_row)

    await _upsert_logo_asset_row(
        session,
        asset_key=asset_key,
        asset_url=logo_url,
        segment=normalized_segment,
        scope=normalized_scope,
        scope_id=normalized_scope_id,
        current_user=current_user,
    )
    await _mark_replaced_logo_if_exists(session, old_logo_url=old_logo_url, new_asset_key=asset_key)

    await session.commit()
    await session.refresh(new_row)

    if background_tasks is not None:
        background_tasks.add_task(_cleanup_replaced_logo_assets, 100)

    item_payload = _serialize_ui_config(new_row)
    item_payload["config_data"] = _normalize_header_config_data(item_payload.get("config_data") or {}, normalized_segment)
    return {
        "ok": True,
        "logo_url": logo_url,
        "logo_meta": logo_meta,
        "storage_health": _site_assets_storage_health(),
        "item": item_payload,
        "cleanup": {"scheduled": True, "retention_days": UI_LOGO_RETENTION_DAYS},
    }


@router.post("/admin/ui/logo-assets/cleanup")
async def admin_cleanup_logo_assets(
    limit: int = Query(default=100, ge=1, le=500),
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    result = await _cleanup_replaced_logo_assets(limit)
    pending_stmt = select(func.count()).select_from(UILogoAsset).where(
        UILogoAsset.is_replaced.is_(True),
        UILogoAsset.is_deleted.is_(False),
    )
    pending_count = (await session.execute(pending_stmt)).scalar_one() or 0
    return {
        "ok": True,
        "deleted": result.get("deleted", 0),
        "skipped": result.get("skipped", 0),
        "pending": int(pending_count),
        "retention_days": UI_LOGO_RETENTION_DAYS,
    }


@router.get("/admin/ui/logo-assets/health")
async def admin_logo_assets_health(
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
):
    del current_user
    storage_health = _site_assets_storage_health()
    return {
        "ok": bool(storage_health.get("writable")),
        "storage_health": storage_health,
    }


@router.get("/ui/{config_type}")
async def get_effective_ui_config(
    config_type: str,
    segment: str = Query(default="individual"),
    tenant_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(segment)

    if normalized_type == "header" and normalized_segment == "individual":
        static_header = _default_header_config("individual")
        return {
            "config_type": normalized_type,
            "segment": normalized_segment,
            "source_scope": "public_default",
            "source_scope_id": None,
            "item": None,
            "config_data": static_header,
            "layout": [],
            "widgets": [],
            "feature_mode": "public_header_static",
        }

    if normalized_type == "header" and normalized_segment == "corporate":
        if not current_user or current_user.get("portal_scope") != "dealer":
            raise _ui_http_error(
                code=UI_ERROR_UNAUTHORIZED_SCOPE,
                message="Kurumsal header config erişimi sadece dealer oturumunda mümkündür",
                status_code=403,
                extras={"required_scope": "dealer"},
            )

    row, source_scope, source_scope_id = await _resolve_effective_ui_config(
        session,
        config_type=normalized_type,
        segment=normalized_segment,
        tenant_id=(tenant_id or "").strip() or None,
        user_id=(user_id or "").strip() or None,
    )
    serialized_item = _serialize_ui_config(row) if row else None
    if serialized_item and normalized_type == "header":
        serialized_item["config_data"] = _normalize_header_config_data(serialized_item.get("config_data") or {}, normalized_segment)

    effective_config = _effective_config_data(row, normalized_type, normalized_segment)
    effective_layout = effective_config.get("layout", []) if normalized_type == "dashboard" else []
    effective_widgets = effective_config.get("widgets", []) if normalized_type == "dashboard" else []
    return {
        "config_type": normalized_type,
        "segment": normalized_segment,
        "source_scope": source_scope,
        "source_scope_id": source_scope_id,
        "item": serialized_item,
        "config_data": effective_config,
        "layout": effective_layout,
        "widgets": effective_widgets,
    }


@router.get("/admin/ui/themes")
async def admin_list_ui_themes(
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    rows = (await session.execute(select(UITheme).order_by(desc(UITheme.updated_at)))).scalars().all()
    return {"items": [_serialize_ui_theme(row) for row in rows]}


@router.post("/admin/ui/themes")
async def admin_create_ui_theme(
    payload: UIThemeCreatePayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    _validate_theme_tokens(payload.tokens or {})
    if payload.is_active:
        await session.execute(update(UITheme).values(is_active=False, updated_at=datetime.now(timezone.utc)))

    row = UITheme(
        name=payload.name.strip(),
        tokens=payload.tokens or {},
        is_active=bool(payload.is_active),
        created_by=_safe_uuid(current_user.get("id")),
        created_by_email=current_user.get("email"),
    )
    session.add(row)
    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Theme name already exists") from exc
    await session.refresh(row)
    return {"ok": True, "item": _serialize_ui_theme(row)}


@router.get("/admin/ui/themes/{theme_id}")
async def admin_get_ui_theme(
    theme_id: str,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    try:
        theme_uuid = uuid.UUID(theme_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid theme id") from exc
    row = await session.get(UITheme, theme_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Theme not found")
    return {"item": _serialize_ui_theme(row)}


@router.patch("/admin/ui/themes/{theme_id}")
async def admin_update_ui_theme(
    theme_id: str,
    payload: UIThemeUpdatePayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    try:
        theme_uuid = uuid.UUID(theme_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid theme id") from exc

    row = await session.get(UITheme, theme_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Theme not found")

    payload_data = payload.model_dump(exclude_unset=True)
    if "name" in payload_data:
        row.name = payload_data["name"].strip()
    if "tokens" in payload_data and payload_data["tokens"] is not None:
        _validate_theme_tokens(payload_data["tokens"])
        row.tokens = payload_data["tokens"]
    if payload_data.get("is_active") is True:
        await session.execute(update(UITheme).where(UITheme.id != row.id).values(is_active=False, updated_at=datetime.now(timezone.utc)))
        row.is_active = True
    if payload_data.get("is_active") is False:
        row.is_active = False

    row.updated_at = datetime.now(timezone.utc)
    try:
        await session.commit()
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Theme name already exists") from exc
    await session.refresh(row)
    return {"ok": True, "item": _serialize_ui_theme(row)}


@router.delete("/admin/ui/themes/{theme_id}")
async def admin_delete_ui_theme(
    theme_id: str,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    try:
        theme_uuid = uuid.UUID(theme_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid theme id") from exc

    row = await session.get(UITheme, theme_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Theme not found")

    assignments = (await session.execute(select(UIThemeAssignment).where(UIThemeAssignment.theme_id == row.id))).scalars().all()
    for assignment in assignments:
        await session.delete(assignment)
    await session.delete(row)
    await session.commit()
    return {"ok": True}


@router.get("/admin/ui/theme-assignments")
async def admin_list_ui_theme_assignments(
    scope: Optional[str] = Query(default=None),
    scope_id: Optional[str] = Query(default=None),
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(UIThemeAssignment).order_by(desc(UIThemeAssignment.updated_at))
    if scope:
        normalized_scope, normalized_scope_id = _normalize_scope(scope, scope_id)
        stmt = stmt.where(*_theme_scope_clause(normalized_scope, normalized_scope_id))
    rows = (await session.execute(stmt)).scalars().all()
    return {"items": [_serialize_ui_theme_assignment(row) for row in rows]}


@router.post("/admin/ui/theme-assignments")
async def admin_assign_ui_theme(
    payload: UIThemeAssignmentPayload,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    try:
        theme_uuid = uuid.UUID(payload.theme_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid theme id") from exc

    theme = await session.get(UITheme, theme_uuid)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    normalized_scope, normalized_scope_id = _normalize_scope(payload.scope, payload.scope_id)
    _validate_theme_scope_v2_or_raise(normalized_scope)

    if normalized_scope == "tenant":
        global_assignment = (
            await session.execute(
                select(UIThemeAssignment)
                .where(*_theme_scope_clause("system", None))
                .order_by(desc(UIThemeAssignment.updated_at))
                .limit(1)
            )
        ).scalar_one_or_none()
        if not global_assignment:
            raise _ui_http_error(
                code=THEME_ERROR_INVALID_SCOPE,
                message="Dealer override için global theme ataması zorunludur",
                status_code=400,
                extras={"missing_dependency": "global_theme_assignment"},
            )

        global_theme = await session.get(UITheme, global_assignment.theme_id)
        if not global_theme:
            raise _ui_http_error(
                code=THEME_ERROR_INVALID_SCOPE,
                message="Dealer override için global theme bulunamadı",
                status_code=400,
                extras={"missing_dependency": "global_theme"},
            )

        global_paths = _flatten_token_paths(global_theme.tokens or {})
        override_paths = _flatten_token_paths(theme.tokens or {})
        invalid_paths = sorted(path for path in override_paths if path not in global_paths)
        if invalid_paths:
            raise _ui_http_error(
                code=THEME_ERROR_INVALID_SCOPE,
                message="Dealer override global theme dışında token alanı içeremez",
                status_code=400,
                extras={"invalid_override_paths": invalid_paths[:20]},
            )

    existing = (
        await session.execute(
            select(UIThemeAssignment)
            .where(*_theme_scope_clause(normalized_scope, normalized_scope_id))
            .order_by(desc(UIThemeAssignment.updated_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    if existing:
        existing.theme_id = theme.id
        existing.assigned_by = _safe_uuid(current_user.get("id"))
        existing.assigned_by_email = current_user.get("email")
        existing.updated_at = datetime.now(timezone.utc)
        row = existing
    else:
        row = UIThemeAssignment(
            theme_id=theme.id,
            scope=normalized_scope,
            scope_id=normalized_scope_id,
            assigned_by=_safe_uuid(current_user.get("id")),
            assigned_by_email=current_user.get("email"),
        )
        session.add(row)

    await session.commit()
    await session.refresh(row)
    _, _, _, _, resolved = await _resolve_effective_theme(
        session,
        tenant_id=normalized_scope_id if normalized_scope == "tenant" else None,
        user_id=None,
    )
    resolution_meta = resolved.get("resolution", {}) if isinstance(resolved, dict) else {}
    return {
        "ok": True,
        "item": _serialize_ui_theme_assignment(row),
        "resolved_snapshot": {
            "owner_type": "dealer" if normalized_scope == "tenant" else "global",
            "owner_id": normalized_scope_id if normalized_scope == "tenant" else "global",
            "resolved_config_hash": resolution_meta.get("resolved_config_hash"),
        },
    }


@router.delete("/admin/ui/theme-assignments/{assignment_id}")
async def admin_delete_ui_theme_assignment(
    assignment_id: str,
    current_user=Depends(check_named_permission(ADMIN_UI_DESIGNER_PERMISSION)),
    session: AsyncSession = Depends(get_db),
):
    try:
        assignment_uuid = uuid.UUID(assignment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid assignment id") from exc

    row = await session.get(UIThemeAssignment, assignment_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Theme assignment not found")
    if row.scope == "user":
        raise _ui_http_error(
            code=UI_ERROR_FEATURE_DISABLED,
            message="Site-level theme override read-only ve deprecated durumdadır",
            status_code=403,
            extras={"feature": "site_level_theme_override", "deprecation_plan": "P2"},
        )
    await session.delete(row)
    await session.commit()
    return {"ok": True}


@router.get("/ui/themes/effective")
async def get_effective_ui_theme(
    tenant_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    theme, source_scope, source_scope_id, assignment, resolved = await _resolve_effective_theme(
        session,
        tenant_id=(tenant_id or "").strip() or None,
        user_id=(user_id or "").strip() or None,
    )
    resolved_tokens = resolved.get("tokens", {}) if isinstance(resolved, dict) else {}
    resolution_meta = resolved.get("resolution", {}) if isinstance(resolved, dict) else {}
    return {
        "source_scope": source_scope,
        "source_scope_id": source_scope_id,
        "assignment": _serialize_ui_theme_assignment(assignment) if assignment else None,
        "theme": _serialize_ui_theme(theme) if theme else None,
        "tokens": resolved_tokens,
        "resolution": {
            "mode": resolution_meta.get("mode"),
            "global_theme_id": resolution_meta.get("global_theme_id"),
            "dealer_theme_id": resolution_meta.get("dealer_theme_id"),
            "resolved_config_hash": resolution_meta.get("resolved_config_hash"),
            "precedence": "dealer_override > global_theme",
        },
    }


@router.get("/ui/themes")
async def get_ui_themes_effective_alias(
    tenant_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    return await get_effective_ui_theme(tenant_id=tenant_id, user_id=user_id, session=session)
