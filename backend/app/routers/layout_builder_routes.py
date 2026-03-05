from __future__ import annotations

from datetime import datetime, timezone
import logging
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import ADMIN_ROLES, check_permissions, get_current_user_optional
from app.domains.layout_builder.service import (
    archive_revision,
    bind_category_to_page,
    create_draft_revision,
    create_layout_page,
    create_or_update_component_definition,
    get_latest_published_revision_for_page,
    publish_revision,
    unbind_category,
    write_layout_audit_log,
)
from app.models.layout_builder import (
    LayoutAuditAction,
    LayoutAuditLog,
    LayoutBinding,
    LayoutComponentDefinition,
    LayoutPage,
    LayoutPageType,
    LayoutRevision,
    LayoutRevisionStatus,
)


router = APIRouter(prefix="/api", tags=["layout_builder"])
logger = logging.getLogger("layout_builder")

ADMIN_LAYOUT_ROLES = ["super_admin", "country_admin"]
RESOLVE_CACHE_TTL_SECONDS = 180

_RESOLVE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_METRICS = {
    "resolve_requests": 0,
    "resolve_cache_hits": 0,
    "resolve_cache_misses": 0,
    "resolve_binding_hits": 0,
    "resolve_default_hits": 0,
    "publish_count": 0,
    "binding_changes": 0,
    "resolve_total_latency_ms": 0.0,
}

LISTING_CREATE_ALLOWED_COMPONENTS = {
    "listing.create.default-content": set(),
    "shared.text-block": {"title", "body"},
    "shared.ad-slot": {"placement"},
    "interactive.doping-selector": {"available_dopings", "show_prices", "default_selected"},
}

LISTING_ALLOWED_AD_PLACEMENTS = {"AD_HOME_TOP", "AD_SEARCH_TOP", "AD_LOGIN_1"}
LISTING_ALLOWED_DOPING_PACKAGES = {
    "Vitrin",
    "Acil",
    "Anasayfa",
    "Premium",
    "Öne Çıkar",
    "Featured",
}
LISTING_MAX_ROWS = 16
LISTING_MAX_COLUMNS_PER_ROW = 4
LISTING_MAX_COMPONENTS_PER_COLUMN = 12
LISTING_TEXT_TITLE_MAX = 160
LISTING_TEXT_BODY_MAX = 4000
LISTING_MAX_DOPING_OPTIONS = 8


class ComponentDefinitionPayload(BaseModel):
    key: str = Field(min_length=2, max_length=128)
    name: str = Field(min_length=2, max_length=200)
    schema_json: dict
    is_active: bool = True


class ComponentDefinitionPatchPayload(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    schema_json: Optional[dict] = None
    is_active: Optional[bool] = None


class LayoutPageCreatePayload(BaseModel):
    page_type: LayoutPageType
    country: str = Field(min_length=2, max_length=5)
    module: str = Field(min_length=2, max_length=64)
    category_id: Optional[str] = None


class LayoutPagePatchPayload(BaseModel):
    country: Optional[str] = Field(default=None, min_length=2, max_length=5)
    module: Optional[str] = Field(default=None, min_length=2, max_length=64)
    category_id: Optional[str] = None


class LayoutDraftPayload(BaseModel):
    payload_json: dict = Field(default_factory=dict)


class LayoutBindingPayload(BaseModel):
    country: str = Field(min_length=2, max_length=5)
    module: str = Field(min_length=2, max_length=64)
    category_id: str
    layout_page_id: str


class LayoutUnbindPayload(BaseModel):
    country: str = Field(min_length=2, max_length=5)
    module: str = Field(min_length=2, max_length=64)
    category_id: str


def _cache_key(country: str, module: str, page_type: LayoutPageType, category_id: Optional[str]) -> str:
    normalized_category = str(category_id or "").strip().lower()
    return f"{country.upper()}|{module.strip().lower()}|{page_type.value}|{normalized_category}"


def _invalidate_resolve_cache() -> None:
    _RESOLVE_CACHE.clear()


def _validate_json_schema_or_400(schema_json: dict) -> None:
    try:
        Draft7Validator.check_schema(schema_json)
    except SchemaError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_json_schema", "message": str(exc)}) from exc


def _as_uuid_or_400(raw_value: Optional[str], *, field_name: str) -> Optional[uuid.UUID]:
    if raw_value in (None, ""):
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


def _serialize_component(row: LayoutComponentDefinition) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "key": row.key,
        "name": row.name,
        "schema_json": row.schema_json,
        "is_active": bool(row.is_active),
        "version": int(row.version),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _serialize_layout_page(row: LayoutPage) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "page_type": row.page_type.value,
        "country": row.country,
        "module": row.module,
        "category_id": str(row.category_id) if row.category_id else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _serialize_layout_revision(row: LayoutRevision) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "layout_page_id": str(row.layout_page_id),
        "status": row.status.value,
        "payload_json": row.payload_json,
        "version": int(row.version),
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "created_by": str(row.created_by) if row.created_by else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _serialize_binding(row: LayoutBinding) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "country": row.country,
        "module": row.module,
        "category_id": str(row.category_id),
        "layout_page_id": str(row.layout_page_id),
        "is_active": bool(row.is_active),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _validate_listing_column_width_or_400(width_payload: Any, *, row_index: int, column_index: int) -> None:
    if not isinstance(width_payload, dict):
        raise HTTPException(status_code=400, detail=f"listing_create_column_width_invalid:r{row_index}:c{column_index}")

    for bp in ("desktop", "tablet", "mobile"):
        raw_value = width_payload.get(bp)
        if raw_value is None:
            raise HTTPException(
                status_code=400,
                detail=f"listing_create_column_width_missing_breakpoint:r{row_index}:c{column_index}:{bp}",
            )
        try:
            parsed_value = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"listing_create_column_width_not_numeric:r{row_index}:c{column_index}:{bp}",
            ) from exc
        if parsed_value < 1 or parsed_value > 12:
            raise HTTPException(
                status_code=400,
                detail=f"listing_create_column_width_out_of_range:r{row_index}:c{column_index}:{bp}",
            )


