from copy import deepcopy
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional
import uuid
import xml.etree.ElementTree as ET

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from PIL import Image
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.dependencies import PERMISSION_ROLE_MAP, check_named_permission
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
        raise HTTPException(status_code=400, detail="SVG parse edilemedi") from exc

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

    raise HTTPException(status_code=400, detail="SVG width/height metadata bulunamadı")


def _validate_logo_constraints(data: bytes, filename: str) -> dict[str, Any]:
    ext = _extract_file_extension(filename)
    if ext not in UI_LOGO_ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Desteklenen formatlar: png/svg/webp")
    if len(data) > UI_LOGO_MAX_BYTES:
        raise HTTPException(status_code=400, detail="Dosya boyutu 2MB sınırını aşıyor")

    if ext == "svg":
        width, height = _parse_svg_size(data)
    else:
        try:
            with Image.open(BytesIO(data)) as image:
                width, height = image.size
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Görsel dosyası okunamadı") from exc

    if not width or not height:
        raise HTTPException(status_code=400, detail="Görsel ölçüsü geçersiz")
    ratio = float(width) / float(height)
    min_ratio = UI_LOGO_RATIO_TARGET * (1 - UI_LOGO_RATIO_TOLERANCE)
    max_ratio = UI_LOGO_RATIO_TARGET * (1 + UI_LOGO_RATIO_TOLERANCE)
    if ratio < min_ratio or ratio > max_ratio:
        raise HTTPException(
            status_code=400,
            detail=f"Logo aspect ratio 3:1 (±%10) olmalı. Mevcut oran: {ratio:.2f}",
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


def _scope_clause(scope: str, scope_id: Optional[str]):
    if scope == "system":
        return [UIConfig.scope == "system", or_(UIConfig.scope_id.is_(None), UIConfig.scope_id == "")]
    return [UIConfig.scope == scope, UIConfig.scope_id == scope_id]


def _theme_scope_clause(scope: str, scope_id: Optional[str]):
    if scope == "system":
        return [UIThemeAssignment.scope == "system", or_(UIThemeAssignment.scope_id.is_(None), UIThemeAssignment.scope_id == "")]
    return [UIThemeAssignment.scope == scope, UIThemeAssignment.scope_id == scope_id]


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
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


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


async def _resolve_effective_theme(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    user_id: Optional[str],
) -> tuple[Optional[UITheme], str, Optional[str], Optional[UIThemeAssignment]]:
    chain = [("user", user_id), ("tenant", tenant_id), ("system", None)]
    for scope, scope_id in chain:
        if scope in {"tenant", "user"} and not scope_id:
            continue
        assignment_stmt = (
            select(UIThemeAssignment)
            .where(*_theme_scope_clause(scope, scope_id))
            .order_by(desc(UIThemeAssignment.updated_at))
            .limit(1)
        )
        assignment = (await session.execute(assignment_stmt)).scalar_one_or_none()
        if not assignment:
            continue
        theme = await session.get(UITheme, assignment.theme_id)
        if theme:
            return theme, scope, scope_id, assignment

    fallback = (
        await session.execute(select(UITheme).where(UITheme.is_active.is_(True)).order_by(desc(UITheme.updated_at)).limit(1))
    ).scalar_one_or_none()
    return fallback, "active_fallback", None, None


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

    session.add(row)
    await session.commit()
    await session.refresh(row)
    return {"ok": True, "item": _serialize_ui_config(row)}


@router.post("/admin/ui/configs/{config_type}/publish/{config_id}")
async def admin_publish_ui_config(
    config_type: str,
    config_id: str,
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

    if row.config_type == "header":
        row.config_data = _normalize_header_config_data(row.config_data or {}, row.segment)
        if row.segment == "corporate":
            _validate_corporate_header_guardrails(row.config_data)
    elif row.config_type == "dashboard":
        normalized_layout, normalized_widgets, next_config_data = _extract_dashboard_layout_widgets(
            layout_payload=row.layout,
            widgets_payload=row.widgets,
            config_data=row.config_data if isinstance(row.config_data, dict) else {},
        )
        _validate_dashboard_guardrails(normalized_layout, normalized_widgets)
        row.layout = normalized_layout
        row.widgets = normalized_widgets
        row.config_data = next_config_data

    await _set_ui_config_scope_to_draft(
        session,
        config_type=row.config_type,
        segment=row.segment,
        scope=row.scope,
        scope_id=row.scope_id,
    )
    row.status = "published"
    row.published_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(row)
    return {"ok": True, "item": _serialize_ui_config(row)}


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
    if normalized_segment != "corporate":
        raise HTTPException(status_code=400, detail="Logo upload bu sprintte sadece corporate segment için açık")
    normalized_scope, normalized_scope_id = _normalize_scope(scope, scope_id)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Dosya boş")

    logo_meta = _validate_logo_constraints(data, file.filename or "")
    try:
        asset_key, _ = store_site_asset(data, file.filename or "logo.webp", folder="ui/logos", allow_svg=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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


@router.get("/ui/{config_type}")
async def get_effective_ui_config(
    config_type: str,
    segment: str = Query(default="individual"),
    tenant_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    normalized_type = _normalize_config_type(config_type)
    normalized_segment = _normalize_segment(segment)

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
    return {"ok": True, "item": _serialize_ui_theme_assignment(row)}


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
    await session.delete(row)
    await session.commit()
    return {"ok": True}


@router.get("/ui/themes/effective")
async def get_effective_ui_theme(
    tenant_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    theme, source_scope, source_scope_id, assignment = await _resolve_effective_theme(
        session,
        tenant_id=(tenant_id or "").strip() or None,
        user_id=(user_id or "").strip() or None,
    )
    return {
        "source_scope": source_scope,
        "source_scope_id": source_scope_id,
        "assignment": _serialize_ui_theme_assignment(assignment) if assignment else None,
        "theme": _serialize_ui_theme(theme) if theme else None,
        "tokens": theme.tokens if theme else {},
    }


@router.get("/ui/themes")
async def get_ui_themes_effective_alias(
    tenant_id: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    return await get_effective_ui_theme(tenant_id=tenant_id, user_id=user_id, session=session)
