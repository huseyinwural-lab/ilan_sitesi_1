from __future__ import annotations

import asyncio
import unicodedata
from datetime import datetime, timedelta, timezone
import logging
import time
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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
    LayoutPresetEvent,
    LayoutPresetEventType,
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
_LAYOUT_ENUM_SYNCED = False

TRANSIENT_DB_ERROR_MARKERS = (
    "timeout",
    "timed out",
    "connection timeout",
    "connection reset",
    "connection aborted",
    "connection refused",
    "connection is closed",
    "server closed the connection",
    "could not connect",
    "could not receive data",
    "lost connection",
    "ssl syscall",
    "eof detected",
    "terminating connection",
    "remaining connection slots",
    "too many connections",
    "queuepool",
    "pool",
    "deadlock",
    "statement timeout",
    "network is unreachable",
    "temporary failure",
    "name or service not known",
    "db_error",
)

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
GENERIC_MAX_ROWS = 20
GENERIC_MAX_COLUMNS_PER_ROW = 4
GENERIC_MAX_COMPONENTS_PER_COLUMN = 16

STANDARD_LAYOUT_PAGE_TYPES: tuple[LayoutPageType, ...] = (
    LayoutPageType.HOME,
    LayoutPageType.CATEGORY_L0_L1,
    LayoutPageType.SEARCH_LN,
    LayoutPageType.URGENT_LISTINGS,
    LayoutPageType.CATEGORY_SHOWCASE,
    LayoutPageType.LISTING_DETAIL,
    LayoutPageType.LISTING_DETAIL_PARAMETERS,
    LayoutPageType.STOREFRONT_PROFILE,
    LayoutPageType.WIZARD_STEP_L0,
    LayoutPageType.WIZARD_STEP_LN,
    LayoutPageType.WIZARD_STEP_FORM,
    LayoutPageType.WIZARD_PREVIEW,
    LayoutPageType.WIZARD_DOPING_PAYMENT,
    LayoutPageType.WIZARD_RESULT,
    LayoutPageType.USER_DASHBOARD,
)

CORE_TEMPLATE_PAGE_TYPES: tuple[LayoutPageType, ...] = (
    LayoutPageType.HOME,
    LayoutPageType.URGENT_LISTINGS,
    LayoutPageType.CATEGORY_L0_L1,
    LayoutPageType.SEARCH_LN,
)

WIZARD_POLICY_PAGE_TYPES: set[LayoutPageType] = {
    LayoutPageType.WIZARD_STEP_L0,
    LayoutPageType.WIZARD_STEP_LN,
    LayoutPageType.WIZARD_STEP_FORM,
    LayoutPageType.WIZARD_PREVIEW,
    LayoutPageType.WIZARD_DOPING_PAYMENT,
    LayoutPageType.WIZARD_RESULT,
    LayoutPageType.LISTING_CREATE_STEPX,
}

SUPPORTED_I18N_LANGS: tuple[str, ...] = ("tr", "de", "fr")
TRANSLATABLE_PROP_KEYS = {
    "title",
    "description",
    "label",
    "body",
    "text",
    "headline",
    "subtitle",
    "cta_label",
    "campaign_label",
    "primary_label",
    "secondary_label",
    "note",
}