def _validate_listing_component_props_or_400(component_key: str, props: dict[str, Any]) -> None:
    if component_key == "shared.text-block":
        title = props.get("title")
        body = props.get("body")
        if title is not None:
            if not isinstance(title, str):
                raise HTTPException(status_code=400, detail="listing_create_text_block_title_must_be_string")
            if len(title.strip()) > LISTING_TEXT_TITLE_MAX:
                raise HTTPException(status_code=400, detail="listing_create_text_block_title_too_long")
        if body is not None:
            if not isinstance(body, str):
                raise HTTPException(status_code=400, detail="listing_create_text_block_body_must_be_string")
            if len(body.strip()) > LISTING_TEXT_BODY_MAX:
                raise HTTPException(status_code=400, detail="listing_create_text_block_body_too_long")

    if component_key == "shared.ad-slot":
        placement = props.get("placement")
        if placement is None:
            return
        placement_value = str(placement).strip()
        if placement_value not in LISTING_ALLOWED_AD_PLACEMENTS:
            raise HTTPException(status_code=400, detail="listing_create_ad_slot_placement_not_allowed")

    if component_key == "interactive.doping-selector":
        available_dopings = props.get("available_dopings") or []
        show_prices = props.get("show_prices")
        default_selected = props.get("default_selected")

        if not isinstance(available_dopings, list) or not available_dopings:
            raise HTTPException(status_code=400, detail="listing_create_doping_options_required")
        if len(available_dopings) > LISTING_MAX_DOPING_OPTIONS:
            raise HTTPException(status_code=400, detail="listing_create_doping_options_limit_exceeded")

        normalized_options = []
        for option in available_dopings:
            option_value = str(option or "").strip()
            if not option_value:
                raise HTTPException(status_code=400, detail="listing_create_doping_option_empty")
            normalized_options.append(option_value)
            if option_value not in LISTING_ALLOWED_DOPING_PACKAGES:
                raise HTTPException(status_code=400, detail="listing_create_doping_option_not_allowed")

        if show_prices is not None and not isinstance(show_prices, bool):
            raise HTTPException(status_code=400, detail="listing_create_doping_show_prices_must_be_boolean")

        if default_selected is not None:
            selected_value = str(default_selected).strip()
            if selected_value and selected_value not in normalized_options:
                raise HTTPException(status_code=400, detail="listing_create_doping_default_selected_invalid")


