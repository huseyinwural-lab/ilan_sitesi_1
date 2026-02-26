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


class UIConfigSavePayload(BaseModel):
    segment: str = Field(default="individual")
    scope: str = Field(default="system")
    scope_id: Optional[str] = None
    status: str = Field(default="draft")
    config_data: dict = Field(default_factory=dict)


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
    return {
        "id": str(row.id),
        "config_type": row.config_type,
        "segment": row.segment,
        "scope": row.scope,
        "scope_id": row.scope_id,
        "status": row.status,
        "version": row.version,
        "config_data": row.config_data or {},
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
    return {
        "item": _serialize_ui_config(current) if current else None,
        "items": [_serialize_ui_config(item) for item in versions],
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
        config_data=payload.config_data or {},
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
    return {
        "config_type": normalized_type,
        "segment": normalized_segment,
        "source_scope": source_scope,
        "source_scope_id": source_scope_id,
        "item": _serialize_ui_config(row) if row else None,
        "config_data": row.config_data if row else {},
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