LOCKED_COMPONENT_POLICY_BY_KEY: dict[str, dict[str, Any]] = {
    "category.navigator": {
        "component": "Category Navigator",
        "menu_path": "Admin Panel → Katalog & İçerik → Kategoriler",
        "data_source": "Kategori ağacı (L0 / L1 / Ln)",
        "api": "GET /api/categories/tree?country=...&depth=L1|all",
        "source_options": "start_level=L0, depth=L1|Lall, placement=side|top",
        "usage": "Ana sayfa sol menü, acil sayfası, kategori sayfaları",
        "click_behavior": "/kategori/{slug}",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "layout.category-navigator-side": {
        "component": "Category Navigator",
        "menu_path": "Admin Panel → Katalog & İçerik → Kategoriler",
        "data_source": "Kategori ağacı (L0 / L1 / Ln)",
        "api": "GET /api/categories/tree?country=...&depth=L1|all",
        "source_options": "start_level=L0, depth=L1|Lall, placement=side|top",
        "usage": "Ana sayfa sol menü, acil sayfası, kategori sayfaları",
        "click_behavior": "/kategori/{slug}",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "layout.category-navigator-top": {
        "component": "Category Navigator",
        "menu_path": "Admin Panel → Katalog & İçerik → Kategoriler",
        "data_source": "Kategori ağacı (L0 / L1 / Ln)",
        "api": "GET /api/categories/tree?country=...&depth=L1|all",
        "source_options": "start_level=L0, depth=L1|Lall, placement=side|top",
        "usage": "Ana sayfa sol menü, acil sayfası, kategori sayfaları",
        "click_behavior": "/kategori/{slug}",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "cta.block": {
        "component": "CTA Block",
        "menu_path": "Menü çağırmaz",
        "data_source": "Manuel stil + Onaylı ilan havuzuna quick_filter yönlendirmesi",
        "api": "Doğrudan veri çekmez (route+query üretir)",
        "source_options": "mode=link|quick_filter (urgent/showcase/campaign)",
        "usage": "Acil / Vitrin / Kampanya yönlendirmesi",
        "click_behavior": "/acil?badge=urgent / /vitrin?badge=showcase / /kampanya?badge=campaign",
        "rbac_visibility": ["super_admin", "country_admin"],
        "locked": True,
    },
    "listing.grid": {
        "component": "Listing Grid",
        "menu_path": "Admin Panel → İlan & Moderasyon → Onaylı Tüm İlanlar",
        "data_source": "Onaylı ilan havuzu",
        "api": "GET /api/public/listings",
        "source_options": "showcase | urgent | campaign | latest | category",
        "usage": "Ana sayfa vitrin ilanları, kategori vitrini",
        "click_behavior": "İlan detayına yönlendirme",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "listing.list": {
        "component": "Listing List",
        "menu_path": "Admin Panel → İlan & Moderasyon → Onaylı Tüm İlanlar",
        "data_source": "İlan havuzu",
        "api": "GET /api/public/listings",
        "source_options": "urgent | category | search",
        "usage": "Acil, kategori liste ve arama sonuç sayfaları",
        "click_behavior": "İlan detayına yönlendirme",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "listing.card": {
        "component": "Listing Card",
        "menu_path": "Menü çağırmaz",
        "data_source": "Listing Grid/List çıktısı",
        "api": "GET /api/public/listings (upstream)",
        "source_options": "badge: urgent | showcase | campaign",
        "usage": "Grid/List görünümünde kart sunumu",
        "click_behavior": "İlan detayına yönlendirme",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "category.sub-category-block": {
        "component": "Sub Category Block",
        "menu_path": "Admin Panel → Katalog & İçerik → Kategoriler",
        "data_source": "Alt kategori listesi",
        "api": "GET /api/categories/children + GET /api/categories/listing-counts",
        "source_options": "columns | show_count | depth",
        "usage": "Kategori sayfalarında alt kırılımlar",
        "click_behavior": "/kategori/{slug}",
        "rbac_visibility": ["super_admin", "country_admin", "moderator"],
        "locked": True,
    },
    "ad.slot": {
        "component": "Ad Slot",
        "menu_path": "Admin Panel → Reklamlar → Reklam Yönetimi",
        "data_source": "Aktif reklam bannerları",
        "api": "GET /api/ads/resolve?placement=...&country=...",
        "source_options": "home_top | home_bottom | category_top | category_bottom | urgent_top",
        "usage": "Sayfa içi banner yerleşimleri",
        "click_behavior": "Reklam hedef URL yönlendirmesi",
        "rbac_visibility": ["super_admin", "ads_manager"],
        "locked": True,
    },
    "shared.ad-slot": {
        "component": "Ad Slot",
        "menu_path": "Admin Panel → Reklamlar → Reklam Yönetimi",
        "data_source": "Aktif reklam bannerları",
        "api": "GET /api/ads/resolve?placement=...&country=...",
        "source_options": "home_top | home_bottom | category_top | category_bottom | urgent_top",
        "usage": "Sayfa içi banner yerleşimleri",
        "click_behavior": "Reklam hedef URL yönlendirmesi",
        "rbac_visibility": ["super_admin", "ads_manager"],
        "locked": True,
    },
    "media.ad-promo-slot": {
        "component": "Ad Slot",
        "menu_path": "Admin Panel → Reklamlar → Reklam Yönetimi",
        "data_source": "Aktif reklam bannerları",
        "api": "GET /api/ads/resolve?placement=...&country=...",
        "source_options": "home_top | home_bottom | category_top | category_bottom | urgent_top",
        "usage": "Sayfa içi banner yerleşimleri",
        "click_behavior": "Reklam hedef URL yönlendirmesi",
        "rbac_visibility": ["super_admin", "ads_manager"],
        "locked": True,
    },
    "media.hero-banner": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "media.carousel": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "media.image": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "media.video": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "media.auto-play-carousel-hero": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "media.advanced-photo-gallery": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "media.video-3d-tour-player": {
        "component": "Hero Banner / Carousel / Image / Video",
        "menu_path": "Statik: Builder manuel • Dinamik: Reklamlar / Vitrin Yönetimi",
        "data_source": "Statik medya veya dinamik banner kaynağı",
        "api": "GET /api/banners?placement=...",
        "source_options": "static | dynamic",
        "usage": "Tanıtım ve vitrin medya alanları",
        "click_behavior": "CTA / hedef medya linki",
        "rbac_visibility": ["super_admin", "country_admin", "ads_manager"],
        "locked": True,
    },
    "map.block": {
        "component": "Map Block",
        "menu_path": "Admin Panel → Sistem Ayarları → Google Maps Ayarları",
        "data_source": "İlan konum bilgileri (latitude/longitude)",
        "api": "GET /api/public/listings",
        "source_options": "-",
        "usage": "İlan detay ve konum odaklı sayfalar",
        "click_behavior": "Harita etkileşimi / lokasyon odak",
        "rbac_visibility": ["super_admin", "country_admin"],
        "locked": True,
    },
    "interactive.interactive-map": {
        "component": "Map Block",
        "menu_path": "Admin Panel → Sistem Ayarları → Google Maps Ayarları",
        "data_source": "İlan konum bilgileri (latitude/longitude)",
        "api": "GET /api/public/listings",
        "source_options": "-",
        "usage": "İlan detay ve konum odaklı sayfalar",
        "click_behavior": "Harita etkileşimi / lokasyon odak",
        "rbac_visibility": ["super_admin", "country_admin"],
        "locked": True,
    },
}


def _resolve_locked_component_policy(key: str | None) -> Optional[dict[str, Any]]:
    normalized = str(key or "").strip().lower()
    if not normalized:
        return None
    policy = LOCKED_COMPONENT_POLICY_BY_KEY.get(normalized)
    if not policy:
        return None
    return {
        **policy,
        "rbac_visibility": list(policy.get("rbac_visibility") or []),
    }


def _normalize_i18n_lang(raw_lang: Optional[str]) -> str:
    normalized = str(raw_lang or "").strip().lower()
    return normalized if normalized in SUPPORTED_I18N_LANGS else "tr"


def _extract_user_preferred_lang(current_user: Any) -> Optional[str]:
    if not current_user:
        return None

    candidates: list[str] = []
    if isinstance(current_user, dict):
        candidates.extend([
            current_user.get("preferred_language"),
            current_user.get("language"),
            current_user.get("locale"),
        ])
    else:
        candidates.extend([
            getattr(current_user, "preferred_language", None),
            getattr(current_user, "language", None),
            getattr(current_user, "locale", None),
        ])

    for candidate in candidates:
        if not candidate:
            continue
        normalized = _normalize_i18n_lang(candidate)
        if normalized in SUPPORTED_I18N_LANGS:
            return normalized
    return None


def _extract_lang_from_accept_header(accept_language: Optional[str]) -> Optional[str]:
    raw = str(accept_language or "").strip()
    if not raw:
        return None
    for item in raw.split(","):
        part = item.split(";", 1)[0].strip().lower()
        if not part:
            continue
        primary = part.split("-", 1)[0]
        if primary in SUPPORTED_I18N_LANGS:
            return primary
    return None


def _resolve_request_i18n_lang(request: Optional[Request], current_user: Any = None) -> str:
    raw_url_lang = str(request.headers.get("x-url-locale") if request else "").strip().lower()
    if raw_url_lang in SUPPORTED_I18N_LANGS:
        return raw_url_lang

    user_lang = _extract_user_preferred_lang(current_user)
    if user_lang:
        return user_lang

    header_lang = _extract_lang_from_accept_header(request.headers.get("accept-language") if request else None)
    if header_lang:
        return header_lang

    return "tr"


def _is_i18n_value_map(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    keys = {str(key).strip().lower() for key in value.keys()}
    return bool(keys) and keys.issubset(set(SUPPORTED_I18N_LANGS))


def _normalize_i18n_text_map(value: Any, *, fallback_value: str = "") -> dict[str, str]:
    fallback = str(fallback_value or "")
    if _is_i18n_value_map(value):
        normalized = {lang: str(value.get(lang) or "").strip() for lang in SUPPORTED_I18N_LANGS}
        seed = normalized.get("tr") or normalized.get("de") or normalized.get("fr") or fallback
        return {
            "tr": normalized.get("tr") or seed,
            "de": normalized.get("de") or seed,
            "fr": normalized.get("fr") or seed,
        }

    seed = str(value or fallback).strip()
    return {"tr": seed, "de": seed, "fr": seed}


def _resolve_i18n_text(value: Any, lang: str) -> Any:
    if not _is_i18n_value_map(value):
        return value
    normalized_lang = _normalize_i18n_lang(lang)
    localized = value.get(normalized_lang)
    if isinstance(localized, str) and localized.strip():
        return localized
    for fallback_lang in SUPPORTED_I18N_LANGS:
        fallback_value = value.get(fallback_lang)
        if isinstance(fallback_value, str) and fallback_value.strip():
            return fallback_value
    return ""


def _localize_payload_values(value: Any, lang: str) -> Any:
    if isinstance(value, list):
        return [_localize_payload_values(item, lang) for item in value]
    if isinstance(value, dict):
        if _is_i18n_value_map(value):
            return _resolve_i18n_text(value, lang)
        return {key: _localize_payload_values(item, lang) for key, item in value.items()}
    return value


def _normalize_seed_props_i18n(props: Optional[dict[str, Any]]) -> dict[str, Any]:
    normalized_props: dict[str, Any] = {}
    for key, value in (props or {}).items():
        if isinstance(value, str) and key in TRANSLATABLE_PROP_KEYS:
            normalized_props[key] = _normalize_i18n_text_map(value)
            continue
        if isinstance(value, dict):
            normalized_props[key] = _normalize_seed_props_i18n(value)
            continue
        if isinstance(value, list):
            normalized_props[key] = [
                _normalize_seed_props_i18n(item) if isinstance(item, dict) else item
                for item in value
            ]
            continue
        normalized_props[key] = value
    return normalized_props


def _is_transient_db_error(exc: Exception) -> bool:
    if isinstance(exc, SQLAlchemyError):
        message = str(getattr(exc, "orig", exc) or "").lower()
    else:
        message = str(exc or "").lower()
    return any(marker in message for marker in TRANSIENT_DB_ERROR_MARKERS)


async def _run_with_db_retry(session: AsyncSession, operation, *, retries: int = 6):
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return await operation()
        except Exception as exc:
            last_exc = exc
            if attempt >= retries or not _is_transient_db_error(exc):
                raise
            try:
                await session.rollback()
            except Exception:
                pass
            await asyncio.sleep(min(0.9 * attempt, 3.0))
    if last_exc:
        raise last_exc
    raise RuntimeError("db_retry_operation_failed")


def _count_components(payload_json: dict[str, Any]) -> int:
    if not isinstance(payload_json, dict):
        return 0
    rows = payload_json.get("rows")
    if not isinstance(rows, list):
        return 0
    total = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        columns = row.get("columns")
        if not isinstance(columns, list):
            continue
        for col in columns:
            if not isinstance(col, dict):
                continue
            comps = col.get("components")
            if isinstance(comps, list):
                total += len(comps)
    return total


def _sanitize_payload_for_sql_ascii(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    if isinstance(value, list):
        return [_sanitize_payload_for_sql_ascii(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_payload_for_sql_ascii(val) for key, val in value.items()}
    return value


def _build_generic_layout_policy_report(payload_json: dict[str, Any], *, page_type: Optional[str] = None) -> dict[str, Any]:
    rows = payload_json.get("rows") if isinstance(payload_json, dict) else None
    stats = {
        "row_count": 0,
        "total_component_count": 0,
        "limit_violations": 0,
        "duplicate_id_violations": 0,
        "width_violations": 0,
    }

    if not isinstance(rows, list):
        checks = [
            {
                "id": "rows_structure",
                "label": "Rows yapısı",
                "status": "fail",
                "blocking": True,
                "detail": "rows dizisi zorunlu",
                "fix_suggestion": "Payload içinde rows dizisi oluşturun ve en az bir row ekleyin.",
            }
        ]
        return {
            "policy": "generic_layout",
            "page_type": page_type,
            "passed": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "suggested_fixes": [checks[0]["fix_suggestion"]],
            "stats": stats,
        }

    stats["row_count"] = len(rows)
    row_ids: set[str] = set()
    col_ids: set[str] = set()
    comp_ids: set[str] = set()

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
        if len(columns) > GENERIC_MAX_COLUMNS_PER_ROW:
            stats["limit_violations"] += 1

        for col in columns:
            if not isinstance(col, dict):
                stats["limit_violations"] += 1
                continue
            col_id = str(col.get("id") or "").strip()
            if not col_id or col_id in col_ids:
                stats["duplicate_id_violations"] += 1
            if col_id:
                col_ids.add(col_id)

            width = col.get("width") if isinstance(col.get("width"), dict) else {}
            for bp in ("desktop", "tablet", "mobile"):
                raw_width = width.get(bp)
                try:
                    parsed = int(raw_width)
                except (TypeError, ValueError):
                    stats["width_violations"] += 1
                    continue
                if parsed < 1 or parsed > 12:
                    stats["width_violations"] += 1

            components = col.get("components")
            if not isinstance(components, list):
                stats["limit_violations"] += 1
                continue
            if len(components) > GENERIC_MAX_COMPONENTS_PER_COLUMN:
                stats["limit_violations"] += 1

            for comp in components:
                stats["total_component_count"] += 1
                if not isinstance(comp, dict):
                    stats["limit_violations"] += 1
                    continue
                comp_id = str(comp.get("id") or "").strip()
                if not comp_id or comp_id in comp_ids:
                    stats["duplicate_id_violations"] += 1
                if comp_id:
                    comp_ids.add(comp_id)

    checks = [
        {
            "id": "rows_structure",
            "label": "Rows/Columns yapısı",
            "status": "pass" if stats["row_count"] > 0 else "fail",
            "blocking": True,
            "detail": f"Row sayısı: {stats['row_count']}",
            "fix_suggestion": "En az bir row ve her row içinde en az bir column tanımlayın.",
        },
        {
            "id": "layout_limits",
            "label": "Satır/Sütun/Bileşen limitleri",
            "status": "pass" if stats["row_count"] <= GENERIC_MAX_ROWS and stats["limit_violations"] == 0 else "fail",
            "blocking": True,
            "detail": f"Limit ihlali: {stats['limit_violations']}",
            "fix_suggestion": f"Row <= {GENERIC_MAX_ROWS}, column/row <= {GENERIC_MAX_COLUMNS_PER_ROW}, component/column <= {GENERIC_MAX_COMPONENTS_PER_COLUMN} olacak şekilde düzenleyin.",
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
        "policy": "generic_layout",
        "page_type": page_type,
        "passed": bool(passed),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "suggested_fixes": suggested_fixes,
        "stats": stats,
    }


def _autofix_generic_layout_payload(payload_json: dict[str, Any], *, default_component_key: str = "shared.text-block") -> tuple[dict[str, Any], list[str]]:
    actions: list[str] = []
    rows = payload_json.get("rows") if isinstance(payload_json, dict) else None
    if not isinstance(rows, list):
        rows = []
        actions.append("rows yapısı yoktu; boş layout iskeleti oluşturuldu.")

    row_ids: set[str] = set()
    col_ids: set[str] = set()
    comp_ids: set[str] = set()
    fixed_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(rows[:GENERIC_MAX_ROWS], start=1):
        if not isinstance(row, dict):
            actions.append(f"Geçersiz row atlandı (index: {row_index}).")
            continue

        row_id = str(row.get("id") or "").strip() or f"row-autofix-{row_index}"
        if row_id in row_ids:
            row_id = f"{row_id}-{row_index}"
        row_ids.add(row_id)

        raw_columns = row.get("columns") if isinstance(row.get("columns"), list) else []
        fixed_columns: list[dict[str, Any]] = []
        for col_index, column in enumerate(raw_columns[:GENERIC_MAX_COLUMNS_PER_ROW], start=1):
            if not isinstance(column, dict):
                continue
            col_id = str(column.get("id") or "").strip() or f"col-autofix-{row_index}-{col_index}"
            if col_id in col_ids:
                col_id = f"{col_id}-{col_index}"
            col_ids.add(col_id)

            width_payload = column.get("width") if isinstance(column.get("width"), dict) else {}
            fixed_width = {
                "desktop": max(1, min(12, _safe_int(width_payload.get("desktop"), fallback=12))),
                "tablet": max(1, min(12, _safe_int(width_payload.get("tablet"), fallback=12))),
                "mobile": max(1, min(12, _safe_int(width_payload.get("mobile"), fallback=12))),
            }

            raw_components = column.get("components") if isinstance(column.get("components"), list) else []
            fixed_components: list[dict[str, Any]] = []
            for cmp_index, component in enumerate(raw_components[:GENERIC_MAX_COMPONENTS_PER_COLUMN], start=1):
                if not isinstance(component, dict):
                    continue
                comp_id = str(component.get("id") or "").strip() or f"cmp-autofix-{row_index}-{col_index}-{cmp_index}"
                if comp_id in comp_ids:
                    comp_id = f"{comp_id}-{cmp_index}"
                comp_ids.add(comp_id)

                component_key = str(component.get("key") or "").strip() or default_component_key
                props = component.get("props") if isinstance(component.get("props"), dict) else {}
                visibility = component.get("visibility") if isinstance(component.get("visibility"), dict) else {
                    "desktop": True,
                    "tablet": True,
                    "mobile": True,
                }
                fixed_components.append(
                    {
                        "id": comp_id,
                        "key": component_key,
                        "props": props,
                        "visibility": visibility,
                    }
                )

            fixed_columns.append(
                {
                    "id": col_id,
                    "width": fixed_width,
                    "components": fixed_components,
                }
            )

        if not fixed_columns:
            fixed_columns.append(
                {
                    "id": f"col-autofix-{row_index}",
                    "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                    "components": [],
                }
            )
            actions.append(f"Row {row_id} için varsayılan column üretildi.")

        fixed_rows.append({"id": row_id, "columns": fixed_columns})

    if not fixed_rows:
        fixed_rows = [{"id": "row-autofix-1", "columns": [{"id": "col-autofix-1", "width": {"desktop": 12, "tablet": 12, "mobile": 12}, "components": []}]}]
        actions.append("Boş payload için varsayılan row/column üretildi.")

    total_components = sum(len(col.get("components") or []) for row in fixed_rows for col in (row.get("columns") or []))
    if total_components == 0:
        fixed_rows[0]["columns"][0]["components"].append(
            {
                "id": "cmp-autofix-default",
                "key": default_component_key,
                "props": {} if default_component_key != "shared.text-block" else {"title": "Varsayılan", "body": "Auto-fix ile eklendi"},
                "visibility": {"desktop": True, "tablet": True, "mobile": True},
            }
        )
        actions.append("Boş component listesine varsayılan bileşen eklendi.")

    return {"rows": fixed_rows}, actions


async def _ensure_layout_page_type_enum_values(session: AsyncSession) -> None:
    global _LAYOUT_ENUM_SYNCED
    if _LAYOUT_ENUM_SYNCED:
        return

    enum_values = [item.value for item in LayoutPageType]
    for value in enum_values:
        safe_value = str(value).replace("'", "''")
        await session.execute(text(f"ALTER TYPE layout_page_type ADD VALUE IF NOT EXISTS '{safe_value}'"))
    await session.commit()
    _LAYOUT_ENUM_SYNCED = True


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
    title_i18n: Optional[dict[str, str]] = None
    description_i18n: Optional[dict[str, str]] = None
    label_i18n: Optional[dict[str, str]] = None


class LayoutPagePatchPayload(BaseModel):
    country: Optional[str] = Field(default=None, min_length=2, max_length=5)
    module: Optional[str] = Field(default=None, min_length=2, max_length=64)
    category_id: Optional[str] = None
    title_i18n: Optional[dict[str, str]] = None
    description_i18n: Optional[dict[str, str]] = None
    label_i18n: Optional[dict[str, str]] = None


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


class LayoutPresetEventPayload(BaseModel):
    preset_id: str = Field(min_length=2, max_length=120)
    preset_label: str = Field(min_length=2, max_length=200)
    persona: str = Field(min_length=2, max_length=32)
    variant: str = Field(min_length=1, max_length=16)
    event_type: LayoutPresetEventType
    page_type: Optional[LayoutPageType] = None
    layout_page_id: Optional[str] = None
    country: Optional[str] = Field(default=None, min_length=2, max_length=5)
    module: Optional[str] = Field(default=None, min_length=2, max_length=64)
    metadata_json: dict = Field(default_factory=dict)


class LayoutSeedDefaultsPayload(BaseModel):
    country: str = Field(min_length=2, max_length=5)
    module: str = Field(min_length=2, max_length=64)
    persona: str = Field(default="individual", min_length=2, max_length=32)
    variant: str = Field(default="A", min_length=1, max_length=16)
    overwrite_existing_draft: bool = True


class LayoutRevisionCopyPayload(BaseModel):
    target_page_type: LayoutPageType
    country: str = Field(min_length=2, max_length=5)
    module: str = Field(min_length=2, max_length=64)
    category_id: Optional[str] = None
    publish_after_copy: bool = False


class LayoutRevisionActivePayload(BaseModel):
    is_active: bool


class StandardTemplatePackInstallPayload(BaseModel):
    countries: list[str] = Field(min_length=1, max_length=20)
    module: str = Field(min_length=2, max_length=64)
    persona: str = Field(default="individual", min_length=2, max_length=32)
    variant: str = Field(default="A", min_length=1, max_length=16)
    overwrite_existing_draft: bool = True
    publish_after_seed: bool = True
    include_extended_templates: bool = False


class LayoutResetAndWireframePayload(BaseModel):
    countries: list[str] = Field(default_factory=lambda: ["TR", "DE", "FR"], min_length=1, max_length=20)
    module: str = Field(default="global", min_length=2, max_length=64)
    passivate_all: bool = True
    hard_delete_demo_pages: bool = True


def _cache_key(country: str, module: str, page_type: LayoutPageType, category_id: Optional[str], lang: str = "tr") -> str:
    normalized_category = str(category_id or "").strip().lower()
    return f"{country.upper()}|{module.strip().lower()}|{page_type.value}|{normalized_category}|{_normalize_i18n_lang(lang)}"


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
    serialized = {
        "id": str(row.id),
        "key": row.key,
        "name": row.name,
        "schema_json": row.schema_json,
        "is_active": bool(row.is_active),
        "version": int(row.version),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
    policy = _resolve_locked_component_policy(row.key)
    if policy:
        serialized["policy_locked"] = True
        serialized["data_source_spec"] = policy
        if policy.get("component"):
            serialized["name"] = str(policy.get("component"))
    else:
        serialized["policy_locked"] = False
    return serialized


def _serialize_layout_page(row: LayoutPage) -> dict[str, Any]:
    title_i18n = _normalize_i18n_text_map(getattr(row, "title_i18n", {}) or {})
    description_i18n = _normalize_i18n_text_map(getattr(row, "description_i18n", {}) or {})
    label_i18n = _normalize_i18n_text_map(getattr(row, "label_i18n", {}) or {})
    return {
        "id": str(row.id),
        "page_type": row.page_type.value,
        "country": row.country,
        "module": row.module,
        "category_id": str(row.category_id) if row.category_id else None,
        "title_i18n": title_i18n,
        "description_i18n": description_i18n,
        "label_i18n": label_i18n,
        "title": _resolve_i18n_text(title_i18n, "tr"),
        "description": _resolve_i18n_text(description_i18n, "tr"),
        "label": _resolve_i18n_text(label_i18n, "tr"),
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
        "is_deleted": bool(getattr(row, "is_deleted", False)),
        "is_active": bool(getattr(row, "is_active", True)),
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "created_by": str(row.created_by) if row.created_by else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _parse_layout_status_filters(raw_statuses: Optional[str]) -> list[LayoutRevisionStatus]:
    normalized = str(raw_statuses or "draft,published").strip().lower()
    if not normalized:
        normalized = "draft,published"

    requested = [item.strip() for item in normalized.split(",") if item.strip()]
    allowed = {status.value: status for status in LayoutRevisionStatus}
    invalid = [item for item in requested if item not in allowed]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid statuses: {', '.join(invalid)}")
    return [allowed[item] for item in requested]


def _build_layout_scope(country: str, module: str, category_id: Optional[str]) -> str:
    normalized_country = str(country or "").upper()
    normalized_module = str(module or "").strip()
    normalized_category = str(category_id or "").strip()
    if normalized_category:
        return f"{normalized_country}/{normalized_module}/{normalized_category}"
    return f"{normalized_country}/{normalized_module}/global"


def _serialize_admin_layout_item(revision: LayoutRevision, page: LayoutPage) -> dict[str, Any]:
    revision_item = _serialize_layout_revision(revision)
    page_item = _serialize_layout_page(page)
    category_id = page_item.get("category_id")
    updated_at = revision_item.get("published_at") or revision_item.get("created_at")
    return {
        "id": revision_item["id"],
        "revision_id": revision_item["id"],
        "layout_page_id": page_item["id"],
        "page_type": page_item["page_type"],
        "country": page_item["country"],
        "module": page_item["module"],
        "category_id": category_id,
        "scope": _build_layout_scope(page_item["country"], page_item["module"], category_id),
        "status": revision_item["status"],
        "version": revision_item["version"],
        "is_deleted": revision_item["is_deleted"],
        "is_active": bool(revision_item.get("is_active", True)),
        "updated_at": updated_at,
        "published_at": revision_item["published_at"],
        "created_at": revision_item["created_at"],
        "payload_json": revision_item["payload_json"],
    }


def _normalize_standard_persona_or_400(raw_persona: str) -> str:
    normalized_persona = str(raw_persona or "individual").strip().lower()
    if normalized_persona not in {"individual", "corporate"}:
        raise HTTPException(status_code=400, detail="persona_must_be_individual_or_corporate")
    return normalized_persona


def _normalize_standard_variant_or_400(raw_variant: str) -> str:
    normalized_variant = str(raw_variant or "A").strip().upper()
    if normalized_variant not in {"A", "B"}:
        raise HTTPException(status_code=400, detail="variant_must_be_A_or_B")
    return normalized_variant


def _normalize_countries_or_400(countries: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in countries:
        token = str(value or "").strip().upper()
        if len(token) < 2 or len(token) > 5:
            raise HTTPException(status_code=400, detail=f"invalid_country: {value}")
        if token not in normalized:
            normalized.append(token)
    if not normalized:
        raise HTTPException(status_code=400, detail="countries_required")
    return normalized


def _parse_countries_csv_or_400(raw_countries: str) -> list[str]:
    return _normalize_countries_or_400([token for token in str(raw_countries or "").split(",") if token.strip()])


def _normalize_layout_list_state_filter_or_400(raw_state: Optional[str]) -> str:
    normalized = str(raw_state or "all").strip().lower()
    if normalized not in {"all", "active", "passive"}:
        raise HTTPException(status_code=400, detail="state_must_be_all_active_or_passive")
    return normalized


def _is_demo_revision_candidate(revision: LayoutRevision, page: LayoutPage) -> bool:
    payload = revision.payload_json or {}
    meta = payload.get("meta") if isinstance(payload, dict) else {}
    generated_by = str((meta or {}).get("generated_by") or "").strip().lower()
    if generated_by in {"agent-demo", "content-list-copy", "test-seed", "wireframe-home-v2"}:
        return True

    if page.page_type in {LayoutPageType.SEARCH_L1, LayoutPageType.SEARCH_L2, LayoutPageType.LISTING_CREATE_STEPX}:
        return True

    if revision.status == LayoutRevisionStatus.DRAFT and revision.published_at is None:
        revision_age = datetime.now(timezone.utc) - (revision.created_at or datetime.now(timezone.utc))
        if revision_age <= timedelta(days=14):
            return True

    return False


def _build_home_wireframe_payload(module: str = "global") -> dict[str, Any]:
    module_key = str(module or "global").strip() or "global"
    return {
        "meta": {
            "template_version": "wireframe-home-v2",
            "generated_by": "wireframe-home-v2",
            "template_locked_after_publish": False,
        },
        "rows": [
            _seed_row([
                _seed_column(12, [
                    _seed_component("shared.text-block", {
                        "title": "HEADER",
                        "body": "",
                    }),
                ]),
            ]),
            _seed_row([
                _seed_column(12, [
                    _seed_component("ad.slot", {
                        "placement": "home_top",
                        "size": "horizontal",
                        "rotation": "on",
                    }),
                ]),
            ]),
            _seed_row([
                _seed_column(3, [
                    _seed_component("cta.block", {
                        "mode": "quick_filter",
                        "quick_filter": "urgent",
                        "title": "ACİL İLANLAR",
                        "style": "danger",
                        "target": "same",
                        "font_size": 15,
                        "font_weight": "700",
                        "font_style": "normal",
                        "text_color": "#ffffff",
                        "bg_color": "#dc2626",
                    }),
                    _seed_component("category.navigator", {
                        "title": "KATEGORİLER",
                        "start_level": "L0",
                        "depth": "L1",
                        "placement": "side",
                        "module": module_key,
                        "show_counts": True,
                        "tree_behavior": "expanded",
                        "style_variant": "classic",
                    }),
                ]),
                _seed_column(9, [
                    _seed_component("content.heading", {
                        "text": "VİTRİN İLANLARI",
                        "font_size": 22,
                        "font_weight": "800",
                        "alignment": "left",
                    }),
                    _seed_component("listing.grid", {
                        "source": "showcase",
                        "columns": 3,
                        "rows": 3,
                        "auto_refresh": "30s",
                        "order": "newest",
                    }),
                    _seed_component("ad.slot", {
                        "placement": "home_bottom",
                        "size": "horizontal",
                        "rotation": "on",
                    }),
                ]),
            ]),
            _seed_row([
                _seed_column(12, [
                    _seed_component("shared.text-block", {
                        "title": "FOOTER",
                        "body": "",
                    }),
                ]),
            ]),
        ],
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


def _serialize_preset_event(row: LayoutPresetEvent) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "layout_page_id": str(row.layout_page_id) if row.layout_page_id else None,
        "page_type": row.page_type.value if row.page_type else None,
        "country": row.country,
        "module": row.module,
        "preset_id": row.preset_id,
        "preset_label": row.preset_label,
        "persona": row.persona,
        "variant": row.variant,
        "event_type": row.event_type.value,
        "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
        "metadata_json": row.metadata_json or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _is_wizard_policy_page_type(page_type: Optional[LayoutPageType]) -> bool:
    return bool(page_type and page_type in WIZARD_POLICY_PAGE_TYPES)


def get_default_component_key(page_type: Optional[LayoutPageType]) -> str:
    if page_type == LayoutPageType.HOME:
        return "home.default-content"
    if page_type in {
        LayoutPageType.SEARCH_L1,
        LayoutPageType.SEARCH_L2,
        LayoutPageType.SEARCH_LN,
        LayoutPageType.CATEGORY_L0_L1,
        LayoutPageType.CATEGORY_SHOWCASE,
        LayoutPageType.URGENT_LISTINGS,
    }:
        return "search.l1.default-content"
    if _is_wizard_policy_page_type(page_type):
        return "listing.create.default-content"
    return "shared.text-block"


def _seed_component(component_key: str, props: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {
        "id": f"cmp-{uuid.uuid4().hex[:10]}",
        "key": component_key,
        "props": _normalize_seed_props_i18n(props),
        "visibility": {"desktop": True, "tablet": True, "mobile": True},
    }


def _seed_column(desktop_width: int, components: list[dict[str, Any]]) -> dict[str, Any]:
    safe_width = max(1, min(12, int(desktop_width)))
    return {
        "id": f"col-{uuid.uuid4().hex[:10]}",
        "width": {"desktop": safe_width, "tablet": 12, "mobile": 12},
        "components": components,
    }


def _seed_row(columns: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": f"row-{uuid.uuid4().hex[:10]}",
        "columns": columns,
    }


def _build_standard_page_seed_payload(
    page_type: LayoutPageType,
    *,
    persona: str = "individual",
    variant: str = "A",
    module: str = "vehicle",
) -> dict[str, Any]:
    persona_key = "corporate" if str(persona).strip().lower() == "corporate" else "individual"
    variant_key = "B" if str(variant).strip().upper() == "B" else "A"
    module_key = str(module or "vehicle").strip() or "vehicle"
    media_assets = {
        "hero_slides": [
            "https://images.unsplash.com/photo-1760263137609-25926f9bd8d9?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzJ8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjYXIlMjBvbiUyMHJvYWQlMjBzdW5zZXR8ZW58MHx8fHwxNzcyNzkyMDQ2fDA&ixlib=rb-4.1.0&q=85",
            "https://images.unsplash.com/photo-1758499692478-13f7e297cd9f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA0MTJ8MHwxfHNlYXJjaHw0fHxsdXh1cnklMjBjYXIlMjBkcml2aW5nJTIwcm9hZHxlbnwwfHx8fDE3NzI3OTIxMjd8MA&ixlib=rb-4.1.0&q=85",
            "https://images.unsplash.com/photo-1764013290141-63b13e311906?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MjJ8MHwxfHNlYXJjaHw0fHxjYXIlMjBzaG93cm9vbSUyMGludGVyaW9yJTIwd2lkZXxlbnwwfHx8fDE3NzI3OTIxMzh8MA&ixlib=rb-4.1.0&q=85",
        ],
        "promo_banner": "https://images.unsplash.com/photo-1643142314913-0cf633d9bbb5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwxfHxjYXIlMjBkZWFsZXJzaGlwJTIwc2hvd3Jvb218ZW58MHx8fHwxNzcyNzkyMDM3fDA&ixlib=rb-4.1.0&q=85",
        "category_banner": "https://images.unsplash.com/photo-1763092262677-4fad66d03134?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MjJ8MHwxfHNlYXJjaHwxfHxjYXIlMjBzaG93cm9vbSUyMGludGVyaW9yJTIwd2lkZXxlbnwwfHx8fDE3NzI3OTIxMzh8MA&ixlib=rb-4.1.0&q=85",
    }

    if page_type == LayoutPageType.HOME:
        return {
            "meta": {
                "template_version": "finalized-p0-v1",
                "template_locked_after_publish": True,
            },
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("content.heading", {"text": "Ana Sayfa", "font_size": 40, "font_weight": "800", "alignment": "left"}),
                        _seed_component("content.text-block", {"text": "Vitrin, kategori keşfi ve hızlı aksiyon alanları.", "font_size": 15, "font_weight": "400", "alignment": "left"}),
                        _seed_component("media.hero-banner", {
                            "mode": "static",
                            "placement": "home_top",
                            "title": "Günün Vitrini",
                            "image_url": media_assets["hero_slides"][0],
                        }),
                        _seed_component("media.carousel", {
                            "mode": "static",
                            "placement": "home_top",
                            "auto_play_seconds": 5,
                            "show_overlay_text": True,
                            "slides": [
                                {"label": "Bugünün Fırsatları", "url": "/vitrin?badge=showcase"},
                                {"label": "Acil İlanlara Git", "url": "/acil?badge=urgent"},
                                {"label": "Kampanya Alanı", "url": "/kampanya?badge=campaign"},
                            ],
                            "images": media_assets["hero_slides"],
                        }),
                    ])
                ]),
                _seed_row([
                    _seed_column(3 if persona_key == "individual" else 4, [
                        _seed_component("category.navigator", {
                            "title": "Kategoriler",
                            "start_level": "L0",
                            "depth": "L1",
                            "placement": "side",
                            "module": module_key,
                            "show_counts": True,
                        }),
                    ]),
                    _seed_column(9 if persona_key == "individual" else 8, [
                        _seed_component("listing.grid", {
                            "source": "showcase",
                            "columns": 3 if variant_key == "B" else 4,
                            "rows": 2,
                            "auto_refresh": "30s",
                            "order": "newest",
                        }),
                    ]),
                ]),
                _seed_row([
                    _seed_column(4, [_seed_component("cta.block", {
                        "mode": "quick_filter",
                        "quick_filter": "urgent",
                        "title": "ACİL",
                        "style": "danger",
                        "target": "same",
                        "font_size": 15,
                        "font_weight": "700",
                        "font_style": "normal",
                        "text_color": "#ffffff",
                        "bg_color": "#dc2626",
                    })]),
                    _seed_column(4, [_seed_component("cta.block", {
                        "mode": "quick_filter",
                        "quick_filter": "showcase",
                        "title": "VİTRİN",
                        "style": "primary",
                        "target": "same",
                        "font_size": 15,
                        "font_weight": "700",
                        "font_style": "normal",
                        "text_color": "#ffffff",
                        "bg_color": "#1d4ed8",
                    })]),
                    _seed_column(4, [_seed_component("cta.block", {
                        "mode": "quick_filter",
                        "quick_filter": "campaign",
                        "title": "KAMPANYA / DOPING",
                        "style": "outline",
                        "target": "same",
                        "font_size": 14,
                        "font_weight": "700",
                        "font_style": "normal",
                        "text_color": "#0f172a",
                        "bg_color": "#f8fafc",
                    })]),
                ]),
                _seed_row([
                    _seed_column(12, [
                        _seed_component("media.image", {
                            "mode": "static",
                            "placement": "home_bottom",
                            "image_url": media_assets["promo_banner"],
                            "alt": "Ana sayfa kampanya banner",
                        }),
                        _seed_component("ad.slot", {
                            "placement": "home_bottom",
                            "size": "horizontal",
                            "rotation": "on",
                        }),
                    ])
                ]),
            ]
        }

    if page_type == LayoutPageType.CATEGORY_L0_L1:
        return {
            "meta": {
                "template_version": "finalized-p0-v1",
                "template_locked_after_publish": True,
            },
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("content.heading", {"text": "Kategori Sayfası", "font_size": 34, "font_weight": "800", "alignment": "left"}),
                        _seed_component("layout.breadcrumb-header"),
                        _seed_component("media.image", {
                            "mode": "static",
                            "placement": "category_top",
                            "image_url": media_assets["category_banner"],
                            "alt": "Kategori üst banner",
                        }),
                        _seed_component("category.navigator", {
                            "title": "Kategori Gezinme",
                            "start_level": "L0",
                            "depth": "L1",
                            "placement": "top",
                            "module": module_key,
                            "show_counts": True,
                        }),
                    ])
                ]),
                _seed_row([
                    _seed_column(4, [_seed_component("category.sub-category-block", {"columns": 1, "show_count": True, "depth": 2})]),
                    _seed_column(8, [
                        _seed_component("listing.grid", {
                            "source": "category",
                            "columns": 4,
                            "rows": 2,
                            "auto_refresh": "30s",
                            "order": "newest",
                        }),
                    ]),
                ]),
                _seed_row([
                    _seed_column(8, [_seed_component("listing.list", {"source": "category", "pagination": True, "per_page": 24, "order": "newest"})]),
                    _seed_column(4, [
                        _seed_component("ad.slot", {"placement": "category_top", "size": "horizontal", "rotation": "on"}),
                        _seed_component("cta.block", {
                            "mode": "quick_filter",
                            "quick_filter": "campaign",
                            "title": "KATEGORİ KAMPANYALARI",
                            "style": "outline",
                            "target": "same",
                            "font_size": 13,
                            "font_weight": "700",
                            "font_style": "normal",
                            "text_color": "#0f172a",
                            "bg_color": "#f8fafc",
                        }),
                    ]),
                ]),
                _seed_row([
                    _seed_column(12, [
                        _seed_component("media.image", {
                            "mode": "static",
                            "placement": "category_bottom",
                            "image_url": media_assets["hero_slides"][2],
                            "alt": "Kategori alt banner",
                        }),
                        _seed_component("ad.slot", {"placement": "category_bottom", "size": "horizontal", "rotation": "off"}),
                    ])
                ]),
            ]
        }

    if page_type == LayoutPageType.URGENT_LISTINGS:
        return {
            "meta": {
                "template_version": "finalized-p0-v1",
                "template_locked_after_publish": True,
            },
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("content.heading", {"text": "Acil İlanlar", "font_size": 36, "font_weight": "800", "alignment": "left"}),
                        _seed_component("content.text-block", {"text": "Acil badge taşıyan ilanların canlı listesi.", "font_size": 15, "font_weight": "400", "alignment": "left"}),
                        _seed_component("media.image", {
                            "mode": "static",
                            "placement": "urgent_top",
                            "image_url": media_assets["hero_slides"][1],
                            "alt": "Acil ilan banner",
                        }),
                        _seed_component("cta.block", {
                            "mode": "quick_filter",
                            "quick_filter": "urgent",
                            "title": "ACİL FİLTRESİ",
                            "style": "danger",
                            "target": "same",
                            "font_size": 14,
                            "font_weight": "700",
                            "font_style": "normal",
                            "text_color": "#ffffff",
                            "bg_color": "#dc2626",
                        }),
                    ])
                ]),
                _seed_row([
                    _seed_column(8, [_seed_component("listing.list", {"source": "urgent", "pagination": True, "per_page": 20, "order": "newest"})]),
                    _seed_column(4, [
                        _seed_component("media.image", {
                            "mode": "static",
                            "placement": "urgent_top",
                            "image_url": media_assets["promo_banner"],
                            "alt": "Acil sağ kolon banner",
                        }),
                        _seed_component("ad.slot", {"placement": "urgent_top", "size": "horizontal", "rotation": "on"}),
                        _seed_component("category.navigator", {
                            "title": "Hızlı Kategori",
                            "start_level": "L0",
                            "depth": "Lall",
                            "placement": "side",
                            "module": module_key,
                            "show_counts": True,
                        }),
                    ]),
                ]),
                _seed_row([
                    _seed_column(12, [_seed_component("listing.grid", {"source": "urgent", "columns": 3 if variant_key == "B" else 4, "rows": 2, "auto_refresh": "30s", "order": "newest"})])
                ]),
            ]
        }

    if page_type in {LayoutPageType.SEARCH_LN, LayoutPageType.CATEGORY_SHOWCASE}:
        header_text = "Vitrin Liste" if page_type == LayoutPageType.CATEGORY_SHOWCASE else "Liste Sayfası"
        return {
            "meta": {
                "template_version": "finalized-p0-v1",
                "template_locked_after_publish": True,
            },
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("content.heading", {"text": header_text, "font_size": 34, "font_weight": "800", "alignment": "left"}),
                        _seed_component("content.text-block", {"text": "Arama/kategori sorgusuna göre liste görünümü.", "font_size": 15, "font_weight": "400", "alignment": "left"}),
                        _seed_component("media.image", {
                            "mode": "static",
                            "placement": "category_top",
                            "image_url": media_assets["hero_slides"][0],
                            "alt": "Liste üst banner",
                        }),
                    ])
                ]),
                _seed_row([
                    _seed_column(3, [
                        _seed_component("category.navigator", {
                            "title": "Kategori Ağacı",
                            "start_level": "L0",
                            "depth": "Lall",
                            "placement": "side",
                            "module": module_key,
                            "show_counts": True,
                        }),
                        _seed_component("category.sub-category-block", {"columns": 1, "show_count": True, "depth": 2}),
                    ]),
                    _seed_column(9, [_seed_component("listing.list", {"source": "search", "pagination": True, "per_page": 20, "order": "newest"})]),
                ]),
                _seed_row([
                    _seed_column(12, [
                        _seed_component("listing.grid", {
                            "source": "showcase" if page_type == LayoutPageType.CATEGORY_SHOWCASE else "latest",
                            "columns": 4,
                            "rows": 2,
                            "auto_refresh": "off",
                            "order": "newest" if page_type == LayoutPageType.CATEGORY_SHOWCASE else "random",
                        }),
                        _seed_component("media.carousel", {
                            "mode": "static",
                            "placement": "category_bottom",
                            "auto_play_seconds": 6,
                            "show_overlay_text": True,
                            "slides": [
                                {"label": "Vitrin İlanlar", "url": "/vitrin?badge=showcase"},
                                {"label": "Kampanyalar", "url": "/kampanya?badge=campaign"},
                            ],
                            "images": [media_assets["category_banner"], media_assets["hero_slides"][1]],
                        }),
                        _seed_component("ad.slot", {"placement": "category_bottom", "size": "horizontal", "rotation": "off"}),
                    ])
                ]),
            ]
        }

    if page_type == LayoutPageType.LISTING_DETAIL:
        return {
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("layout.breadcrumb-header"),
                        _seed_component("media.advanced-photo-gallery"),
                        *([_seed_component("media.video-3d-tour-player", {"provider": "youtube", "source_url": "", "auto_play": False})] if variant_key == "B" else []),
                    ])
                ]),
                _seed_row([
                    _seed_column(8, [
                        _seed_component("data.price-title-block"),
                        _seed_component("data.attribute-grid-dynamic"),
                        _seed_component("data.description-text-area"),
                        _seed_component("interactive.similar-listings-slider", {"source": "similar", "max_items": 8}),
                    ]),
                    _seed_column(4, [
                        _seed_component("data.seller-card", {"show_rating": True, "show_membership": True, "show_all_listings_link": True}),
                        _seed_component("interactive.interactive-map", {"default_zoom": 14, "show_nearby_layers": True, "map_style": "standard"}),
                        _seed_component("layout.sticky-action-bar", {"position": "bottom", "primary_label": "Call Now", "secondary_label": "Send Message", "phone_number": ""}),
                    ]),
                ]),
            ]
        }

    if page_type == LayoutPageType.LISTING_DETAIL_PARAMETERS:
        return {
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("shared.text-block", {"title": "Listing Parameters", "body": "Standard seed layout for detailed parameter blocks."}),
                        _seed_component("data.attribute-grid-dynamic", {"include_modules": ["core_fields", "parameter_fields", "detail_groups"], "compact_mode": False}),
                    ])
                ])
            ]
        }

    if page_type == LayoutPageType.STOREFRONT_PROFILE:
        return {
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("shared.text-block", {"title": "Storefront Profile", "body": "Showcase and profile content for storefront pages."}),
                        _seed_component("data.seller-card"),
                    ])
                ]),
                _seed_row([
                    _seed_column(8, [_seed_component("interactive.similar-listings-slider", {"source": "seller_other", "max_items": 12})]),
                    _seed_column(4, [
                        _seed_component("interactive.interactive-map"),
                        _seed_component("media.ad-promo-slot", {"placement": "AD_HOME_TOP", "campaign_label": "Store Campaign"}),
                    ]),
                ]),
            ]
        }

    if page_type == LayoutPageType.USER_DASHBOARD:
        return {
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("shared.text-block", {"title": "User Dashboard", "body": "Standard content block for listings, favorites and quick actions."}),
                    ])
                ]),
                _seed_row([
                    _seed_column(6, [_seed_component("interactive.similar-listings-slider", {"source": "seller_other", "max_items": 6})]),
                    _seed_column(6, [_seed_component("data.seller-card")]),
                ]),
            ]
        }

    if page_type == LayoutPageType.WIZARD_DOPING_PAYMENT:
        return {
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("listing.create.default-content"),
                        _seed_component("shared.text-block", {"title": "Promotion and Payment", "body": "Select promotion packages and continue to payment."}),
                    ])
                ]),
                _seed_row([
                    _seed_column(12, [
                        _seed_component("interactive.doping-selector", {
                            "available_dopings": ["Premium", "Vitrin", "Anasayfa"] if persona_key == "corporate" else ["Vitrin", "Acil", "Anasayfa"],
                            "show_prices": True,
                            "default_selected": "Premium" if persona_key == "corporate" else "Vitrin",
                        }),
                        _seed_component("shared.ad-slot", {"placement": "AD_LOGIN_1"}),
                    ])
                ]),
            ]
        }

    if page_type in {
        LayoutPageType.WIZARD_STEP_L0,
        LayoutPageType.WIZARD_STEP_LN,
        LayoutPageType.WIZARD_STEP_FORM,
        LayoutPageType.WIZARD_PREVIEW,
        LayoutPageType.WIZARD_RESULT,
        LayoutPageType.LISTING_CREATE_STEPX,
    }:
        title_map = {
            LayoutPageType.WIZARD_STEP_L0: "Step 1 - Category",
            LayoutPageType.WIZARD_STEP_LN: "Step 2 - Subcategory",
            LayoutPageType.WIZARD_STEP_FORM: "Step 3 - Form",
            LayoutPageType.WIZARD_PREVIEW: "Step 4 - Preview",
            LayoutPageType.WIZARD_RESULT: "Step 5 - Result",
            LayoutPageType.LISTING_CREATE_STEPX: "Create Listing",
        }
        return {
            "rows": [
                _seed_row([
                    _seed_column(12, [
                        _seed_component("listing.create.default-content"),
                        _seed_component("shared.text-block", {
                            "title": title_map.get(page_type, "Create Listing Flow"),
                            "body": "This step is managed by a standardized template.",
                        }),
                    ])
                ]),
                _seed_row([
                    _seed_column(12, [
                        _seed_component("shared.ad-slot", {"placement": "AD_LOGIN_1"}),
                    ])
                ]),
            ]
        }

    return {
        "rows": [
            _seed_row([
                _seed_column(12, [
                    _seed_component(get_default_component_key(page_type)),
                    _seed_component("shared.text-block", {"title": "Standard Template", "body": "Default template applied for this page type."}),
                ])
            ])
        ]
    }