def _build_listing_policy_report(payload_json: dict[str, Any]) -> dict[str, Any]:
    rows = payload_json.get("rows") if isinstance(payload_json, dict) else None

    stats = {
        "row_count": 0,
        "total_component_count": 0,
        "default_component_count": 0,
        "doping_selector_count": 0,
        "limit_violations": 0,
        "duplicate_id_violations": 0,
        "width_violations": 0,
        "allowed_component_violations": 0,
        "props_violations": 0,
        "ad_placement_violations": 0,
        "doping_violations": 0,
    }

    row_ids: set[str] = set()
    column_ids: set[str] = set()
    component_ids: set[str] = set()

    if isinstance(rows, list):
        stats["row_count"] = len(rows)

    if not isinstance(rows, list):
        checks = [
            {
                "id": "rows_structure",
                "label": "Rows yapısı",
                "status": "fail",
                "blocking": True,
                "detail": "rows dizisi zorunlu",
                "fix_suggestion": "Payload içinde rows dizisini oluşturun ve en az bir row ekleyin.",
            }
        ]
        return {
            "policy": "listing_create",
            "passed": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "suggested_fixes": [checks[0]["fix_suggestion"]],
            "stats": stats,
        }

    for row in rows:
        if not isinstance(row, dict):
            stats["limit_violations"] += 1
            continue

        row_id = str(row.get("id") or "").strip()
        if not row_id or row_id in row_ids:
            stats["duplicate_id_violations"] += 1
        if row_id:
            row_ids.add(row_id)

        columns = row.get("columns")
        if not isinstance(columns, list):
            stats["limit_violations"] += 1
            continue

        if len(columns) > LISTING_MAX_COLUMNS_PER_ROW:
            stats["limit_violations"] += 1

        for column in columns:
            if not isinstance(column, dict):
                stats["limit_violations"] += 1
                continue

            column_id = str(column.get("id") or "").strip()
            if not column_id or column_id in column_ids:
                stats["duplicate_id_violations"] += 1
            if column_id:
                column_ids.add(column_id)

            width = column.get("width")
            if not isinstance(width, dict):
                stats["width_violations"] += 1
            else:
                for bp in ("desktop", "tablet", "mobile"):
                    raw_width = width.get(bp)
                    try:
                        parsed = int(raw_width)
                    except (TypeError, ValueError):
                        stats["width_violations"] += 1
                        continue
                    if parsed < 1 or parsed > 12:
                        stats["width_violations"] += 1

            components = column.get("components")
            if not isinstance(components, list):
                stats["limit_violations"] += 1
                continue

            if len(components) > LISTING_MAX_COMPONENTS_PER_COLUMN:
                stats["limit_violations"] += 1

            for component in components:
                stats["total_component_count"] += 1

                if not isinstance(component, dict):
                    stats["allowed_component_violations"] += 1
                    continue

                component_id = str(component.get("id") or "").strip()
                if not component_id or component_id in component_ids:
                    stats["duplicate_id_violations"] += 1
                if component_id:
                    component_ids.add(component_id)

                component_key = component.get("key")
                if component_key not in LISTING_CREATE_ALLOWED_COMPONENTS:
                    stats["allowed_component_violations"] += 1
                    continue

                if component_key == "listing.create.default-content":
                    stats["default_component_count"] += 1
                if component_key == "interactive.doping-selector":
                    stats["doping_selector_count"] += 1

                props = component.get("props") or {}
                if not isinstance(props, dict):
                    stats["props_violations"] += 1
                    continue

                allowed_props = LISTING_CREATE_ALLOWED_COMPONENTS[component_key]
                invalid_props = sorted(set(props.keys()) - allowed_props)
                if invalid_props:
                    stats["props_violations"] += 1

                if component_key == "shared.ad-slot":
                    placement = props.get("placement")
                    if placement is not None and str(placement).strip() not in LISTING_ALLOWED_AD_PLACEMENTS:
                        stats["ad_placement_violations"] += 1

                if component_key == "interactive.doping-selector":
                    doping_options = props.get("available_dopings")
                    selected = props.get("default_selected")
                    if not isinstance(doping_options, list) or not doping_options:
                        stats["doping_violations"] += 1
                    else:
                        normalized_options = [str(option or "").strip() for option in doping_options]
                        if len(normalized_options) > LISTING_MAX_DOPING_OPTIONS:
                            stats["doping_violations"] += 1
                        if any(not option for option in normalized_options):
                            stats["doping_violations"] += 1
                        if any(option not in LISTING_ALLOWED_DOPING_PACKAGES for option in normalized_options):
                            stats["doping_violations"] += 1
                        selected_value = str(selected or "").strip()
                        if selected_value and selected_value not in normalized_options:
                            stats["doping_violations"] += 1

    checks = [
        {
            "id": "rows_structure",
            "label": "Rows/Columns yapısı",
            "status": "pass" if isinstance(rows, list) and stats["row_count"] > 0 else "fail",
            "blocking": True,
            "detail": f"Row sayısı: {stats['row_count']}",
            "fix_suggestion": "En az bir row ve her row içinde en az bir column tanımlayın.",
        },
        {
            "id": "layout_limits",
            "label": "Satır/Sütun/Bileşen limitleri",
            "status": "pass" if stats["row_count"] <= LISTING_MAX_ROWS and stats["limit_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Limit ihlali: {stats['limit_violations']}",
            "fix_suggestion": f"Row <= {LISTING_MAX_ROWS}, column/row <= {LISTING_MAX_COLUMNS_PER_ROW}, component/column <= {LISTING_MAX_COMPONENTS_PER_COLUMN} olacak şekilde düzenleyin.",
        },
        {
            "id": "unique_ids",
            "label": "Tekil ID politikası",
            "status": "pass" if stats["duplicate_id_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Duplicate/eksik id ihlali: {stats['duplicate_id_violations']}",
            "fix_suggestion": "Her row/column/component için benzersiz ve boş olmayan id kullanın.",
        },
        {
            "id": "width_breakpoints",
            "label": "Breakpoint width doğrulaması",
            "status": "pass" if stats["width_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Width ihlali: {stats['width_violations']}",
            "fix_suggestion": "Tüm column width değerlerini desktop/tablet/mobile için 1..12 aralığında tanımlayın.",
        },
        {
            "id": "allowed_components",
            "label": "İzinli bileşen doğrulaması",
            "status": "pass" if stats["allowed_component_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"İzinli olmayan bileşen ihlali: {stats['allowed_component_violations']}",
            "fix_suggestion": "Sadece listing.create.default-content, shared.text-block, shared.ad-slot ve interactive.doping-selector kullanın.",
        },
        {
            "id": "props_policy",
            "label": "Bileşen prop politikası",
            "status": "pass" if stats["props_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Prop ihlali: {stats['props_violations']}",
            "fix_suggestion": "Her bileşende yalnızca whitelist prop alanlarını gönderin (fazla alanları kaldırın).",
        },
        {
            "id": "default_component",
            "label": "Tek default içerik bloğu",
            "status": "pass" if stats["default_component_count"] == 1 else "fail",
            "blocking": True,
            "detail": f"Default component sayısı: {stats['default_component_count']}",
            "fix_suggestion": "Payload içinde listing.create.default-content bileşeni tam olarak 1 adet olmalı.",
        },
        {
            "id": "ad_placement",
            "label": "Reklam placement politikası",
            "status": "pass" if stats["ad_placement_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Placement ihlali: {stats['ad_placement_violations']}",
            "fix_suggestion": "shared.ad-slot placement değerini whitelist içinden seçin (AD_HOME_TOP / AD_SEARCH_TOP / AD_LOGIN_1).",
        },
        {
            "id": "doping_selector",
            "label": "Doping selector politikası",
            "status": "pass" if stats["doping_selector_count"] <= 1 and stats["doping_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Selector sayısı: {stats['doping_selector_count']}, ihlal: {stats['doping_violations']}",
            "fix_suggestion": "interactive.doping-selector en fazla 1 adet olmalı; available_dopings whitelist'ten seçilmeli ve default_selected listedeki bir değer olmalı.",
        },
        {
            "id": "total_components",
            "label": "Toplam bileşen kontrolü",
            "status": "pass" if stats["total_component_count"] > 0 else "fail",
            "blocking": True,
            "detail": f"Toplam bileşen: {stats['total_component_count']}",
            "fix_suggestion": "Canvas üzerinde en az bir bileşen bulundurun.",
        },
    ]

    suggested_fixes = [
        check["fix_suggestion"]
        for check in checks
        if check.get("status") == "fail" and check.get("fix_suggestion")
    ]

    passed = all(check["status"] == "pass" for check in checks if check.get("blocking"))
    return {
        "policy": "listing_create",
        "passed": bool(passed),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "suggested_fixes": suggested_fixes,
        "stats": stats,
    }


def _validate_listing_runtime_guard_or_400(payload_json: dict) -> None:
    rows = payload_json.get("rows") if isinstance(payload_json, dict) else None
    if not isinstance(rows, list):
        raise HTTPException(status_code=400, detail="listing_create_payload_rows_must_be_array")
    if not rows:
        raise HTTPException(status_code=400, detail="listing_create_payload_rows_required")
    if len(rows) > LISTING_MAX_ROWS:
        raise HTTPException(status_code=400, detail="listing_create_payload_rows_limit_exceeded")

    row_ids: set[str] = set()
    column_ids: set[str] = set()
    component_ids: set[str] = set()
    default_component_count = 0
    doping_selector_count = 0
    total_component_count = 0

    for row_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise HTTPException(status_code=400, detail=f"listing_create_row_invalid:r{row_index}")

        row_id = str(row.get("id") or "").strip()
        if not row_id:
            raise HTTPException(status_code=400, detail=f"listing_create_row_id_required:r{row_index}")
        if row_id in row_ids:
            raise HTTPException(status_code=400, detail=f"listing_create_row_id_duplicate:{row_id}")
        row_ids.add(row_id)

        columns = row.get("columns")
        if not isinstance(columns, list):
            raise HTTPException(status_code=400, detail="listing_create_payload_columns_must_be_array")
        if not columns:
            raise HTTPException(status_code=400, detail=f"listing_create_row_columns_required:r{row_index}")
        if len(columns) > LISTING_MAX_COLUMNS_PER_ROW:
            raise HTTPException(status_code=400, detail=f"listing_create_row_columns_limit_exceeded:r{row_index}")

        for column_index, column in enumerate(columns, start=1):
            if not isinstance(column, dict):
                raise HTTPException(status_code=400, detail=f"listing_create_column_invalid:r{row_index}:c{column_index}")

            column_id = str(column.get("id") or "").strip()
            if not column_id:
                raise HTTPException(status_code=400, detail=f"listing_create_column_id_required:r{row_index}:c{column_index}")
            if column_id in column_ids:
                raise HTTPException(status_code=400, detail=f"listing_create_column_id_duplicate:{column_id}")
            column_ids.add(column_id)

            _validate_listing_column_width_or_400(column.get("width"), row_index=row_index, column_index=column_index)

            components = column.get("components") if isinstance(column, dict) else None
            if not isinstance(components, list):
                raise HTTPException(status_code=400, detail="listing_create_payload_components_must_be_array")
            if len(components) > LISTING_MAX_COMPONENTS_PER_COLUMN:
                raise HTTPException(
                    status_code=400,
                    detail=f"listing_create_column_components_limit_exceeded:r{row_index}:c{column_index}",
                )

            for component_index, component in enumerate(components, start=1):
                total_component_count += 1
                if not isinstance(component, dict):
                    raise HTTPException(status_code=400, detail="listing_create_component_invalid")

                component_id = str(component.get("id") or "").strip()
                if not component_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"listing_create_component_id_required:r{row_index}:c{column_index}:i{component_index}",
                    )
                if component_id in component_ids:
                    raise HTTPException(status_code=400, detail=f"listing_create_component_id_duplicate:{component_id}")
                component_ids.add(component_id)

                component_key = component.get("key")
                if component_key not in LISTING_CREATE_ALLOWED_COMPONENTS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"listing_create_component_not_allowed:{component_key}",
                    )

                props = component.get("props") or {}
                if not isinstance(props, dict):
                    raise HTTPException(status_code=400, detail="listing_create_component_props_must_be_object")

                allowed_props = LISTING_CREATE_ALLOWED_COMPONENTS[component_key]
                invalid_props = sorted(set(props.keys()) - allowed_props)
                if invalid_props:
                    raise HTTPException(
                        status_code=400,
                        detail=f"listing_create_component_props_not_allowed:{component_key}:{','.join(invalid_props)}",
                    )

                _validate_listing_component_props_or_400(component_key, props)

                if component_key == "listing.create.default-content":
                    default_component_count += 1
                if component_key == "interactive.doping-selector":
                    doping_selector_count += 1

    if total_component_count <= 0:
        raise HTTPException(status_code=400, detail="listing_create_payload_must_include_components")
    if default_component_count != 1:
        raise HTTPException(status_code=400, detail="listing_create_default_component_must_be_exactly_one")
    if doping_selector_count > 1:
        raise HTTPException(status_code=400, detail="listing_create_doping_selector_must_be_zero_or_one")


@router.get("/admin/site/content-layout/components")
async def list_layout_components(
    key: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    query = select(LayoutComponentDefinition)
    if key:
        query = query.where(LayoutComponentDefinition.key.ilike(f"%{key.strip()}%"))
    if is_active is not None:
        query = query.where(LayoutComponentDefinition.is_active.is_(bool(is_active)))

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(count_result.scalar() or 0)

    rows_result = await session.execute(
        query.order_by(desc(LayoutComponentDefinition.updated_at), LayoutComponentDefinition.key.asc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = rows_result.scalars().all()
    return {
        "items": [_serialize_component(row) for row in rows],
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.post("/admin/site/content-layout/components")
async def create_layout_component(
    payload: ComponentDefinitionPayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    _validate_json_schema_or_400(payload.schema_json)
    existing_result = await session.execute(
        select(LayoutComponentDefinition).where(LayoutComponentDefinition.key == payload.key.strip())
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Component key already exists")

    try:
        row = await create_or_update_component_definition(
            session,
            key=payload.key.strip(),
            name=payload.name.strip(),
            schema_json=payload.schema_json,
            is_active=bool(payload.is_active),
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        if str(exc) == "component_key_conflict":
            raise HTTPException(status_code=409, detail="Component key already exists") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Component key already exists") from exc

    return {"ok": True, "item": _serialize_component(row)}


@router.patch("/admin/site/content-layout/components/{component_id}")
async def patch_layout_component(
    component_id: str,
    payload: ComponentDefinitionPatchPayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    component_uuid = _as_uuid_or_400(component_id, field_name="component_id")
    row = await session.get(LayoutComponentDefinition, component_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Component definition not found")

    before = _serialize_component(row)
    if payload.schema_json is not None:
        _validate_json_schema_or_400(payload.schema_json)
        row.schema_json = payload.schema_json
    if payload.name is not None:
        row.name = payload.name.strip()
    if payload.is_active is not None:
        row.is_active = bool(payload.is_active)
    row.version = int(row.version) + 1
    row.updated_at = datetime.now(timezone.utc)

    await write_layout_audit_log(
        session,
        actor_user_id=current_user.get("id"),
        action=LayoutAuditAction.UPDATE_SCHEMA,
        entity_type="layout_component_definition",
        entity_id=str(row.id),
        before_json=before,
        after_json={
            "key": row.key,
            "name": row.name,
            "schema_json": row.schema_json,
            "is_active": bool(row.is_active),
            "version": int(row.version),
        },
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    await session.commit()
    return {"ok": True, "item": _serialize_component(row)}


@router.get("/admin/site/content-layout/pages")
async def list_layout_pages(
    page_type: Optional[LayoutPageType] = Query(default=None),
    country: Optional[str] = Query(default=None),
    module: Optional[str] = Query(default=None),
    category_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    query = select(LayoutPage)
    if page_type:
        query = query.where(LayoutPage.page_type == page_type)
    if country:
        query = query.where(LayoutPage.country == country.upper())
    if module:
        query = query.where(LayoutPage.module == module.strip())
    if category_id:
        category_uuid = _as_uuid_or_400(category_id, field_name="category_id")
        query = query.where(LayoutPage.category_id == category_uuid)

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(count_result.scalar() or 0)

    rows_result = await session.execute(
        query.order_by(desc(LayoutPage.updated_at), LayoutPage.id.asc()).offset((page - 1) * limit).limit(limit)
    )
    rows = rows_result.scalars().all()
    return {
        "items": [_serialize_layout_page(row) for row in rows],
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.post("/admin/site/content-layout/pages")
async def create_layout_page_admin(
    payload: LayoutPageCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    try:
        row = await create_layout_page(
            session,
            page_type=payload.page_type,
            country=payload.country,
            module=payload.module,
            category_id=payload.category_id,
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        if str(exc) == "layout_page_scope_conflict":
            raise HTTPException(status_code=409, detail="Layout page scope already exists") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_page(row)}


@router.patch("/admin/site/content-layout/pages/{page_id}")
async def patch_layout_page_admin(
    page_id: str,
    payload: LayoutPagePatchPayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    page_uuid = _as_uuid_or_400(page_id, field_name="page_id")
    row = await session.get(LayoutPage, page_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Layout page not found")

    before = _serialize_layout_page(row)
    if payload.country is not None:
        row.country = payload.country.upper()
    if payload.module is not None:
        row.module = payload.module.strip()
    if payload.category_id is not None:
        row.category_id = _as_uuid_or_400(payload.category_id, field_name="category_id")
    row.updated_at = datetime.now(timezone.utc)

    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Layout page scope already exists") from exc

    await write_layout_audit_log(
        session,
        actor_user_id=current_user.get("id"),
        action=LayoutAuditAction.CREATE_PAGE,
        entity_type="layout_page",
        entity_id=str(row.id),
        before_json=before,
        after_json=_serialize_layout_page(row),
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    await session.commit()
    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_page(row)}


@router.post("/admin/site/content-layout/pages/{page_id}/revisions/draft")
async def create_draft_revision_admin(
    page_id: str,
    payload: LayoutDraftPayload,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    page_uuid = _as_uuid_or_400(page_id, field_name="page_id")
    page_row = await session.get(LayoutPage, page_uuid)
    if not page_row:
        raise HTTPException(status_code=404, detail="Layout page not found")
    if page_row.page_type == LayoutPageType.LISTING_CREATE_STEPX:
        _validate_listing_runtime_guard_or_400(payload.payload_json)

    try:
        row = await create_draft_revision(
            session,
            layout_page_id=page_id,
            payload_json=payload.payload_json,
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        code = str(exc)
        if code == "layout_page_not_found":
            raise HTTPException(status_code=404, detail="Layout page not found") from exc
        if code == "layout_revision_version_conflict":
            raise HTTPException(status_code=409, detail="Revision version conflict") from exc
        raise HTTPException(status_code=400, detail=code) from exc

    return {"ok": True, "item": _serialize_layout_revision(row)}


@router.patch("/admin/site/content-layout/revisions/{revision_id}/draft")
async def patch_draft_revision_admin(
    revision_id: str,
    payload: LayoutDraftPayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")
    if row.status != LayoutRevisionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft revisions can be updated")

    page_row = await session.get(LayoutPage, row.layout_page_id)
    if page_row and page_row.page_type == LayoutPageType.LISTING_CREATE_STEPX:
        _validate_listing_runtime_guard_or_400(payload.payload_json)

    before = _serialize_layout_revision(row)
    row.payload_json = payload.payload_json or {}

    await write_layout_audit_log(
        session,
        actor_user_id=current_user.get("id"),
        action=LayoutAuditAction.CREATE_REVISION,
        entity_type="layout_revision",
        entity_id=str(row.id),
        before_json=before,
        after_json=_serialize_layout_revision(row),
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    await session.commit()
    return {"ok": True, "item": _serialize_layout_revision(row)}


@router.post("/admin/site/content-layout/revisions/{revision_id}/publish")
async def publish_revision_admin(
    revision_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    target_revision = await session.get(LayoutRevision, revision_uuid)
    if target_revision:
        page_row = await session.get(LayoutPage, target_revision.layout_page_id)
        if page_row and page_row.page_type == LayoutPageType.LISTING_CREATE_STEPX:
            _validate_listing_runtime_guard_or_400(target_revision.payload_json or {})

    try:
        published = await publish_revision(
            session,
            revision_id=revision_id,
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        code = str(exc)
        if code == "revision_not_found":
            raise HTTPException(status_code=404, detail="Revision not found") from exc
        if code in {"only_draft_can_be_published", "published_revision_conflict"}:
            raise HTTPException(status_code=409, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Publish conflict") from exc

    _METRICS["publish_count"] += 1
    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_revision(published)}


@router.get("/admin/site/content-layout/revisions/{revision_id}/policy-report")
async def get_revision_policy_report_admin(
    revision_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")

    page_row = await session.get(LayoutPage, row.layout_page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Layout page not found")

    if page_row.page_type != LayoutPageType.LISTING_CREATE_STEPX:
        return {
            "ok": True,
            "report": {
                "policy": "not_applicable",
                "passed": True,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "checks": [
                    {
                        "id": "not_applicable",
                        "label": "Policy report",
                        "status": "pass",
                        "blocking": False,
                        "detail": "Bu page_type için listing_create policy report uygulanmaz.",
                        "fix_suggestion": None,
                    }
                ],
                "suggested_fixes": [],
                "stats": {},
            },
        }

    report = _build_listing_policy_report(row.payload_json or {})
    return {"ok": True, "report": report}


@router.post("/admin/site/content-layout/revisions/{revision_id}/archive")
async def archive_revision_admin(
    revision_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    try:
        row = await archive_revision(
            session,
            revision_id=revision_id,
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        code = str(exc)
        if code == "revision_not_found":
            raise HTTPException(status_code=404, detail="Revision not found") from exc
        raise HTTPException(status_code=400, detail=code) from exc

    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_revision(row)}


@router.get("/admin/site/content-layout/pages/{page_id}/revisions")
async def list_revisions_for_page(
    page_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    page_uuid = _as_uuid_or_400(page_id, field_name="page_id")
    page_row = await session.get(LayoutPage, page_uuid)
    if not page_row:
        raise HTTPException(status_code=404, detail="Layout page not found")

    result = await session.execute(
        select(LayoutRevision)
        .where(LayoutRevision.layout_page_id == page_uuid)
        .order_by(desc(LayoutRevision.version), desc(LayoutRevision.created_at))
        .limit(100)
    )
    rows = result.scalars().all()
    return {"items": [_serialize_layout_revision(row) for row in rows]}


@router.post("/admin/site/content-layout/bindings")
async def bind_layout_page_to_category(
    payload: LayoutBindingPayload,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    try:
        row = await bind_category_to_page(
            session,
            country=payload.country,
            module=payload.module,
            category_id=payload.category_id,
            layout_page_id=payload.layout_page_id,
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        code = str(exc)
        if code in {"layout_page_not_found"}:
            raise HTTPException(status_code=404, detail="Layout page not found") from exc
        if code in {"active_binding_conflict"}:
            raise HTTPException(status_code=409, detail=code) from exc
        raise HTTPException(status_code=400, detail=code) from exc

    _METRICS["binding_changes"] += 1
    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_binding(row)}


@router.post("/admin/site/content-layout/bindings/unbind")
async def unbind_layout_page_from_category(
    payload: LayoutUnbindPayload,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    try:
        unbound_count = await unbind_category(
            session,
            country=payload.country,
            module=payload.module,
            category_id=payload.category_id,
            actor_user_id=current_user.get("id"),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _METRICS["binding_changes"] += 1
    _invalidate_resolve_cache()
    return {"ok": True, "unbound_count": int(unbound_count)}


@router.get("/admin/site/content-layout/bindings/active")
async def get_active_binding(
    country: str,
    module: str,
    category_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    category_uuid = _as_uuid_or_400(category_id, field_name="category_id")
    result = await session.execute(
        select(LayoutBinding)
        .where(
            and_(
                LayoutBinding.country == country.upper(),
                LayoutBinding.module == module.strip(),
                LayoutBinding.category_id == category_uuid,
                LayoutBinding.is_active.is_(True),
            )
        )
        .order_by(desc(LayoutBinding.updated_at))
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return {"item": None}
    return {"item": _serialize_binding(row)}


@router.get("/admin/site/content-layout/audit-logs")
async def list_layout_audit_logs(
    entity_type: Optional[str] = Query(default=None),
    entity_id: Optional[str] = Query(default=None),
    actor_user_id: Optional[str] = Query(default=None),
    action: Optional[LayoutAuditAction] = Query(default=None),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=200),
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    query = select(LayoutAuditLog)
    if entity_type:
        query = query.where(LayoutAuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(LayoutAuditLog.entity_id == entity_id)
    if actor_user_id:
        query = query.where(LayoutAuditLog.actor_user_id == _as_uuid_or_400(actor_user_id, field_name="actor_user_id"))
    if action:
        query = query.where(LayoutAuditLog.action == action)
    if start_at:
        query = query.where(LayoutAuditLog.created_at >= start_at)
    if end_at:
        query = query.where(LayoutAuditLog.created_at <= end_at)

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(count_result.scalar() or 0)
    rows_result = await session.execute(
        query.order_by(desc(LayoutAuditLog.created_at)).offset((page - 1) * limit).limit(limit)
    )
    rows = rows_result.scalars().all()
    return {
        "items": [
            {
                "id": str(row.id),
                "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
                "action": row.action.value,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "before_json": row.before_json,
                "after_json": row.after_json,
                "ip": row.ip,
                "user_agent": row.user_agent,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
        "pagination": {"page": page, "limit": limit, "total": total},
    }


async def _resolve_effective_layout(
    session: AsyncSession,
    *,
    country: str,
    module: str,
    page_type: LayoutPageType,
    category_id: Optional[str],
    preview_mode: str = "published",
) -> dict[str, Any]:
    async def _latest_by_status(layout_page_id: uuid.UUID, status: LayoutRevisionStatus) -> LayoutRevision | None:
        result = await session.execute(
            select(LayoutRevision)
            .where(
                and_(
                    LayoutRevision.layout_page_id == layout_page_id,
                    LayoutRevision.status == status,
                )
            )
            .order_by(desc(LayoutRevision.version), desc(LayoutRevision.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    category_uuid = _as_uuid_or_400(category_id, field_name="category_id") if category_id else None

    if category_uuid:
        bound_page_result = await session.execute(
            select(LayoutPage)
            .join(LayoutBinding, LayoutBinding.layout_page_id == LayoutPage.id)
            .where(
                and_(
                    LayoutBinding.country == country,
                    LayoutBinding.module == module,
                    LayoutBinding.category_id == category_uuid,
                    LayoutBinding.is_active.is_(True),
                    LayoutPage.page_type == page_type,
                )
            )
            .order_by(desc(LayoutBinding.updated_at))
            .limit(1)
        )
        bound_page = bound_page_result.scalar_one_or_none()
        if bound_page:
            published = await get_latest_published_revision_for_page(session, layout_page_id=bound_page.id)
            if preview_mode == "draft":
                draft = await _latest_by_status(bound_page.id, LayoutRevisionStatus.DRAFT)
                if not draft:
                    if not published:
                        raise HTTPException(status_code=409, detail="bound_layout_has_no_draft_or_published_revision")
                    _METRICS["resolve_binding_hits"] += 1
                    return {
                        "source": "binding_draft_fallback",
                        "preview_mode": "draft",
                        "draft_available": False,
                        "layout_page": _serialize_layout_page(bound_page),
                        "revision": _serialize_layout_revision(published),
                        "comparison": {
                            "published_revision": _serialize_layout_revision(published),
                        },
                    }
                _METRICS["resolve_binding_hits"] += 1
                return {
                    "source": "binding_draft",
                    "preview_mode": "draft",
                    "draft_available": True,
                    "layout_page": _serialize_layout_page(bound_page),
                    "revision": _serialize_layout_revision(draft),
                    "comparison": {
                        "published_revision": _serialize_layout_revision(published) if published else None,
                    },
                }

            if not published:
                raise HTTPException(status_code=409, detail="bound_layout_has_no_published_revision")
            _METRICS["resolve_binding_hits"] += 1
            return {
                "source": "binding",
                "layout_page": _serialize_layout_page(bound_page),
                "revision": _serialize_layout_revision(published),
            }

    default_page_result = await session.execute(
        select(LayoutPage)
        .where(
            and_(
                LayoutPage.country == country,
                LayoutPage.module == module,
                LayoutPage.page_type == page_type,
                LayoutPage.category_id.is_(None),
            )
        )
        .order_by(desc(LayoutPage.updated_at))
        .limit(1)
    )
    default_page = default_page_result.scalar_one_or_none()
    if not default_page:
        raise HTTPException(status_code=404, detail="layout_page_not_found")

    published = await get_latest_published_revision_for_page(session, layout_page_id=default_page.id)
    if preview_mode == "draft":
        draft = await _latest_by_status(default_page.id, LayoutRevisionStatus.DRAFT)
        if not draft:
            if not published:
                raise HTTPException(status_code=409, detail="default_layout_has_no_draft_or_published_revision")
            _METRICS["resolve_default_hits"] += 1
            return {
                "source": "default_draft_fallback",
                "preview_mode": "draft",
                "draft_available": False,
                "layout_page": _serialize_layout_page(default_page),
                "revision": _serialize_layout_revision(published),
                "comparison": {
                    "published_revision": _serialize_layout_revision(published),
                },
            }
        _METRICS["resolve_default_hits"] += 1
        return {
            "source": "default_draft",
            "preview_mode": "draft",
            "draft_available": True,
            "layout_page": _serialize_layout_page(default_page),
            "revision": _serialize_layout_revision(draft),
            "comparison": {
                "published_revision": _serialize_layout_revision(published) if published else None,
            },
        }

    if not published:
        raise HTTPException(status_code=409, detail="default_layout_has_no_published_revision")

    _METRICS["resolve_default_hits"] += 1
    return {
        "source": "default",
        "layout_page": _serialize_layout_page(default_page),
        "revision": _serialize_layout_revision(published),
    }


@router.get("/site/content-layout/resolve")
async def resolve_content_layout(
    country: str,
    module: str,
    page_type: LayoutPageType,
    category_id: Optional[str] = None,
    layout_preview: str = Query(default="published"),
    current_user=Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
):
    started_at = time.perf_counter()
    normalized_country = country.upper()
    normalized_module = module.strip()
    preview_mode = "draft" if str(layout_preview).strip().lower() == "draft" else "published"

    if preview_mode == "draft":
        if not current_user or current_user.get("role") not in ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Draft preview requires admin role")

    _METRICS["resolve_requests"] += 1
    key = _cache_key(normalized_country, normalized_module, page_type, category_id)
    now_ts = time.time()
    cached = _RESOLVE_CACHE.get(key) if preview_mode == "published" else None
    if cached and cached[0] > now_ts:
        _METRICS["resolve_cache_hits"] += 1
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        _METRICS["resolve_total_latency_ms"] += elapsed_ms
        logger.info("layout_resolve source=cache key=%s latency_ms=%.2f", key, elapsed_ms)
        return {**cached[1], "source": "cache"}

    _METRICS["resolve_cache_misses"] += 1
    payload = await _resolve_effective_layout(
        session,
        country=normalized_country,
        module=normalized_module,
        page_type=page_type,
        category_id=category_id,
        preview_mode=preview_mode,
    )
    if preview_mode == "published":
        _RESOLVE_CACHE[key] = (now_ts + RESOLVE_CACHE_TTL_SECONDS, payload)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    _METRICS["resolve_total_latency_ms"] += elapsed_ms
    logger.info(
        "layout_resolve source=db key=%s strategy=%s preview=%s latency_ms=%.2f",
        key,
        payload.get("source"),
        preview_mode,
        elapsed_ms,
    )
    return payload


@router.get("/admin/site/content-layout/metrics")
async def get_layout_builder_metrics(
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
):
    requests_total = int(_METRICS.get("resolve_requests", 0))
    avg_latency = (
        float(_METRICS.get("resolve_total_latency_ms", 0.0)) / requests_total
        if requests_total > 0
        else 0.0
    )
    return {
        "metrics": {
            "resolve_requests": requests_total,
            "resolve_cache_hits": int(_METRICS.get("resolve_cache_hits", 0)),
            "resolve_cache_misses": int(_METRICS.get("resolve_cache_misses", 0)),
            "resolve_cache_hit_rate": (
                round((int(_METRICS.get("resolve_cache_hits", 0)) / requests_total) * 100, 2)
                if requests_total > 0
                else 0.0
            ),
            "resolve_binding_hits": int(_METRICS.get("resolve_binding_hits", 0)),
            "resolve_default_hits": int(_METRICS.get("resolve_default_hits", 0)),
            "publish_count": int(_METRICS.get("publish_count", 0)),
            "binding_changes": int(_METRICS.get("binding_changes", 0)),
            "resolve_avg_latency_ms": round(avg_latency, 2),
        }
    }