def _default_layout_page_i18n(page_type: LayoutPageType) -> dict[str, dict[str, str]]:
    title_map = {
        LayoutPageType.HOME: "Ana Sayfa",
        LayoutPageType.CATEGORY_L0_L1: "L0/L1 Kategori",
        LayoutPageType.SEARCH_LN: "Kategori Listeleme",
        LayoutPageType.URGENT_LISTINGS: "Acil Ilanlar",
        LayoutPageType.CATEGORY_SHOWCASE: "Kategori Vitrin",
        LayoutPageType.LISTING_DETAIL: "Ilan Detay",
        LayoutPageType.LISTING_DETAIL_PARAMETERS: "Ilan Parametreleri",
        LayoutPageType.STOREFRONT_PROFILE: "Magaza Profili",
        LayoutPageType.WIZARD_STEP_L0: "Ilan Ver Adim 1",
        LayoutPageType.WIZARD_STEP_LN: "Ilan Ver Adim 2",
        LayoutPageType.WIZARD_STEP_FORM: "Ilan Ver Adim 3",
        LayoutPageType.WIZARD_PREVIEW: "Ilan Ver Onizleme",
        LayoutPageType.WIZARD_DOPING_PAYMENT: "Doping ve Odeme",
        LayoutPageType.WIZARD_RESULT: "Ilan Ver Sonuc",
        LayoutPageType.USER_DASHBOARD: "Kullanici Paneli",
        LayoutPageType.SEARCH_L1: "Search L1",
        LayoutPageType.SEARCH_L2: "Search L2",
        LayoutPageType.LISTING_CREATE_STEPX: "Ilan Ver",
    }
    tr_title = title_map.get(page_type, page_type.value)
    return {
        "title_i18n": _normalize_i18n_text_map(tr_title),
        "description_i18n": _normalize_i18n_text_map(f"{tr_title} sayfasi icin varsayilan yerlesim"),
        "label_i18n": _normalize_i18n_text_map(tr_title),
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
            if not isinstance(title, (str, dict)):
                raise HTTPException(status_code=400, detail="listing_create_text_block_title_must_be_string")
            if isinstance(title, dict):
                title_map = _normalize_i18n_text_map(title)
                if any(len(str(value or "").strip()) > LISTING_TEXT_TITLE_MAX for value in title_map.values()):
                    raise HTTPException(status_code=400, detail="listing_create_text_block_title_too_long")
            elif len(title.strip()) > LISTING_TEXT_TITLE_MAX:
                raise HTTPException(status_code=400, detail="listing_create_text_block_title_too_long")
        if body is not None:
            if not isinstance(body, (str, dict)):
                raise HTTPException(status_code=400, detail="listing_create_text_block_body_must_be_string")
            if isinstance(body, dict):
                body_map = _normalize_i18n_text_map(body)
                if any(len(str(value or "").strip()) > LISTING_TEXT_BODY_MAX for value in body_map.values()):
                    raise HTTPException(status_code=400, detail="listing_create_text_block_body_too_long")
            elif len(body.strip()) > LISTING_TEXT_BODY_MAX:
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


def _safe_bool(value: Any, *, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return fallback


def _safe_int(value: Any, *, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _autofix_listing_payload(payload_json: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    actions: list[str] = []
    rows = payload_json.get("rows") if isinstance(payload_json, dict) else None
    if not isinstance(rows, list):
        rows = []
        actions.append("rows yapısı yoktu; boş layout iskeleti oluşturuldu.")

    row_ids: set[str] = set()
    col_ids: set[str] = set()
    cmp_ids: set[str] = set()

    fixed_rows: list[dict[str, Any]] = []
    default_component_count = 0
    doping_selector_count = 0

    for row_index, row in enumerate(rows[:LISTING_MAX_ROWS], start=1):
        if not isinstance(row, dict):
            actions.append(f"Row {row_index} geçersizdi; atlandı.")
            continue

        row_id = str(row.get("id") or "").strip() or f"row-autofix-{row_index}"
        if row_id in row_ids:
            row_id = f"{row_id}-{row_index}"
            actions.append(f"Duplicate row id düzeltildi: {row_id}")
        row_ids.add(row_id)

        raw_columns = row.get("columns")
        if not isinstance(raw_columns, list):
            raw_columns = []
            actions.append(f"Row {row_id} için columns dizisi oluşturuldu.")

        fixed_columns: list[dict[str, Any]] = []
        for col_index, column in enumerate(raw_columns[:LISTING_MAX_COLUMNS_PER_ROW], start=1):
            if not isinstance(column, dict):
                actions.append(f"Row {row_id} içindeki geçersiz column atlandı.")
                continue

            col_id = str(column.get("id") or "").strip() or f"col-autofix-{row_index}-{col_index}"
            if col_id in col_ids:
                col_id = f"{col_id}-{col_index}"
                actions.append(f"Duplicate column id düzeltildi: {col_id}")
            col_ids.add(col_id)

            width_payload = column.get("width") if isinstance(column.get("width"), dict) else {}
            fixed_width = {
                "desktop": max(1, min(12, _safe_int(width_payload.get("desktop"), fallback=12))),
                "tablet": max(1, min(12, _safe_int(width_payload.get("tablet"), fallback=12))),
                "mobile": max(1, min(12, _safe_int(width_payload.get("mobile"), fallback=12))),
            }

            raw_components = column.get("components")
            if not isinstance(raw_components, list):
                raw_components = []
                actions.append(f"Column {col_id} için components dizisi oluşturuldu.")

            fixed_components: list[dict[str, Any]] = []
            for cmp_index, component in enumerate(raw_components[:LISTING_MAX_COMPONENTS_PER_COLUMN], start=1):
                if not isinstance(component, dict):
                    actions.append(f"Column {col_id} içindeki geçersiz component atlandı.")
                    continue

                component_key = component.get("key")
                if component_key not in LISTING_CREATE_ALLOWED_COMPONENTS:
                    component_key = "shared.text-block"
                    actions.append(f"İzinli olmayan component text-block'a çevrildi (column: {col_id}).")

                component_id = str(component.get("id") or "").strip() or f"cmp-autofix-{row_index}-{col_index}-{cmp_index}"
                if component_id in cmp_ids:
                    component_id = f"{component_id}-{cmp_index}"
                    actions.append(f"Duplicate component id düzeltildi: {component_id}")
                cmp_ids.add(component_id)

                raw_props = component.get("props") if isinstance(component.get("props"), dict) else {}
                allowed_props = LISTING_CREATE_ALLOWED_COMPONENTS[component_key]
                cleaned_props = {key: raw_props.get(key) for key in raw_props.keys() if key in allowed_props}

                if component_key == "shared.text-block":
                    title = cleaned_props.get("title")
                    body = cleaned_props.get("body")
                    if isinstance(title, dict):
                        title_map = _normalize_i18n_text_map(title, fallback_value="Bilgilendirme")
                        cleaned_props["title"] = {
                            lang: str(text or "")[:LISTING_TEXT_TITLE_MAX]
                            for lang, text in title_map.items()
                        }
                    else:
                        cleaned_props["title"] = str(title or "Bilgilendirme")[:LISTING_TEXT_TITLE_MAX]

                    if isinstance(body, dict):
                        body_map = _normalize_i18n_text_map(body)
                        cleaned_props["body"] = {
                            lang: str(text or "")[:LISTING_TEXT_BODY_MAX]
                            for lang, text in body_map.items()
                        }
                    else:
                        cleaned_props["body"] = str(body or "")[:LISTING_TEXT_BODY_MAX]

                if component_key == "shared.ad-slot":
                    placement = str(cleaned_props.get("placement") or "").strip()
                    if placement not in LISTING_ALLOWED_AD_PLACEMENTS:
                        cleaned_props["placement"] = "AD_LOGIN_1"
                        actions.append(f"Column {col_id} ad-slot placement değeri AD_LOGIN_1 olarak düzeltildi.")

                if component_key == "interactive.doping-selector":
                    doping_selector_count += 1
                    if doping_selector_count > 1:
                        actions.append("Fazla doping-selector bileşeni kaldırıldı.")
                        continue

                    raw_options = cleaned_props.get("available_dopings")
                    if not isinstance(raw_options, list):
                        raw_options = []
                    normalized_options = [
                        str(item or "").strip()
                        for item in raw_options
                        if str(item or "").strip() in LISTING_ALLOWED_DOPING_PACKAGES
                    ][:LISTING_MAX_DOPING_OPTIONS]
                    if not normalized_options:
                        normalized_options = ["Vitrin", "Acil", "Anasayfa"]
                        actions.append("Doping seçenekleri whitelist'e göre varsayılana çekildi.")

                    cleaned_props["available_dopings"] = normalized_options
                    cleaned_props["show_prices"] = _safe_bool(cleaned_props.get("show_prices"), fallback=True)
                    selected = str(cleaned_props.get("default_selected") or "").strip()
                    cleaned_props["default_selected"] = selected if selected in normalized_options else normalized_options[0]

                if component_key == "listing.create.default-content":
                    default_component_count += 1
                    if default_component_count > 1:
                        actions.append("Fazla default-content bileşeni kaldırıldı.")
                        continue
                    cleaned_props = {}

                fixed_components.append(
                    {
                        "id": component_id,
                        "key": component_key,
                        "props": cleaned_props,
                        "visibility": component.get("visibility") if isinstance(component.get("visibility"), dict) else {
                            "desktop": True,
                            "tablet": True,
                            "mobile": True,
                        },
                    }
                )

            fixed_columns.append(
                {
                    "id": col_id,
                    "width": fixed_width,
                    "components": fixed_components,
                }
            )

        if not fixed_columns:
            generated_column_id = f"col-autofix-{row_index}-1"
            if generated_column_id in col_ids:
                generated_column_id = f"{generated_column_id}-{row_index}"
            col_ids.add(generated_column_id)
            fixed_columns.append(
                {
                    "id": generated_column_id,
                    "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                    "components": [],
                }
            )
            actions.append(f"Row {row_id} için varsayılan column üretildi.")

        fixed_rows.append(
            {
                "id": row_id,
                "columns": fixed_columns,
            }
        )

    if not fixed_rows:
        fixed_rows = [
            {
                "id": "row-autofix-1",
                "columns": [
                    {
                        "id": "col-autofix-1",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [],
                    }
                ],
            }
        ]
        row_ids.add("row-autofix-1")
        col_ids.add("col-autofix-1")
        actions.append("Boş payload için varsayılan row/column üretildi.")

    if default_component_count == 0:
        target_column = fixed_rows[0]["columns"][0]
        default_component_id = "cmp-autofix-default"
        if default_component_id in cmp_ids:
            default_component_id = f"{default_component_id}-{len(cmp_ids)+1}"
        cmp_ids.add(default_component_id)
        target_column["components"].insert(
            0,
            {
                "id": default_component_id,
                "key": "listing.create.default-content",
                "props": {},
                "visibility": {"desktop": True, "tablet": True, "mobile": True},
            },
        )
        actions.append("Eksik default-content bileşeni otomatik eklendi.")

    total_components = sum(
        len(column.get("components") or [])
        for row in fixed_rows
        for column in (row.get("columns") or [])
    )
    if total_components == 0:
        target_column = fixed_rows[0]["columns"][0]
        target_column["components"].append(
            {
                "id": "cmp-autofix-text",
                "key": "shared.text-block",
                "props": {"title": "Bilgilendirme", "body": "İçerik alanı otomatik düzeltme ile oluşturuldu."},
                "visibility": {"desktop": True, "tablet": True, "mobile": True},
            }
        )
        actions.append("Boş component listesine bilgilendirme text-block eklendi.")

    return {"rows": fixed_rows}, actions


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
    normalized_key = payload.key.strip()
    component_policy = _resolve_locked_component_policy(normalized_key)
    existing_result = await session.execute(
        select(LayoutComponentDefinition).where(LayoutComponentDefinition.key == normalized_key)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Component key already exists")

    try:
        row = await create_or_update_component_definition(
            session,
            key=normalized_key,
            name=str(component_policy.get("component")) if component_policy and component_policy.get("component") else payload.name.strip(),
            schema_json=payload.schema_json,
            is_active=True if component_policy else bool(payload.is_active),
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
    component_policy = _resolve_locked_component_policy(row.key)
    if component_policy:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "component_policy_locked",
                "message": "Bu component policy ile kilitli. Düzenleme devre dışı.",
            },
        )

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


@router.get("/admin/layouts")
async def list_admin_layouts(
    include_deleted: bool = Query(default=False),
    statuses: Optional[str] = Query(default="draft,published"),
    state: str = Query(default="all"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    status_filters = _parse_layout_status_filters(statuses)
    state_filter = _normalize_layout_list_state_filter_or_400(state)

    query = select(LayoutRevision, LayoutPage).join(LayoutPage, LayoutPage.id == LayoutRevision.layout_page_id)
    if status_filters:
        query = query.where(LayoutRevision.status.in_(status_filters))
    if not include_deleted:
        query = query.where(LayoutRevision.is_deleted.is_(False))
    if state_filter == "active":
        query = query.where(and_(LayoutRevision.is_deleted.is_(False), LayoutRevision.is_active.is_(True)))
    elif state_filter == "passive":
        query = query.where(
            (LayoutRevision.is_deleted.is_(True))
            | (LayoutRevision.is_active.is_(False))
        )

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = int(count_result.scalar() or 0)

    rows_result = await session.execute(
        query
        .order_by(desc(LayoutRevision.created_at), desc(LayoutRevision.version))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = rows_result.all()
    items = [_serialize_admin_layout_item(revision, layout_page) for revision, layout_page in rows]
    return {
        "items": items,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.delete("/admin/layouts/{revision_id}")
async def soft_delete_admin_layout(
    revision_id: str,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Layout revision not found")

    if bool(getattr(row, "is_deleted", False)):
        return {"ok": True, "already_deleted": True, "item": _serialize_layout_revision(row)}

    row.is_deleted = True
    row.is_active = False
    await write_layout_audit_log(
        session,
        actor_user_id=current_user.get("id"),
        action=LayoutAuditAction.ARCHIVE,
        entity_type="layout_revision",
        entity_id=str(row.id),
        before_json={"is_deleted": False, "is_active": True, "status": row.status.value},
        after_json={"is_deleted": True, "is_active": False, "status": row.status.value},
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    await session.commit()
    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_revision(row)}


@router.patch("/admin/layouts/{revision_id}/active")
async def set_admin_layout_active_state(
    revision_id: str,
    payload: LayoutRevisionActivePayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Layout revision not found")
    if bool(getattr(row, "is_deleted", False)):
        raise HTTPException(status_code=400, detail="deleted_revision_cannot_be_toggled")

    before = {
        "is_active": bool(getattr(row, "is_active", True)),
        "is_deleted": bool(getattr(row, "is_deleted", False)),
        "status": row.status.value,
    }
    row.is_active = bool(payload.is_active)

    await write_layout_audit_log(
        session,
        actor_user_id=current_user.get("id"),
        action=LayoutAuditAction.CREATE_REVISION,
        entity_type="layout_revision",
        entity_id=str(row.id),
        before_json=before,
        after_json={
            "is_active": bool(row.is_active),
            "is_deleted": bool(getattr(row, "is_deleted", False)),
            "status": row.status.value,
        },
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    await session.commit()
    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_revision(row)}


@router.post("/admin/layouts/{revision_id}/restore")
async def restore_admin_layout_revision(
    revision_id: str,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Layout revision not found")

    before = {
        "is_active": bool(getattr(row, "is_active", True)),
        "is_deleted": bool(getattr(row, "is_deleted", False)),
        "status": row.status.value,
    }
    row.is_deleted = False
    row.is_active = True

    await write_layout_audit_log(
        session,
        actor_user_id=current_user.get("id"),
        action=LayoutAuditAction.CREATE_REVISION,
        entity_type="layout_revision",
        entity_id=str(row.id),
        before_json=before,
        after_json={
            "is_active": bool(row.is_active),
            "is_deleted": bool(getattr(row, "is_deleted", False)),
            "status": row.status.value,
        },
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    await session.commit()
    _invalidate_resolve_cache()
    return {"ok": True, "item": _serialize_layout_revision(row)}


@router.post("/admin/layouts/workflows/reset-and-seed-home-wireframe")
async def reset_layouts_and_seed_home_wireframe(
    payload: LayoutResetAndWireframePayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    await _ensure_layout_page_type_enum_values(session)

    normalized_countries = _normalize_countries_or_400(payload.countries)
    normalized_module = str(payload.module or "global").strip()
    passivate_all = bool(payload.passivate_all)
    hard_delete_demo_pages = bool(payload.hard_delete_demo_pages)

    revisions_result = await session.execute(
        select(LayoutRevision, LayoutPage)
        .join(LayoutPage, LayoutPage.id == LayoutRevision.layout_page_id)
        .where(LayoutRevision.status.in_([LayoutRevisionStatus.DRAFT, LayoutRevisionStatus.PUBLISHED]))
        .order_by(desc(LayoutRevision.created_at))
    )
    revision_pairs = revisions_result.all()

    summary = {
        "hard_deleted_demo_revisions": 0,
        "passivated_revisions": 0,
        "reactivated_home_revisions": 0,
        "home_pages_touched": 0,
    }

    for revision_row, page_row in revision_pairs:
        if hard_delete_demo_pages and _is_demo_revision_candidate(revision_row, page_row):
            await session.delete(revision_row)
            summary["hard_deleted_demo_revisions"] += 1
            continue

        if passivate_all:
            changed = False
            if bool(getattr(revision_row, "is_active", True)):
                revision_row.is_active = False
                changed = True
            if bool(getattr(revision_row, "is_deleted", False)):
                revision_row.is_deleted = False
                changed = True
            if changed:
                summary["passivated_revisions"] += 1

    for country_code in normalized_countries:
        page_result = await session.execute(
            select(LayoutPage)
            .where(
                and_(
                    LayoutPage.page_type == LayoutPageType.HOME,
                    LayoutPage.country == country_code,
                    LayoutPage.module == normalized_module,
                    LayoutPage.category_id.is_(None),
                )
            )
            .order_by(desc(LayoutPage.updated_at), desc(LayoutPage.created_at))
            .limit(1)
        )
        page_row = page_result.scalar_one_or_none()
        if not page_row:
            i18n = _default_layout_page_i18n(LayoutPageType.HOME)
            page_row = await create_layout_page(
                session,
                page_type=LayoutPageType.HOME,
                country=country_code,
                module=normalized_module,
                category_id=None,
                title_i18n=i18n["title_i18n"],
                description_i18n=i18n["description_i18n"],
                label_i18n=i18n["label_i18n"],
                actor_user_id=current_user.get("id"),
            )

        draft_row = await create_draft_revision(
            session,
            layout_page_id=str(page_row.id),
            payload_json=_build_home_wireframe_payload(module=normalized_module),
            actor_user_id=current_user.get("id"),
        )
        draft_row.is_active = True

        published_row = await publish_revision(
            session,
            revision_id=str(draft_row.id),
            actor_user_id=current_user.get("id"),
        )
        published_row.is_active = True

        await write_layout_audit_log(
            session,
            actor_user_id=current_user.get("id"),
            action=LayoutAuditAction.PUBLISH,
            entity_type="layout_page",
            entity_id=str(page_row.id),
            before_json={
                "country": country_code,
                "module": normalized_module,
            },
            after_json={
                "country": country_code,
                "module": normalized_module,
                "wireframe_revision_id": str(published_row.id),
            },
            ip=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )

        summary["home_pages_touched"] += 1
        summary["reactivated_home_revisions"] += 1

    await session.commit()
    _invalidate_resolve_cache()
    return {
        "ok": True,
        "countries": normalized_countries,
        "module": normalized_module,
        "summary": summary,
    }


@router.post("/admin/layouts/{revision_id}/copy")
async def copy_admin_layout_revision(
    revision_id: str,
    payload: LayoutRevisionCopyPayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    await _ensure_layout_page_type_enum_values(session)

    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    source_revision = await session.get(LayoutRevision, revision_uuid)
    if not source_revision or bool(getattr(source_revision, "is_deleted", False)):
        raise HTTPException(status_code=404, detail="Layout revision not found")

    source_page = await session.get(LayoutPage, source_revision.layout_page_id)
    if not source_page:
        raise HTTPException(status_code=404, detail="Source layout page not found")

    target_country = payload.country.upper().strip()
    target_module = payload.module.strip()
    target_category_uuid = _as_uuid_or_400(payload.category_id, field_name="category_id") if payload.category_id else None

    target_page_result = await session.execute(
        select(LayoutPage)
        .where(
            and_(
                LayoutPage.page_type == payload.target_page_type,
                LayoutPage.country == target_country,
                LayoutPage.module == target_module,
                LayoutPage.category_id == target_category_uuid,
            )
        )
        .order_by(desc(LayoutPage.updated_at), desc(LayoutPage.created_at))
        .limit(1)
    )
    target_page = target_page_result.scalar_one_or_none()

    if not target_page:
        target_page = await create_layout_page(
            session,
            page_type=payload.target_page_type,
            country=target_country,
            module=target_module,
            category_id=str(target_category_uuid) if target_category_uuid else None,
            title_i18n=_normalize_i18n_text_map(source_page.title_i18n or {}, fallback_value=payload.target_page_type.value),
            description_i18n=_normalize_i18n_text_map(source_page.description_i18n or {}, fallback_value=""),
            label_i18n=_normalize_i18n_text_map(source_page.label_i18n or {}, fallback_value=payload.target_page_type.value),
            actor_user_id=current_user.get("id"),
        )

    copied_payload = _sanitize_payload_for_sql_ascii(source_revision.payload_json or {})
    draft_result = await session.execute(
        select(LayoutRevision)
        .where(
            and_(
                LayoutRevision.layout_page_id == target_page.id,
                LayoutRevision.status == LayoutRevisionStatus.DRAFT,
                LayoutRevision.is_deleted.is_(False),
            )
        )
        .order_by(desc(LayoutRevision.version), desc(LayoutRevision.created_at))
        .limit(1)
    )
    target_revision = draft_result.scalar_one_or_none()

    action = "created_draft"
    if target_revision:
        before = {
            "status": target_revision.status.value,
            "version": int(target_revision.version),
            "is_deleted": bool(target_revision.is_deleted),
        }
        target_revision.payload_json = copied_payload
        target_revision.is_deleted = False
        target_revision.is_active = bool(getattr(source_revision, "is_active", True))
        await write_layout_audit_log(
            session,
            actor_user_id=current_user.get("id"),
            action=LayoutAuditAction.CREATE_REVISION,
            entity_type="layout_revision",
            entity_id=str(target_revision.id),
            before_json=before,
            after_json={
                "status": target_revision.status.value,
                "version": int(target_revision.version),
                "is_deleted": bool(target_revision.is_deleted),
                "copied_from_revision_id": str(source_revision.id),
            },
            ip=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
        action = "updated_draft"
    else:
        target_revision = await create_draft_revision(
            session,
            layout_page_id=str(target_page.id),
            payload_json=copied_payload,
            actor_user_id=current_user.get("id"),
        )
        target_revision.is_active = bool(getattr(source_revision, "is_active", True))

    if payload.publish_after_copy:
        target_revision = await publish_revision(
            session,
            revision_id=str(target_revision.id),
            actor_user_id=current_user.get("id"),
        )
        action = "published_copy"

    await session.commit()
    _invalidate_resolve_cache()
    return {
        "ok": True,
        "action": action,
        "source_revision_id": str(source_revision.id),
        "target_page": _serialize_layout_page(target_page),
        "target_revision": _serialize_layout_revision(target_revision),
    }


@router.post("/admin/site/content-layout/pages")
async def create_layout_page_admin(
    payload: LayoutPageCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    await _ensure_layout_page_type_enum_values(session)
    try:
        async def _op():
            created_row = await create_layout_page(
                session,
                page_type=payload.page_type,
                country=payload.country,
                module=payload.module,
                category_id=payload.category_id,
                title_i18n=_normalize_i18n_text_map(payload.title_i18n or {}, fallback_value=payload.page_type.value),
                description_i18n=_normalize_i18n_text_map(payload.description_i18n or {}, fallback_value=""),
                label_i18n=_normalize_i18n_text_map(payload.label_i18n or {}, fallback_value=payload.page_type.value),
                actor_user_id=current_user.get("id"),
            )
            await session.commit()
            return created_row

        row = await _run_with_db_retry(session, _op)
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
    if payload.title_i18n is not None:
        row.title_i18n = _normalize_i18n_text_map(payload.title_i18n, fallback_value=row.page_type.value)
    if payload.description_i18n is not None:
        row.description_i18n = _normalize_i18n_text_map(payload.description_i18n)
    if payload.label_i18n is not None:
        row.label_i18n = _normalize_i18n_text_map(payload.label_i18n, fallback_value=row.page_type.value)
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


async def _seed_standard_pages_for_scope(
    session: AsyncSession,
    *,
    actor_user_id: Optional[str],
    country: str,
    module: str,
    persona: str,
    variant: str,
    overwrite_existing_draft: bool,
    publish_after_seed: bool,
    page_types: Optional[list[LayoutPageType]] = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary = {
        "created_pages": 0,
        "created_drafts": 0,
        "updated_drafts": 0,
        "skipped_drafts": 0,
        "published_revisions": 0,
    }
    seeded_items: list[dict[str, Any]] = []

    target_page_types = page_types or list(STANDARD_LAYOUT_PAGE_TYPES)

    for page_type in target_page_types:
        page_result = await session.execute(
            select(LayoutPage)
            .where(
                and_(
                    LayoutPage.page_type == page_type,
                    LayoutPage.country == country,
                    LayoutPage.module == module,
                    LayoutPage.category_id.is_(None),
                )
            )
            .order_by(desc(LayoutPage.updated_at), desc(LayoutPage.created_at))
            .limit(1)
        )
        page_row = page_result.scalar_one_or_none()

        page_created = False
        page_i18n = _default_layout_page_i18n(page_type)
        if not page_row:
            page_row = await create_layout_page(
                session,
                page_type=page_type,
                country=country,
                module=module,
                category_id=None,
                title_i18n=page_i18n["title_i18n"],
                description_i18n=page_i18n["description_i18n"],
                label_i18n=page_i18n["label_i18n"],
                actor_user_id=actor_user_id,
            )
            page_created = True
            summary["created_pages"] += 1
        else:
            has_mutation = False
            if not isinstance(page_row.title_i18n, dict) or not page_row.title_i18n:
                page_row.title_i18n = page_i18n["title_i18n"]
                has_mutation = True
            if not isinstance(page_row.description_i18n, dict) or not page_row.description_i18n:
                page_row.description_i18n = page_i18n["description_i18n"]
                has_mutation = True
            if not isinstance(page_row.label_i18n, dict) or not page_row.label_i18n:
                page_row.label_i18n = page_i18n["label_i18n"]
                has_mutation = True
            if has_mutation:
                page_row.updated_at = datetime.now(timezone.utc)

        seed_payload = _build_standard_page_seed_payload(
            page_type,
            persona=persona,
            variant=variant,
            module=module,
        )

        draft_result = await session.execute(
            select(LayoutRevision)
            .where(
                and_(
                    LayoutRevision.layout_page_id == page_row.id,
                    LayoutRevision.status == LayoutRevisionStatus.DRAFT,
                    LayoutRevision.is_deleted.is_(False),
                )
            )
            .order_by(desc(LayoutRevision.version), desc(LayoutRevision.created_at))
            .limit(1)
        )
        draft_row = draft_result.scalar_one_or_none()

        draft_action = "skipped"
        if draft_row:
            if overwrite_existing_draft:
                draft_row.payload_json = seed_payload
                draft_row.is_active = True
                draft_action = "updated"
                summary["updated_drafts"] += 1
            else:
                summary["skipped_drafts"] += 1
        else:
            draft_row = await create_draft_revision(
                session,
                layout_page_id=str(page_row.id),
                payload_json=seed_payload,
                actor_user_id=actor_user_id,
            )
            draft_row.is_active = True
            draft_action = "created"
            summary["created_drafts"] += 1

        published_revision_id: Optional[str] = None
        if publish_after_seed and draft_row and draft_row.status == LayoutRevisionStatus.DRAFT:
            published_row = await publish_revision(
                session,
                revision_id=str(draft_row.id),
                actor_user_id=actor_user_id,
            )
            published_row.is_active = True
            published_revision_id = str(published_row.id)
            summary["published_revisions"] += 1

        seeded_items.append(
            {
                "page_type": page_type.value,
                "layout_page_id": str(page_row.id),
                "layout_page_created": page_created,
                "draft_revision_id": str(draft_row.id) if draft_row else None,
                "draft_action": draft_action,
                "published_revision_id": published_revision_id,
            }
        )

    return summary, seeded_items


@router.post("/admin/site/content-layout/pages/seed-defaults")
async def seed_standard_layout_pages_admin(
    payload: LayoutSeedDefaultsPayload,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    await _ensure_layout_page_type_enum_values(session)

    normalized_country = payload.country.upper().strip()
    normalized_module = payload.module.strip()
    normalized_persona = _normalize_standard_persona_or_400(payload.persona)
    normalized_variant = _normalize_standard_variant_or_400(payload.variant)

    async def _op():
        summary, seeded_items = await _seed_standard_pages_for_scope(
            session,
            actor_user_id=current_user.get("id"),
            country=normalized_country,
            module=normalized_module,
            persona=normalized_persona,
            variant=normalized_variant,
            overwrite_existing_draft=bool(payload.overwrite_existing_draft),
            publish_after_seed=False,
        )
        await session.commit()
        return summary, seeded_items

    try:
        summary, items = await _run_with_db_retry(session, _op)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="seed_defaults_conflict") from exc

    return {
        "ok": True,
        "country": normalized_country,
        "module": normalized_module,
        "persona": normalized_persona,
        "variant": normalized_variant,
        "summary": summary,
        "items": items,
    }


@router.post("/admin/site/content-layout/preset/install-standard-pack")
async def install_standard_template_pack(
    payload: StandardTemplatePackInstallPayload,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    normalized_countries = _normalize_countries_or_400(payload.countries)
    normalized_module = payload.module.strip()
    normalized_persona = _normalize_standard_persona_or_400(payload.persona)
    normalized_variant = _normalize_standard_variant_or_400(payload.variant)
    target_page_types = list(STANDARD_LAYOUT_PAGE_TYPES if payload.include_extended_templates else CORE_TEMPLATE_PAGE_TYPES)

    try:
        await _ensure_layout_page_type_enum_values(session)
    except Exception as exc:
        try:
            await session.rollback()
        except Exception:
            pass
        return {
            "ok": False,
            "module": normalized_module,
            "countries": normalized_countries,
            "persona": normalized_persona,
            "variant": normalized_variant,
            "publish_after_seed": bool(payload.publish_after_seed),
            "include_extended_templates": bool(payload.include_extended_templates),
            "template_scope": "extended" if payload.include_extended_templates else "core",
            "summary": {
                "created_pages": 0,
                "created_drafts": 0,
                "updated_drafts": 0,
                "skipped_drafts": 0,
                "published_revisions": 0,
            },
            "results": [],
            "failed_countries": [
                {
                    "country": country_code,
                    "error": "db_error",
                    "detail": str(exc),
                }
                for country_code in normalized_countries
            ],
        }

    aggregate_summary = {
        "created_pages": 0,
        "created_drafts": 0,
        "updated_drafts": 0,
        "skipped_drafts": 0,
        "published_revisions": 0,
    }
    results: list[dict[str, Any]] = []
    failed_countries: list[dict[str, Any]] = []

    for country_code in normalized_countries:
        async def _country_op():
            summary, items = await _seed_standard_pages_for_scope(
                session,
                actor_user_id=current_user.get("id"),
                country=country_code,
                module=normalized_module,
                persona=normalized_persona,
                variant=normalized_variant,
                overwrite_existing_draft=bool(payload.overwrite_existing_draft),
                publish_after_seed=bool(payload.publish_after_seed),
                page_types=target_page_types,
            )
            await session.commit()
            return summary, items

        try:
            summary, items = await _run_with_db_retry(session, _country_op, retries=6)
            for key in aggregate_summary:
                aggregate_summary[key] += int(summary.get(key, 0))
            results.append(
                {
                    "country": country_code,
                    "module": normalized_module,
                    "summary": summary,
                    "items": items,
                }
            )
        except ValueError as exc:
            await session.rollback()
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except IntegrityError as exc:
            await session.rollback()
            failed_countries.append(
                {
                    "country": country_code,
                    "error": "preset_install_conflict",
                    "detail": str(exc),
                }
            )
        except Exception as exc:
            await session.rollback()
            failed_countries.append(
                {
                    "country": country_code,
                    "error": "db_error" if _is_transient_db_error(exc) else "operation_error",
                    "detail": str(exc),
                }
            )
            continue

    return {
        "ok": len(failed_countries) == 0,
        "module": normalized_module,
        "countries": normalized_countries,
        "persona": normalized_persona,
        "variant": normalized_variant,
        "publish_after_seed": bool(payload.publish_after_seed),
        "include_extended_templates": bool(payload.include_extended_templates),
        "template_scope": "extended" if payload.include_extended_templates else "core",
        "summary": aggregate_summary,
        "results": results,
        "failed_countries": failed_countries,
    }


@router.get("/admin/site/content-layout/preset/verify-standard-pack")
async def verify_standard_template_pack(
    countries: str = Query(..., min_length=2),
    module: str = Query(..., min_length=2, max_length=64),
    include_extended_templates: bool = Query(default=False),
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    normalized_countries = _parse_countries_csv_or_400(countries)
    normalized_module = module.strip()
    target_page_types = list(STANDARD_LAYOUT_PAGE_TYPES if include_extended_templates else CORE_TEMPLATE_PAGE_TYPES)

    matrix: list[dict[str, Any]] = []
    ready_rows = 0
    total_rows = len(normalized_countries) * len(target_page_types)

    for country_code in normalized_countries:
        for page_type in target_page_types:
            page_result = await session.execute(
                select(LayoutPage)
                .where(
                    and_(
                        LayoutPage.page_type == page_type,
                        LayoutPage.country == country_code,
                        LayoutPage.module == normalized_module,
                        LayoutPage.category_id.is_(None),
                    )
                )
                .order_by(desc(LayoutPage.updated_at), desc(LayoutPage.created_at))
                .limit(1)
            )
            page_row = page_result.scalar_one_or_none()

            published_revision = None
            if page_row:
                published_result = await session.execute(
                    select(LayoutRevision)
                    .where(
                        and_(
                            LayoutRevision.layout_page_id == page_row.id,
                            LayoutRevision.status == LayoutRevisionStatus.PUBLISHED,
                            LayoutRevision.is_deleted.is_(False),
                        )
                    )
                    .order_by(desc(LayoutRevision.version), desc(LayoutRevision.created_at))
                    .limit(1)
                )
                published_revision = published_result.scalar_one_or_none()

            is_ready = bool(page_row and published_revision and bool(getattr(published_revision, "is_active", False)))
            if is_ready:
                ready_rows += 1

            matrix.append(
                {
                    "country": country_code,
                    "module": normalized_module,
                    "page_type": page_type.value,
                    "layout_page_id": str(page_row.id) if page_row else None,
                    "published_revision_id": str(published_revision.id) if published_revision else None,
                    "published_revision_active": bool(getattr(published_revision, "is_active", False)) if published_revision else False,
                    "published_at": published_revision.published_at.isoformat() if published_revision and published_revision.published_at else None,
                    "is_ready": is_ready,
                }
            )

    return {
        "ok": True,
        "module": normalized_module,
        "countries": normalized_countries,
        "include_extended_templates": bool(include_extended_templates),
        "template_scope": "extended" if include_extended_templates else "core",
        "summary": {
            "ready_rows": ready_rows,
            "total_rows": total_rows,
            "ready_ratio": round((ready_rows / total_rows) * 100, 2) if total_rows else 0,
        },
        "items": matrix,
    }


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
    if _is_wizard_policy_page_type(page_row.page_type):
        _validate_listing_runtime_guard_or_400(payload.payload_json)

    safe_payload = _sanitize_payload_for_sql_ascii(payload.payload_json)

    try:
        async def _op():
            created_row = await create_draft_revision(
                session,
                layout_page_id=page_id,
                payload_json=safe_payload,
                actor_user_id=current_user.get("id"),
            )
            await session.commit()
            return created_row

        row = await _run_with_db_retry(session, _op)
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
    if bool(getattr(row, "is_deleted", False)):
        raise HTTPException(status_code=404, detail="Revision not found")
    if row.status != LayoutRevisionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft revisions can be updated")

    page_row = await session.get(LayoutPage, row.layout_page_id)
    if page_row and _is_wizard_policy_page_type(page_row.page_type):
        _validate_listing_runtime_guard_or_400(payload.payload_json)

    before_payload = row.payload_json or {}
    before = {
        "id": str(row.id),
        "status": row.status.value,
        "version": int(row.version),
        "row_count": len(before_payload.get("rows") or []) if isinstance(before_payload, dict) else 0,
        "component_count": _count_components(before_payload),
    }
    row.payload_json = _sanitize_payload_for_sql_ascii(payload.payload_json or {})
    after_payload = row.payload_json or {}

    try:
        await write_layout_audit_log(
            session,
            actor_user_id=current_user.get("id"),
            action=LayoutAuditAction.CREATE_REVISION,
            entity_type="layout_revision",
            entity_id=str(row.id),
            before_json=before,
            after_json={
                "id": str(row.id),
                "status": row.status.value,
                "version": int(row.version),
                "row_count": len(after_payload.get("rows") or []) if isinstance(after_payload, dict) else 0,
                "component_count": _count_components(after_payload),
            },
            ip=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
        )
    except Exception:
        logger.warning("layout_draft_audit_skipped", exc_info=True)

    async def _op():
        await session.commit()
        return True

    await _run_with_db_retry(session, _op)
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
        if bool(getattr(target_revision, "is_deleted", False)):
            raise HTTPException(status_code=404, detail="Revision not found")
        page_row = await session.get(LayoutPage, target_revision.layout_page_id)
        if page_row and _is_wizard_policy_page_type(page_row.page_type):
            _validate_listing_runtime_guard_or_400(target_revision.payload_json or {})

    try:
        async def _op():
            published_row = await publish_revision(
                session,
                revision_id=revision_id,
                actor_user_id=current_user.get("id"),
            )
            await session.commit()
            return published_row

        published = await _run_with_db_retry(session, _op)
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
    if bool(getattr(row, "is_deleted", False)):
        raise HTTPException(status_code=404, detail="Revision not found")

    page_row = await session.get(LayoutPage, row.layout_page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Layout page not found")

    if _is_wizard_policy_page_type(page_row.page_type):
        report = _build_listing_policy_report(row.payload_json or {})
    else:
        report = _build_generic_layout_policy_report(row.payload_json or {}, page_type=page_row.page_type.value if page_row.page_type else None)
    return {"ok": True, "report": report}


@router.post("/admin/site/content-layout/revisions/{revision_id}/policy-autofix")
async def auto_fix_revision_policy_admin(
    revision_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    revision_uuid = _as_uuid_or_400(revision_id, field_name="revision_id")
    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")
    if bool(getattr(row, "is_deleted", False)):
        raise HTTPException(status_code=404, detail="Revision not found")

    page_row = await session.get(LayoutPage, row.layout_page_id)
    if not page_row:
        raise HTTPException(status_code=404, detail="Layout page not found")

    before_payload = row.payload_json or {}
    if _is_wizard_policy_page_type(page_row.page_type):
        report_before = _build_listing_policy_report(before_payload)
        fixed_payload, auto_fix_actions = _autofix_listing_payload(before_payload)
        report_after = _build_listing_policy_report(fixed_payload)
    else:
        report_before = _build_generic_layout_policy_report(before_payload, page_type=page_row.page_type.value if page_row.page_type else None)
        fixed_payload, auto_fix_actions = _autofix_generic_layout_payload(
            before_payload,
            default_component_key=get_default_component_key(page_row.page_type),
        )
        report_after = _build_generic_layout_policy_report(
            fixed_payload,
            page_type=page_row.page_type.value if page_row.page_type else None,
        )

    row.payload_json = fixed_payload

    async def _op():
        await session.commit()
        return True

    await _run_with_db_retry(session, _op)

    return {
        "ok": True,
        "item": _serialize_layout_revision(row),
        "report_before": report_before,
        "report_after": report_after,
        "auto_fix_actions": auto_fix_actions,
    }


@router.post("/admin/site/content-layout/revisions/{revision_id}/archive")
async def archive_revision_admin(
    revision_id: str,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    try:
        async def _op():
            archived_row = await archive_revision(
                session,
                revision_id=revision_id,
                actor_user_id=current_user.get("id"),
            )
            await session.commit()
            return archived_row

        row = await _run_with_db_retry(session, _op)
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
        .where(
            and_(
                LayoutRevision.layout_page_id == page_uuid,
                LayoutRevision.is_deleted.is_(False),
            )
        )
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
        async def _op():
            bind_row = await bind_category_to_page(
                session,
                country=payload.country,
                module=payload.module,
                category_id=payload.category_id,
                layout_page_id=payload.layout_page_id,
                actor_user_id=current_user.get("id"),
            )
            await session.commit()
            return bind_row

        row = await _run_with_db_retry(session, _op)
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
        async def _op():
            count = await unbind_category(
                session,
                country=payload.country,
                module=payload.module,
                category_id=payload.category_id,
                actor_user_id=current_user.get("id"),
            )
            await session.commit()
            return count

        unbound_count = await _run_with_db_retry(session, _op)
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


@router.post("/admin/site/content-layout/preset-events")
async def create_layout_preset_event(
    payload: LayoutPresetEventPayload,
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    layout_page_uuid = _as_uuid_or_400(payload.layout_page_id, field_name="layout_page_id") if payload.layout_page_id else None

    actor_user_uuid = None
    raw_actor_id = current_user.get("id") if isinstance(current_user, dict) else None
    if raw_actor_id:
        try:
            actor_user_uuid = uuid.UUID(str(raw_actor_id))
        except (TypeError, ValueError):
            actor_user_uuid = None

    row = LayoutPresetEvent(
        layout_page_id=layout_page_uuid,
        page_type=payload.page_type,
        country=payload.country.upper() if payload.country else None,
        module=payload.module.strip() if payload.module else None,
        preset_id=payload.preset_id.strip(),
        preset_label=payload.preset_label.strip(),
        persona=payload.persona.strip().lower(),
        variant=payload.variant.strip().upper(),
        event_type=payload.event_type,
        actor_user_id=actor_user_uuid,
        metadata_json=payload.metadata_json if isinstance(payload.metadata_json, dict) else {},
    )
    session.add(row)

    async def _op():
        await session.commit()
        await session.refresh(row)
        return True

    await _run_with_db_retry(session, _op)
    return {"ok": True, "item": _serialize_preset_event(row)}


@router.get("/admin/site/content-layout/preset-events/summary")
async def get_layout_preset_event_summary(
    days: int = Query(default=30, ge=1, le=365),
    page_type: Optional[LayoutPageType] = Query(default=None),
    country: Optional[str] = Query(default=None),
    module: Optional[str] = Query(default=None),
    current_user=Depends(check_permissions(ADMIN_LAYOUT_ROLES)),
    session: AsyncSession = Depends(get_db),
):
    del current_user
    start_at = datetime.now(timezone.utc) - timedelta(days=days)

    query = select(LayoutPresetEvent).where(LayoutPresetEvent.created_at >= start_at)
    if page_type:
        query = query.where(LayoutPresetEvent.page_type == page_type)
    if country:
        query = query.where(LayoutPresetEvent.country == country.upper())
    if module:
        query = query.where(LayoutPresetEvent.module == module.strip())

    rows = (
        (
            await session.execute(
                query.order_by(desc(LayoutPresetEvent.created_at)).limit(5000)
            )
        )
        .scalars()
        .all()
    )

    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row.preset_id, row.preset_label, row.persona, row.variant)
        if key not in grouped:
            grouped[key] = {
                "preset_id": row.preset_id,
                "preset_label": row.preset_label,
                "persona": row.persona,
                "variant": row.variant,
                "apply_count": 0,
                "publish_count": 0,
                "last_event_at": row.created_at.isoformat() if row.created_at else None,
            }
        target = grouped[key]
        if row.event_type == LayoutPresetEventType.APPLY:
            target["apply_count"] += 1
        if row.event_type == LayoutPresetEventType.PUBLISH:
            target["publish_count"] += 1
        if row.created_at and (not target["last_event_at"] or row.created_at.isoformat() > str(target["last_event_at"])):
            target["last_event_at"] = row.created_at.isoformat()

    summary = []
    for item in grouped.values():
        apply_count = int(item["apply_count"])
        publish_count = int(item["publish_count"])
        item["publish_rate"] = int(round((publish_count / apply_count) * 100)) if apply_count > 0 else 0
        summary.append(item)

    summary.sort(key=lambda item: (item["apply_count"], item["publish_count"]), reverse=True)
    return {
        "ok": True,
        "days": int(days),
        "total_events": int(len(rows)),
        "items": summary,
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
                    LayoutRevision.is_deleted.is_(False),
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
    request: Request = None,
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

    requested_lang = _resolve_request_i18n_lang(request, current_user=current_user)

    _METRICS["resolve_requests"] += 1
    key = _cache_key(normalized_country, normalized_module, page_type, category_id, requested_lang)
    now_ts = time.time()
    cached = _RESOLVE_CACHE.get(key) if preview_mode == "published" else None
    if cached and cached[0] > now_ts:
        _METRICS["resolve_cache_hits"] += 1
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        _METRICS["resolve_total_latency_ms"] += elapsed_ms
        logger.info("layout_resolve source=cache key=%s latency_ms=%.2f", key, elapsed_ms)
        return {**cached[1], "source": "cache", "lang": requested_lang}

    _METRICS["resolve_cache_misses"] += 1
    payload = await _resolve_effective_layout(
        session,
        country=normalized_country,
        module=normalized_module,
        page_type=page_type,
        category_id=category_id,
        preview_mode=preview_mode,
    )
    localized_payload = {
        **payload,
        "layout_page": _localize_payload_values(payload.get("layout_page"), requested_lang),
        "revision": _localize_payload_values(payload.get("revision"), requested_lang),
        "comparison": _localize_payload_values(payload.get("comparison"), requested_lang),
        "lang": requested_lang,
    }

    if preview_mode == "published":
        _RESOLVE_CACHE[key] = (now_ts + RESOLVE_CACHE_TTL_SECONDS, localized_payload)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    _METRICS["resolve_total_latency_ms"] += elapsed_ms
    logger.info(
        "layout_resolve source=db key=%s strategy=%s preview=%s latency_ms=%.2f",
        key,
        localized_payload.get("source"),
        preview_mode,
        elapsed_ms,
    )
    return localized_payload


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
