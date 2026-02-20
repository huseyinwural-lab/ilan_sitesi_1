import os
import re
import io
import csv
import urllib.request
import xml.etree.ElementTree as ET
import hashlib
import secrets
import logging
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Optional, Dict, Any
import time

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Body, Response
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field, EmailStr

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.mongo import get_mongo_client, get_db_name
from app.admin_country_context import resolve_admin_country_context

from app.dependencies import get_current_user, get_current_user_optional, check_permissions
from app.countries_seed import default_countries
from app.menu_seed import default_top_menu
from app.categories_seed import vehicle_category_tree
from app.master_data_seed import default_vehicle_makes, default_vehicle_models


from fastapi import UploadFile, File
from fastapi.responses import FileResponse

from app.vehicle_listings_store import (
    create_vehicle_listing,
    get_vehicle_listing,
    add_media as add_vehicle_media,
    set_status as set_vehicle_status,
)
from app.vehicle_publish_guard import validate_publish, validate_listing_schema
from app.vehicle_media_storage import store_image, resolve_public_media_path

# Vehicle Master Data (file-based REV-B)
from app.vehicle_master_file import get_vehicle_master_dir, load_current_master
from app.vehicle_master_admin_file import validate_upload, rollback as vehicle_master_rollback, get_status as vehicle_master_status


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

SUPPORTED_COUNTRIES = {"DE", "CH", "FR", "AT"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ATTRIBUTE_KEY_PATTERN = re.compile(r"^[a-z0-9_]+$")

# P1 Failed-login rate limit (in-process)
FAILED_LOGIN_WINDOW_SECONDS = 10 * 60  # 10 min sliding window
FAILED_LOGIN_MAX_ATTEMPTS = 3
FAILED_LOGIN_BLOCK_SECONDS = 15 * 60  # 15 min block

_failed_login_attempts: Dict[str, List[float]] = {}
_failed_login_blocked_until: Dict[str, float] = {}

# Dealer Application reasons (v1)
DEALER_APP_REJECT_REASONS_V1 = {
    "incomplete_documents",
    "invalid_company_info",
    "duplicate_application",
    "compliance_issue",
    "other",
}

INDIVIDUAL_APP_REJECT_REASONS_V1 = {
    "incomplete_documents",
    "failed_verification",
    "duplicate_application",
    "country_not_supported",
    "other",
}

# Dealer Application audit event types
DEALER_APPLICATION_EVENT_TYPES = {"DEALER_APPLICATION_APPROVED", "DEALER_APPLICATION_REJECTED"}

_failed_login_block_audited: Dict[str, bool] = {}



class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    country_scope: List[str] = Field(default_factory=list)
    preferred_language: str = "tr"
    is_active: bool = True
    is_verified: bool = True
    deleted_at: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None
    invite_status: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def _normalize_user_status(doc: dict) -> str:
    if doc.get("deleted_at"):
        return "deleted"
    status = doc.get("status") or "active"
    if status == "suspended" or doc.get("is_active") is False:
        return "suspended"
    return "active"


def _determine_user_type(role: str) -> str:
    if role in ADMIN_ROLE_OPTIONS:
        return "admin"
    if role == "dealer":
        return "dealer"
    return "individual"


def _normalize_phone_e164(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = re.sub(r"[^\d+]", "", value)
    if not cleaned:
        return None
    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"
    if cleaned.startswith("+"):
        digits = re.sub(r"\D", "", cleaned[1:])
        return f"+{digits}" if digits else None
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None
    if digits.startswith("49"):
        return f"+{digits}"
    return digits


def _normalize_phone_candidates(value: Optional[str]) -> List[str]:
    if not value:
        return []
    cleaned = re.sub(r"[^\d+]", "", value)
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return []
    candidates = set()
    if cleaned.startswith("+"):
        candidates.add(f"+{digits}")
    if digits.startswith("00"):
        trimmed = digits[2:]
        if trimmed:
            candidates.add(f"+{trimmed}")
            candidates.add(trimmed)
    if digits.startswith("49"):
        candidates.add(f"+{digits}")
    candidates.add(digits)
    return list(candidates)


def _resolve_user_phone_e164(doc: dict) -> Optional[str]:
    raw_phone = (
        doc.get("phone_e164")
        or doc.get("phone_number")
        or doc.get("phone")
        or doc.get("mobile")
    )
    return _normalize_phone_e164(raw_phone)


def _extract_moderation_reason(payload: Optional[AdminUserActionPayload]) -> tuple[Optional[str], Optional[str]]:
    if not payload:
        return None, None
    reason_code = (payload.reason_code or payload.reason or "").strip()
    reason_detail = (payload.reason_detail or "").strip()
    return (reason_code or None), (reason_detail or None)


def _parse_suspension_until(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        iso_value = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(iso_value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid suspension_until") from exc


def _build_user_summary(doc: dict, listing_stats: Optional[Dict[str, Any]] = None, plan_map: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    listing_stats = listing_stats or {}
    plan_map = plan_map or {}
    plan = plan_map.get(doc.get("plan_id"), {})
    status = _normalize_user_status(doc)
    user_type = _determine_user_type(doc.get("role", "individual"))
    phone_verified = bool(doc.get("phone_verified") or doc.get("phone_verified_at"))
    plan_expiry = doc.get("plan_expires_at") or doc.get("plan_end_at") or doc.get("plan_ends_at")

    return {
        "id": doc.get("id"),
        "full_name": doc.get("full_name"),
        "first_name": doc.get("first_name"),
        "last_name": doc.get("last_name"),
        "email": doc.get("email"),
        "role": doc.get("role"),
        "user_type": user_type,
        "country_code": doc.get("country_code"),
        "country_scope": doc.get("country_scope") or [],
        "status": status,
        "is_active": bool(doc.get("is_active", True)),
        "deleted_at": doc.get("deleted_at"),
        "created_at": doc.get("created_at"),
        "last_login": doc.get("last_login"),
        "email_verified": bool(doc.get("is_verified", False)),
        "phone_verified": phone_verified,
        "phone_e164": _resolve_user_phone_e164(doc),
        "total_listings": listing_stats.get("total", 0),
        "active_listings": listing_stats.get("active", 0),
        "plan_id": doc.get("plan_id"),
        "plan_name": plan.get("name") if plan else None,
        "plan_expires_at": plan_expiry,
    }


def _user_to_response(doc: dict) -> UserResponse:
    return UserResponse(
        id=doc["id"],
        email=doc["email"],
        full_name=doc.get("full_name", ""),
        role=doc.get("role", "support"),
        country_scope=doc.get("country_scope") or [],
        preferred_language=doc.get("preferred_language", "tr"),
        is_active=bool(doc.get("is_active", True)),
        is_verified=bool(doc.get("is_verified", True)),
        deleted_at=doc.get("deleted_at"),
        created_at=doc.get("created_at") or datetime.now(timezone.utc).isoformat(),
        last_login=doc.get("last_login"),
        invite_status=doc.get("invite_status"),
    )


async def build_audit_entry(
    event_type: str,
    actor: dict,
    target_id: str,
    target_type: str,
    country_code: Optional[str],
    details: Optional[dict],
    request: Optional[Request],
) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid.uuid4()),
        "created_at": now_iso,
        "event_type": event_type,
        "action": event_type,
        "resource_type": target_type,
        "resource_id": target_id,
        "admin_user_id": actor.get("id"),
        "user_id": actor.get("id"),
        "user_email": actor.get("email"),
        "country_code": country_code,
        "country_scope": actor.get("country_scope") or [],
        "metadata": details or {},
        "request_ip": request.client.host if request and request.client else None,
        "applied": True,
    }


async def _ensure_admin_user(db):
    now_iso = datetime.now(timezone.utc).isoformat()
    admin_email = "admin@platform.com"
    admin_password = "Admin123!"

    existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
    hashed = get_password_hash(admin_password)

    if existing:
        # Force reset for reliability in preview environments
        await db.users.update_one(
            {"email": admin_email},
            {
                "$set": {
                    "hashed_password": hashed,
                    "status": "active",
                    "is_active": True,
                    "role": existing.get("role") or "super_admin",
                    "country_code": existing.get("country_code") or "TR",
                    "updated_at": now_iso,
                }
            },
        )
        return

    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "hashed_password": hashed,
            "full_name": "System Administrator",
            "role": "super_admin",
            "status": "active",
            "is_active": True,
            "is_verified": True,
            "country_scope": ["*"],
            "country_code": "TR",
            "preferred_language": "tr",
            "created_at": now_iso,
            "last_login": None,
        }
    )



async def _ensure_dealer_user(db):
    now_iso = datetime.now(timezone.utc).isoformat()
    dealer_email = "dealer@platform.com"
    dealer_password = "Dealer123!"

    existing = await db.users.find_one({"email": dealer_email}, {"_id": 0})
    hashed = get_password_hash(dealer_password)

    if existing:
        await db.users.update_one(
            {"email": dealer_email},
            {
                "$set": {
                    "hashed_password": hashed,
                    "status": "active",
                    "is_active": True,
                    "role": "dealer",
                    "country_scope": existing.get("country_scope") or ["DE"],
                    "country_code": existing.get("country_code") or "DE",
                    "updated_at": now_iso,
                }
            },
        )
        return

    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": dealer_email,
            "hashed_password": hashed,
            "full_name": "Dealer Demo",
            "role": "dealer",
            "status": "active",
            "is_active": True,
            "is_verified": True,
            "country_scope": ["DE"],
            "country_code": "DE",
            "preferred_language": "tr",
            "created_at": now_iso,
            "last_login": None,
        }
    )


async def _ensure_test_user(db):
    now_iso = datetime.now(timezone.utc).isoformat()
    user_email = "user@platform.com"
    user_password = "User123!"

    existing = await db.users.find_one({"email": user_email}, {"_id": 0})
    hashed = get_password_hash(user_password)

    if existing:
        await db.users.update_one(
            {"email": user_email},
            {
                "$set": {
                    "hashed_password": hashed,
                    "status": "active",
                    "is_active": True,
                    "role": "individual",
                    "full_name": "Test User",
                    "first_name": "Test",
                    "last_name": "User",
                    "phone_e164": "+491701112233",
                    "country_scope": existing.get("country_scope") or ["DE"],
                    "country_code": existing.get("country_code") or "DE",
                    "updated_at": now_iso,
                },
                "$unset": {"deleted_at": ""},
            },
        )
        return

    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": user_email,
            "hashed_password": hashed,
            "full_name": "Test User",
            "first_name": "Test",
            "last_name": "User",
            "phone_e164": "+491701112233",
            "role": "individual",
            "status": "active",
            "is_active": True,
            "is_verified": True,
            "country_scope": ["DE"],
            "country_code": "DE",
            "preferred_language": "tr",
            "created_at": now_iso,
            "last_login": None,
        }
    )


async def _ensure_individual_fixtures(db):
    now = datetime.now(timezone.utc)
    fixtures = [
        {
            "email": "ayse.kaya@platform.com",
            "first_name": "Ayşe",
            "last_name": "Kaya",
            "phone_e164": "+905321234567",
            "country_code": "TR",
        },
        {
            "email": "mehmet.yilmaz@platform.com",
            "first_name": "Mehmet",
            "last_name": "Yılmaz",
            "phone_e164": "+905551112233",
            "country_code": "TR",
        },
        {
            "email": "elif.demir@platform.com",
            "first_name": "Elif",
            "last_name": "Demir",
            "phone_e164": "+491701234567",
            "country_code": "DE",
        },
        {
            "email": "zeynep.sari@platform.com",
            "first_name": "Zeynep",
            "last_name": "Sarı",
            "phone_e164": "+43123456789",
            "country_code": "AT",
        },
        {
            "email": "mert.ozkan@platform.com",
            "first_name": "Mert",
            "last_name": "Özkan",
            "phone_e164": "+41791234567",
            "country_code": "CH",
        },
    ]

    for idx, fixture in enumerate(fixtures):
        now_iso = (now - timedelta(days=idx + 1)).isoformat()
        email = fixture["email"]
        existing = await db.users.find_one({"email": email}, {"_id": 0})
        user_id = existing.get("id") if existing else str(uuid.uuid4())
        hashed = get_password_hash("User123!")

        payload = {
            "id": user_id,
            "email": email,
            "hashed_password": hashed,
            "full_name": f"{fixture['first_name']} {fixture['last_name']}",
            "first_name": fixture["first_name"],
            "last_name": fixture["last_name"],
            "phone_e164": fixture["phone_e164"],
            "role": "individual",
            "status": "active",
            "is_active": True,
            "is_verified": True,
            "country_scope": [fixture["country_code"]],
            "country_code": fixture["country_code"],
            "preferred_language": "tr",
            "created_at": now_iso,
            "last_login": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if existing:
            await db.users.update_one({"email": email}, {"$set": payload, "$unset": {"deleted_at": ""}})
        else:
            await db.users.insert_one(payload)


async def _ensure_country_admin_user(db):
    now_iso = datetime.now(timezone.utc).isoformat()
    admin_email = "countryadmin@platform.com"
    admin_password = "Country123!"

    existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
    hashed = get_password_hash(admin_password)

    if existing:
        await db.users.update_one(
            {"email": admin_email},
            {
                "$set": {
                    "hashed_password": hashed,
                    "status": "active",
                    "is_active": True,
                    "role": "country_admin",
                    "country_scope": existing.get("country_scope") or ["DE"],
                    "country_code": existing.get("country_code") or "DE",
                    "updated_at": now_iso,
                }
            },
        )
        return

    await db.users.insert_one(
        {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "hashed_password": hashed,
            "full_name": "Country Admin",
            "role": "country_admin",
            "status": "active",
            "is_active": True,
            "is_verified": True,
            "country_scope": ["DE"],
            "country_code": "DE",
            "preferred_language": "tr",
            "created_at": now_iso,
            "last_login": None,
        }
    )


async def _ensure_fixture_category_schema(db):
    now_iso = datetime.now(timezone.utc).isoformat()
    slug = "e2e-fixture-category"
    name = "E2E Fixture Category"
    country_code = "DE"

    schema = {
        "status": "published",
        "core_fields": {
            "title": {
                "required": True,
                "min": 10,
                "max": 120,
                "messages": {
                    "required": "Başlık zorunludur.",
                    "min": "Başlık çok kısa.",
                    "max": "Başlık çok uzun.",
                },
            },
            "description": {
                "required": True,
                "min": 30,
                "max": 4000,
                "messages": {
                    "required": "Açıklama zorunludur.",
                    "min": "Açıklama çok kısa.",
                    "max": "Açıklama çok uzun.",
                },
            },
            "price": {
                "required": True,
                "range": {"min": 1, "max": 100000},
                "currency_primary": "EUR",
                "currency_secondary": "CHF",
                "secondary_enabled": False,
                "decimal_places": 0,
                "messages": {
                    "required": "Fiyat zorunludur.",
                    "range": "Fiyat aralık dışında",
                },
            },
        },
        "dynamic_fields": [
            {
                "id": "extra_option",
                "label": "Ekstra Seçim",
                "key": "extra_option",
                "type": "select",
                "required": True,
                "options": ["A", "B"],
                "messages": {"required": "Ekstra seçim zorunlu"},
            }
        ],
        "detail_groups": [
            {
                "id": "features",
                "title": "Donanım",
                "required": True,
                "options": ["ABS", "Airbag", "Klima", "ESP"],
                "messages": {"required": "Donanım seçimi zorunlu"},
            }
        ],
        "modules": {
            "address": {"enabled": True},
            "photos": {"enabled": True},
            "contact": {"enabled": False},
            "payment": {"enabled": False},
        },
        "photo_config": {"max": 12},
        "payment_options": {"package": False, "doping": False},
    }

    existing = await db.categories.find_one({"slug": slug, "country_code": country_code}, {"_id": 0})
    payload = {
        "name": name,
        "slug": slug,
        "module": "vehicle",
        "country_code": country_code,
        "active_flag": True,
        "sort_order": 0,
        "parent_id": None,
        "hierarchy_complete": True,
        "form_schema": schema,
        "updated_at": now_iso,
    }

    if existing:
        await db.categories.update_one({"id": existing["id"]}, {"$set": payload})
        return

    payload.update(
        {
            "id": str(uuid.uuid4()),
            "created_at": now_iso,
        }
    )
    await db.categories.insert_one(payload)



async def lifespan(app: FastAPI):
    client = get_mongo_client()
    db = client[get_db_name()]

    # Ping
    await db.command("ping")

    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.admin_invites.create_index("token_hash", unique=True)
    await db.admin_invites.create_index("email")
    await db.countries.create_index("code", unique=True)
    await db.countries.create_index("id", unique=True)
    await db.vehicle_listings.create_index("id", unique=True)
    await db.vehicle_listings.create_index("status")
    await db.vehicle_listings.create_index("created_by")
    await db.vehicle_listings.create_index("country")
    await db.vehicle_listings.create_index("category_key")
    await db.reports.create_index("id", unique=True)
    await db.reports.create_index("status")
    await db.reports.create_index("listing_id")
    await db.reports.create_index("country_code")
    await db.reports.create_index("reason")
    await db.invoices.create_index("id", unique=True)
    await db.invoices.create_index("dealer_user_id")
    await db.invoices.create_index("country_code")
    await db.invoices.create_index("status")
    await db.invoices.create_index("paid_at")
    await db.tax_rates.create_index("id", unique=True)
    await db.tax_rates.create_index("country_code")
    await db.tax_rates.create_index("active_flag")
    await db.plans.create_index("id", unique=True)
    await db.plans.create_index("country_code")
    await db.plans.create_index("active_flag")
    await db.countries.create_index(
        "country_code",
        unique=True,
        partialFilterExpression={"country_code": {"$type": "string"}},
    )
    await db.countries.create_index("code", unique=True)
    await db.system_settings.create_index("id", unique=True)
    await db.system_settings.create_index([("key", 1), ("country_code", 1)], unique=True)
    await db.attributes.create_index([("key", 1), ("category_id", 1), ("country_code", 1)], unique=True)
    await db.vehicle_makes.create_index([("slug", 1), ("country_code", 1)], unique=True)
    await db.vehicle_models.create_index([("slug", 1), ("make_id", 1)], unique=True)
    await db.categories.create_index("id", unique=True)
    await db.categories.create_index(
        [("slug", 1), ("country_code", 1)],
        unique=True,
        partialFilterExpression={"slug": {"$type": "string"}},
        name="slug_country_code_partial_idx"
    )
    await db.categories.create_index("parent_id")
    await db.categories.create_index("active_flag")
    await db.categories_versions.create_index("id", unique=True)
    await db.categories_versions.create_index([("category_id", 1), ("version", -1)], unique=True)
    await db.audit_logs.create_index("event_type")
    await db.audit_logs.create_index([("event_type", 1), ("created_at", -1)])
    await db.attributes.create_index("id", unique=True)
    await db.attributes.create_index([("key", 1), ("category_id", 1), ("country_code", 1)], unique=True)
    await db.attributes.create_index("category_id")
    await db.attributes.create_index("active_flag")
    await db.vehicle_makes.create_index("id", unique=True)
    await db.vehicle_makes.create_index([("slug", 1), ("country_code", 1)], unique=True)
    await db.vehicle_makes.create_index("country_code")
    await db.vehicle_makes.create_index("active_flag")
    await db.vehicle_models.create_index("id", unique=True)
    await db.vehicle_models.create_index([("slug", 1), ("make_id", 1)], unique=True)
    await db.vehicle_models.create_index("make_id")
    await db.vehicle_models.create_index("active_flag")

    # Seed admin user
    await _ensure_admin_user(db)

    # Seed dealer user (dev/test only)
    if os.environ.get("ENV", "dev") != "production":
        await _ensure_dealer_user(db)
        await _ensure_test_user(db)
        await _ensure_individual_fixtures(db)
        await _ensure_country_admin_user(db)
        await _ensure_fixture_category_schema(db)

    # Seed countries
    now_iso = datetime.now(timezone.utc).isoformat()
    for c in default_countries(now_iso):
        seed_payload = dict(c)
        seed_payload.pop("active_flag", None)
        seed_payload.pop("is_enabled", None)
        seed_payload.pop("updated_at", None)
        await db.countries.update_one(
            {"$or": [{"code": c["code"]}, {"country_code": c["code"]}]},
            {"$setOnInsert": seed_payload, "$set": {"active_flag": True, "is_enabled": True, "updated_at": now_iso}},
            upsert=True,
        )

    # Deactivate unwanted seed countries (e.g., PL)
    await db.countries.update_many(
        {"$or": [{"code": "PL"}, {"country_code": "PL"}]},
        {"$set": {"active_flag": False, "is_enabled": False, "updated_at": now_iso}},
    )

    existing_countries = await db.countries.find({"active_flag": True}, {"_id": 0, "code": 1, "country_code": 1}).to_list(length=500)
    SUPPORTED_COUNTRIES.clear()
    SUPPORTED_COUNTRIES.update(
        [
            (doc.get("country_code") or doc.get("code") or "").upper()
            for doc in existing_countries
            if doc.get("country_code") or doc.get("code")
        ]
    )

    # Seed menu
    await db.menu_top_items.create_index("key", unique=True)
    await db.menu_top_items.create_index("id", unique=True)
    # remove deprecated vehicle link (elektrikli)
    await db.menu_top_items.update_many({}, {"$pull": {"sections.0.links": {"url": {"$regex": "/vasita/elektrikli"}}}})
    for item in default_top_menu(now_iso):
        await db.menu_top_items.update_one(
            {"key": item["key"]},
            {"$setOnInsert": item},
            upsert=True,
        )

    # Seed vehicle categories (locked)
    await db.categories.create_index("id", unique=True)
    await db.categories.create_index([("module", 1), ("parent_id", 1)])
    # remove deprecated vehicle segments (e.g., elektrikli)
    await db.categories.delete_many(
        {"module": "vehicle", "$or": [{"slug.tr": "elektrikli"}, {"slug": "elektrikli"}]}
    )
    for cat in vehicle_category_tree(now_iso):
        await db.categories.update_one(
            {"id": cat["id"]},
            {"$setOnInsert": cat},
            upsert=True,
        )

    legacy_cats = await db.categories.find({"slug": {"$type": "object"}}).to_list(length=200)
    for legacy in legacy_cats:
        slug_obj = legacy.get("slug") or {}
        slug_value = slug_obj.get("tr") or slug_obj.get("en") or slug_obj.get("de") or slug_obj.get("fr")
        name_value = legacy.get("name")
        if not name_value:
            translations = legacy.get("translations") or []
            for t in translations:
                if t.get("language") == "tr":
                    name_value = t.get("name")
                    break
        if slug_value:
            await db.categories.update_one(
                {"id": legacy.get("id")},
                {"$set": {"slug": slug_value, "name": name_value or slug_value, "active_flag": True}},
            )

    if await db.vehicle_makes.count_documents({}) == 0:
        await db.vehicle_makes.insert_many(default_vehicle_makes(now_iso))
    if await db.vehicle_models.count_documents({}) == 0:
        await db.vehicle_models.insert_many(default_vehicle_models(now_iso))

    # Vehicle master data (file-based) preload (fail-fast)
    vehicle_data_dir = get_vehicle_master_dir()
    app.state.vehicle_master_dir = vehicle_data_dir

    # Ensure minimal default master data exists in preview/dev environments
    # so the API can boot even if /data/vehicle_master is not provisioned yet.
    from app.vehicle_master_admin_file import ensure_default_master_data

    ensure_default_master_data(vehicle_data_dir)
    app.state.vehicle_master = load_current_master(vehicle_data_dir)

    app.state.mongo_client = client
    app.state.db = db

    yield

    client.close()


app = FastAPI(
    title="Admin Panel API (Mongo)",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = os.environ.get("CORS_ORIGINS", "*")
origins = ["*"] if cors_origins == "*" else [o.strip() for o in cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def _get_client_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # first IP in list is the original client
        return xff.split(",")[0].strip() or None
    return request.client.host if request.client else None


def _enforce_export_rate_limit(request: Request, user_id: str) -> None:
    now = time.time()
    key = f"{user_id}:{_get_client_ip(request)}"
    attempts = _export_attempts.get(key, [])
    attempts = [ts for ts in attempts if (now - ts) <= EXPORT_RATE_LIMIT_WINDOW_SECONDS]
    if len(attempts) >= EXPORT_RATE_LIMIT_MAX_ATTEMPTS:
        retry_after_seconds = int(EXPORT_RATE_LIMIT_WINDOW_SECONDS - (now - attempts[0]))
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED", "retry_after_seconds": max(retry_after_seconds, 1)},
        )
    attempts.append(now)
    _export_attempts[key] = attempts


def _enforce_admin_invite_rate_limit(request: Request, user_id: str) -> None:
    now = time.time()
    key = f"invite:{user_id}:{_get_client_ip(request)}"
    attempts = _admin_invite_attempts.get(key, [])
    attempts = [ts for ts in attempts if (now - ts) <= ADMIN_INVITE_RATE_LIMIT_WINDOW_SECONDS]
    if len(attempts) >= ADMIN_INVITE_RATE_LIMIT_MAX_ATTEMPTS:
        retry_after_seconds = int(ADMIN_INVITE_RATE_LIMIT_WINDOW_SECONDS - (now - attempts[0]))
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED", "retry_after_seconds": max(retry_after_seconds, 1)},
        )
    attempts.append(now)
    _admin_invite_attempts[key] = attempts


def _hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_admin_base_url(request: Request) -> str:
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")
    referer = request.headers.get("referer")
    if referer:
        return referer.split("/admin")[0].rstrip("/")
    base = str(request.base_url).rstrip("/")
    if base.endswith("/api"):
        base = base[:-4]
    return base


def _send_admin_invite_email(to_email: str, full_name: str, invite_link: str) -> None:
    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    if not sendgrid_key or not sender_email:
        _admin_invite_logger.error("SendGrid configuration missing: SENDGRID_API_KEY or SENDER_EMAIL")
        raise HTTPException(status_code=503, detail="SendGrid is not configured")

    subject = "Admin Daveti"
    html_content = f"""
    <html>
      <body>
        <h2>Admin Daveti</h2>
        <p>Merhaba {full_name or to_email},</p>
        <p>Admin hesabınız oluşturuldu. Daveti kabul etmek ve şifre belirlemek için aşağıdaki bağlantıyı kullanın:</p>
        <p><a href=\"{invite_link}\">Daveti Kabul Et</a></p>
        <p>Bağlantı 24 saat boyunca geçerlidir.</p>
      </body>
    </html>
    """
    message = Mail(
        from_email=sender_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        if response.status_code not in (200, 202):
            raise HTTPException(status_code=502, detail="Failed to send invite email")
    except HTTPException:
        raise
    except Exception as exc:
        _admin_invite_logger.error("SendGrid send error: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to send invite email")


def _normalize_scope(role: str, scope: Optional[List[str]], active_countries: List[str]) -> List[str]:
    if role == "super_admin":
        return ["*"]
    normalized = [code.strip().upper() for code in (scope or []) if code and code.strip()]
    if role == "country_admin" and not normalized:
        raise HTTPException(status_code=400, detail="Country scope required for country_admin")
    if "*" in normalized:
        raise HTTPException(status_code=400, detail="Invalid country scope value")
    for code in normalized:
        if code not in active_countries:
            raise HTTPException(status_code=400, detail=f"Invalid country scope: {code}")
    return normalized


async def _assert_super_admin_invariant(db, target_user: dict, payload_role: Optional[str], payload_active: Optional[bool], actor: dict) -> None:
    if not target_user:
        return
    target_role = target_user.get("role")
    target_id = target_user.get("id")
    actor_id = actor.get("id")

    if payload_role and target_id == actor_id and payload_role != target_role:
        raise HTTPException(status_code=400, detail="Self role change is not allowed")
    if payload_active is not None and target_id == actor_id and payload_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    demoting = payload_role and target_role == "super_admin" and payload_role != "super_admin"
    deactivating = payload_active is False and target_role == "super_admin"
    if demoting or deactivating:
        super_admin_count = await db.users.count_documents({"role": "super_admin", "is_active": True})
        if super_admin_count <= 1:
            raise HTTPException(status_code=400, detail="At least one super_admin must remain active")


def _parse_country_codes(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    codes = [code.strip().upper() for code in value.split(",") if code.strip()]
    return codes or None


def _dashboard_cache_key(role: str, country_codes: Optional[List[str]], trend_days: int) -> str:
    trend_label = f"trend{trend_days}"
    if not country_codes:
        return f"{role}:global:{trend_label}"
    joined = ",".join(sorted(country_codes))
    return f"{role}:{joined}:{trend_label}"


def _country_compare_cache_key(
    role: str,
    country_codes: Optional[List[str]],
    selected_codes: Optional[List[str]],
    period: str,
    start_date: Optional[str],
    end_date: Optional[str],
    sort_by: Optional[str],
    sort_dir: Optional[str],
) -> str:
    joined = ",".join(sorted(country_codes)) if country_codes else "global"
    selected = ",".join(sorted(selected_codes)) if selected_codes else "all"
    return f"{role}:{joined}:{selected}:{period}:{start_date or ''}:{end_date or ''}:{sort_by or ''}:{sort_dir or ''}"


def _get_cached_dashboard_summary(cache_key: str) -> Optional[Dict[str, Any]]:
    entry = _dashboard_summary_cache.get(cache_key)
    if not entry:
        return None
    if (time.time() - entry.get("timestamp", 0)) > DASHBOARD_CACHE_TTL_SECONDS:
        _dashboard_summary_cache.pop(cache_key, None)
        return None
    return entry.get("data")


def _set_cached_dashboard_summary(cache_key: str, data: Dict[str, Any]) -> None:
    _dashboard_summary_cache[cache_key] = {"timestamp": time.time(), "data": data}


def _get_cached_country_compare(cache_key: str) -> Optional[Dict[str, Any]]:
    entry = _country_compare_cache.get(cache_key)
    if not entry:
        return None
    if (time.time() - entry.get("timestamp", 0)) > COUNTRY_COMPARE_CACHE_TTL_SECONDS:
        _country_compare_cache.pop(cache_key, None)
        return None
    return entry.get("data")


def _set_cached_country_compare(cache_key: str, data: Dict[str, Any]) -> None:
    _country_compare_cache[cache_key] = {"timestamp": time.time(), "data": data}


def _fetch_ecb_rates() -> Optional[Dict[str, float]]:
    try:
        with urllib.request.urlopen(ECB_DAILY_URL, timeout=20) as response:
            xml_bytes = response.read()
        root = ET.fromstring(xml_bytes)
        ns = {
            "gesmes": "http://www.gesmes.org/xml/2002-08-01",
            "ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
        }
        rates: Dict[str, float] = {ECB_RATE_BASE: 1.0}
        for cube in root.findall(".//ecb:Cube[@currency]", ns):
            currency = cube.get("currency")
            rate = cube.get("rate")
            if currency and rate:
                try:
                    rates[currency.upper()] = float(rate)
                except ValueError:
                    continue
        return rates
    except Exception:
        return None


def _get_ecb_rates() -> Dict[str, Any]:
    now = time.time()
    if _ecb_rates_cache.get("rates") and (now - _ecb_rates_cache.get("timestamp", 0)) < ECB_CACHE_TTL_SECONDS:
        return _ecb_rates_cache

    rates = _fetch_ecb_rates()
    if rates:
        fetched_at = datetime.now(timezone.utc).isoformat()
        _ecb_rates_cache.update({
            "timestamp": now,
            "rates": rates,
            "last_success_at": fetched_at,
            "fallback": False,
        })
        global _ecb_rates_fallback
        _ecb_rates_fallback = dict(_ecb_rates_cache)
        return _ecb_rates_cache

    if _ecb_rates_fallback and _ecb_rates_fallback.get("rates"):
        fallback = dict(_ecb_rates_fallback)
        fallback["fallback"] = True
        _ecb_rates_cache.update(fallback)
        _ecb_rates_cache["timestamp"] = now
        return _ecb_rates_cache

    return {
        "timestamp": now,
        "rates": {ECB_RATE_BASE: 1.0},
        "last_success_at": None,
        "fallback": True,
    }


def _convert_to_eur(amount: float, currency: Optional[str], rates: Dict[str, float]) -> Optional[float]:
    if amount is None:
        return None
    currency_code = (currency or ECB_RATE_BASE).upper()
    rate = rates.get(currency_code)
    if not rate or rate == 0:
        return None
    return round(float(amount) / rate, 4)


def _format_uptime(seconds: int) -> str:
    if seconds < 0:
        return "0s"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def _resolve_period_window(period: str, start_date: Optional[str], end_date: Optional[str]) -> tuple[datetime, datetime, str]:
    now = datetime.now(timezone.utc)
    period_key = (period or "30d").lower()

    if period_key == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        return start, end, "Bugün"

    if period_key in {"7d", "7", "last_7_days"}:
        start = now - timedelta(days=7)
        end = now
        return start, end, "Son 7 Gün"

    if period_key in {"30d", "30", "last_30_days"}:
        start = now - timedelta(days=30)
        end = now
        return start, end, "Son 30 Gün"

    if period_key == "mtd":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
        return start, end, "MTD"

    if period_key == "custom":
        start_dt = _parse_iso(start_date)
        end_dt = _parse_iso(end_date)
        if not start_dt or not end_dt:
            raise HTTPException(status_code=400, detail="custom start_date and end_date required")
        start = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
        if end < start:
            raise HTTPException(status_code=400, detail="end_date must be after start_date")
        range_days = (end - start).days + 1
        if range_days < DASHBOARD_TREND_MIN_DAYS or range_days > DASHBOARD_TREND_MAX_DAYS:
            raise HTTPException(status_code=400, detail="custom range must be between 7 and 365 days")
        return start, end, "Özel"

    start = now - timedelta(days=30)
    end = now
    return start, end, "Son 30 Gün"


def _growth_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    current_val = float(current or 0)
    prev_val = float(previous or 0)
    if prev_val == 0:
        return None if current_val == 0 else 100.0
    return round(((current_val - prev_val) / prev_val) * 100, 2)


def _safe_ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    num = float(numerator or 0)
    den = float(denominator or 0)
    if den == 0:
        return None
    return round(num / den, 4)


# Audit event taxonomy (v1)
AUDIT_EVENT_TYPES_V1 = {
    "MODERATION_APPROVE",
    "MODERATION_REJECT",
    "MODERATION_NEEDS_REVISION",
    "FAILED_LOGIN",
    "RATE_LIMIT_BLOCK",
    "ADMIN_ROLE_CHANGE",
    "UNAUTHORIZED_ROLE_CHANGE_ATTEMPT",
    "DEALER_STATUS_CHANGE",
    "DEALER_APPLICATION_APPROVED",
    "DEALER_APPLICATION_REJECTED",
    "INDIVIDUAL_APPLICATION_APPROVED",
    "INDIVIDUAL_APPLICATION_REJECTED",
    "LISTING_SOFT_DELETE",
    "LISTING_FORCE_UNPUBLISH",
    "REPORT_STATUS_CHANGE",
    "REPORT_CREATED",
    "INVOICE_STATUS_CHANGE",
    "TAX_RATE_CHANGE",
    "PLAN_CHANGE",
    "ADMIN_PLAN_ASSIGNMENT",
    "COUNTRY_CHANGE",
    "SYSTEM_SETTING_CHANGE",
    "CATEGORY_CHANGE",
    "MENU_CHANGE",
    "ATTRIBUTE_CHANGE",
    "VEHICLE_MASTER_DATA_CHANGE",
}

api_router = APIRouter(prefix="/api")


# Moderation reasons (v1.0.0 single-source contract)
REJECT_REASONS_V1 = {"duplicate", "spam", "illegal", "wrong_category"}
NEEDS_REVISION_REASONS_V1 = {"missing_photos", "insufficient_description", "wrong_price", "other"}

# Report reasons (v1)
REPORT_REASONS_V1 = {
    "spam",
    "scam_fraud",
    "prohibited_item",
    "wrong_category",
    "harassment",
    "copyright",
    "other",
}

REPORT_STATUS_SET = {"open", "in_review", "resolved", "dismissed"}
INVOICE_STATUS_SET = {"unpaid", "paid", "cancelled"}
KEY_NAMESPACE_REGEX = re.compile(r"^[a-z0-9]+(\.[a-z0-9_]+)+$")

REPORT_STATUS_TRANSITIONS = {
    "open": {"in_review"},
    "in_review": {"resolved", "dismissed"},
}

REPORT_RATE_LIMIT_WINDOW_SECONDS = 10 * 60
REPORT_RATE_LIMIT_MAX_ATTEMPTS = 5
_report_submit_attempts: Dict[str, List[float]] = {}

EXPORT_RATE_LIMIT_WINDOW_SECONDS = 60
EXPORT_RATE_LIMIT_MAX_ATTEMPTS = 10
_export_attempts: Dict[str, List[float]] = {}

ADMIN_INVITE_RATE_LIMIT_WINDOW_SECONDS = 60
ADMIN_INVITE_RATE_LIMIT_MAX_ATTEMPTS = 5

ADMIN_ROLE_OPTIONS = {"super_admin", "country_admin", "finance", "support", "moderator"}

_admin_invite_attempts: Dict[str, List[float]] = {}
_admin_invite_logger = logging.getLogger("admin_invites")

APP_START_TIME = datetime.now(timezone.utc)

DASHBOARD_TREND_DAYS = 14
DASHBOARD_TREND_MIN_DAYS = 7
DASHBOARD_TREND_MAX_DAYS = 365
DASHBOARD_KPI_DAYS = 7
DASHBOARD_MULTI_IP_WINDOW_HOURS = 24
DASHBOARD_MULTI_IP_THRESHOLD = 3
DASHBOARD_SLA_HOURS = 24
DASHBOARD_PENDING_PAYMENT_DAYS = 7

ECB_DAILY_URL = os.environ.get("ECB_DAILY_URL")
ECB_CACHE_TTL_SECONDS_RAW = os.environ.get("ECB_CACHE_TTL_SECONDS")
ECB_CACHE_TTL_SECONDS = int(ECB_CACHE_TTL_SECONDS_RAW) if ECB_CACHE_TTL_SECONDS_RAW else 0
ECB_RATE_BASE = "EUR"

if not ECB_DAILY_URL or ECB_CACHE_TTL_SECONDS <= 0:
    raise RuntimeError("ECB_DAILY_URL and ECB_CACHE_TTL_SECONDS must be set")

DASHBOARD_CACHE_TTL_SECONDS = int(os.environ.get("DASHBOARD_CACHE_TTL_SECONDS", "60"))
COUNTRY_COMPARE_CACHE_TTL_SECONDS = 60
_dashboard_summary_cache: Dict[str, Dict[str, Any]] = {}
_country_compare_cache: Dict[str, Dict[str, Any]] = {}
_ecb_rates_cache: Dict[str, Any] = {"timestamp": 0, "rates": None, "last_success_at": None, "fallback": False}
_ecb_rates_fallback: Optional[Dict[str, Any]] = None
_dashboard_cache_hits = 0
_dashboard_cache_misses = 0

ALLOWED_MODERATION_ROLES = {"moderator", "country_admin", "super_admin"}


@api_router.get("/health")
async def health_check(request: Request):
    db = request.app.state.db
    await db.command("ping")
    return {"status": "healthy", "supported_countries": SUPPORTED_COUNTRIES, "database": "mongo"}


@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    db = request.app.state.db

    email = (credentials.email or "").lower().strip()
    ip_address = _get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Rate-limit key: IP + email (email may be empty but EmailStr should be present)
    rl_key = f"{ip_address}:{email}"
    now = time.time()

    blocked_until = _failed_login_blocked_until.get(rl_key)
    if blocked_until and now < blocked_until:
        # Log RATE_LIMIT_BLOCK only once per block window
        if not _failed_login_block_audited.get(rl_key):
            await db.audit_logs.insert_one(
                {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "event_type": "RATE_LIMIT_BLOCK",
                    "action": "RATE_LIMIT_BLOCK",
                    "resource_type": "auth",
                    "resource_id": None,
                    "email": email,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                }
            )
            _failed_login_block_audited[rl_key] = True
        retry_after_seconds = int(blocked_until - now)
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED", "retry_after_seconds": retry_after_seconds},
        )

    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("hashed_password", "")):
        # FAILED_LOGIN audit (always)
        await db.audit_logs.insert_one(
            {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "event_type": "FAILED_LOGIN",
                "action": "FAILED_LOGIN",
                "resource_type": "auth",
                "resource_id": None,
                "email": email,


                "ip_address": ip_address,
                "user_agent": user_agent,
            }
        )

        # Update attempts window
        attempts = _failed_login_attempts.get(rl_key, [])
        attempts = [ts for ts in attempts if (now - ts) <= FAILED_LOGIN_WINDOW_SECONDS]
        attempts.append(now)
        _failed_login_attempts[rl_key] = attempts

        # Start block when threshold is exceeded (3 fails allowed, 4th attempt blocked)
        if len(attempts) > FAILED_LOGIN_MAX_ATTEMPTS:
            _failed_login_blocked_until[rl_key] = now + FAILED_LOGIN_BLOCK_SECONDS
            _failed_login_block_audited[rl_key] = False



        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS"})

    if user.get("deleted_at"):
        raise HTTPException(status_code=403, detail="User account deleted")
    if user.get("status") == "suspended" or not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account suspended")


    # successful login: reset failed-login counters
    _failed_login_attempts.pop(rl_key, None)
    _failed_login_blocked_until.pop(rl_key, None)
    _failed_login_block_audited.pop(rl_key, None)

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": now_iso}})
    user["last_login"] = now_iso

    audit_entry = await build_audit_entry(
        event_type="LOGIN_SUCCESS",
        actor=user,
        target_id=user.get("id"),
        target_type="auth",
        country_code=user.get("country_code"),
        details={"ip_address": ip_address},
        request=request,
    )
    audit_entry["action"] = "LOGIN_SUCCESS"
    audit_entry["user_agent"] = user_agent
    await db.audit_logs.insert_one(audit_entry)

    token_data = {"sub": user["id"], "email": user["email"], "role": user.get("role")}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=_user_to_response(user),
    )


@api_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(data: RefreshTokenRequest, request: Request):
    db = request.app.state.db

    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_data = {"sub": user["id"], "email": user["email"], "role": user.get("role")}

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=_user_to_response(user),
    )


class UpdateUserPayload(BaseModel):
    role: Optional[str] = None


class AdminUserCreatePayload(BaseModel):
    full_name: str
    email: EmailStr
    role: str
    country_scope: Optional[List[str]] = None
    is_active: Optional[bool] = True


class AdminUserUpdatePayload(BaseModel):
    role: Optional[str] = None
    country_scope: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AdminInviteAcceptPayload(BaseModel):
    token: str
    password: str


class BulkDeactivatePayload(BaseModel):
    user_ids: List[str]


class AdminUserActionPayload(BaseModel):
    reason: Optional[str] = None
    reason_code: Optional[str] = None
    reason_detail: Optional[str] = None
    suspension_until: Optional[str] = None


@api_router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Enforce country scope for country_admin
    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        target_country = target.get("country_code")
        if "*" not in scope and target_country and target_country not in scope:
            # Audit unauthorized attempt
            await db.audit_logs.insert_one(
                {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "event_type": "UNAUTHORIZED_ROLE_CHANGE_ATTEMPT",
                    "action": "UNAUTHORIZED_ROLE_CHANGE_ATTEMPT",
                    "resource_type": "user",
                    "resource_id": user_id,
                    "target_user_id": user_id,
                    "changed_by_admin_id": current_user.get("id"),
                    "previous_role": target.get("role"),
                    "new_role": payload.role,
                    "country_scope": current_user.get("country_scope") or [],
                    "mode": getattr(ctx, "mode", "global"),
                    "country_code": target_country,
                }
            )
            raise HTTPException(status_code=403, detail="Country scope forbidden")

    if payload.role is None:
        return {"ok": True}

    prev_role = target.get("role")
    new_role = payload.role

    # Role update + audit: "audit yoksa update yok" garantisi
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "event_type": "ADMIN_ROLE_CHANGE",
        "action": "ADMIN_ROLE_CHANGE",
        "resource_type": "user",
        "resource_id": user_id,
        "target_user_id": user_id,
        "changed_by_admin_id": current_user.get("id"),
        "previous_role": prev_role,
        "new_role": new_role,
        "country_scope": current_user.get("country_scope") or [],
        "mode": getattr(ctx, "mode", "global"),
        "country_code": target.get("country_code"),
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)

    res = await db.users.update_one({"id": user_id, "role": prev_role}, {"$set": {"role": new_role, "updated_at": datetime.now(timezone.utc).isoformat()}})
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Role changed concurrently")

    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    return {"ok": True}


@api_router.get("/admin/users")
async def list_admin_users(
    request: Request,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "desc",
    skip: int = 0,
    limit: int = 200,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict[str, Any] = {"role": {"$in": list(ADMIN_ROLE_OPTIONS)}}

    if role:
        query["role"] = role

    status_key = status.lower() if status else None
    if status_key == "deleted":
        query["deleted_at"] = {"$exists": True}
    else:
        query["deleted_at"] = {"$exists": False}
        if status_key == "active":
            query["is_active"] = True
        elif status_key == "inactive":
            query["is_active"] = False
        elif status_key == "invited":
            query["invite_status"] = "pending"

    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]

    if country:
        country_code = country.upper()
        query["country_scope"] = {"$in": [country_code, "*"]}

    sort_field_map = {
        "email": "email",
        "full_name": "full_name",
        "role": "role",
        "created_at": "created_at",
        "last_login": "last_login",
        "is_active": "is_active",
    }
    sort_field = sort_field_map.get(sort_by or "", "created_at")
    sort_direction = -1 if (sort_dir or "desc").lower() == "desc" else 1

    cursor = (
        db.users.find(query, {"_id": 0})
        .sort(sort_field, sort_direction)
        .skip(max(skip, 0))
        .limit(min(limit, 500))
    )
    docs = await cursor.to_list(length=limit)
    return {"items": [_user_to_response(doc).model_dump() for doc in docs]}


@api_router.post("/admin/users")
async def create_admin_user(
    request: Request,
    payload: AdminUserCreatePayload,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    _enforce_admin_invite_rate_limit(request, current_user.get("id"))

    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    if not sendgrid_key or not sender_email:
        _admin_invite_logger.error("SendGrid configuration missing: SENDGRID_API_KEY or SENDER_EMAIL")
        raise HTTPException(status_code=503, detail="SendGrid is not configured")

    role_value = payload.role
    if role_value not in ADMIN_ROLE_OPTIONS:
        raise HTTPException(status_code=400, detail="Invalid admin role")

    email_value = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email_value}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    active_countries_docs = await db.countries.find({"active_flag": True}, {"_id": 0, "country_code": 1, "code": 1}).to_list(length=200)
    active_countries = [
        (doc.get("country_code") or doc.get("code") or "").upper()
        for doc in active_countries_docs
        if doc.get("country_code") or doc.get("code")
    ]

    country_scope = _normalize_scope(role_value, payload.country_scope, active_countries)

    now_iso = datetime.now(timezone.utc).isoformat()
    user_id = str(uuid.uuid4())
    invite_expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    user_doc = {
        "id": user_id,
        "email": email_value,
        "full_name": payload.full_name.strip(),
        "role": role_value,
        "country_scope": country_scope,
        "status": "active",
        "is_active": bool(payload.is_active),
        "is_verified": False,
        "invite_status": "pending",
        "created_at": now_iso,
        "updated_at": now_iso,
        "last_login": None,
        "preferred_language": "tr",
    }
    await db.users.insert_one(user_doc)

    token = secrets.token_urlsafe(32)
    token_hash = _hash_invite_token(token)
    invite_id = str(uuid.uuid4())
    invite_doc = {
        "id": invite_id,
        "token_hash": token_hash,
        "user_id": user_id,
        "email": email_value,
        "role": role_value,
        "country_scope": country_scope,
        "expires_at": invite_expires_at,
        "created_at": now_iso,
        "created_by": current_user.get("id"),
        "used_at": None,
    }
    await db.admin_invites.insert_one(invite_doc)

    invite_link = f"{_get_admin_base_url(request)}/admin/invite/accept?token={token}"

    try:
        _send_admin_invite_email(email_value, payload.full_name.strip(), invite_link)
    except HTTPException:
        await db.admin_invites.delete_one({"id": invite_id})
        await db.users.delete_one({"id": user_id})
        raise

    audit_created = await build_audit_entry(
        event_type="admin_user_created",
        actor=current_user,
        target_id=user_id,
        target_type="admin_user",
        country_code=None,
        details={"email": email_value, "role": role_value},
        request=request,
    )
    audit_created["action"] = "admin_user_created"
    await db.audit_logs.insert_one(audit_created)

    audit_invited = await build_audit_entry(
        event_type="admin_invited",
        actor=current_user,
        target_id=user_id,
        target_type="admin_user",
        country_code=None,
        details={"email": email_value, "role": role_value, "invite_expires_at": invite_expires_at},
        request=request,
    )
    audit_invited["action"] = "admin_invited"
    await db.audit_logs.insert_one(audit_invited)

    return {"ok": True, "invite_expires_at": invite_expires_at}


@api_router.patch("/admin/users/{user_id}")
async def update_admin_user(
    user_id: str,
    payload: AdminUserUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Admin user not found")

    next_role = payload.role or target.get("role")
    if payload.role and payload.role not in ADMIN_ROLE_OPTIONS:
        raise HTTPException(status_code=400, detail="Invalid admin role")

    active_countries_docs = await db.countries.find({"active_flag": True}, {"_id": 0, "country_code": 1, "code": 1}).to_list(length=200)
    active_countries = [
        (doc.get("country_code") or doc.get("code") or "").upper()
        for doc in active_countries_docs
        if doc.get("country_code") or doc.get("code")
    ]

    if next_role == "country_admin" and payload.country_scope is None and not (target.get("country_scope") or []):
        raise HTTPException(status_code=400, detail="Country scope required for country_admin")

    next_scope = target.get("country_scope") or []
    if payload.country_scope is not None or payload.role:
        next_scope = _normalize_scope(next_role, payload.country_scope or next_scope, active_countries)

    await _assert_super_admin_invariant(db, target, payload.role, payload.is_active, current_user)

    updates: Dict[str, Any] = {}
    if payload.role and payload.role != target.get("role"):
        updates["role"] = payload.role
    if payload.country_scope is not None or payload.role:
        updates["country_scope"] = next_scope
    if payload.is_active is not None and payload.is_active != target.get("is_active", True):
        updates["is_active"] = bool(payload.is_active)

    if not updates:
        return {"ok": True}

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": user_id}, {"$set": updates})

    if payload.role and payload.role != target.get("role"):
        audit_role = await build_audit_entry(
            event_type="admin_role_changed",
            actor=current_user,
            target_id=user_id,
            target_type="admin_user",
            country_code=None,
            details={"from": target.get("role"), "to": payload.role},
            request=request,
        )
        audit_role["action"] = "admin_role_changed"
        await db.audit_logs.insert_one(audit_role)

    if payload.is_active is not None and payload.is_active is False:
        audit_deactivate = await build_audit_entry(
            event_type="admin_deactivated",
            actor=current_user,
            target_id=user_id,
            target_type="admin_user",
            country_code=None,
            details={"email": target.get("email")},
            request=request,
        )
        audit_deactivate["action"] = "admin_deactivated"
        await db.audit_logs.insert_one(audit_deactivate)

    return {"ok": True}


@api_router.post("/admin/users/bulk-deactivate")
async def bulk_deactivate_admins(
    request: Request,
    payload: BulkDeactivatePayload,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    user_ids = list(dict.fromkeys(payload.user_ids or []))
    if not user_ids:
        return {"ok": True, "count": 0}
    if len(user_ids) > 20:
        raise HTTPException(status_code=400, detail="Bulk deactivate limit is 20")

    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0}).to_list(length=200)
    if not users:
        return {"ok": True, "count": 0}

    for user in users:
        await _assert_super_admin_invariant(db, user, None, False, current_user)
        if user.get("id") == current_user.get("id"):
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_many({"id": {"$in": user_ids}}, {"$set": {"is_active": False, "updated_at": now_iso}})

    for user in users:
        audit_deactivate = await build_audit_entry(
            event_type="admin_deactivated",
            actor=current_user,
            target_id=user.get("id"),
            target_type="admin_user",
            country_code=None,
            details={"email": user.get("email")},
            request=request,
        )
        audit_deactivate["action"] = "admin_deactivated"
        await db.audit_logs.insert_one(audit_deactivate)

    return {"ok": True, "count": len(user_ids)}


@api_router.get("/admin/invite/preview")
async def admin_invite_preview(token: str, request: Request):
    db = request.app.state.db
    token_hash = _hash_invite_token(token)
    invite = await db.admin_invites.find_one({"token_hash": token_hash}, {"_id": 0})
    if not invite or invite.get("used_at"):
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.get("expires_at") and invite.get("expires_at") < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="Invite expired")

    user = await db.users.find_one({"id": invite.get("user_id")}, {"_id": 0})
    return {
        "email": invite.get("email"),
        "full_name": user.get("full_name") if user else None,
        "role": invite.get("role"),
        "expires_at": invite.get("expires_at"),
    }


@api_router.post("/admin/invite/accept")
async def admin_invite_accept(payload: AdminInviteAcceptPayload, request: Request):
    db = request.app.state.db
    token_hash = _hash_invite_token(payload.token)
    invite = await db.admin_invites.find_one({"token_hash": token_hash}, {"_id": 0})
    if not invite or invite.get("used_at"):
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.get("expires_at") and invite.get("expires_at") < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="Invite expired")

    if not payload.password or len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = await db.users.find_one({"id": invite.get("user_id")}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"id": invite.get("user_id")},
        {
            "$set": {
                "hashed_password": get_password_hash(payload.password),
                "is_verified": True,
                "invite_status": None,
                "invite_accepted_at": now_iso,
                "updated_at": now_iso,
            }
        },
    )
    await db.admin_invites.update_one({"id": invite.get("id")}, {"$set": {"used_at": now_iso}})

    audit_accept = await build_audit_entry(
        event_type="admin_invite_accepted",
        actor=user,
        target_id=user.get("id"),
        target_type="admin_user",
        country_code=None,
        details={"email": user.get("email")},
        request=request,
    )
    audit_accept["action"] = "admin_invite_accepted"
    await db.audit_logs.insert_one(audit_accept)

    return {"ok": True}


@api_router.post("/admin/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: Request,
    payload: Optional[AdminUserActionPayload] = None,
    current_user=Depends(check_permissions(["super_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("deleted_at"):
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") in ADMIN_ROLE_OPTIONS:
        raise HTTPException(status_code=400, detail="Admin accounts must be managed in Admin Users")

    reason_code, reason_detail = _extract_moderation_reason(payload)
    if not reason_code:
        raise HTTPException(status_code=400, detail="Reason is required")

    suspension_until = _parse_suspension_until(payload.suspension_until if payload else None)

    await _assert_super_admin_invariant(db, user, None, False, current_user)

    now_iso = datetime.now(timezone.utc).isoformat()
    before_state = {
        "status": user.get("status"),
        "is_active": user.get("is_active", True),
        "suspension_until": user.get("suspension_until"),
        "deleted_at": user.get("deleted_at"),
    }

    update_ops: Dict[str, Any] = {
        "$set": {
            "status": "suspended",
            "is_active": False,
            "updated_at": now_iso,
        }
    }
    if suspension_until:
        update_ops["$set"]["suspension_until"] = suspension_until
    else:
        update_ops["$unset"] = {"suspension_until": ""}

    if user.get("role") == "dealer":
        update_ops["$set"]["dealer_status"] = "suspended"

    await db.users.update_one({"id": user_id}, update_ops)

    after_state = {
        **before_state,
        "status": "suspended",
        "is_active": False,
        "suspension_until": suspension_until,
    }

    audit_entry = await build_audit_entry(
        event_type="user_suspended",
        actor=current_user,
        target_id=user_id,
        target_type="user",
        country_code=user.get("country_code"),
        details={
            "reason_code": reason_code,
            "reason_detail": reason_detail,
            "suspension_until": suspension_until,
            "before": before_state,
            "after": after_state,
        },
        request=request,
    )
    audit_entry["action"] = "user_suspended"
    await db.audit_logs.insert_one(audit_entry)

    return {"ok": True}


@api_router.post("/admin/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    request: Request,
    payload: Optional[AdminUserActionPayload] = None,
    current_user=Depends(check_permissions(["super_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user or user.get("deleted_at"):
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") in ADMIN_ROLE_OPTIONS:
        raise HTTPException(status_code=400, detail="Admin accounts must be managed in Admin Users")

    reason_code, reason_detail = _extract_moderation_reason(payload)
    if not reason_code:
        raise HTTPException(status_code=400, detail="Reason is required")

    now_iso = datetime.now(timezone.utc).isoformat()
    before_state = {
        "status": user.get("status"),
        "is_active": user.get("is_active", True),
        "suspension_until": user.get("suspension_until"),
        "deleted_at": user.get("deleted_at"),
    }

    update_ops: Dict[str, Any] = {
        "$set": {
            "status": "active",
            "is_active": True,
            "updated_at": now_iso,
        },
        "$unset": {"suspension_until": ""},
    }

    if user.get("role") == "dealer":
        update_ops["$set"]["dealer_status"] = "active"

    await db.users.update_one({"id": user_id}, update_ops)

    after_state = {
        **before_state,
        "status": "active",
        "is_active": True,
        "suspension_until": None,
    }

    audit_entry = await build_audit_entry(
        event_type="user_reactivated",
        actor=current_user,
        target_id=user_id,
        target_type="user",
        country_code=user.get("country_code"),
        details={
            "reason_code": reason_code,
            "reason_detail": reason_detail,
            "before": before_state,
            "after": after_state,
        },
        request=request,
    )
    audit_entry["action"] = "user_reactivated"
    await db.audit_logs.insert_one(audit_entry)

    return {"ok": True}


@api_router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    payload: Optional[AdminUserActionPayload] = None,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin_target = user.get("role") in ADMIN_ROLE_OPTIONS

    if user.get("deleted_at"):
        return {"ok": True}

    reason_code, reason_detail = _extract_moderation_reason(payload)
    if not is_admin_target and not reason_code:
        raise HTTPException(status_code=400, detail="Reason is required")

    await _assert_super_admin_invariant(db, user, None, False, current_user)

    before_state = {
        "status": user.get("status"),
        "is_active": user.get("is_active", True),
        "role": user.get("role"),
        "country_scope": user.get("country_scope") or [],
        "deleted_at": user.get("deleted_at"),
        "suspension_until": user.get("suspension_until"),
    }

    now_iso = datetime.now(timezone.utc).isoformat()
    update_ops: Dict[str, Any] = {
        "$set": {
            "status": "deleted",
            "is_active": False,
            "deleted_at": now_iso,
            "updated_at": now_iso,
        },
        "$unset": {"suspension_until": ""},
    }

    if user.get("role") == "dealer":
        update_ops["$set"]["dealer_status"] = "deleted"

    await db.users.update_one(
        {"id": user_id},
        update_ops,
    )

    after_state = {
        **before_state,
        "status": "deleted",
        "is_active": False,
        "deleted_at": now_iso,
        "suspension_until": None,
    }

    if is_admin_target:
        audit_entry = await build_audit_entry(
            event_type="admin_deleted",
            actor=current_user,
            target_id=user_id,
            target_type="admin_user",
            country_code=user.get("country_code"),
            details={
                "reason_code": reason_code,
                "reason_detail": reason_detail,
                "before": before_state,
                "after": after_state,
            },
            request=request,
        )
        audit_entry["action"] = "admin_deleted"
    else:
        audit_entry = await build_audit_entry(
            event_type="user_deleted",
            actor=current_user,
            target_id=user_id,
            target_type="user",
            country_code=user.get("country_code"),
            details={
                "reason_code": reason_code,
                "reason_detail": reason_detail,
                "before": before_state,
                "after": after_state,
            },
            request=request,
        )
        audit_entry["action"] = "user_deleted"

    await db.audit_logs.insert_one(audit_entry)

    return {"ok": True}


@api_router.get("/admin/users/{user_id}/detail")
async def admin_user_detail(
    user_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    listing_stats_map: Dict[str, Dict[str, Any]] = {}
    listing_stats = await db.vehicle_listings.aggregate([
        {"$match": {"created_by": user_id}},
        {
            "$group": {
                "_id": "$created_by",
                "total": {"$sum": 1},
                "active": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$status", "published"]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
    ]).to_list(length=10)
    if listing_stats:
        listing_stats_map = {
            listing_stats[0].get("_id"): {
                "total": listing_stats[0].get("total", 0),
                "active": listing_stats[0].get("active", 0),
            }
        }

    plan_map: Dict[str, Any] = {}
    if user.get("plan_id"):
        plan = await db.plans.find_one({"id": user.get("plan_id")}, {"_id": 0})
        if plan:
            plan_map = {plan.get("id"): plan}

    audit_logs = await db.audit_logs.find(
        {"$or": [{"actor_id": user_id}, {"target_id": user_id}]},
        {"_id": 0, "event_type": 1, "created_at": 1, "action": 1},
    ).sort("created_at", -1).limit(10).to_list(length=10)

    return {
        "user": _build_user_summary(user, listing_stats_map.get(user_id, {}), plan_map),
        "audit_logs": audit_logs,
        "listings_link": f"/admin/listings?owner_id={user_id}",
    }


@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return _user_to_response(current_user)


@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    users_query = {}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        users_query = {"country_code": ctx.country}

    users_total = await db.users.count_documents(users_query)
    users_active = await db.users.count_documents({**users_query, "is_active": True})

    # Minimal response compatible with Dashboard.js usage
    return {
        "users": {"total": users_total, "active": users_active},
        "countries": {"enabled": len(SUPPORTED_COUNTRIES)},
        "feature_flags": {"enabled": 0, "total": 0},
        "users_by_role": {
            "super_admin": await db.users.count_documents({**users_query, "role": "super_admin"}),
            "country_admin": await db.users.count_documents({**users_query, "role": "country_admin"}),
            "moderator": await db.users.count_documents({**users_query, "role": "moderator"}),
            "support": await db.users.count_documents({**users_query, "role": "support"}),
            "finance": await db.users.count_documents({**users_query, "role": "finance"}),
        },
        "recent_activity": [],
    }


@api_router.get("/users")
async def list_users(
    request: Request,
    search: Optional[str] = None,
    role: Optional[str] = None,
    user_type: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "desc",
    limit: int = 100,
    skip: int = 0,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict[str, Any] = {}

    country_code = ctx.country if ctx and getattr(ctx, "country", None) else None
    if country:
        country_code = country.upper()
    if country_code:
        query["country_code"] = country_code

    if user_type:
        user_type_key = user_type.lower()
        if user_type_key == "admin":
            query["role"] = {"$in": list(ADMIN_ROLE_OPTIONS)}
        elif user_type_key == "dealer":
            query["role"] = "dealer"
        elif user_type_key == "individual":
            query["role"] = {"$nin": list(ADMIN_ROLE_OPTIONS) + ["dealer"]}

    if role:
        query["role"] = role

    if status:
        status_key = status.lower()
        if status_key == "deleted":
            query["deleted_at"] = {"$exists": True}
        else:
            query["deleted_at"] = {"$exists": False}
            if status_key == "inactive":
                query["$or"] = [{"status": "suspended"}, {"is_active": False}]
            elif status_key == "active":
                query["status"] = {"$ne": "suspended"}
                query["is_active"] = {"$ne": False}
    else:
        query["deleted_at"] = {"$exists": False}

    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]

    sort_field_map = {
        "email": "email",
        "full_name": "full_name",
        "role": "role",
        "created_at": "created_at",
        "last_login": "last_login",
        "status": "status",
    }
    sort_field = sort_field_map.get(sort_by or "", "created_at")
    sort_direction = -1 if (sort_dir or "desc").lower() == "desc" else 1

    cursor = (
        db.users.find(query, {"_id": 0})
        .sort(sort_field, sort_direction)
        .skip(max(skip, 0))
        .limit(min(limit, 300))
    )
    docs = await cursor.to_list(length=limit)

    user_ids = [doc.get("id") for doc in docs if doc.get("id")]
    listing_stats_map: Dict[str, Dict[str, Any]] = {}
    if user_ids:
        pipeline = [
            {"$match": {"created_by": {"$in": user_ids}}},
            {
                "$group": {
                    "_id": "$created_by",
                    "total": {"$sum": 1},
                    "active": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "published"]},
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]
        listing_stats = await db.vehicle_listings.aggregate(pipeline).to_list(length=5000)
        listing_stats_map = {
            stat.get("_id"): {"total": stat.get("total", 0), "active": stat.get("active", 0)}
            for stat in listing_stats
        }

    plan_ids = [doc.get("plan_id") for doc in docs if doc.get("plan_id")]
    plan_map: Dict[str, Any] = {}
    if plan_ids:
        plan_docs = await db.plans.find({"id": {"$in": plan_ids}}, {"_id": 0}).to_list(length=200)
        plan_map = {doc.get("id"): doc for doc in plan_docs}

    items = [
        _build_user_summary(doc, listing_stats_map.get(doc.get("id"), {}), plan_map)
        for doc in docs
    ]

    return {"items": items}


def _build_individual_users_query(
    search: Optional[str],
    country_code: Optional[str],
    status: Optional[str],
) -> Dict[str, Any]:
    query: Dict[str, Any] = {
        "role": {"$nin": list(ADMIN_ROLE_OPTIONS) + ["dealer"]},
    }

    if country_code:
        query["country_code"] = country_code

    status_key = (status or "").lower().strip()
    if status_key == "deleted":
        query["deleted_at"] = {"$exists": True}
    else:
        query["deleted_at"] = {"$exists": False}
        if status_key == "suspended":
            query["$and"] = [{"$or": [{"status": "suspended"}, {"is_active": False}]}]
        elif status_key == "active":
            query["status"] = {"$ne": "suspended"}
            query["is_active"] = {"$ne": False}

    if search:
        safe_search = re.escape(search)
        or_conditions = [
            {"first_name": {"$regex": safe_search, "$options": "i"}},
            {"last_name": {"$regex": safe_search, "$options": "i"}},
            {"email": {"$regex": safe_search, "$options": "i"}},
            {"full_name": {"$regex": safe_search, "$options": "i"}},
        ]
        phone_candidates = _normalize_phone_candidates(search)
        if phone_candidates:
            phone_fields = ["phone_e164", "phone_number", "phone", "mobile"]
            for candidate in phone_candidates:
                pattern = re.escape(candidate)
                for field in phone_fields:
                    or_conditions.append({field: {"$regex": pattern}})
        if query.get("$and"):
            query["$and"].append({"$or": or_conditions})
        else:
            query["$or"] = or_conditions

    return query


def _build_individual_users_sort(sort_by: Optional[str], sort_dir: Optional[str]):
    sort_field_map = {
        "email": "email",
        "created_at": "created_at",
        "last_login": "last_login",
        "first_name": "first_name",
        "last_name": "last_name",
    }
    sort_key = sort_field_map.get(sort_by or "last_name", "last_name")
    sort_direction = 1 if (sort_dir or "asc").lower() == "asc" else -1

    sort_name_expr = {"$ifNull": ["$last_name", {"$ifNull": ["$first_name", "$email"]}]}
    sort_first_expr = {"$ifNull": ["$first_name", "$email"]}
    sort_spec = {
        "sort_name": sort_direction,
        "sort_first": sort_direction,
        "email": sort_direction,
    }
    if sort_key != "last_name":
        sort_spec = {sort_key: sort_direction, "email": sort_direction}

    return sort_spec, sort_name_expr, sort_first_expr, sort_direction


@api_router.get("/admin/individual-users")
async def list_individual_users(
    request: Request,
    search: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "last_name",
    sort_dir: Optional[str] = "asc",
    page: int = 1,
    limit: int = 50,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    country_code = ctx.country if ctx and getattr(ctx, "country", None) else None
    if country:
        country_code = country.upper()

    query = _build_individual_users_query(search, country_code, status)

    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), 200)
    skip = (safe_page - 1) * safe_limit

    total_count = await db.users.count_documents(query)

    sort_spec, sort_name_expr, sort_first_expr, sort_direction = _build_individual_users_sort(sort_by, sort_dir)

    pipeline = [
        {"$match": query},
        {"$addFields": {"sort_name": sort_name_expr, "sort_first": sort_first_expr}},
        {"$sort": sort_spec},
        {"$skip": skip},
        {"$limit": safe_limit},
    ]

    docs = await db.users.aggregate(pipeline).to_list(length=safe_limit)

    user_ids = [doc.get("id") for doc in docs if doc.get("id")]
    listing_stats_map: Dict[str, Dict[str, Any]] = {}
    if user_ids:
        pipeline_stats = [
            {"$match": {"created_by": {"$in": user_ids}}},
            {
                "$group": {
                    "_id": "$created_by",
                    "total": {"$sum": 1},
                    "active": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$status", "published"]},
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
        ]
        listing_stats = await db.vehicle_listings.aggregate(pipeline_stats).to_list(length=5000)
        listing_stats_map = {
            stat.get("_id"): {"total": stat.get("total", 0), "active": stat.get("active", 0)}
            for stat in listing_stats
        }

    plan_ids = [doc.get("plan_id") for doc in docs if doc.get("plan_id")]
    plan_map: Dict[str, Any] = {}
    if plan_ids:
        plan_docs = await db.plans.find({"id": {"$in": plan_ids}}, {"_id": 0}).to_list(length=200)
        plan_map = {doc.get("id"): doc for doc in plan_docs}

    items = [
        _build_user_summary(doc, listing_stats_map.get(doc.get("id"), {}), plan_map)
        for doc in docs
    ]

    total_pages = max(1, (total_count + safe_limit - 1) // safe_limit)

    return {
        "items": items,
        "total_count": total_count,
        "page": safe_page,
        "limit": safe_limit,
        "total_pages": total_pages,
    }


@api_router.get("/admin/individual-users/export/csv")
async def admin_individual_users_export_csv(
    request: Request,
    search: Optional[str] = None,
    country: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "last_name",
    sort_dir: Optional[str] = "asc",
    current_user=Depends(check_permissions(["super_admin", "marketing"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )
    _enforce_export_rate_limit(request, current_user.get("id"))

    country_code = ctx.country if ctx and getattr(ctx, "country", None) else None
    if country:
        country_code = country.upper()

    query = _build_individual_users_query(search, country_code, status)
    sort_spec, sort_name_expr, sort_first_expr, _ = _build_individual_users_sort(sort_by, sort_dir)

    pipeline = [
        {"$match": query},
        {"$addFields": {"sort_name": sort_name_expr, "sort_first": sort_first_expr}},
        {"$sort": sort_spec},
    ]

    docs = await db.users.aggregate(pipeline).to_list(length=10000)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Email", "Name", "Country", "Type"])

    for doc in docs:
        full_name = doc.get("full_name")
        if not full_name:
            first = doc.get("first_name") or ""
            last = doc.get("last_name") or ""
            full_name = " ".join(part for part in [first, last] if part).strip() or doc.get("email")
        writer.writerow([
            doc.get("email"),
            full_name,
            doc.get("country_code"),
            _determine_user_type(doc.get("role", "individual")),
        ])

    csv_content = buffer.getvalue().encode("utf-8")
    buffer.close()

    total_count = len(docs)
    filename = f"individual-users-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"

    audit_doc = await build_audit_entry(
        event_type="individual_users_export_csv",
        actor=current_user,
        target_id="individual_users",
        target_type="individual_users",
        country_code=country_code,
        details={
            "search": search,
            "country": country_code,
            "status": status,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "total_count": total_count,
        },
        request=request,
    )
    audit_doc["action"] = "individual_users_export_csv"
    audit_doc["user_agent"] = request.headers.get("user-agent")
    await db.audit_logs.insert_one(audit_doc)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


@api_router.get("/menu/top-items")
async def get_top_menu_items(request: Request):
    db = request.app.state.db
    items = await db.menu_top_items.find({"is_enabled": True}, {"_id": 0}).to_list(length=50)
    items.sort(key=lambda x: x.get("sort_order", 0))
    return items


@api_router.patch("/menu/top-items/{item_id}")
async def toggle_menu_item(item_id: str, data: dict, request: Request, current_user=Depends(check_permissions(["super_admin"]))):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    is_enabled = data.get("is_enabled")
    payload = {}
    if is_enabled is not None:
        payload["is_enabled"] = bool(is_enabled)
    if not payload:
        return {"ok": True}
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    res = await db.menu_top_items.update_one({"id": item_id}, {"$set": payload})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")

    return {"ok": True}


@api_router.get("/categories")
async def list_categories(
    request: Request,
    module: str = "vehicle",
    country: Optional[str] = None,
    current_user=Depends(get_current_user_optional),
):
    db = request.app.state.db

    if current_user:
        await resolve_admin_country_context(request, current_user=current_user, db=db, )

    if not country:
        raise HTTPException(status_code=400, detail="country is required")
    code = country.upper()

    query = {
        "module": module,
        "$and": [
            {"$or": [{"country_code": None}, {"country_code": ""}, {"country_code": code}]},
            {"$or": [{"active_flag": True}, {"active_flag": {"$exists": False}}]},
        ],
    }
    docs = await db.categories.find(query, {"_id": 0}).to_list(length=500)
    docs.sort(key=lambda x: (x.get("sort_order", 0), str(_pick_label(x.get("name")) or "")))
    return [_normalize_category_doc(doc) for doc in docs]


@api_router.get("/catalog/schema")
async def get_catalog_schema(
    category_id: str,
    request: Request,
    country: str | None = None,
):
    db = request.app.state.db
    category = await db.categories.find_one({"id": category_id, "active_flag": True})
    if not category:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    if country and category.get("country_code") and category.get("country_code") != country:
        raise HTTPException(status_code=403, detail="Kategori ülke kapsamı dışında")
    raw_schema = category.get("form_schema")
    if not raw_schema:
        raise HTTPException(status_code=409, detail="Kategori şeması oluşturulmadı")
    schema = _normalize_category_schema(raw_schema)
    if schema.get("status") == "draft":
        raise HTTPException(status_code=409, detail="Kategori şeması taslak durumda")
    return {"category": _normalize_category_doc(category), "schema": schema}


# =====================
# Sprint 1.1 — Dealer Management (Admin)
# =====================

@api_router.get("/admin/dealers")
async def admin_list_dealers(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict = {"role": "dealer"}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country

    status_key = (status or "").lower().strip()
    if status_key:
        if status_key == "deleted":
            query["deleted_at"] = {"$exists": True}
        else:
            query["deleted_at"] = {"$exists": False}
            if status_key == "suspended":
                query["$or"] = [{"status": "suspended"}, {"is_active": False}]
            elif status_key == "active":
                query["status"] = {"$ne": "suspended"}
                query["is_active"] = {"$ne": False}
    else:
        query["deleted_at"] = {"$exists": False}

    if search:
        query["email"] = {"$regex": search, "$options": "i"}

    limit = min(100, max(1, int(limit)))
    cursor = db.users.find(query, {"_id": 0}).skip(int(skip)).limit(limit)
    docs = await cursor.to_list(length=limit)

    out = []
    for u in docs:
        out.append(
            {
                "id": u.get("id"),
                "email": u.get("email"),
                "dealer_status": u.get("dealer_status", "active"),
                "status": _normalize_user_status(u),
                "suspension_until": u.get("suspension_until"),
                "country_code": u.get("country_code"),
                "plan_id": u.get("plan_id"),
                "created_at": u.get("created_at"),
            }
        )

    total = await db.users.count_documents(query)
    return {"items": out, "pagination": {"total": total, "skip": int(skip), "limit": limit}}


@api_router.get("/admin/dealers/{dealer_id}")
async def admin_get_dealer_detail(
    dealer_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict = {"id": dealer_id, "role": "dealer"}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country

    dealer = await db.users.find_one(query, {"_id": 0})
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    _assert_country_scope(dealer.get("country_code"), current_user)

    # Basic finance linkage (MVP)
    last_invoice = (
        await db.invoices.find({"dealer_user_id": dealer_id}, {"_id": 0})
        .sort("issued_at", -1)
        .limit(1)
        .to_list(1)
    )
    last_invoice = last_invoice[0] if last_invoice else None
    unpaid_count = await db.invoices.count_documents({"dealer_user_id": dealer_id, "status": "unpaid"})
    active_plan = None
    if dealer.get("plan_id"):
        active_plan = await db.plans.find_one({"id": dealer.get("plan_id")}, {"_id": 0})

    return {
        "dealer": {
            "id": dealer.get("id"),
            "email": dealer.get("email"),
            "dealer_status": dealer.get("dealer_status", "active"),
            "country_code": dealer.get("country_code"),
            "plan_id": dealer.get("plan_id"),
            "created_at": dealer.get("created_at"),
        },
        "active_plan": active_plan,
        "last_invoice": last_invoice,
        "unpaid_count": unpaid_count,
        "package": {
            "plan_id": dealer.get("plan_id"),
            "last_invoice": last_invoice,
        },
    }


class DealerStatusPayload(BaseModel):
    dealer_status: str


@api_router.post("/admin/dealers/{dealer_id}/status")
async def admin_set_dealer_status(
    dealer_id: str,
    payload: DealerStatusPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    new_status = (payload.dealer_status or "").strip().lower()
    if new_status not in ["active", "suspended"]:
        raise HTTPException(status_code=400, detail="Invalid dealer_status")

    query: Dict = {"id": dealer_id, "role": "dealer"}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country

    dealer = await db.users.find_one(query, {"_id": 0})
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    prev_status = dealer.get("dealer_status", "active")

    # Normalize missing field
    if "dealer_status" not in dealer:
        await db.users.update_one({"id": dealer_id}, {"$set": {"dealer_status": prev_status}})

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "event_type": "DEALER_STATUS_CHANGE",
        "action": "DEALER_STATUS_CHANGE",
        "resource_type": "user",
        "resource_id": dealer_id,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "country_code": dealer.get("country_code"),
        "country_scope": current_user.get("country_scope") or [],
        "previous_status": prev_status,
        "new_status": new_status,
        "applied": False,
    }

    # audit-first
    await db.audit_logs.insert_one(audit_doc)



# =====================
# Sprint 1.2 — Dealer Applications (Admin)
# =====================

@api_router.get("/admin/dealer-applications")
async def admin_list_dealer_applications(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict = {}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
        ]

    limit = min(100, max(1, int(limit)))
    cursor = db.dealer_applications.find(query, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(limit)
    docs = await cursor.to_list(length=limit)

    total = await db.dealer_applications.count_documents(query)
    return {"items": docs, "pagination": {"total": total, "skip": int(skip), "limit": limit}}


@api_router.get("/admin/individual-applications")
async def admin_list_individual_applications(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict = {}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]

    limit = min(100, max(1, int(limit)))
    cursor = db.individual_applications.find(query, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(limit)
    docs = await cursor.to_list(length=limit)
    total = await db.individual_applications.count_documents(query)
    return {"items": docs, "pagination": {"total": total, "skip": int(skip), "limit": limit}}


class DealerApplicationRejectPayload(BaseModel):
    reason: str
    reason_note: Optional[str] = None


class IndividualApplicationRejectPayload(BaseModel):
    reason: str
    reason_note: Optional[str] = None


@api_router.post("/admin/dealer-applications/{app_id}/reject")
async def admin_reject_dealer_application(
    app_id: str,
    payload: DealerApplicationRejectPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    app = await db.dealer_applications.find_one({"id": app_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # country-scope enforcement
    if getattr(ctx, "mode", "global") == "country" and ctx.country and app.get("country_code") != ctx.country:
        raise HTTPException(status_code=403, detail="Country scope forbidden")

    if app.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Application already reviewed")

    reason = (payload.reason or "").strip()
    if reason not in DEALER_APP_REJECT_REASONS_V1:
        raise HTTPException(status_code=400, detail="Invalid reason")

    reason_note = (payload.reason_note or "").strip() or None
    if reason == "other" and not reason_note:
        raise HTTPException(status_code=400, detail="reason_note is required when reason=other")

    prev_status = app.get("status")
    now_iso = datetime.now(timezone.utc).isoformat()

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "DEALER_APPLICATION_REJECTED",
        "action": "DEALER_APPLICATION_REJECTED",
        "resource_type": "dealer_application",
        "resource_id": app_id,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "country_code": app.get("country_code"),
        "country_scope": current_user.get("country_scope") or [],
        "previous_status": prev_status,
        "new_status": "rejected",
        "reason": reason,
        "reason_note": reason_note,
        "applied": False,
    }

    # audit-first
    await db.audit_logs.insert_one(audit_doc)

    res = await db.dealer_applications.update_one(
        {"id": app_id, "status": "pending"},
        {
            "$set": {
                "status": "rejected",
                "reason": reason,
                "reason_note": reason_note,
                "reviewed_at": now_iso,
                "reviewed_by": current_user.get("id"),
                "updated_at": now_iso,
            }
        },
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Application changed concurrently")

    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    return {"ok": True}


@api_router.post("/admin/dealer-applications/{app_id}/approve")
async def admin_approve_dealer_application(
    app_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    app = await db.dealer_applications.find_one({"id": app_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # country-scope enforcement
    if getattr(ctx, "mode", "global") == "country" and ctx.country and app.get("country_code") != ctx.country:
        raise HTTPException(status_code=403, detail="Country scope forbidden")

    if app.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Application already reviewed")

    now_iso = datetime.now(timezone.utc).isoformat()

    # Create dealer user (audit-first protects us from partial state)
    existing = await db.users.find_one({"email": app.get("email")}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "DEALER_APPLICATION_APPROVED",
        "action": "DEALER_APPLICATION_APPROVED",
        "resource_type": "dealer_application",
        "resource_id": app_id,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "country_code": app.get("country_code"),
        "country_scope": current_user.get("country_scope") or [],
        "previous_status": "pending",
        "new_status": "approved",
        "applied": False,
    }

    # audit-first
    await db.audit_logs.insert_one(audit_doc)

    # Create dealer user
    new_user_id = str(uuid.uuid4())
    raw_password = str(uuid.uuid4())[:12] + "!"  # MVP: temporary password
    hashed = get_password_hash(raw_password)

    await db.users.insert_one(
        {
            "id": new_user_id,
            "email": app.get("email"),
            "hashed_password": hashed,
            "role": "dealer",
            "dealer_status": "active",
            "country_code": app.get("country_code"),
            "plan_id": None,
            "is_active": True,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
    )

    # Update application
    res = await db.dealer_applications.update_one(
        {"id": app_id, "status": "pending"},
        {
            "$set": {
                "status": "approved",
                "reviewed_at": now_iso,
                "reviewed_by": current_user.get("id"),
                "updated_at": now_iso,
            }
        },
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Application changed concurrently")

    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    # Return temp password for MVP testing (in real prod, send email)
    return {"ok": True, "dealer_user": {"id": new_user_id, "email": app.get("email"), "temp_password": raw_password}}


@api_router.post("/admin/individual-applications/{app_id}/approve")
async def admin_approve_individual_application(
    app_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db)

    app = await db.individual_applications.find_one({"id": app_id})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if getattr(ctx, "mode", "global") == "country" and app.get("country_code") != ctx.country:
        raise HTTPException(status_code=403, detail="Country scope violation")
    if app.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Application not pending")

    existing_user = await db.users.find_one({"email": app.get("email")})
    if not existing_user:
        await db.users.insert_one(
            {
                "id": str(uuid.uuid4()),
                "email": app.get("email"),
                "name": app.get("full_name") or app.get("email"),
                "password": get_password_hash("User123!"),
                "role": "user",
                "country_code": app.get("country_code"),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

    res = await db.individual_applications.update_one(
        {"id": app_id, "status": "pending"},
        {"$set": {
            "status": "approved",
            "reviewed_at": datetime.utcnow().isoformat(),
            "reviewed_by": current_user.get("id"),
            "updated_at": datetime.utcnow().isoformat(),
        }},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Application changed concurrently")

    audit_entry = await build_audit_entry(
        event_type="INDIVIDUAL_APPLICATION_APPROVED",
        actor=current_user,
        target_id=app.get("id"),
        target_type="individual_application",
        country_code=app.get("country_code"),
        details={"email": app.get("email")},
        request=request,
    )
    await db.audit_logs.insert_one(audit_entry)
    return {"ok": True}


@api_router.post("/admin/individual-applications/{app_id}/reject")
async def admin_reject_individual_application(
    app_id: str,
    payload: IndividualApplicationRejectPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db)

    app = await db.individual_applications.find_one({"id": app_id})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if getattr(ctx, "mode", "global") == "country" and app.get("country_code") != ctx.country:
        raise HTTPException(status_code=403, detail="Country scope violation")
    if app.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Application not pending")
    if payload.reason not in INDIVIDUAL_APP_REJECT_REASONS_V1:
        raise HTTPException(status_code=400, detail="Invalid reject reason")

    res = await db.individual_applications.update_one(
        {"id": app_id, "status": "pending"},
        {"$set": {
            "status": "rejected",
            "reason": payload.reason,
            "reason_note": payload.reason_note,
            "reviewed_at": datetime.utcnow().isoformat(),
            "reviewed_by": current_user.get("id"),
            "updated_at": datetime.utcnow().isoformat(),
        }},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Application changed concurrently")

    audit_entry = await build_audit_entry(
        event_type="INDIVIDUAL_APPLICATION_REJECTED",
        actor=current_user,
        target_id=app.get("id"),
        target_type="individual_application",
        country_code=app.get("country_code"),
        details={"email": app.get("email"), "reason": payload.reason},
        request=request,
    )
    await db.audit_logs.insert_one(audit_entry)
    return {"ok": True}





@api_router.get("/countries")
async def list_countries(request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db
    # Countries list is global; still resolve context for uniform audit/error handling
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    docs = await db.countries.find({}, {"_id": 0}).to_list(length=200)
    docs.sort(key=lambda x: x.get("code", ""))
    return docs

 

@api_router.patch("/countries/{country_id}")
async def update_country(country_id: str, data: dict, request: Request, current_user=Depends(check_permissions(["super_admin", "country_admin"]))):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )
    allowed = {"is_enabled", "default_currency", "default_language", "support_email"}
    payload = {k: v for k, v in data.items() if k in allowed}
    if not payload:
        return {"ok": True}

    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.countries.update_one({"id": country_id}, {"$set": payload})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Country not found")


    # Minimal audit log (country-aware)
    try:
        await db.audit_logs.insert_one(
            {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "user_id": current_user.get("id"),
                "user_email": current_user.get("email"),
                # Backoffice AuditLogs UI expects `action`, while moderation spec requires `event_type`.
                # We store both for compatibility.
                "action": "UPDATE",
                "event_type": "UPDATE",
                "resource_type": "country",
                "resource_id": country_id,
                "mode": getattr(ctx, "mode", "global"),
                "country_scope": getattr(ctx, "country", None),
                "path": str(request.url.path),
                "previous_status": None,
                "new_status": None,
            }
        )
    except Exception:
        # audit should not block the operation
        pass

    return {"ok": True}




# =====================
# Audit Logs (Mongo) - Backoffice
# =====================

@api_router.get("/audit-logs")
async def list_audit_logs(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    admin_user_id: Optional[str] = None,
    country: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    country_scope: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    q: Dict = {}
    if action:
        q["action"] = action
    if event_type:
        q["event_type"] = event_type
    if resource_type:
        q["resource_type"] = resource_type
    if user_id:
        q["user_id"] = user_id
    if admin_user_id:
        q["admin_user_id"] = admin_user_id
    if country:
        q["country_code"] = country.strip().upper()
    if start or end:
        created_at_q: Dict = {}
        if start:
            created_at_q["$gte"] = start
        if end:
            created_at_q["$lte"] = end
        q["created_at"] = created_at_q
    if country_scope:
        q["country_scope"] = country_scope

    cursor = db.audit_logs.find(q, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(int(limit))
    docs = await cursor.to_list(length=int(limit))
    return docs


# =====================
# Moderation (Mongo) - Backoffice
# =====================

def _ensure_moderation_rbac(current_user: dict):
    role = current_user.get("role")
    if role not in ALLOWED_MODERATION_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def _validate_reason(reason: str, allowed: set[str]) -> str:
    r = (reason or "").strip()
    if not r:
        raise HTTPException(status_code=400, detail="reason is required")
    if r not in allowed:
        raise HTTPException(status_code=400, detail="Invalid reason")
    return r


async def _moderation_transition(
    *,
    db,
    listing_id: str,
    current_user: dict,
    event_type: str,
    new_status: str,
    reason: Optional[str] = None,
    reason_note: Optional[str] = None,
) -> dict:
    """Apply listing moderation transition + write audit log.

    Mongo standalone environments may not support multi-document transactions.
    To keep the invariant "no state change without an audit row", we insert audit
    first with `applied=False`, then update listing, then mark audit as applied.
    """

    _ensure_moderation_rbac(current_user)

    listing = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Country-scope enforcement for country_admin
    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope and listing.get("country") not in scope:
            raise HTTPException(status_code=403, detail="Country scope forbidden")

    prev_status = listing.get("status")
    if prev_status != "pending_moderation":
        raise HTTPException(status_code=400, detail="Listing not pending_moderation")

    audit_id = str(uuid.uuid4())

    # action is for Backoffice AuditLogs UI compatibility
    if event_type.startswith("MODERATION_"):
        action_map = {
            "MODERATION_APPROVE": "APPROVE",
            "MODERATION_REJECT": "REJECT",
            "MODERATION_NEEDS_REVISION": "NEEDS_REVISION",
        }
        action_val = action_map.get(event_type, event_type)
    else:
        action_val = event_type

    audit_doc = {
        "id": audit_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "action": action_val,
        "listing_id": listing_id,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "country_code": listing.get("country"),
        "country_scope": current_user.get("country_scope") or [],
        "reason": reason,
        "reason_note": reason_note,
        "previous_status": prev_status,
        "new_status": new_status,
        "resource_type": "listing",
        "resource_id": listing_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)

    res = await db.vehicle_listings.update_one(
        {"id": listing_id, "status": prev_status},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.matched_count == 0:
        # Listing changed concurrently; keep audit row as applied=false
        raise HTTPException(status_code=409, detail="Listing status changed")

    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    updated = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})
    return updated


@api_router.get("/admin/moderation/queue")
async def moderation_queue(
    request: Request,
    status: str = "pending_moderation",
    dealer_only: Optional[bool] = None,
    country: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    _ensure_moderation_rbac(current_user)

    q: Dict = {"status": status}
    if dealer_only is not None:
        q["dealer_only"] = dealer_only
    if country:
        q["country"] = country.strip().upper()
    if module and module != "vehicle":
        # Only vehicle listings exist in Mongo MVP
        return []

    cursor = db.vehicle_listings.find(q, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(int(limit))
    docs = await cursor.to_list(length=int(limit))

    out = []
    for d in docs:
        attrs = d.get("attributes") or {}
        media = d.get("media") or []
        vehicle = d.get("vehicle") or {}
        title = (d.get("title") or "").strip() or f"{(vehicle.get('make_key') or '').upper()} {vehicle.get('model_key') or ''} {vehicle.get('year') or ''}".strip()
        out.append(
            {
                "id": d["id"],
                "title": title,
                "status": d.get("status"),
                "country": d.get("country"),
                "module": "vehicle",
                "city": "",
                "price": attrs.get("price_eur"),
                "currency": "EUR",
                "image_count": len(media),
                "created_at": d.get("created_at"),
                "is_dealer_listing": bool(d.get("dealer_only")),
                "dealer_only": bool(d.get("dealer_only")),
                "is_premium": False,
            }
        )

    return out


@api_router.get("/admin/moderation/queue/count")
async def moderation_queue_count(
    request: Request,
    status: str = "pending_moderation",
    dealer_only: Optional[bool] = None,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    _ensure_moderation_rbac(current_user)
    query: Dict[str, Any] = {"status": status}
    if dealer_only is not None:
        query["dealer_only"] = dealer_only
    count = await db.vehicle_listings.count_documents(query)
    return {"count": count}


@api_router.get("/admin/moderation/listings/{listing_id}")
async def moderation_listing_detail(
    listing_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    _ensure_moderation_rbac(current_user)

    listing = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # country-scope check for country_admin
    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope and listing.get("country") not in scope:
            raise HTTPException(status_code=403, detail="Country scope forbidden")

    v = listing.get("vehicle") or {}
    attrs = listing.get("attributes") or {}
    media = listing.get("media") or []

    title = (listing.get("title") or "").strip() or f"{(v.get('make_key') or '').upper()} {v.get('model_key') or ''} {v.get('year') or ''}".strip()

    moderation_history = await db.audit_logs.find(
        {"listing_id": listing_id, "resource_type": "listing"}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)

    return {
        "id": listing_id,
        "title": title,
        "status": listing.get("status"),
        "module": "vehicle",
        "country": listing.get("country"),
        "city": "",
        "price": attrs.get("price_eur"),
        "currency": "EUR",
        "description": "",
        "attributes": {**(v or {}), **(attrs or {})},
        "images": [],
        "image_count": len(media),
        "created_at": listing.get("created_at"),
        "moderation_history": moderation_history,
    }


class ModerationReasonPayload(BaseModel):
    reason: Optional[str] = None
    reason_note: Optional[str] = None


class ListingAdminActionPayload(BaseModel):
    reason: Optional[str] = None
    reason_note: Optional[str] = None


class ReportCreatePayload(BaseModel):
    listing_id: str
    reason: str
    reason_note: Optional[str] = None


class ReportStatusPayload(BaseModel):
    target_status: str
    note: str


class InvoiceCreatePayload(BaseModel):
    dealer_user_id: str
    country_code: str
    plan_id: str
    amount_net: float
    tax_rate: float
    currency: str
    issued_at: Optional[str] = None


class InvoiceStatusPayload(BaseModel):
    target_status: str
    note: Optional[str] = None


class TaxRateCreatePayload(BaseModel):
    country_code: str
    rate: float
    effective_date: str
    active_flag: Optional[bool] = True


class TaxRateUpdatePayload(BaseModel):
    rate: Optional[float] = None
    effective_date: Optional[str] = None
    active_flag: Optional[bool] = None


class PlanCreatePayload(BaseModel):
    name: str
    country_code: str
    price: float
    currency: str
    listing_quota: int
    showcase_quota: int
    active_flag: Optional[bool] = True


class PlanUpdatePayload(BaseModel):
    name: Optional[str] = None
    country_code: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    listing_quota: Optional[int] = None
    showcase_quota: Optional[int] = None
    active_flag: Optional[bool] = None


class DealerPlanAssignmentPayload(BaseModel):
    plan_id: Optional[str] = None


class CountryCreatePayload(BaseModel):
    country_code: str
    name: str
    active_flag: Optional[bool] = True
    default_currency: str
    default_language: Optional[str] = None


class CountryUpdatePayload(BaseModel):
    name: Optional[str] = None
    active_flag: Optional[bool] = None
    default_currency: Optional[str] = None
    default_language: Optional[str] = None


class SystemSettingCreatePayload(BaseModel):
    key: str
    value: Any
    country_code: Optional[str] = None
    is_readonly: Optional[bool] = False
    description: Optional[str] = None


class SystemSettingUpdatePayload(BaseModel):
    value: Optional[Any] = None
    country_code: Optional[str] = None
    is_readonly: Optional[bool] = None
    description: Optional[str] = None


class CategoryCreatePayload(BaseModel):
    name: str
    slug: str
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = True
    sort_order: Optional[int] = 0
    hierarchy_complete: Optional[bool] = None
    form_schema: Optional[Dict[str, Any]] = None


class CategoryUpdatePayload(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None
    sort_order: Optional[int] = None
    hierarchy_complete: Optional[bool] = None
    form_schema: Optional[Dict[str, Any]] = None
    expected_updated_at: Optional[str] = None


class MenuItemCreatePayload(BaseModel):
    label: str
    slug: str
    url: Optional[str] = None
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = True
    sort_order: Optional[int] = 0


class MenuItemUpdatePayload(BaseModel):
    label: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    parent_id: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None
    sort_order: Optional[int] = None


class AttributeCreatePayload(BaseModel):
    category_id: str
    name: str
    key: str
    type: str
    required_flag: Optional[bool] = False
    filterable_flag: Optional[bool] = False
    options: Optional[List[str]] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = True


class AttributeUpdatePayload(BaseModel):
    name: Optional[str] = None
    key: Optional[str] = None
    type: Optional[str] = None
    required_flag: Optional[bool] = None
    filterable_flag: Optional[bool] = None
    options: Optional[List[str]] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None


class VehicleMakeCreatePayload(BaseModel):
    name: str
    slug: str
    country_code: str
    active_flag: Optional[bool] = True


class VehicleMakeUpdatePayload(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    country_code: Optional[str] = None
    active_flag: Optional[bool] = None


class VehicleModelCreatePayload(BaseModel):
    make_id: str
    name: str
    slug: str
    active_flag: Optional[bool] = True


class VehicleModelUpdatePayload(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    make_id: Optional[str] = None
    active_flag: Optional[bool] = None


def _resolve_listing_title(listing: dict) -> str:
    title = (listing.get("title") or "").strip()
    if title:
        return title
    v = listing.get("vehicle") or {}
    return f"{(v.get('make_key') or '').upper()} {v.get('model_key') or ''} {v.get('year') or ''}".strip()


def _parse_bool_flag(value: Optional[str | bool]) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raw = str(value).strip().lower()
    if raw in {"1", "true", "yes", "y"}:
        return True
    if raw in {"0", "false", "no", "n"}:
        return False
    return None


async def _admin_listing_action(
    *,
    db,
    listing_id: str,
    current_user: dict,
    event_type: str,
    new_status: str,
    reason: Optional[str] = None,
    reason_note: Optional[str] = None,
) -> dict:
    listing = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope and listing.get("country") not in scope:
            raise HTTPException(status_code=403, detail="Country scope forbidden")

    prev_status = listing.get("status")
    if prev_status == new_status:
        raise HTTPException(status_code=400, detail="Listing already in target status")

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": event_type,
        "action": event_type,
        "listing_id": listing_id,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "country_code": listing.get("country"),
        "country_scope": current_user.get("country_scope") or [],
        "reason": reason,
        "reason_note": reason_note,
        "previous_status": prev_status,
        "new_status": new_status,
        "resource_type": "listing",
        "resource_id": listing_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)

    update_payload = {
        "status": new_status,
        "updated_at": now_iso,
        "admin_last_action": event_type,
        "admin_last_action_at": now_iso,
    }
    if event_type == "LISTING_SOFT_DELETE":
        update_payload["archived_at"] = now_iso
        update_payload["archived_by"] = current_user.get("id")
    if event_type == "LISTING_FORCE_UNPUBLISH":
        update_payload["unpublished_at"] = now_iso
        update_payload["unpublished_by"] = current_user.get("id")

    res = await db.vehicle_listings.update_one(
        {"id": listing_id, "status": prev_status},
        {"$set": update_payload},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Listing changed concurrently")

    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    updated = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})
    return updated


def _check_report_rate_limit(request: Request, listing_id: str, reporter_user_id: Optional[str]) -> None:
    ip_address = _get_client_ip(request) or "unknown"
    key = f"{ip_address}:{reporter_user_id or 'anon'}:{listing_id}"
    now = time.time()
    attempts = _report_submit_attempts.get(key, [])
    attempts = [ts for ts in attempts if (now - ts) <= REPORT_RATE_LIMIT_WINDOW_SECONDS]
    if len(attempts) >= REPORT_RATE_LIMIT_MAX_ATTEMPTS:
        retry_after_seconds = int(REPORT_RATE_LIMIT_WINDOW_SECONDS - (now - attempts[0]))
        raise HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED", "retry_after_seconds": max(retry_after_seconds, 1)},
        )
    attempts.append(now)
    _report_submit_attempts[key] = attempts


def _validate_report_reason(reason: str, reason_note: Optional[str]) -> tuple[str, Optional[str]]:
    r = _validate_reason(reason, REPORT_REASONS_V1)
    note = (reason_note or "").strip() or None
    if r == "other" and not note:
        raise HTTPException(status_code=400, detail="reason_note is required when reason=other")
    return r, note


def _assert_country_scope(country_code: str, current_user: dict) -> None:
    if country_code not in SUPPORTED_COUNTRIES:
        raise HTTPException(status_code=400, detail="Invalid country code")
    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope and country_code not in scope:
            raise HTTPException(status_code=403, detail="Country scope forbidden")


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    if not value:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    value = value.replace(" ", "+")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


def _normalize_country_doc(doc: dict) -> dict:
    name = doc.get("name")
    if isinstance(name, dict):
        name_value = name.get("tr") or name.get("en") or name.get("de") or name.get("fr") or next(iter(name.values()), None)
    else:
        name_value = name
    return {
        "country_code": (doc.get("country_code") or doc.get("code") or "").upper(),
        "name": name_value,
        "active_flag": doc.get("active_flag", doc.get("is_enabled", True)),
        "default_currency": doc.get("default_currency"),
        "default_language": doc.get("default_language"),
        "updated_at": doc.get("updated_at"),
        "created_at": doc.get("created_at"),
    }


def _pick_label(value) -> Optional[str]:
    if isinstance(value, dict):
        return value.get("tr") or value.get("en") or value.get("de") or value.get("fr") or next(iter(value.values()), None)
    return value


def _normalize_category_doc(doc: dict, include_schema: bool = False) -> dict:
    payload = {
        "id": doc.get("id"),
        "parent_id": doc.get("parent_id"),
        "name": _pick_label(doc.get("name")) or _pick_label(doc.get("translations", [{}])[0].get("name") if doc.get("translations") else None),
        "slug": _pick_label(doc.get("slug")) or doc.get("segment"),
        "country_code": doc.get("country_code"),
        "active_flag": doc.get("active_flag", doc.get("is_enabled", True)),
        "sort_order": doc.get("sort_order", 0),
        "hierarchy_complete": doc.get("hierarchy_complete", True),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }
    if include_schema:
        payload["form_schema"] = _normalize_category_schema(doc.get("form_schema")) if doc.get("form_schema") else None
    return payload


def _deep_merge_schema(base: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not override:
        return base
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge_schema(base[key], value)
        else:
            base[key] = value
    return base


def _default_category_schema() -> Dict[str, Any]:
    return {
        "core_fields": {
            "title": {
                "required": True,
                "min": 10,
                "max": 80,
                "messages": {
                    "required": "Başlık zorunludur.",
                    "min": "Başlık çok kısa.",
                    "max": "Başlık çok uzun.",
                    "duplicate": "Bu başlık zaten kullanılıyor.",
                },
                "ui": {"bold": True},
            },
            "description": {
                "required": True,
                "min": 30,
                "max": 2000,
                "messages": {
                    "required": "Açıklama zorunludur.",
                    "min": "Açıklama çok kısa.",
                    "max": "Açıklama çok uzun.",
                },
                "ui": {"min_rows": 6, "max_rows": 8, "auto_grow": True, "show_counter": True},
            },
            "price": {
                "required": True,
                "currency_primary": "EUR",
                "currency_secondary": "CHF",
                "secondary_enabled": False,
                "decimal_places": 0,
                "range": {"min": None, "max": None},
                "messages": {
                    "required": "Fiyat zorunludur.",
                    "numeric": "Geçerli bir fiyat girin.",
                    "range": "Fiyat aralık dışında.",
                },
                "input_mask": {"thousand_separator": True},
            },
        },
        "title_uniqueness": {"enabled": False, "scope": "category"},
        "status": "published",
        "dynamic_fields": [],
        "detail_groups": [],
        "modules": {
            "address": {"enabled": True},
            "photos": {"enabled": True, "max_uploads": 10},
            "contact": {"enabled": True},
            "payment": {"enabled": True},
        },
        "payment_options": {"package": True, "doping": False},
        "module_order": [
            "core_fields",
            "dynamic_fields",
            "address",
            "detail_groups",
            "photos",
            "contact",
            "payment",
        ],
    }


def _normalize_category_schema(schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base = _default_category_schema()
    merged = _deep_merge_schema(base, schema or {})
    merged.setdefault("status", "published")
    title_messages = merged["core_fields"]["title"].setdefault("messages", {})
    desc_messages = merged["core_fields"]["description"].setdefault("messages", {})
    price_messages = merged["core_fields"]["price"].setdefault("messages", {})
    title_messages.setdefault("required", "Başlık zorunludur.")
    title_messages.setdefault("min", "Başlık çok kısa.")
    title_messages.setdefault("max", "Başlık çok uzun.")
    title_messages.setdefault("duplicate", "Bu başlık zaten kullanılıyor.")
    desc_messages.setdefault("required", "Açıklama zorunludur.")
    desc_messages.setdefault("min", "Açıklama çok kısa.")
    desc_messages.setdefault("max", "Açıklama çok uzun.")
    price_messages.setdefault("required", "Fiyat zorunludur.")
    price_messages.setdefault("numeric", "Geçerli bir fiyat girin.")
    price_messages.setdefault("range", "Fiyat aralık dışında.")
    merged["validation_messages"] = {
        "core_fields": {
            "title": title_messages,
            "description": desc_messages,
            "price": price_messages,
        },
        "dynamic_fields": {
            field.get("key"): field.get("messages", {})
            for field in merged.get("dynamic_fields", [])
        },
        "detail_groups": {
            group.get("id"): group.get("messages", {})
            for group in merged.get("detail_groups", [])
        },
    }
    return merged


async def _record_category_version(
    db,
    category_id: str,
    schema_snapshot: Dict[str, Any],
    actor: dict,
    status: str,
    max_versions: int = 20,
) -> dict:
    latest = await db.categories_versions.find(
        {"category_id": category_id},
        {"_id": 0, "version": 1},
    ).sort("version", -1).to_list(length=1)
    next_version = (latest[0].get("version", 0) if latest else 0) + 1
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "category_id": category_id,
        "version": next_version,
        "status": status,
        "schema_snapshot": schema_snapshot,
        "created_at": now_iso,
        "created_by": actor.get("id"),
        "created_by_role": actor.get("role"),
        "created_by_email": actor.get("email"),
    }
    await db.categories_versions.insert_one(doc)

    if max_versions and max_versions > 0:
        overflow = await db.categories_versions.find(
            {"category_id": category_id},
            {"_id": 0, "id": 1},
        ).sort("version", -1).skip(max_versions).to_list(length=200)
        if overflow:
            await db.categories_versions.delete_many({"id": {"$in": [v.get("id") for v in overflow if v.get("id")]}})

    return doc


async def _mark_latest_category_version_published(
    db,
    category_id: str,
    schema_snapshot: Dict[str, Any],
    actor: dict,
    max_versions: int = 20,
) -> dict:
    latest = await db.categories_versions.find(
        {"category_id": category_id},
        {"_id": 0},
    ).sort("version", -1).to_list(length=1)
    now_iso = datetime.now(timezone.utc).isoformat()
    if latest:
        latest_doc = latest[0]
        await db.categories_versions.update_one(
            {"id": latest_doc.get("id")},
            {"$set": {"status": "published", "published_at": now_iso, "published_by": actor.get("id")}},
        )
        latest_doc.update({"status": "published", "published_at": now_iso, "published_by": actor.get("id")})
        return latest_doc

    return await _record_category_version(db, category_id, schema_snapshot, actor, "published", max_versions=max_versions)


def _serialize_category_version(doc: dict, include_snapshot: bool = False) -> dict:
    payload = {
        "id": doc.get("id"),
        "category_id": doc.get("category_id"),
        "version": doc.get("version"),
        "status": doc.get("status"),
        "created_at": doc.get("created_at"),
        "created_by": doc.get("created_by"),
        "created_by_role": doc.get("created_by_role"),
        "created_by_email": doc.get("created_by_email"),
        "published_at": doc.get("published_at"),
        "published_by": doc.get("published_by"),
    }
    if include_snapshot:
        payload["schema_snapshot"] = doc.get("schema_snapshot")
    return payload


async def _get_schema_version_for_export(db, category_id: str) -> int:
    latest_docs = await db.categories_versions.find(
        {"category_id": category_id},
        {"_id": 0, "version": 1},
    ).sort("version", -1).to_list(length=1)
    if not latest_docs:
        return 0
    return int(latest_docs[0].get("version") or 0)


def _schema_to_csv_rows(schema: Dict[str, Any]) -> list[list[str]]:
    rows = []
    rows.append([
        "section",
        "field_key",
        "label",
        "type",
        "required",
        "enabled",
        "options",
        "messages_required",
        "messages_invalid",
        "messages_min",
        "messages_max",
        "messages_range",
        "messages_duplicate",
    ])

    core = schema.get("core_fields") or {}
    for key in ["title", "description", "price"]:
        cfg = core.get(key) or {}
        messages = cfg.get("messages") or {}
        rows.append([
            "core_fields",
            key,
            key,
            cfg.get("type") or ("price" if key == "price" else "text"),
            str(bool(cfg.get("required"))),
            "",
            "",
            str(messages.get("required", "")),
            str(messages.get("invalid", "")),
            str(messages.get("min", "")),
            str(messages.get("max", "")),
            str(messages.get("range", "")),
            str(messages.get("duplicate", "")),
        ])

    for field in schema.get("dynamic_fields", []) or []:
        messages = field.get("messages") or {}
        options = ",".join(field.get("options") or [])
        rows.append([
            "dynamic_fields",
            str(field.get("key")),
            str(field.get("label")),
            str(field.get("type")),
            str(bool(field.get("required"))),
            "",
            options,
            str(messages.get("required", "")),
            str(messages.get("invalid", "")),
            str(messages.get("min", "")),
            str(messages.get("max", "")),
            str(messages.get("range", "")),
            str(messages.get("duplicate", "")),
        ])

    for group in schema.get("detail_groups", []) or []:
        messages = group.get("messages") or {}
        options = ",".join(group.get("options") or [])
        rows.append([
            "detail_groups",
            str(group.get("id") or group.get("title")),
            str(group.get("title")),
            "checkbox_group",
            str(bool(group.get("required"))),
            "",
            options,
            str(messages.get("required", "")),
            str(messages.get("invalid", "")),
            str(messages.get("min", "")),
            str(messages.get("max", "")),
            str(messages.get("range", "")),
            str(messages.get("duplicate", "")),
        ])

    modules = schema.get("modules") or {}
    for key, module in modules.items():
        enabled = bool(module.get("enabled")) if isinstance(module, dict) else bool(module)
        rows.append([
            "modules",
            str(key),
            str(key),
            "module",
            "",
            str(enabled),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ])

    payment = schema.get("payment_options") or {}
    if payment:
        rows.append([
            "payment_options",
            "package",
            "package",
            "payment",
            "",
            str(bool(payment.get("package"))),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ])
        rows.append([
            "payment_options",
            "doping",
            "doping",
            "payment",
            "",
            str(bool(payment.get("doping"))),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ])

    title_uniqueness = schema.get("title_uniqueness") or {}
    if title_uniqueness.get("enabled"):
        rows.append([
            "rules",
            "title_uniqueness",
            "title_uniqueness",
            "rule",
            "",
            str(bool(title_uniqueness.get("enabled"))),
            "",
            "",
            "",
            "",
            "",
            "",
            str(title_uniqueness.get("scope") or ""),
        ])

    return rows


def _build_schema_pdf(schema: Dict[str, Any], category: dict, version: int, hierarchy: dict) -> bytes:
    styles = getSampleStyleSheet()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Schema Export")
    elements = []
    elements.append(Paragraph("Kategori Şema Export", styles["Title"]))
    elements.append(Paragraph(f"Kategori: {category.get('name')} ({category.get('slug')})", styles["Normal"]))
    elements.append(Paragraph(f"Versiyon: v{version}", styles["Normal"]))
    elements.append(Paragraph(f"Durum: {schema.get('status')}", styles["Normal"]))
    elements.append(Paragraph(f"Ana kategori: {hierarchy.get('parent') or '-'}", styles["Normal"]))
    elements.append(Paragraph(f"Alt kategoriler: {', '.join(hierarchy.get('children') or []) or '-'}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    def add_table(title: str, rows: list[list[str]]):
        if not rows:
            return
        elements.append(Paragraph(title, styles["Heading3"]))
        table = Table(rows, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

    core_rows = [["Alan", "Required", "Min", "Max", "Range", "Messages"]]
    for key, cfg in (schema.get("core_fields") or {}).items():
        messages = cfg.get("messages") or {}
        range_cfg = cfg.get("range") or {}
        core_rows.append([
            key,
            str(cfg.get("required")),
            str(cfg.get("min", "")),
            str(cfg.get("max", "")),
            f"{range_cfg.get('min', '')}-{range_cfg.get('max', '')}",
            ", ".join([str(v) for v in messages.values() if v]),
        ])
    add_table("Çekirdek Alanlar", core_rows)

    dynamic_rows = [["Key", "Label", "Type", "Required", "Options", "Messages"]]
    for field in schema.get("dynamic_fields", []) or []:
        messages = field.get("messages") or {}
        dynamic_rows.append([
            str(field.get("key")),
            str(field.get("label")),
            str(field.get("type")),
            str(field.get("required")),
            ",".join(field.get("options") or []),
            ", ".join([str(v) for v in messages.values() if v]),
        ])
    add_table("Parametre Alanları (2a)", dynamic_rows)

    detail_rows = [["Group", "Required", "Options", "Messages"]]
    for group in schema.get("detail_groups", []) or []:
        messages = group.get("messages") or {}
        detail_rows.append([
            str(group.get("title")),
            str(group.get("required")),
            ",".join(group.get("options") or []),
            ", ".join([str(v) for v in messages.values() if v]),
        ])
    add_table("Detay Grupları (2c)", detail_rows)

    modules_rows = [["Module", "Enabled"]]
    for key, module in (schema.get("modules") or {}).items():
        enabled = bool(module.get("enabled")) if isinstance(module, dict) else bool(module)
        modules_rows.append([str(key), str(enabled)])
    add_table("Modüller", modules_rows)

    if (schema.get("payment_options") or {}):
        payment = schema.get("payment_options") or {}
        payment_rows = [["Option", "Enabled"]]
        payment_rows.append(["package", str(bool(payment.get("package")))])
        payment_rows.append(["doping", str(bool(payment.get("doping")))])
        add_table("Ödeme Seçenekleri", payment_rows)

    title_uniqueness = schema.get("title_uniqueness") or {}
    if title_uniqueness:
        rule_rows = [["Rule", "Enabled", "Scope"]]
        rule_rows.append(["title_uniqueness", str(bool(title_uniqueness.get("enabled"))), str(title_uniqueness.get("scope") or "")])
        add_table("Duplicate Kuralı", rule_rows)

    doc.build(elements)
    return buffer.getvalue()



def _validate_category_schema(schema: Dict[str, Any]) -> None:
    core = schema.get("core_fields") or {}
    title = core.get("title") or {}
    description = core.get("description") or {}
    price = core.get("price") or {}
    if not title.get("required", True):
        raise HTTPException(status_code=400, detail="Başlık alanı zorunlu olmalıdır.")
    if not description.get("required", True):
        raise HTTPException(status_code=400, detail="Açıklama alanı zorunlu olmalıdır.")
    if not price.get("required", True):
        raise HTTPException(status_code=400, detail="Fiyat alanı zorunlu olmalıdır.")

    if title.get("min") and title.get("max") and title.get("min") > title.get("max"):
        raise HTTPException(status_code=400, detail="Başlık min değeri max değerinden büyük olamaz.")
    if description.get("min") and description.get("max") and description.get("min") > description.get("max"):
        raise HTTPException(status_code=400, detail="Açıklama min değeri max değerinden büyük olamaz.")

    currency_primary = price.get("currency_primary")
    if currency_primary not in {"EUR", "CHF"}:
        raise HTTPException(status_code=400, detail="Fiyat para birimi EUR veya CHF olmalıdır.")
    secondary = price.get("currency_secondary")
    if secondary and secondary not in {"EUR", "CHF"}:
        raise HTTPException(status_code=400, detail="İkincil para birimi EUR veya CHF olmalıdır.")
    if secondary and secondary == currency_primary:
        raise HTTPException(status_code=400, detail="Birincil ve ikincil para birimi aynı olamaz.")
    price_range = price.get("range") or {}
    if price_range.get("max") is not None and price_range.get("min") is not None:
        if price_range.get("min") > price_range.get("max"):
            raise HTTPException(status_code=400, detail="Fiyat aralığı min/max hatalı.")

    for field in schema.get("dynamic_fields", []):
        field_type = field.get("type")
        if field_type not in {"radio", "select", "text", "number"}:
            raise HTTPException(status_code=400, detail="Parametre alanı tipi radio/select/text/number olmalıdır.")
        options = field.get("options") or []
        if field_type in {"radio", "select"} and not options:
            raise HTTPException(status_code=400, detail="Parametre alanı için seçenek listesi zorunludur.")
        if not field.get("key"):
            raise HTTPException(status_code=400, detail="Parametre alanı anahtarı zorunludur.")
        if not field.get("label"):
            raise HTTPException(status_code=400, detail="Parametre alanı etiketi zorunludur.")

    for group in schema.get("detail_groups", []):
        if not group.get("title"):
            raise HTTPException(status_code=400, detail="Detay grubu başlığı zorunludur.")
        options = group.get("options") or []
        if not options:
            raise HTTPException(status_code=400, detail="Detay grubu için seçenek listesi zorunludur.")

    modules = schema.get("modules") or {}
    photos = modules.get("photos") or {}
    if photos.get("enabled") and not photos.get("max_uploads"):
        raise HTTPException(status_code=400, detail="Fotoğraf modülü için upload limiti zorunludur.")


def _normalize_attribute_doc(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "category_id": doc.get("category_id"),
        "name": doc.get("name"),
        "key": doc.get("key"),
        "type": doc.get("type"),
        "required_flag": doc.get("required_flag", False),
        "filterable_flag": doc.get("filterable_flag", False),
        "options": doc.get("options"),
        "country_code": doc.get("country_code"),
        "active_flag": doc.get("active_flag", True),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _normalize_vehicle_make_doc(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "slug": doc.get("slug"),
        "country_code": doc.get("country_code"),
        "active_flag": doc.get("active_flag", True),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _normalize_vehicle_model_doc(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "make_id": doc.get("make_id"),
        "name": doc.get("name"),
        "slug": doc.get("slug"),
        "active_flag": doc.get("active_flag", True),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


async def _get_required_attribute_keys(db, category_id: str, country_code: Optional[str]) -> list[str]:
    if not category_id:
        return []
    query = {
        "category_id": category_id,
        "required_flag": True,
        "active_flag": True,
    }
    if country_code:
        query["$or"] = [
            {"country_code": None},
            {"country_code": ""},
            {"country_code": country_code},
        ]
    docs = await db.attributes.find(query, {"_id": 0, "key": 1}).to_list(length=500)
    return [doc.get("key") for doc in docs if doc.get("key")]


async def _build_vehicle_master_from_db(db, country_code: str) -> dict:
    if not country_code:
        return {"makes": {}, "models": {}}
    make_docs = await db.vehicle_makes.find(
        {"country_code": country_code, "active_flag": True},
        {"_id": 0, "id": 1, "slug": 1, "name": 1},
    ).to_list(length=500)
    makes = [
        {
            "make_key": doc.get("slug"),
            "name": doc.get("name"),
            "is_active": doc.get("active_flag", True),
        }
        for doc in make_docs
        if doc.get("slug")
    ]
    make_ids = [doc["id"] for doc in make_docs if doc.get("id")]
    if not make_ids:
        return {"makes": makes, "models_by_make": {}}
    model_docs = await db.vehicle_models.find(
        {"make_id": {"$in": make_ids}, "active_flag": True},
        {"_id": 0, "make_id": 1, "slug": 1},
    ).to_list(length=1000)
    models_by_make: dict = {}
    make_slug_by_id = {doc["id"]: doc["slug"] for doc in make_docs if doc.get("id")}
    for model in model_docs:
        make_slug = make_slug_by_id.get(model.get("make_id"))
        if not make_slug or not model.get("slug"):
            continue
        models_by_make.setdefault(make_slug, []).append(
            {
                "model_key": model.get("slug"),
                "name": model.get("name"),
                "is_active": model.get("active_flag", True),
            }
        )
    return {"makes": makes, "models_by_make": models_by_make}


async def _report_transition(
    *,
    db,
    report_id: str,
    current_user: dict,
    target_status: str,
    note: str,
) -> dict:
    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope and report.get("country_code") not in scope:
            raise HTTPException(status_code=403, detail="Country scope forbidden")

    prev_status = report.get("status")
    allowed = REPORT_STATUS_TRANSITIONS.get(prev_status, set())
    if target_status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status transition")

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "REPORT_STATUS_CHANGE",
        "action": "REPORT_STATUS_CHANGE",
        "report_id": report_id,
        "listing_id": report.get("listing_id"),
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "country_code": report.get("country_code"),
        "country_scope": current_user.get("country_scope") or [],
        "note": note,
        "previous_status": prev_status,
        "new_status": target_status,
        "resource_type": "report",
        "resource_id": report_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)

    res = await db.reports.update_one(
        {"id": report_id, "status": prev_status},
        {
            "$set": {
                "status": target_status,
                "updated_at": now_iso,
                "handled_by_admin_id": current_user.get("id"),
                "status_note": note,
            }
        },
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=409, detail="Report status changed concurrently")

    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})
    updated = await db.reports.find_one({"id": report_id}, {"_id": 0})
    return updated


@api_router.post("/admin/listings/{listing_id}/approve")
async def admin_approve_listing(
    listing_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    updated = await _moderation_transition(
        db=db,
        listing_id=listing_id,
        current_user=current_user,
        event_type="MODERATION_APPROVE",
        new_status="published",
    )
    return {"ok": True, "listing": {"id": updated["id"], "status": updated.get("status")}}


@api_router.post("/admin/listings/{listing_id}/reject")
async def admin_reject_listing(
    listing_id: str,
    payload: ModerationReasonPayload,
    request: Request,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    reason = _validate_reason(payload.reason, REJECT_REASONS_V1)
    updated = await _moderation_transition(
        db=db,
        listing_id=listing_id,
        current_user=current_user,
        event_type="MODERATION_REJECT",
        new_status="rejected",
        reason=reason,
        reason_note=(payload.reason_note or None),
    )
    return {"ok": True, "listing": {"id": updated["id"], "status": updated.get("status")}}


@api_router.post("/admin/listings/{listing_id}/needs_revision")
async def admin_needs_revision_listing(
    listing_id: str,
    payload: ModerationReasonPayload,
    request: Request,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    reason = _validate_reason(payload.reason, NEEDS_REVISION_REASONS_V1)
    reason_note = (payload.reason_note or "").strip() or None
    if reason == "other" and not reason_note:
        raise HTTPException(status_code=400, detail="reason_note is required when reason=other")

    updated = await _moderation_transition(
        db=db,
        listing_id=listing_id,
        current_user=current_user,
        event_type="MODERATION_NEEDS_REVISION",
        new_status="needs_revision",
        reason=reason,
        reason_note=reason_note,
    )
    return {"ok": True, "listing": {"id": updated["id"], "status": updated.get("status")}}


# =====================
# Sprint 2.1 — Admin Global Listing Management
# =====================


@api_router.get("/admin/listings")
async def admin_listings(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    q: Optional[str] = None,
    dealer_only: Optional[str] = None,
    category_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict = {}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country"] = ctx.country
    if status:
        query["status"] = status

    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"id": {"$regex": q, "$options": "i"}},
            {"vehicle.make_key": {"$regex": q, "$options": "i"}},
            {"vehicle.model_key": {"$regex": q, "$options": "i"}},
        ]

    if category_id:
        keys = [category_id]
        cat = await db.categories.find_one(
            {
                "$or": [
                    {"slug": category_id},
                    {"id": category_id},
                ],
            },
            {"_id": 0, "id": 1, "slug": 1},
        )
        if cat:
            if cat.get("id"):
                keys.append(cat["id"])
            slug_value = _pick_label(cat.get("slug"))
            if slug_value:
                keys.append(slug_value)
        query["category_key"] = {"$in": list(set(keys))}

    if owner_id:
        query["created_by"] = owner_id

    dealer_only_flag = _parse_bool_flag(dealer_only)
    if dealer_only_flag and not owner_id:
        dealer_query: Dict = {"role": "dealer"}
        if getattr(ctx, "mode", "global") == "country" and ctx.country:
            dealer_query["country_code"] = ctx.country
        dealer_users = await db.users.find(dealer_query, {"_id": 0, "id": 1}).to_list(length=5000)
        dealer_ids = [u.get("id") for u in dealer_users if u.get("id")]
        if not dealer_ids:
            return {"items": [], "pagination": {"total": 0, "skip": int(skip), "limit": min(100, max(1, int(limit)))}}
        query["created_by"] = {"$in": dealer_ids}

    limit = min(100, max(1, int(limit)))
    cursor = db.vehicle_listings.find(query, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(limit)
    docs = await cursor.to_list(length=limit)

    owner_ids = [d.get("created_by") for d in docs if d.get("created_by")]
    user_map: Dict[str, dict] = {}
    if owner_ids:
        users = await db.users.find({"id": {"$in": owner_ids}}, {"_id": 0, "id": 1, "email": 1, "role": 1}).to_list(length=len(owner_ids))
        user_map = {u.get("id"): u for u in users}

    items = []
    for d in docs:
        attrs = d.get("attributes") or {}
        media = d.get("media") or []
        owner = user_map.get(d.get("created_by"), {})
        items.append(
            {
                "id": d.get("id"),
                "title": _resolve_listing_title(d),
                "status": d.get("status"),
                "country": d.get("country"),
                "category_key": d.get("category_key"),
                "price": attrs.get("price_eur"),
                "currency": "EUR",
                "image_count": len(media),
                "created_at": d.get("created_at"),
                "owner_id": d.get("created_by"),
                "owner_email": owner.get("email"),
                "owner_role": owner.get("role"),
                "is_dealer_listing": owner.get("role") == "dealer",
            }
        )

    total = await db.vehicle_listings.count_documents(query)
    return {"items": items, "pagination": {"total": total, "skip": int(skip), "limit": limit}}


@api_router.post("/admin/listings/{listing_id}/soft-delete")
async def admin_soft_delete_listing(
    listing_id: str,
    payload: ListingAdminActionPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    updated = await _admin_listing_action(
        db=db,
        listing_id=listing_id,
        current_user=current_user,
        event_type="LISTING_SOFT_DELETE",
        new_status="archived",
        reason=(payload.reason or None),
        reason_note=(payload.reason_note or None),
    )
    return {"ok": True, "listing": {"id": updated["id"], "status": updated.get("status")}}


@api_router.post("/admin/listings/{listing_id}/force-unpublish")
async def admin_force_unpublish_listing(
    listing_id: str,
    payload: ListingAdminActionPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    listing = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0, "status": 1})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("status") != "published":
        raise HTTPException(status_code=400, detail="Only published listings can be force-unpublished")

    updated = await _admin_listing_action(
        db=db,
        listing_id=listing_id,
        current_user=current_user,
        event_type="LISTING_FORCE_UNPUBLISH",
        new_status="unpublished",
        reason=(payload.reason or None),
        reason_note=(payload.reason_note or None),
    )
    return {"ok": True, "listing": {"id": updated["id"], "status": updated.get("status")}}


# =====================
# Sprint 2.2 — Reports Engine
# =====================


@api_router.post("/reports")
async def create_report(
    payload: ReportCreatePayload,
    request: Request,
    current_user=Depends(get_current_user_optional),
):
    db = request.app.state.db
    listing_id = payload.listing_id
    listing = await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("status") != "published":
        raise HTTPException(status_code=400, detail="Only published listings can be reported")

    reason, reason_note = _validate_report_reason(payload.reason, payload.reason_note)
    reporter_user_id = current_user.get("id") if current_user else None
    _check_report_rate_limit(request, listing_id, reporter_user_id)

    now_iso = datetime.now(timezone.utc).isoformat()
    report_id = str(uuid.uuid4())
    report_doc = {
        "id": report_id,
        "listing_id": listing_id,
        "reporter_user_id": reporter_user_id,
        "reason": reason,
        "reason_note": reason_note,
        "status": "open",
        "country_code": listing.get("country"),
        "created_at": now_iso,
        "updated_at": None,
        "handled_by_admin_id": None,
    }

    await db.reports.insert_one(report_doc)

    await db.audit_logs.insert_one(
        {
            "id": str(uuid.uuid4()),
            "created_at": now_iso,
            "event_type": "REPORT_CREATED",
            "action": "REPORT_CREATED",
            "report_id": report_id,
            "listing_id": listing_id,
            "user_id": reporter_user_id,
            "user_email": current_user.get("email") if current_user else None,
            "country_code": listing.get("country"),
            "reason": reason,
            "resource_type": "report",
            "resource_id": report_id,
        }
    )

    return {"ok": True, "report_id": report_id, "status": "open"}


@api_router.get("/admin/reports")
async def admin_reports(
    request: Request,
    status: Optional[str] = None,
    reason: Optional[str] = None,
    listing_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    q: Dict = {}
    if status:
        if status not in REPORT_STATUS_SET:
            raise HTTPException(status_code=400, detail="Invalid status")
        q["status"] = status
    if reason:
        _validate_reason(reason, REPORT_REASONS_V1)
        q["reason"] = reason
    if listing_id:
        q["listing_id"] = listing_id

    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        q["country_code"] = ctx.country
    elif current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope:
            q["country_code"] = {"$in": scope}

    limit = min(100, max(1, int(limit)))
    cursor = db.reports.find(q, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(limit)
    docs = await cursor.to_list(length=limit)

    listing_ids = [d.get("listing_id") for d in docs if d.get("listing_id")]
    listing_map: Dict[str, dict] = {}
    if listing_ids:
        listings = await db.vehicle_listings.find({"id": {"$in": listing_ids}}, {"_id": 0}).to_list(length=len(listing_ids))
        listing_map = {listing_doc.get("id"): listing_doc for listing_doc in listings}

    reporter_ids = [d.get("reporter_user_id") for d in docs if d.get("reporter_user_id")]
    seller_ids = [listing_doc.get("created_by") for listing_doc in listing_map.values() if listing_doc.get("created_by")]
    user_ids = list({*reporter_ids, *seller_ids})
    user_map: Dict[str, dict] = {}
    if user_ids:
        users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "role": 1, "dealer_status": 1}).to_list(length=len(user_ids))
        user_map = {u.get("id"): u for u in users}

    items = []
    for d in docs:
        listing = listing_map.get(d.get("listing_id"), {})
        seller = user_map.get(listing.get("created_by"), {})
        reporter = user_map.get(d.get("reporter_user_id"), {})
        items.append(
            {
                "id": d.get("id"),
                "listing_id": d.get("listing_id"),
                "reason": d.get("reason"),
                "reason_note": d.get("reason_note"),
                "status": d.get("status"),
                "country_code": d.get("country_code"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
                "reporter_user_id": d.get("reporter_user_id"),
                "reporter_email": reporter.get("email"),
                "listing_title": _resolve_listing_title(listing) if listing else None,
                "listing_status": listing.get("status"),
                "seller_id": listing.get("created_by"),
                "seller_email": seller.get("email"),
                "seller_role": seller.get("role"),
                "seller_dealer_status": seller.get("dealer_status"),
            }
        )

    total = await db.reports.count_documents(q)
    return {"items": items, "pagination": {"total": total, "skip": int(skip), "limit": limit}}


@api_router.get("/admin/reports/{report_id}")
async def admin_report_detail(
    report_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        if report.get("country_code") != ctx.country:
            raise HTTPException(status_code=403, detail="Country scope forbidden")
    elif current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope and report.get("country_code") not in scope:
            raise HTTPException(status_code=403, detail="Country scope forbidden")

    listing = await db.vehicle_listings.find_one({"id": report.get("listing_id")}, {"_id": 0})
    seller = None
    if listing and listing.get("created_by"):
        seller = await db.users.find_one({"id": listing.get("created_by")}, {"_id": 0, "id": 1, "email": 1, "role": 1, "dealer_status": 1, "country_code": 1})

    reporter = None
    if report.get("reporter_user_id"):
        reporter = await db.users.find_one({"id": report.get("reporter_user_id")}, {"_id": 0, "id": 1, "email": 1, "role": 1})

    listing_snapshot = None
    if listing:
        attrs = listing.get("attributes") or {}
        listing_snapshot = {
            "id": listing.get("id"),
            "title": _resolve_listing_title(listing),
            "status": listing.get("status"),
            "country": listing.get("country"),
            "category_key": listing.get("category_key"),
            "price": attrs.get("price_eur"),
            "currency": "EUR",
            "created_at": listing.get("created_at"),
        }

    seller_summary = None
    if seller:
        seller_summary = {
            "id": seller.get("id"),
            "email": seller.get("email"),
            "role": seller.get("role"),
            "dealer_status": seller.get("dealer_status"),
            "country_code": seller.get("country_code"),
        }

    reporter_summary = None
    if reporter:
        reporter_summary = {
            "id": reporter.get("id"),
            "email": reporter.get("email"),
            "role": reporter.get("role"),
        }

    return {
        **report,
        "listing_snapshot": listing_snapshot,
        "seller_summary": seller_summary,
        "reporter_summary": reporter_summary,
    }


@api_router.post("/admin/reports/{report_id}/status")
async def admin_report_status_change(
    report_id: str,
    payload: ReportStatusPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    target_status = (payload.target_status or "").strip()
    if target_status not in REPORT_STATUS_SET:
        raise HTTPException(status_code=400, detail="Invalid target_status")
    note = (payload.note or "").strip()
    if not note:
        raise HTTPException(status_code=400, detail="note is required")

    updated = await _report_transition(
        db=db,
        report_id=report_id,
        current_user=current_user,
        target_status=target_status,
        note=note,
    )
    return {"ok": True, "report": {"id": updated["id"], "status": updated.get("status")}}


# =====================
# Sprint 3 — Finance Domain
# =====================


@api_router.post("/admin/invoices")
async def admin_create_invoice(
    payload: InvoiceCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    country_code = (payload.country_code or "").upper()
    _assert_country_scope(country_code, current_user)
    if payload.amount_net <= 0:
        raise HTTPException(status_code=400, detail="amount_net must be positive")
    if not (0 <= payload.tax_rate <= 100):
        raise HTTPException(status_code=400, detail="tax_rate must be between 0 and 100")

    dealer = await db.users.find_one({"id": payload.dealer_user_id, "role": "dealer"}, {"_id": 0})
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")

    plan = await db.plans.find_one({"id": payload.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    tax_amount = round(payload.amount_net * (payload.tax_rate / 100), 2)
    amount_gross = round(payload.amount_net + tax_amount, 2)
    now_iso = datetime.now(timezone.utc).isoformat()
    issued_at = payload.issued_at or now_iso
    invoice_id = str(uuid.uuid4())

    invoice_doc = {
        "id": invoice_id,
        "dealer_user_id": payload.dealer_user_id,
        "country_code": country_code,
        "plan_id": payload.plan_id,
        "amount_net": payload.amount_net,
        "tax_rate": payload.tax_rate,
        "tax_amount": tax_amount,
        "amount_gross": amount_gross,
        "currency": payload.currency,
        "status": "unpaid",
        "issued_at": issued_at,
        "paid_at": None,
        "created_at": now_iso,
    }

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "INVOICE_STATUS_CHANGE",
        "action": "INVOICE_CREATE",
        "invoice_id": invoice_id,
        "dealer_user_id": payload.dealer_user_id,
        "plan_id": payload.plan_id,
        "country_code": country_code,
        "previous_status": None,
        "new_status": "unpaid",
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "invoice",
        "resource_id": invoice_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.invoices.insert_one(invoice_doc)
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    invoice_doc.pop("_id", None)
    return {"ok": True, "invoice": invoice_doc}


@api_router.get("/admin/invoices")
async def admin_list_invoices(
    request: Request,
    country: Optional[str] = None,
    dealer_user_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    if not country:
        raise HTTPException(status_code=400, detail="country is required")
    country_code = country.upper()
    _assert_country_scope(country_code, current_user)

    q: Dict = {"country_code": country_code}
    if dealer_user_id:
        q["dealer_user_id"] = dealer_user_id
    if status:
        if status not in INVOICE_STATUS_SET:
            raise HTTPException(status_code=400, detail="Invalid status")
        q["status"] = status

    limit = min(100, max(1, int(limit)))
    cursor = db.invoices.find(q, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(limit)
    docs = await cursor.to_list(length=limit)

    dealer_ids = [d.get("dealer_user_id") for d in docs]
    plan_ids = [d.get("plan_id") for d in docs]
    dealers = await db.users.find({"id": {"$in": dealer_ids}}, {"_id": 0, "id": 1, "email": 1}).to_list(length=len(dealer_ids))
    plans = await db.plans.find({"id": {"$in": plan_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(length=len(plan_ids))
    dealer_map = {d.get("id"): d for d in dealers}
    plan_map = {p.get("id"): p for p in plans}

    items = []
    for doc in docs:
        dealer = dealer_map.get(doc.get("dealer_user_id"), {})
        plan = plan_map.get(doc.get("plan_id"), {})
        items.append({
            **doc,
            "dealer_email": dealer.get("email"),
            "plan_name": plan.get("name"),
        })

    total = await db.invoices.count_documents(q)
    return {"items": items, "pagination": {"total": total, "skip": int(skip), "limit": limit}}


@api_router.get("/admin/invoices/{invoice_id}")
async def admin_invoice_detail(
    invoice_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _assert_country_scope(invoice.get("country_code"), current_user)

    dealer = await db.users.find_one({"id": invoice.get("dealer_user_id")}, {"_id": 0, "id": 1, "email": 1, "dealer_status": 1})
    plan = await db.plans.find_one({"id": invoice.get("plan_id")}, {"_id": 0})

    return {"invoice": invoice, "dealer": dealer, "plan": plan}


@api_router.post("/admin/invoices/{invoice_id}/status")
async def admin_invoice_status_change(
    invoice_id: str,
    payload: InvoiceStatusPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _assert_country_scope(invoice.get("country_code"), current_user)

    target_status = (payload.target_status or "").strip()
    if target_status not in {"paid", "cancelled"}:
        raise HTTPException(status_code=400, detail="Invalid target_status")
    if invoice.get("status") != "unpaid":
        raise HTTPException(status_code=400, detail="Only unpaid invoices can be updated")

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "INVOICE_STATUS_CHANGE",
        "action": "INVOICE_STATUS_CHANGE",
        "invoice_id": invoice_id,
        "dealer_user_id": invoice.get("dealer_user_id"),
        "plan_id": invoice.get("plan_id"),
        "country_code": invoice.get("country_code"),
        "previous_status": invoice.get("status"),
        "new_status": target_status,
        "note": payload.note,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "invoice",
        "resource_id": invoice_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)

    update_fields = {"status": target_status, "updated_at": now_iso}
    if target_status == "paid":
        update_fields["paid_at"] = now_iso
    else:
        update_fields["paid_at"] = None

    await db.invoices.update_one({"id": invoice_id}, {"$set": update_fields})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    return {"ok": True, "invoice": {"id": invoice_id, "status": target_status}}


@api_router.get("/admin/finance/revenue")
async def admin_revenue(
    request: Request,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    if not country:
        raise HTTPException(status_code=400, detail="country is required")
    country_code = country.upper()
    _assert_country_scope(country_code, current_user)

    start_dt = _parse_iso_datetime(start_date, "start_date")
    end_dt = _parse_iso_datetime(end_date, "end_date")
    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    start_iso = start_dt.astimezone(timezone.utc).isoformat()
    end_iso = end_dt.astimezone(timezone.utc).isoformat()

    q = {
        "country_code": country_code,
        "status": "paid",
        "paid_at": {"$gte": start_iso, "$lte": end_iso},
    }
    docs = await db.invoices.find(q, {"_id": 0, "amount_gross": 1, "currency": 1}).to_list(length=10000)
    totals: Dict[str, float] = {}
    for doc in docs:
        currency = doc.get("currency") or "UNKNOWN"
        totals[currency] = totals.get(currency, 0) + float(doc.get("amount_gross") or 0)
    total_gross = sum(totals.values())

    return {
        "country_code": country_code,
        "start_date": start_iso,
        "end_date": end_iso,
        "total_gross": round(total_gross, 2),
        "totals_by_currency": {k: round(v, 2) for k, v in totals.items()},
    }


@api_router.get("/admin/tax-rates")
async def admin_list_tax_rates(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    q: Dict = {}
    if country:
        country_code = country.upper()
        _assert_country_scope(country_code, current_user)
        q["country_code"] = country_code
    elif current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope:
            q["country_code"] = {"$in": scope}

    items = await db.tax_rates.find(q, {"_id": 0}).sort("effective_date", -1).to_list(length=500)
    return {"items": items}


@api_router.post("/admin/tax-rates")
async def admin_create_tax_rate(
    payload: TaxRateCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    country_code = payload.country_code.upper()
    _assert_country_scope(country_code, current_user)
    if not (0 <= payload.rate <= 100):
        raise HTTPException(status_code=400, detail="rate must be between 0 and 100")

    now_iso = datetime.now(timezone.utc).isoformat()
    tax_id = str(uuid.uuid4())
    tax_doc = {
        "id": tax_id,
        "country_code": country_code,
        "rate": payload.rate,
        "effective_date": payload.effective_date,
        "active_flag": True if payload.active_flag is None else payload.active_flag,
        "created_at": now_iso,
        "updated_at": None,
    }

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "TAX_RATE_CHANGE",
        "action": "TAX_RATE_CREATE",
        "tax_rate_id": tax_id,
        "country_code": country_code,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "tax_rate",
        "resource_id": tax_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.tax_rates.insert_one(tax_doc)
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    tax_doc.pop("_id", None)
    return {"ok": True, "tax_rate": tax_doc}


@api_router.patch("/admin/tax-rates/{tax_id}")
async def admin_update_tax_rate(
    tax_id: str,
    payload: TaxRateUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    tax_rate = await db.tax_rates.find_one({"id": tax_id}, {"_id": 0})
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    _assert_country_scope(tax_rate.get("country_code"), current_user)

    updates: Dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.rate is not None:
        if not (0 <= payload.rate <= 100):
            raise HTTPException(status_code=400, detail="rate must be between 0 and 100")
        updates["rate"] = payload.rate
    if payload.effective_date is not None:
        updates["effective_date"] = payload.effective_date
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": updates["updated_at"],
        "event_type": "TAX_RATE_CHANGE",
        "action": "TAX_RATE_UPDATE",
        "tax_rate_id": tax_id,
        "country_code": tax_rate.get("country_code"),
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "tax_rate",
        "resource_id": tax_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.tax_rates.update_one({"id": tax_id}, {"$set": updates})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    updated = await db.tax_rates.find_one({"id": tax_id}, {"_id": 0})
    return {"ok": True, "tax_rate": updated}


@api_router.delete("/admin/tax-rates/{tax_id}")
async def admin_delete_tax_rate(
    tax_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    tax_rate = await db.tax_rates.find_one({"id": tax_id}, {"_id": 0})
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    _assert_country_scope(tax_rate.get("country_code"), current_user)

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "TAX_RATE_CHANGE",
        "action": "TAX_RATE_DELETE",
        "tax_rate_id": tax_id,
        "country_code": tax_rate.get("country_code"),
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "tax_rate",
        "resource_id": tax_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.tax_rates.update_one({"id": tax_id}, {"$set": {"active_flag": False, "updated_at": now_iso}})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})
    return {"ok": True}


@api_router.get("/admin/plans")
async def admin_list_plans(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    q: Dict = {}
    if country:
        country_code = country.upper()
        _assert_country_scope(country_code, current_user)
        q["country_code"] = country_code
    elif current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope:
            q["country_code"] = {"$in": scope}

    items = await db.plans.find(q, {"_id": 0}).sort("created_at", -1).to_list(length=500)
    return {"items": items}


@api_router.post("/admin/plans")
async def admin_create_plan(
    payload: PlanCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    country_code = payload.country_code.upper()
    _assert_country_scope(country_code, current_user)
    if payload.price < 0:
        raise HTTPException(status_code=400, detail="price must be >= 0")
    if payload.listing_quota < 0 or payload.showcase_quota < 0:
        raise HTTPException(status_code=400, detail="quota must be >= 0")

    now_iso = datetime.now(timezone.utc).isoformat()
    plan_id = str(uuid.uuid4())
    plan_doc = {
        "id": plan_id,
        "name": payload.name,
        "country_code": country_code,
        "price": payload.price,
        "currency": payload.currency,
        "listing_quota": payload.listing_quota,
        "showcase_quota": payload.showcase_quota,
        "active_flag": True if payload.active_flag is None else payload.active_flag,
        "created_at": now_iso,
        "updated_at": None,
    }

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "PLAN_CHANGE",
        "action": "PLAN_CREATE",
        "plan_id": plan_id,
        "country_code": country_code,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "plan",
        "resource_id": plan_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.plans.insert_one(plan_doc)
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    plan_doc.pop("_id", None)
    return {"ok": True, "plan": plan_doc}


@api_router.patch("/admin/plans/{plan_id}")
async def admin_update_plan(
    plan_id: str,
    payload: PlanUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    _assert_country_scope(plan.get("country_code"), current_user)

    updates: Dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ["name", "country_code", "price", "currency", "listing_quota", "showcase_quota", "active_flag"]:
        value = getattr(payload, field)
        if value is not None:
            if field == "price" and value < 0:
                raise HTTPException(status_code=400, detail="price must be >= 0")
            if field in {"listing_quota", "showcase_quota"} and value < 0:
                raise HTTPException(status_code=400, detail="quota must be >= 0")
            if field == "country_code":
                value = value.upper()
                _assert_country_scope(value, current_user)
            updates[field] = value

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": updates["updated_at"],
        "event_type": "PLAN_CHANGE",
        "action": "PLAN_UPDATE",
        "plan_id": plan_id,
        "country_code": plan.get("country_code"),
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "plan",
        "resource_id": plan_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.plans.update_one({"id": plan_id}, {"$set": updates})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    updated = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    return {"ok": True, "plan": updated}


@api_router.delete("/admin/plans/{plan_id}")
async def admin_delete_plan(
    plan_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    _assert_country_scope(plan.get("country_code"), current_user)

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "PLAN_CHANGE",
        "action": "PLAN_DELETE",
        "plan_id": plan_id,
        "country_code": plan.get("country_code"),
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "plan",
        "resource_id": plan_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.plans.update_one({"id": plan_id}, {"$set": {"active_flag": False, "updated_at": now_iso}})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})
    return {"ok": True}


@api_router.post("/admin/dealers/{dealer_id}/plan")
async def admin_assign_dealer_plan(
    dealer_id: str,
    payload: DealerPlanAssignmentPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    dealer = await db.users.find_one({"id": dealer_id, "role": "dealer"}, {"_id": 0})
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    _assert_country_scope(dealer.get("country_code"), current_user)

    plan_id = payload.plan_id
    plan = None
    if plan_id:
        plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if plan.get("country_code") != dealer.get("country_code"):
            raise HTTPException(status_code=400, detail="Plan country mismatch")

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "ADMIN_PLAN_ASSIGNMENT",
        "action": "ADMIN_PLAN_ASSIGNMENT",
        "dealer_user_id": dealer_id,
        "country_code": dealer.get("country_code"),
        "previous_plan_id": dealer.get("plan_id"),
        "new_plan_id": plan_id,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "dealer",
        "resource_id": dealer_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.users.update_one({"id": dealer_id}, {"$set": {"plan_id": plan_id, "updated_at": now_iso}})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    return {"ok": True, "plan_id": plan_id}


# =====================
# Sprint 4 — System + Dashboard
# =====================


@api_router.get("/admin/countries")
async def admin_list_countries(
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    q: Dict = {}
    if current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope:
            q["$or"] = [{"country_code": {"$in": scope}}, {"code": {"$in": scope}}]
    docs = await db.countries.find(q, {"_id": 0}).sort("code", 1).to_list(length=500)
    items = [_normalize_country_doc(doc) for doc in docs]
    return {"items": items}


@api_router.get("/admin/countries/{code}")
async def admin_get_country(
    code: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    code_upper = code.upper()
    doc = await db.countries.find_one({"$or": [{"country_code": code_upper}, {"code": code_upper}]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"country": _normalize_country_doc(doc)}


@api_router.post("/admin/countries", status_code=201)
async def admin_create_country(
    payload: CountryCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    code = payload.country_code.strip().upper()
    if not re.match(r"^[A-Z]{2}$", code):
        raise HTTPException(status_code=400, detail="country_code must be 2-letter ISO")
    if not payload.default_currency:
        raise HTTPException(status_code=400, detail="default_currency is required")

    existing = await db.countries.find_one({"$or": [{"country_code": code}, {"code": code}]})
    if existing:
        raise HTTPException(status_code=409, detail="Country already exists")

    now_iso = datetime.now(timezone.utc).isoformat()
    country_doc = {
        "id": code,
        "code": code,
        "country_code": code,
        "name": payload.name,
        "active_flag": True if payload.active_flag is None else payload.active_flag,
        "is_enabled": True if payload.active_flag is None else payload.active_flag,
        "default_currency": payload.default_currency.upper(),
        "default_language": payload.default_language,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "COUNTRY_CHANGE",
        "action": "COUNTRY_CREATE",
        "country_code": code,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "country",
        "resource_id": code,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.countries.insert_one(country_doc)
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    country_doc.pop("_id", None)
    SUPPORTED_COUNTRIES.add(code)
    return {"ok": True, "country": _normalize_country_doc(country_doc)}


@api_router.patch("/admin/countries/{code}")
async def admin_update_country(
    code: str,
    payload: CountryUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    code_upper = code.upper()
    country = await db.countries.find_one({"$or": [{"country_code": code_upper}, {"code": code_upper}]}, {"_id": 0})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    updates: Dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.default_currency is not None:
        updates["default_currency"] = payload.default_currency.upper()
    if payload.default_language is not None:
        updates["default_language"] = payload.default_language
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag
        updates["is_enabled"] = payload.active_flag

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": updates["updated_at"],
        "event_type": "COUNTRY_CHANGE",
        "action": "COUNTRY_UPDATE",
        "country_code": code_upper,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "country",
        "resource_id": code_upper,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.countries.update_one({"$or": [{"country_code": code_upper}, {"code": code_upper}]}, {"$set": updates})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    updated = await db.countries.find_one({"$or": [{"country_code": code_upper}, {"code": code_upper}]}, {"_id": 0})
    return {"ok": True, "country": _normalize_country_doc(updated)}


@api_router.delete("/admin/countries/{code}")
async def admin_delete_country(
    code: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    code_upper = code.upper()
    country = await db.countries.find_one({"$or": [{"country_code": code_upper}, {"code": code_upper}]}, {"_id": 0})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "COUNTRY_CHANGE",
        "action": "COUNTRY_DELETE",
        "country_code": code_upper,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "country",
        "resource_id": code_upper,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.countries.update_one({"$or": [{"country_code": code_upper}, {"code": code_upper}]}, {"$set": {"active_flag": False, "is_enabled": False, "updated_at": now_iso}})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})
    return {"ok": True}


@api_router.get("/admin/system-settings")
async def admin_list_system_settings(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    q: Dict = {}
    if country:
        code = country.upper()
        _assert_country_scope(code, current_user)
        q["country_code"] = code
    elif current_user.get("role") == "country_admin":
        scope = current_user.get("country_scope") or []
        if "*" not in scope:
            q["$or"] = [{"country_code": None}, {"country_code": ""}, {"country_code": {"$in": scope}}]
    items = await db.system_settings.find(q, {"_id": 0}).sort("key", 1).to_list(length=1000)
    return {"items": items}


@api_router.post("/admin/system-settings", status_code=201)
async def admin_create_system_setting(
    payload: SystemSettingCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    key = payload.key.strip()
    if not KEY_NAMESPACE_REGEX.match(key):
        raise HTTPException(status_code=400, detail="Invalid key namespace")
    country_code = payload.country_code.upper() if payload.country_code else None

    existing = await db.system_settings.find_one({"key": key, "country_code": country_code})
    if existing:
        raise HTTPException(status_code=409, detail="Setting already exists")

    now_iso = datetime.now(timezone.utc).isoformat()
    setting_id = str(uuid.uuid4())
    setting_doc = {
        "id": setting_id,
        "key": key,
        "value": payload.value,
        "country_code": country_code,
        "is_readonly": bool(payload.is_readonly),
        "description": payload.description,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": now_iso,
        "event_type": "SYSTEM_SETTING_CHANGE",
        "action": "SYSTEM_SETTING_CREATE",
        "setting_id": setting_id,
        "key": key,
        "country_code": country_code,
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "system_setting",
        "resource_id": setting_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.system_settings.insert_one(setting_doc)
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    setting_doc.pop("_id", None)
    return {"ok": True, "setting": setting_doc}


@api_router.patch("/admin/system-settings/{setting_id}")
async def admin_update_system_setting(
    setting_id: str,
    payload: SystemSettingUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    setting = await db.system_settings.find_one({"id": setting_id}, {"_id": 0})
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    if setting.get("is_readonly") and payload.value is not None:
        raise HTTPException(status_code=400, detail="Setting is read-only")

    updates: Dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.value is not None:
        updates["value"] = payload.value
    if payload.country_code is not None:
        updates["country_code"] = payload.country_code.upper() if payload.country_code else None
    if payload.is_readonly is not None:
        updates["is_readonly"] = payload.is_readonly
    if payload.description is not None:
        updates["description"] = payload.description

    audit_id = str(uuid.uuid4())
    audit_doc = {
        "id": audit_id,
        "created_at": updates["updated_at"],
        "event_type": "SYSTEM_SETTING_CHANGE",
        "action": "SYSTEM_SETTING_UPDATE",
        "setting_id": setting_id,
        "key": setting.get("key"),
        "country_code": setting.get("country_code"),
        "admin_user_id": current_user.get("id"),
        "user_id": current_user.get("id"),
        "user_email": current_user.get("email"),
        "role": current_user.get("role"),
        "resource_type": "system_setting",
        "resource_id": setting_id,
        "applied": False,
    }

    await db.audit_logs.insert_one(audit_doc)
    await db.system_settings.update_one({"id": setting_id}, {"$set": updates})
    await db.audit_logs.update_one({"id": audit_id}, {"$set": {"applied": True}})

    updated = await db.system_settings.find_one({"id": setting_id}, {"_id": 0})
    return {"ok": True, "setting": updated}


@api_router.get("/system-settings/effective")
async def system_settings_effective(request: Request, country: Optional[str] = None):
    db = request.app.state.db
    country_code = country.upper() if country else None
    global_settings = await db.system_settings.find({"$or": [{"country_code": None}, {"country_code": ""}]}, {"_id": 0}).to_list(length=1000)
    country_settings = []
    if country_code:
        country_settings = await db.system_settings.find({"country_code": country_code}, {"_id": 0}).to_list(length=1000)

    merged: Dict[str, dict] = {}
    for item in global_settings:
        merged[item["key"]] = {**item, "source": "global"}
    for item in country_settings:
        merged[item["key"]] = {**item, "source": "country"}

    items = sorted(merged.values(), key=lambda x: x.get("key"))
    return {"country_code": country_code, "items": items}


# =====================
# Master Data: Categories / Attributes / Vehicle
# =====================


@api_router.get("/admin/categories")
async def admin_list_categories(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    query: Dict = {}
    if country:
        code = country.upper()
        _assert_country_scope(code, current_user)
        query["country_code"] = code
    docs = await db.categories.find(query, {"_id": 0}).sort("sort_order", 1).to_list(length=1000)
    return {"items": [_normalize_category_doc(doc, include_schema=True) for doc in docs]}


@api_router.post("/admin/categories", status_code=201)
async def admin_create_category(
    payload: CategoryCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    slug = payload.slug.strip().lower()
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="slug format invalid")

    parent_id = payload.parent_id
    if parent_id:
        parent = await db.categories.find_one({"id": parent_id}, {"_id": 0, "id": 1})
        if not parent:
            raise HTTPException(status_code=400, detail="parent_id not found")

    country_code = payload.country_code.upper() if payload.country_code else None
    if country_code:
        _assert_country_scope(country_code, current_user)

    now_iso = datetime.now(timezone.utc).isoformat()
    category_id = str(uuid.uuid4())
    hierarchy_complete = payload.hierarchy_complete if payload.hierarchy_complete is not None else True
    schema = None
    schema_status = None
    if payload.form_schema is not None:
        schema = _normalize_category_schema(payload.form_schema)
        schema_status = schema.get("status", "published")
        if not hierarchy_complete:
            raise HTTPException(status_code=409, detail="Kategori hiyerarşisi tamamlanmadan kaydedilemez")
        if schema_status != "draft":
            _validate_category_schema(schema)
    doc = {
        "id": category_id,
        "parent_id": parent_id,
        "name": payload.name.strip(),
        "slug": slug,
        "country_code": country_code,
        "active_flag": payload.active_flag if payload.active_flag is not None else True,
        "sort_order": payload.sort_order or 0,
        "hierarchy_complete": hierarchy_complete,
        "form_schema": schema,
        "created_at": now_iso,
        "updated_at": now_iso,
        "module": "vehicle",
    }
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "CATEGORY_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": country_code,
        "subject_type": "category",
        "subject_id": category_id,
        "action": "create",
        "created_at": now_iso,
        "metadata": {"name": doc["name"], "slug": doc["slug"]},
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.categories.insert_one(doc)
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Category slug already exists")
        raise

    if schema:
        if schema_status == "draft":
            await _record_category_version(db, category_id, schema, current_user, "draft")
        else:
            await _record_category_version(db, category_id, schema, current_user, "published")

    return {"category": _normalize_category_doc(doc, include_schema=True)}


@api_router.patch("/admin/categories/{category_id}")
async def admin_update_category(
    category_id: str,
    payload: CategoryUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.expected_updated_at is not None:
        current_updated_at = category.get("updated_at")
        if current_updated_at and payload.expected_updated_at != current_updated_at:
            raise HTTPException(status_code=409, detail="Category updated in another session")

    updates: Dict = {}
    schema = None
    schema_status = None
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.slug is not None:
        slug = payload.slug.strip().lower()
        if not SLUG_PATTERN.match(slug):
            raise HTTPException(status_code=400, detail="slug format invalid")
        updates["slug"] = slug
    if payload.parent_id is not None:
        if payload.parent_id:
            parent = await db.categories.find_one({"id": payload.parent_id}, {"_id": 0})
            if not parent:
                raise HTTPException(status_code=400, detail="parent_id not found")
        updates["parent_id"] = payload.parent_id
    if payload.country_code is not None:
        code = payload.country_code.upper() if payload.country_code else None
        if code:
            _assert_country_scope(code, current_user)
        updates["country_code"] = code
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag
    if payload.sort_order is not None:
        updates["sort_order"] = payload.sort_order
    if payload.hierarchy_complete is not None:
        updates["hierarchy_complete"] = payload.hierarchy_complete
    if payload.form_schema is not None:
        schema = _normalize_category_schema(payload.form_schema)
        schema_status = schema.get("status", "published")
        hierarchy_complete = updates.get("hierarchy_complete", category.get("hierarchy_complete", True))
        if not hierarchy_complete:
            raise HTTPException(status_code=409, detail="Kategori hiyerarşisi tamamlanmadan kaydedilemez")
        if schema_status != "draft":
            _validate_category_schema(schema)
        updates["form_schema"] = schema

    if not updates:
        return {"category": _normalize_category_doc(category, include_schema=True)}

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "CATEGORY_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": updates.get("country_code", category.get("country_code")),
        "subject_type": "category",
        "subject_id": category_id,
        "action": "update",
        "created_at": updates["updated_at"],
        "metadata": updates,
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.categories.update_one({"id": category_id}, {"$set": updates})
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Category slug already exists")
        raise
    category.update(updates)

    if schema:
        if schema_status == "draft":
            await _record_category_version(db, category_id, schema, current_user, "draft")
        else:
            await _mark_latest_category_version_published(db, category_id, schema, current_user)

    return {"category": _normalize_category_doc(category, include_schema=True)}


@api_router.get("/admin/categories/{category_id}/versions")
async def admin_list_category_versions(
    category_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.get("country_code"):
        _assert_country_scope(category.get("country_code"), current_user)

    docs = await db.categories_versions.find({"category_id": category_id}, {"_id": 0}).sort("version", -1).to_list(length=100)
    return {"items": [_serialize_category_version(doc) for doc in docs]}


@api_router.get("/admin/categories/{category_id}/versions/{version_id}")
async def admin_get_category_version(
    category_id: str,
    version_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.get("country_code"):
        _assert_country_scope(category.get("country_code"), current_user)

    doc = await db.categories_versions.find_one({"id": version_id, "category_id": category_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Category version not found")

    return {"version": _serialize_category_version(doc, include_snapshot=True)}


@api_router.get("/admin/categories/{category_id}/export/pdf")
async def admin_export_category_pdf(
    category_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    _enforce_export_rate_limit(request, current_user.get("id"))

    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.get("country_code"):
        _assert_country_scope(category.get("country_code"), current_user)

    schema = _normalize_category_schema(category.get("form_schema")) if category.get("form_schema") else None
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    if schema.get("status") != "draft":
        raise HTTPException(status_code=409, detail="Sadece draft şema export edilebilir")

    version = await _get_schema_version_for_export(db, category_id)
    parent_doc = None
    if category.get("parent_id"):
        parent_doc = await db.categories.find_one({"id": category.get("parent_id")}, {"_id": 0})
    parent_label = _pick_label(parent_doc.get("name")) if parent_doc else category.get("name")
    children_docs = await db.categories.find({"parent_id": category_id}, {"_id": 0, "name": 1, "slug": 1}).to_list(length=200)
    children = [(_pick_label(doc.get("name")) or doc.get("slug")) for doc in children_docs if doc]

    pdf_bytes = _build_schema_pdf(schema, {"name": category.get("name"), "slug": category.get("slug")}, version, {
        "parent": parent_label,
        "children": children,
    })

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"schema-{category_id}-v{version}-{timestamp}.pdf"

    audit_doc = await build_audit_entry(
        event_type="schema_export_pdf",
        actor=current_user,
        target_id=category_id,
        target_type="category_schema",
        country_code=category.get("country_code"),
        details={"schema_version": version, "format": "pdf"},
        request=request,
    )
    audit_doc["action"] = "schema_export_pdf"
    audit_doc["user_agent"] = request.headers.get("user-agent")
    await db.audit_logs.insert_one(audit_doc)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


@api_router.get("/admin/categories/{category_id}/export/csv")
async def admin_export_category_csv(
    category_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    _enforce_export_rate_limit(request, current_user.get("id"))

    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.get("country_code"):
        _assert_country_scope(category.get("country_code"), current_user)

    schema = _normalize_category_schema(category.get("form_schema")) if category.get("form_schema") else None
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    if schema.get("status") != "draft":
        raise HTTPException(status_code=409, detail="Sadece draft şema export edilebilir")

    version = await _get_schema_version_for_export(db, category_id)
    parent_doc = None
    if category.get("parent_id"):
        parent_doc = await db.categories.find_one({"id": category.get("parent_id")}, {"_id": 0})
    parent_label = _pick_label(parent_doc.get("name")) if parent_doc else category.get("name")
    children_docs = await db.categories.find({"parent_id": category_id}, {"_id": 0, "name": 1, "slug": 1}).to_list(length=200)
    children = [(_pick_label(doc.get("name")) or doc.get("slug")) for doc in children_docs if doc]

    rows = _schema_to_csv_rows(schema)
    rows.append(["hierarchy", "parent", parent_label or "", "", "", "", "", "", "", "", "", "", ""])
    rows.append(["hierarchy", "children", ",".join(children), "", "", "", "", "", "", "", "", "", ""])

    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    csv_bytes = output.getvalue().encode("utf-8")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"schema-{category_id}-v{version}-{timestamp}.csv"

    audit_doc = await build_audit_entry(
        event_type="schema_export_csv",
        actor=current_user,
        target_id=category_id,
        target_type="category_schema",
        country_code=category.get("country_code"),
        details={"schema_version": version, "format": "csv"},
        request=request,
    )
    audit_doc["action"] = "schema_export_csv"
    audit_doc["user_agent"] = request.headers.get("user-agent")
    await db.audit_logs.insert_one(audit_doc)

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


@api_router.delete("/admin/categories/{category_id}")
async def admin_delete_category(
    category_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "CATEGORY_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": category.get("country_code"),
        "subject_type": "category",
        "subject_id": category_id,
        "action": "delete",
        "created_at": now_iso,
        "metadata": {"active_flag": False},
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.categories.update_one({"id": category_id}, {"$set": {"active_flag": False, "updated_at": now_iso}})
    category["active_flag"] = False
    category["updated_at"] = now_iso
    return {"category": _normalize_category_doc(category, include_schema=True)}


@api_router.get("/admin/menu-items")
async def admin_list_menu_items(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db)
    query: Dict[str, Any] = {}
    if country:
        country_code = country.upper()
        _assert_country_scope(country_code, current_user)
        query["country_code"] = country_code
    elif ctx.mode == "country" and ctx.country:
        query["country_code"] = ctx.country

    items = await db.menu_items.find(query, {"_id": 0}).sort("sort_order", 1).to_list(length=1000)
    return {"items": items}


@api_router.post("/admin/menu-items")
async def admin_create_menu_item(
    payload: MenuItemCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db)
    now_iso = datetime.now(timezone.utc).isoformat()
    slug = payload.slug.strip()
    if not slug:
        raise HTTPException(status_code=400, detail="Slug is required")

    country_code = payload.country_code.upper() if payload.country_code else None
    if ctx.mode == "country" and ctx.country:
        country_code = country_code or ctx.country
    if country_code:
        _assert_country_scope(country_code, current_user)

    if payload.parent_id:
        parent = await db.menu_items.find_one({"id": payload.parent_id}, {"_id": 0})
        if not parent:
            raise HTTPException(status_code=404, detail="Parent menu item not found")

    existing = await db.menu_items.find_one({"slug": slug, "country_code": country_code}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Menu slug already exists")

    menu_id = str(uuid.uuid4())
    doc = {
        "id": menu_id,
        "label": payload.label.strip(),
        "slug": slug,
        "url": payload.url.strip() if payload.url else None,
        "parent_id": payload.parent_id,
        "country_code": country_code,
        "active_flag": payload.active_flag if payload.active_flag is not None else True,
        "sort_order": payload.sort_order or 0,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "MENU_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": country_code,
        "subject_type": "menu_item",
        "subject_id": menu_id,
        "action": "create",
        "created_at": now_iso,
        "metadata": {"label": doc["label"], "slug": doc["slug"], "url": doc["url"]},
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.menu_items.insert_one(doc)
    doc.pop("_id", None)
    return {"menu_item": doc}


@api_router.patch("/admin/menu-items/{menu_id}")
async def admin_update_menu_item(
    menu_id: str,
    payload: MenuItemUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db)
    existing = await db.menu_items.find_one({"id": menu_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Menu item not found")

    updates: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.label is not None:
        updates["label"] = payload.label.strip()
    if payload.slug is not None:
        slug = payload.slug.strip()
        if not slug:
            raise HTTPException(status_code=400, detail="Slug is required")
        updates["slug"] = slug
    if payload.url is not None:
        updates["url"] = payload.url.strip() if payload.url else None
    if payload.parent_id is not None:
        if payload.parent_id == menu_id:
            raise HTTPException(status_code=400, detail="Menu item cannot be its own parent")
        if payload.parent_id:
            parent = await db.menu_items.find_one({"id": payload.parent_id}, {"_id": 0})
            if not parent:
                raise HTTPException(status_code=404, detail="Parent menu item not found")
        updates["parent_id"] = payload.parent_id or None
    if payload.country_code is not None:
        country_code = payload.country_code.upper() if payload.country_code else None
        if ctx.mode == "country" and ctx.country:
            country_code = country_code or ctx.country
        if country_code:
            _assert_country_scope(country_code, current_user)
        updates["country_code"] = country_code
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag
    if payload.sort_order is not None:
        updates["sort_order"] = payload.sort_order

    new_slug = updates.get("slug", existing.get("slug"))
    new_country = updates.get("country_code", existing.get("country_code"))
    if new_slug != existing.get("slug") or new_country != existing.get("country_code"):
        conflict = await db.menu_items.find_one(
            {"slug": new_slug, "country_code": new_country, "id": {"$ne": menu_id}},
            {"_id": 0},
        )
        if conflict:
            raise HTTPException(status_code=409, detail="Menu slug already exists")

    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "MENU_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": updates.get("country_code", existing.get("country_code")),
        "subject_type": "menu_item",
        "subject_id": menu_id,
        "action": "update",
        "created_at": updates["updated_at"],
        "metadata": updates,
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.menu_items.update_one({"id": menu_id}, {"$set": updates})
    updated = await db.menu_items.find_one({"id": menu_id}, {"_id": 0})
    return {"menu_item": updated}


@api_router.delete("/admin/menu-items/{menu_id}")
async def admin_delete_menu_item(
    menu_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    existing = await db.menu_items.find_one({"id": menu_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Menu item not found")

    updates = {
        "active_flag": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    }
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "MENU_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": existing.get("country_code"),
        "subject_type": "menu_item",
        "subject_id": menu_id,
        "action": "delete",
        "created_at": updates["updated_at"],
        "metadata": {"label": existing.get("label"), "slug": existing.get("slug")},
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.menu_items.update_one({"id": menu_id}, {"$set": updates})
    return {"success": True}


@api_router.get("/attributes")
async def public_attributes(category_id: str, country: Optional[str] = None, request: Request = None):
    db = request.app.state.db
    query: Dict = {"category_id": category_id}
    filters = [{"$or": [{"active_flag": True}, {"active_flag": {"$exists": False}}]}]
    if country:
        code = country.upper()
        filters.append({
            "$or": [
                {"country_code": None},
                {"country_code": ""},
                {"country_code": code},
            ]
        })
    if filters:
        query["$and"] = filters
    docs = await db.attributes.find(query, {"_id": 0}).sort("name", 1).to_list(length=500)
    return {"items": [_normalize_attribute_doc(doc) for doc in docs]}


@api_router.get("/admin/attributes")
async def admin_list_attributes(
    request: Request,
    category_id: Optional[str] = None,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    query: Dict = {}
    if category_id:
        query["category_id"] = category_id
    if country:
        code = country.upper()
        _assert_country_scope(code, current_user)
        query["$or"] = [
            {"country_code": None},
            {"country_code": ""},
            {"country_code": code},
        ]
    docs = await db.attributes.find(query, {"_id": 0}).sort("name", 1).to_list(length=1000)
    return {"items": [_normalize_attribute_doc(doc) for doc in docs]}


@api_router.post("/admin/attributes", status_code=201)
async def admin_create_attribute(
    payload: AttributeCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    key = payload.key.strip().lower()
    if not ATTRIBUTE_KEY_PATTERN.match(key):
        raise HTTPException(status_code=400, detail="key format invalid")
    if payload.type not in {"text", "number", "select", "boolean"}:
        raise HTTPException(status_code=400, detail="type invalid")
    if payload.type == "select" and not payload.options:
        raise HTTPException(status_code=400, detail="options required for select")

    category = await db.categories.find_one({"id": payload.category_id}, {"_id": 0, "id": 1})
    if not category:
        raise HTTPException(status_code=400, detail="category_id not found")

    country_code = payload.country_code.upper() if payload.country_code else None
    if country_code:
        _assert_country_scope(country_code, current_user)

    now_iso = datetime.now(timezone.utc).isoformat()
    attr_id = str(uuid.uuid4())
    doc = {
        "id": attr_id,
        "category_id": payload.category_id,
        "name": payload.name.strip(),
        "key": key,
        "type": payload.type,
        "required_flag": bool(payload.required_flag),
        "filterable_flag": bool(payload.filterable_flag),
        "options": payload.options,
        "country_code": country_code,
        "active_flag": payload.active_flag if payload.active_flag is not None else True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "ATTRIBUTE_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": country_code,
        "subject_type": "attribute",
        "subject_id": attr_id,
        "action": "create",
        "created_at": now_iso,
        "metadata": {"key": doc["key"], "category_id": doc["category_id"]},
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.attributes.insert_one(doc)
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Attribute key already exists")
        raise
    return {"attribute": _normalize_attribute_doc(doc)}


@api_router.patch("/admin/attributes/{attribute_id}")
async def admin_update_attribute(
    attribute_id: str,
    payload: AttributeUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    attr = await db.attributes.find_one({"id": attribute_id}, {"_id": 0})
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    updates: Dict = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.key is not None:
        key = payload.key.strip().lower()
        if not ATTRIBUTE_KEY_PATTERN.match(key):
            raise HTTPException(status_code=400, detail="key format invalid")
        updates["key"] = key
    if payload.type is not None:
        if payload.type not in {"text", "number", "select", "boolean"}:
            raise HTTPException(status_code=400, detail="type invalid")
        updates["type"] = payload.type
    if payload.options is not None:
        updates["options"] = payload.options
    if payload.required_flag is not None:
        updates["required_flag"] = payload.required_flag
    if payload.filterable_flag is not None:
        updates["filterable_flag"] = payload.filterable_flag
    if payload.country_code is not None:
        code = payload.country_code.upper() if payload.country_code else None
        if code:
            _assert_country_scope(code, current_user)
        updates["country_code"] = code
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag
    if not updates:
        return {"attribute": _normalize_attribute_doc(attr)}

    if updates.get("type") == "select" and not (updates.get("options") or attr.get("options")):
        raise HTTPException(status_code=400, detail="options required for select")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "ATTRIBUTE_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": updates.get("country_code", attr.get("country_code")),
        "subject_type": "attribute",
        "subject_id": attribute_id,
        "action": "update",
        "created_at": updates["updated_at"],
        "metadata": updates,
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.attributes.update_one({"id": attribute_id}, {"$set": updates})
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Attribute key already exists")
        raise
    attr.update(updates)
    return {"attribute": _normalize_attribute_doc(attr)}


@api_router.delete("/admin/attributes/{attribute_id}")
async def admin_delete_attribute(
    attribute_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    attr = await db.attributes.find_one({"id": attribute_id}, {"_id": 0})
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "ATTRIBUTE_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": attr.get("country_code"),
        "subject_type": "attribute",
        "subject_id": attribute_id,
        "action": "delete",
        "created_at": now_iso,
        "metadata": {"active_flag": False},
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.attributes.update_one({"id": attribute_id}, {"$set": {"active_flag": False, "updated_at": now_iso}})
    attr["active_flag"] = False
    attr["updated_at"] = now_iso
    return {"attribute": _normalize_attribute_doc(attr)}


@api_router.get("/admin/vehicle-makes")
async def admin_list_vehicle_makes(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    query: Dict = {}
    if country:
        code = country.upper()
        _assert_country_scope(code, current_user)
        query["country_code"] = code
    docs = await db.vehicle_makes.find(query, {"_id": 0}).sort("name", 1).to_list(length=1000)
    return {"items": [_normalize_vehicle_make_doc(doc) for doc in docs]}


@api_router.post("/admin/vehicle-makes", status_code=201)
async def admin_create_vehicle_make(
    payload: VehicleMakeCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    slug = payload.slug.strip().lower()
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="slug format invalid")
    code = payload.country_code.upper()
    _assert_country_scope(code, current_user)

    now_iso = datetime.now(timezone.utc).isoformat()
    make_id = str(uuid.uuid4())
    doc = {
        "id": make_id,
        "name": payload.name.strip(),
        "slug": slug,
        "country_code": code,
        "active_flag": payload.active_flag if payload.active_flag is not None else True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "VEHICLE_MASTER_DATA_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": code,
        "subject_type": "vehicle_make",
        "subject_id": make_id,
        "action": "create",
        "created_at": now_iso,
        "metadata": {"slug": doc["slug"], "name": doc["name"]},
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.vehicle_makes.insert_one(doc)
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Make slug already exists")
        raise
    return {"make": _normalize_vehicle_make_doc(doc)}


@api_router.patch("/admin/vehicle-makes/{make_id}")
async def admin_update_vehicle_make(
    make_id: str,
    payload: VehicleMakeUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    make = await db.vehicle_makes.find_one({"id": make_id}, {"_id": 0})
    if not make:
        raise HTTPException(status_code=404, detail="Make not found")
    updates: Dict = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.slug is not None:
        slug = payload.slug.strip().lower()
        if not SLUG_PATTERN.match(slug):
            raise HTTPException(status_code=400, detail="slug format invalid")
        updates["slug"] = slug
    if payload.country_code is not None:
        code = payload.country_code.upper() if payload.country_code else None
        if code:
            _assert_country_scope(code, current_user)
        updates["country_code"] = code
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag
    if not updates:
        return {"make": _normalize_vehicle_make_doc(make)}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "VEHICLE_MASTER_DATA_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": updates.get("country_code", make.get("country_code")),
        "subject_type": "vehicle_make",
        "subject_id": make_id,
        "action": "update",
        "created_at": updates["updated_at"],
        "metadata": updates,
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.vehicle_makes.update_one({"id": make_id}, {"$set": updates})
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Make slug already exists")
        raise
    make.update(updates)
    return {"make": _normalize_vehicle_make_doc(make)}


@api_router.delete("/admin/vehicle-makes/{make_id}")
async def admin_delete_vehicle_make(
    make_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    make = await db.vehicle_makes.find_one({"id": make_id}, {"_id": 0})
    if not make:
        raise HTTPException(status_code=404, detail="Make not found")
    now_iso = datetime.now(timezone.utc).isoformat()
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "VEHICLE_MASTER_DATA_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": make.get("country_code"),
        "subject_type": "vehicle_make",
        "subject_id": make_id,
        "action": "delete",
        "created_at": now_iso,
        "metadata": {"active_flag": False},
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.vehicle_makes.update_one({"id": make_id}, {"$set": {"active_flag": False, "updated_at": now_iso}})
    make["active_flag"] = False
    make["updated_at"] = now_iso
    return {"make": _normalize_vehicle_make_doc(make)}


@api_router.get("/admin/vehicle-models")
async def admin_list_vehicle_models(
    request: Request,
    make_id: Optional[str] = None,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db)
    query: Dict = {}
    if make_id:
        make_doc = await db.vehicle_makes.find_one({"id": make_id}, {"_id": 0, "country_code": 1})
        if make_doc:
            _assert_country_scope(make_doc.get("country_code"), current_user)
        query["make_id"] = make_id
    elif country:
        country_code = country.upper()
        _assert_country_scope(country_code, current_user)
        make_ids = await db.vehicle_makes.find(
            {"country_code": country_code}, {"_id": 0, "id": 1}
        ).to_list(length=500)
        query["make_id"] = {"$in": [m["id"] for m in make_ids]}
    docs = await db.vehicle_models.find(query, {"_id": 0}).sort("name", 1).to_list(length=1000)
    return {"items": [_normalize_vehicle_model_doc(doc) for doc in docs]}


@api_router.post("/admin/vehicle-models", status_code=201)
async def admin_create_vehicle_model(
    payload: VehicleModelCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    slug = payload.slug.strip().lower()
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="slug format invalid")

    make = await db.vehicle_makes.find_one({"id": payload.make_id}, {"_id": 0, "id": 1, "country_code": 1})
    if not make:
        raise HTTPException(status_code=400, detail="make_id not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    model_id = str(uuid.uuid4())
    doc = {
        "id": model_id,
        "make_id": payload.make_id,
        "name": payload.name.strip(),
        "slug": slug,
        "active_flag": payload.active_flag if payload.active_flag is not None else True,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "VEHICLE_MASTER_DATA_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": make.get("country_code"),
        "subject_type": "vehicle_model",
        "subject_id": model_id,
        "action": "create",
        "created_at": now_iso,
        "metadata": {"slug": doc["slug"], "name": doc["name"], "make_id": payload.make_id},
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.vehicle_models.insert_one(doc)
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Model slug already exists")
        raise
    return {"model": _normalize_vehicle_model_doc(doc)}


@api_router.patch("/admin/vehicle-models/{model_id}")
async def admin_update_vehicle_model(
    model_id: str,
    payload: VehicleModelUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    model = await db.vehicle_models.find_one({"id": model_id}, {"_id": 0})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    updates: Dict = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.slug is not None:
        slug = payload.slug.strip().lower()
        if not SLUG_PATTERN.match(slug):
            raise HTTPException(status_code=400, detail="slug format invalid")
        updates["slug"] = slug
    if payload.make_id is not None:
        make = await db.vehicle_makes.find_one({"id": payload.make_id}, {"_id": 0})
        if not make:
            raise HTTPException(status_code=400, detail="make_id not found")
        updates["make_id"] = payload.make_id
    if payload.active_flag is not None:
        updates["active_flag"] = payload.active_flag
    if not updates:
        return {"model": _normalize_vehicle_model_doc(model)}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    make_lookup_id = updates.get("make_id", model.get("make_id"))
    make_doc = await db.vehicle_makes.find_one({"id": make_lookup_id}, {"_id": 0, "country_code": 1})
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "VEHICLE_MASTER_DATA_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": make_doc.get("country_code") if make_doc else None,
        "subject_type": "vehicle_model",
        "subject_id": model_id,
        "action": "update",
        "created_at": updates["updated_at"],
        "metadata": updates,
    }
    await db.audit_logs.insert_one(audit_doc)
    try:
        await db.vehicle_models.update_one({"id": model_id}, {"$set": updates})
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail="Model slug already exists")
        raise
    model.update(updates)
    return {"model": _normalize_vehicle_model_doc(model)}


@api_router.delete("/admin/vehicle-models/{model_id}")
async def admin_delete_vehicle_model(
    model_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "moderator"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    model = await db.vehicle_models.find_one({"id": model_id}, {"_id": 0})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    now_iso = datetime.now(timezone.utc).isoformat()
    make_doc = await db.vehicle_makes.find_one({"id": model.get("make_id")}, {"_id": 0, "country_code": 1})
    audit_doc = {
        "id": str(uuid.uuid4()),
        "event_type": "VEHICLE_MASTER_DATA_CHANGE",
        "actor_id": current_user["id"],
        "actor_role": current_user.get("role"),
        "country_code": make_doc.get("country_code") if make_doc else None,
        "subject_type": "vehicle_model",
        "subject_id": model_id,
        "action": "delete",
        "created_at": now_iso,
        "metadata": {"active_flag": False},
    }
    await db.audit_logs.insert_one(audit_doc)
    await db.vehicle_models.update_one({"id": model_id}, {"$set": {"active_flag": False, "updated_at": now_iso}})
    model["active_flag"] = False
    model["updated_at"] = now_iso
    return {"model": _normalize_vehicle_model_doc(model)}


async def _dashboard_metrics(db, country_code: str, include_revenue: bool = True) -> dict:
    total_listings = await db.vehicle_listings.count_documents({"country": country_code})
    published_listings = await db.vehicle_listings.count_documents({"country": country_code, "status": "published"})
    pending_moderation = await db.vehicle_listings.count_documents({"country": country_code, "status": "pending_moderation"})
    active_dealers = await db.users.count_documents({"role": "dealer", "dealer_status": "active", "country_code": country_code})

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_iso = month_start.isoformat()

    revenue_mtd = None
    totals: Dict[str, float] = {}
    if include_revenue:
        invoices = await db.invoices.find({
            "country_code": country_code,
            "status": "paid",
            "paid_at": {"$gte": month_start_iso},
        }, {"_id": 0, "amount_gross": 1, "currency": 1}).to_list(length=10000)
        for inv in invoices:
            currency = inv.get("currency") or "UNKNOWN"
            totals[currency] = totals.get(currency, 0) + float(inv.get("amount_gross") or 0)
        revenue_mtd = sum(totals.values())

    return {
        "total_listings": total_listings,
        "published_listings": published_listings,
        "pending_moderation": pending_moderation,
        "active_dealers": active_dealers,
        "revenue_mtd": round(revenue_mtd, 2) if revenue_mtd is not None else None,
        "revenue_currency_totals": {k: round(v, 2) for k, v in totals.items()} if include_revenue else None,
        "month_start_utc": month_start_iso,
    }


async def _dashboard_metrics_scope(db, country_codes: Optional[List[str]], include_revenue: bool = True) -> dict:
    listing_query: Dict[str, Any] = {}
    user_query: Dict[str, Any] = {}
    invoice_query: Dict[str, Any] = {"status": "paid"}
    if country_codes:
        listing_query["country"] = {"$in": country_codes}
        user_query["country_code"] = {"$in": country_codes}
        invoice_query["country_code"] = {"$in": country_codes}

    total_listings = await db.vehicle_listings.count_documents(listing_query)
    published_listings = await db.vehicle_listings.count_documents({**listing_query, "status": "published"})
    pending_moderation = await db.vehicle_listings.count_documents({**listing_query, "status": "pending_moderation"})
    active_dealers = await db.users.count_documents({**user_query, "role": "dealer", "dealer_status": "active"})

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_iso = month_start.isoformat()

    revenue_mtd = None
    totals: Dict[str, float] = {}
    if include_revenue:
        invoice_query["paid_at"] = {"$gte": month_start_iso}
        invoices = await db.invoices.find(invoice_query, {"_id": 0, "amount_gross": 1, "currency": 1}).to_list(length=10000)
        for inv in invoices:
            currency = inv.get("currency") or "UNKNOWN"
            totals[currency] = totals.get(currency, 0) + float(inv.get("amount_gross") or 0)
        revenue_mtd = sum(totals.values())

    return {
        "total_listings": total_listings,
        "published_listings": published_listings,
        "pending_moderation": pending_moderation,
        "active_dealers": active_dealers,
        "revenue_mtd": round(revenue_mtd, 2) if revenue_mtd is not None else None,
        "revenue_currency_totals": {k: round(v, 2) for k, v in totals.items()} if include_revenue else None,
        "month_start_utc": month_start_iso,
    }


async def _dashboard_invoice_totals(db, invoice_query: Dict[str, Any]) -> tuple[float, Dict[str, float]]:
    invoices = await db.invoices.find(invoice_query, {"_id": 0, "amount_gross": 1, "currency": 1}).to_list(length=10000)
    totals: Dict[str, float] = {}
    for inv in invoices:
        currency = inv.get("currency") or "UNKNOWN"
        totals[currency] = totals.get(currency, 0) + float(inv.get("amount_gross") or 0)
    total_amount = sum(totals.values())
    return round(total_amount, 2), {k: round(v, 2) for k, v in totals.items()}


async def _dashboard_kpis(db, effective_countries: Optional[List[str]], include_revenue: bool) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=DASHBOARD_KPI_DAYS)

    listing_query: Dict[str, Any] = {"created_at": {"$gte": today_start.isoformat()}}
    listing_week_query: Dict[str, Any] = {"created_at": {"$gte": week_start.isoformat()}}
    user_query: Dict[str, Any] = {"created_at": {"$gte": today_start.isoformat()}}
    user_week_query: Dict[str, Any] = {"created_at": {"$gte": week_start.isoformat()}}

    if effective_countries:
        listing_query["country"] = {"$in": effective_countries}
        listing_week_query["country"] = {"$in": effective_countries}
        user_query["country_code"] = {"$in": effective_countries}
        user_week_query["country_code"] = {"$in": effective_countries}

    today_listings = await db.vehicle_listings.count_documents(listing_query)
    week_listings = await db.vehicle_listings.count_documents(listing_week_query)
    today_users = await db.users.count_documents(user_query)
    week_users = await db.users.count_documents(user_week_query)

    today_revenue_total = None
    today_revenue_totals = None
    week_revenue_total = None
    week_revenue_totals = None

    if include_revenue:
        invoice_base: Dict[str, Any] = {"status": "paid"}
        if effective_countries:
            invoice_base["country_code"] = {"$in": effective_countries}
        today_revenue_total, today_revenue_totals = await _dashboard_invoice_totals(
            db,
            {**invoice_base, "paid_at": {"$gte": today_start.isoformat()}},
        )
        week_revenue_total, week_revenue_totals = await _dashboard_invoice_totals(
            db,
            {**invoice_base, "paid_at": {"$gte": week_start.isoformat()}},
        )

    return {
        "today": {
            "new_listings": today_listings,
            "new_users": today_users,
            "revenue_total": today_revenue_total,
            "revenue_currency_totals": today_revenue_totals,
        },
        "last_7_days": {
            "new_listings": week_listings,
            "new_users": week_users,
            "revenue_total": week_revenue_total,
            "revenue_currency_totals": week_revenue_totals,
        },
    }


async def _dashboard_trends(
    db, effective_countries: Optional[List[str]], include_revenue: bool, window_days: int
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    listings_trend: List[Dict[str, Any]] = []
    revenue_trend: List[Dict[str, Any]] = []

    invoice_base: Dict[str, Any] = {"status": "paid"}
    if effective_countries:
        invoice_base["country_code"] = {"$in": effective_countries}

    for offset in range(window_days):
        day = (now - timedelta(days=(window_days - 1 - offset))).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day + timedelta(days=1)
        start_iso = day.isoformat()
        end_iso = day_end.isoformat()

        listing_query: Dict[str, Any] = {"created_at": {"$gte": start_iso, "$lt": end_iso}}
        if effective_countries:
            listing_query["country"] = {"$in": effective_countries}
        listing_count = await db.vehicle_listings.count_documents(listing_query)
        listings_trend.append({"date": day.date().isoformat(), "count": listing_count})

        if include_revenue:
            revenue_total, revenue_totals = await _dashboard_invoice_totals(
                db,
                {**invoice_base, "paid_at": {"$gte": start_iso, "$lt": end_iso}},
            )
            revenue_trend.append({
                "date": day.date().isoformat(),
                "amount": revenue_total,
                "currency_totals": revenue_totals,
            })

    return {
        "window_days": window_days,
        "listings": listings_trend,
        "revenue": revenue_trend if include_revenue else None,
    }


async def _dashboard_risk_panel(db, effective_countries: Optional[List[str]], include_finance: bool) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    login_since_iso = (now - timedelta(hours=DASHBOARD_MULTI_IP_WINDOW_HOURS)).isoformat()
    login_query: Dict[str, Any] = {
        "event_type": "LOGIN_SUCCESS",
        "created_at": {"$gte": login_since_iso},
    }
    if effective_countries:
        login_query["country_code"] = {"$in": effective_countries}

    login_logs = await db.audit_logs.find(
        login_query,
        {"_id": 0, "user_id": 1, "admin_user_id": 1, "user_email": 1, "metadata": 1, "request_ip": 1},
    ).to_list(length=5000)

    user_ips: Dict[str, set] = defaultdict(set)
    user_emails: Dict[str, Optional[str]] = {}
    for log in login_logs:
        user_id = log.get("user_id") or log.get("admin_user_id")
        if not user_id:
            continue
        metadata = log.get("metadata") or {}
        ip_address = metadata.get("ip_address") or log.get("request_ip")
        if not ip_address:
            continue
        user_ips[user_id].add(ip_address)
        if log.get("user_email"):
            user_emails[user_id] = log.get("user_email")

    suspicious_users = [
        {"user_id": user_id, "user_email": user_emails.get(user_id), "ip_count": len(ips)}
        for user_id, ips in user_ips.items()
        if len(ips) >= DASHBOARD_MULTI_IP_THRESHOLD
    ]
    suspicious_users.sort(key=lambda item: item["ip_count"], reverse=True)

    sla_cutoff_iso = (now - timedelta(hours=DASHBOARD_SLA_HOURS)).isoformat()
    sla_query: Dict[str, Any] = {"status": "pending_moderation", "created_at": {"$lt": sla_cutoff_iso}}
    if effective_countries:
        sla_query["country"] = {"$in": effective_countries}

    sla_count = await db.vehicle_listings.count_documents(sla_query)
    sla_docs = await db.vehicle_listings.find(
        sla_query,
        {"_id": 0, "id": 1, "title": 1, "created_at": 1, "country": 1},
    ).sort("created_at", 1).limit(5).to_list(length=5)
    sla_samples = [
        {
            "listing_id": doc.get("id"),
            "title": doc.get("title"),
            "created_at": doc.get("created_at"),
            "country": doc.get("country"),
        }
        for doc in sla_docs
    ]

    pending_payments: Dict[str, Any]
    if include_finance:
        payment_cutoff_iso = (now - timedelta(days=DASHBOARD_PENDING_PAYMENT_DAYS)).isoformat()
        invoice_query: Dict[str, Any] = {"status": "unpaid", "issued_at": {"$lt": payment_cutoff_iso}}
        if effective_countries:
            invoice_query["country_code"] = {"$in": effective_countries}
        invoices = await db.invoices.find(
            invoice_query,
            {"_id": 0, "id": 1, "amount_gross": 1, "currency": 1, "issued_at": 1, "country_code": 1},
        ).to_list(length=5000)
        totals: Dict[str, float] = {}
        for inv in invoices:
            currency = inv.get("currency") or "UNKNOWN"
            totals[currency] = totals.get(currency, 0) + float(inv.get("amount_gross") or 0)
        pending_payments = {
            "count": len(invoices),
            "threshold_days": DASHBOARD_PENDING_PAYMENT_DAYS,
            "total_amount": round(sum(totals.values()), 2),
            "currency_totals": {k: round(v, 2) for k, v in totals.items()},
            "items": [
                {
                    "invoice_id": inv.get("id"),
                    "amount": inv.get("amount_gross"),
                    "currency": inv.get("currency"),
                    "issued_at": inv.get("issued_at"),
                    "country_code": inv.get("country_code"),
                }
                for inv in invoices[:5]
            ],
        }
    else:
        pending_payments = {"count": None, "hidden": True}

    return {
        "suspicious_logins": {
            "count": len(suspicious_users),
            "threshold": DASHBOARD_MULTI_IP_THRESHOLD,
            "window_hours": DASHBOARD_MULTI_IP_WINDOW_HOURS,
            "items": suspicious_users[:5],
        },
        "sla_breaches": {
            "count": sla_count,
            "threshold": DASHBOARD_SLA_HOURS,
            "window_hours": DASHBOARD_SLA_HOURS,
            "items": sla_samples,
        },
        "pending_payments": pending_payments,
        "finance_visible": include_finance,
    }


async def _dashboard_db_health(db) -> tuple[str, int]:
    start = time.perf_counter()
    status = "ok"
    try:
        await db.command("ping")
    except Exception:
        status = "error"
    latency_ms = int((time.perf_counter() - start) * 1000)
    return status, latency_ms


def _build_dashboard_pdf(summary: Dict[str, Any], trend_window: int) -> bytes:
    styles = getSampleStyleSheet()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Dashboard Export")
    elements = []

    def format_number(value: Optional[float]) -> str:
        if value is None:
            return "-"
        try:
            return f"{float(value):,.2f}".replace(",", " ")
        except Exception:
            return str(value)

    def format_currency_totals(totals: Optional[Dict[str, Any]]) -> str:
        if not totals:
            return "-"
        parts = []
        for currency, amount in totals.items():
            parts.append(f"{format_number(amount)} {currency}")
        return " / ".join(parts)

    def add_table(title: str, rows: List[List[str]]):
        if not rows:
            return
        elements.append(Paragraph(title, styles["Heading3"]))
        table = Table(rows, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

    countries = summary.get("country_codes") or []
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    elements.append(Paragraph("Dashboard Özet Raporu", styles["Title"]))
    elements.append(Paragraph(f"Kapsam: {summary.get('scope')}", styles["Normal"]))
    elements.append(Paragraph(f"Ülkeler: {', '.join(countries) or '-'}", styles["Normal"]))
    elements.append(Paragraph(f"Trend Aralığı: {trend_window} gün", styles["Normal"]))
    elements.append(Paragraph(f"Oluşturma: {generated_at}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    finance_visible = bool(summary.get("finance_visible"))
    kpis = summary.get("kpis") or {}
    today = kpis.get("today") or {}
    week = kpis.get("last_7_days") or {}
    kpi_rows = [["Periyot", "Yeni İlan", "Yeni Kullanıcı", "Gelir"]]
    def kpi_revenue_label(data: Dict[str, Any]) -> str:
        if not finance_visible:
            return "Gizli"
        total = data.get("revenue_total")
        totals = data.get("revenue_currency_totals")
        if total is None and not totals:
            return "0"
        return f"{format_number(total)} ({format_currency_totals(totals)})"

    kpi_rows.append([
        "Bugün",
        str(today.get("new_listings", 0)),
        str(today.get("new_users", 0)),
        kpi_revenue_label(today),
    ])
    kpi_rows.append([
        "Son 7 Gün",
        str(week.get("new_listings", 0)),
        str(week.get("new_users", 0)),
        kpi_revenue_label(week),
    ])
    add_table("KPI Özeti", kpi_rows)

    metrics = summary.get("metrics") or {}
    users = summary.get("users") or {}
    active_countries = summary.get("active_countries") or {}
    active_modules = summary.get("active_modules") or {}
    metrics_rows = [["Metri̇k", "Değer"]]
    metrics_rows.append(["Toplam Kullanıcı", str(users.get("total", 0))])
    metrics_rows.append(["Aktif / Pasif", f"{users.get('active', 0)} / {users.get('inactive', 0)}"])
    metrics_rows.append(["Toplam İlan", str(metrics.get("total_listings", 0))])
    metrics_rows.append(["Yayınlı İlan", str(metrics.get("published_listings", 0))])
    metrics_rows.append(["Moderasyon Bekleyen", str(metrics.get("pending_moderation", 0))])
    metrics_rows.append(["Aktif Dealer", str(metrics.get("active_dealers", 0))])
    metrics_rows.append(["Aktif Ülke", str(active_countries.get("count", 0))])
    metrics_rows.append(["Aktif Modül", str(active_modules.get("count", 0))])
    add_table("Genel Metrikler", metrics_rows)

    risk = summary.get("risk_panel") or {}
    suspicious = risk.get("suspicious_logins") or {}
    sla = risk.get("sla_breaches") or {}
    pending = risk.get("pending_payments") or {}
    risk_rows = [["Risk Başlığı", "Sayı", "Eşik", "Detay"]]
    risk_rows.append([
        "Çoklu IP girişleri",
        str(suspicious.get("count", 0)),
        f"{suspicious.get('threshold', '-') } IP / {suspicious.get('window_hours', '-') } saat",
        "Örnek kayıtlar: " + str(len(suspicious.get("items") or [])),
    ])
    risk_rows.append([
        "Moderasyon SLA ihlali",
        str(sla.get("count", 0)),
        f"> {sla.get('threshold', '-') } saat",
        "Örnek kayıtlar: " + str(len(sla.get("items") or [])),
    ])
    if finance_visible:
        risk_rows.append([
            "Bekleyen ödemeler",
            str(pending.get("count", 0)),
            f"> {pending.get('threshold_days', '-') } gün",
            f"Toplam: {format_number(pending.get('total_amount'))} | {format_currency_totals(pending.get('currency_totals'))}",
        ])
    else:
        risk_rows.append([
            "Bekleyen ödemeler",
            "-",
            "-",
            "Gizli",
        ])
    add_table("Risk & Alarm Merkezi", risk_rows)

    trends = summary.get("trends") or {}
    listings = trends.get("listings") or []
    revenue = trends.get("revenue") or []
    revenue_map = {item.get("date"): item for item in revenue}
    trend_rows = [["Tarih", "İlan", "Gelir"]]
    for item in listings:
        date_label = item.get("date")
        revenue_item = revenue_map.get(date_label) or {}
        revenue_label = "Gizli" if not finance_visible else format_number(revenue_item.get("amount"))
        trend_rows.append([
            str(date_label),
            str(item.get("count", 0)),
            revenue_label,
        ])
    add_table("Trend Detayı", trend_rows)

    health = summary.get("health") or {}
    health_rows = [["Bileşen", "Değer"]]
    health_rows.append(["API status", str(health.get("api_status"))])
    health_rows.append(["DB status", str(health.get("db_status"))])
    health_rows.append(["API gecikme", f"{health.get('api_latency_ms')} ms"])
    health_rows.append(["DB gecikme", f"{health.get('db_latency_ms')} ms"])
    health_rows.append(["Son deploy", str(health.get("deployed_at"))])
    health_rows.append(["Son restart", str(health.get("restart_at"))])
    health_rows.append(["Uptime", str(health.get("uptime_human"))])
    add_table("Sistem Sağlığı", health_rows)

    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value


@api_router.get("/admin/dashboard/summary")
async def admin_dashboard_summary(
    request: Request,
    country: Optional[str] = None,
    trend_days: Optional[int] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support", "finance"])),
):
    start_perf = time.perf_counter()
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    role = current_user.get("role")
    can_view_finance = role in {"finance", "super_admin"}
    trend_window = trend_days or DASHBOARD_TREND_DAYS
    if trend_window < DASHBOARD_TREND_MIN_DAYS or trend_window > DASHBOARD_TREND_MAX_DAYS:
        raise HTTPException(status_code=400, detail="trend_days must be between 7 and 365")
    scope = (current_user.get("country_scope") or [])
    country_code = country.upper() if country else None

    if role == "country_admin":
        if not scope:
            raise HTTPException(status_code=403, detail="Country scope required")
        if country_code and country_code not in scope:
            raise HTTPException(status_code=403, detail="Country scope violation")
        effective_countries = [country_code] if country_code else scope
    else:
        effective_countries = [country_code] if country_code else None

    cache_key = _dashboard_cache_key(role, effective_countries, trend_window)
    cached = _get_cached_dashboard_summary(cache_key)
    if cached:
        response = {**cached}
        health = dict(response.get("health") or {})
        health["api_latency_ms"] = int((time.perf_counter() - start_perf) * 1000)
        response["health"] = health
        return response

    metrics = await _dashboard_metrics_scope(db, effective_countries, include_revenue=can_view_finance)

    active_country_query: Dict[str, Any] = {"active_flag": True}
    if effective_countries:
        active_country_query["$or"] = [
            {"country_code": {"$in": effective_countries}},
            {"code": {"$in": effective_countries}},
        ]
    active_countries_docs = await db.countries.find(active_country_query, {"_id": 0, "country_code": 1, "code": 1}).to_list(length=1000)
    active_country_codes = [
        (doc.get("country_code") or doc.get("code")) for doc in active_countries_docs if (doc.get("country_code") or doc.get("code"))
    ]

    user_scope_query: Dict[str, Any] = {}
    if effective_countries:
        user_scope_query["country_code"] = {"$in": effective_countries}
    total_users = await db.users.count_documents(user_scope_query)
    active_users = await db.users.count_documents({**user_scope_query, "$or": [{"is_active": True}, {"is_active": {"$exists": False}}]})
    inactive_users = await db.users.count_documents({**user_scope_query, "is_active": False})

    role_distribution = {}
    for role_name in ["super_admin", "country_admin", "moderator", "support", "finance", "dealer", "individual"]:
        role_distribution[role_name] = await db.users.count_documents({**user_scope_query, "role": role_name})

    categories_query: Dict[str, Any] = {}
    if effective_countries:
        categories_query["$or"] = [
            {"country_code": {"$in": effective_countries}},
            {"country_code": None},
            {"country_code": ""},
        ]
    categories = await db.categories.find(categories_query, {"_id": 0, "form_schema": 1}).to_list(length=2000)
    active_modules = set()
    for cat in categories:
        schema = _normalize_category_schema(cat.get("form_schema")) if cat.get("form_schema") else {}
        for key, module in (schema.get("modules") or {}).items():
            enabled = bool(module.get("enabled")) if isinstance(module, dict) else bool(module)
            if enabled:
                active_modules.add(key)

    recent_query: Dict[str, Any] = {}
    if effective_countries:
        recent_query["country_code"] = {"$in": effective_countries}
    recent_logs = await db.audit_logs.find(recent_query, {"_id": 0}).sort("created_at", -1).limit(10).to_list(length=10)
    recent_activity = [
        {
            "id": log.get("id"),
            "event_type": log.get("event_type") or log.get("action"),
            "action": log.get("action"),
            "resource_type": log.get("resource_type") or log.get("subject_type"),
            "user_email": log.get("user_email"),
            "created_at": log.get("created_at"),
            "country_code": log.get("country_code"),
        }
        for log in recent_logs
    ]

    now = datetime.now(timezone.utc)
    since_iso = (now - timedelta(hours=24)).isoformat()
    listing_recent_query = {"created_at": {"$gte": since_iso}}
    if effective_countries:
        listing_recent_query["country"] = {"$in": effective_countries}
    new_listings = await db.vehicle_listings.count_documents(listing_recent_query)

    user_recent_query = {"created_at": {"$gte": since_iso}}
    if effective_countries:
        user_recent_query["country_code"] = {"$in": effective_countries}
    new_users = await db.users.count_documents(user_recent_query)

    delete_query = {
        "event_type": {"$in": ["LISTING_SOFT_DELETE", "LISTING_FORCE_UNPUBLISH"]},
        "created_at": {"$gte": since_iso},
    }
    if effective_countries:
        delete_query["country_code"] = {"$in": effective_countries}
    deleted_content = await db.audit_logs.count_documents(delete_query)

    kpis = await _dashboard_kpis(db, effective_countries, include_revenue=can_view_finance)
    trends = await _dashboard_trends(db, effective_countries, include_revenue=can_view_finance, window_days=trend_window)
    risk_panel = await _dashboard_risk_panel(db, effective_countries, include_finance=can_view_finance)

    db_status, db_latency_ms = await _dashboard_db_health(db)
    uptime_seconds = int((now - APP_START_TIME).total_seconds())
    api_latency_ms = int((time.perf_counter() - start_perf) * 1000)

    summary = {
        "scope": "country" if effective_countries else "global",
        "country_codes": effective_countries or active_country_codes,
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
        },
        "active_countries": {
            "count": len(active_country_codes),
            "codes": active_country_codes,
        },
        "active_modules": {
            "count": len(active_modules),
            "items": sorted(active_modules),
        },
        "recent_activity": recent_activity,
        "role_distribution": role_distribution,
        "activity_24h": {
            "new_listings": new_listings,
            "new_users": new_users,
            "deleted_content": deleted_content,
        },
        "health": {
            "api_status": "ok",
            "db_status": db_status,
            "api_latency_ms": api_latency_ms,
            "db_latency_ms": db_latency_ms,
            "deployed_at": os.environ.get("DEPLOYED_AT") or "unknown",
            "restart_at": APP_START_TIME.isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_human": _format_uptime(uptime_seconds),
        },
        "metrics": metrics,
        "kpis": kpis,
        "trends": trends,
        "risk_panel": risk_panel,
        "finance_visible": can_view_finance,
    }

    _set_cached_dashboard_summary(cache_key, summary)
    return summary


@api_router.get("/admin/dashboard/export/pdf")
async def admin_dashboard_export_pdf(
    request: Request,
    country: Optional[str] = None,
    trend_days: Optional[int] = None,
    current_user=Depends(check_permissions(["super_admin"])),
):
    db = request.app.state.db
    _enforce_export_rate_limit(request, current_user.get("id"))

    summary = await admin_dashboard_summary(
        request=request,
        country=country,
        trend_days=trend_days,
        current_user=current_user,
    )
    trend_window = (summary.get("trends") or {}).get("window_days") or DASHBOARD_TREND_DAYS
    pdf_bytes = _build_dashboard_pdf(summary, trend_window)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    filename = f"dashboard-summary-{timestamp}.pdf"

    audit_doc = await build_audit_entry(
        event_type="dashboard_export_pdf",
        actor=current_user,
        target_id="dashboard_summary",
        target_type="dashboard_summary",
        country_code=country.upper() if country else None,
        details={"trend_days": trend_window, "format": "pdf", "scope": summary.get("scope")},
        request=request,
    )
    audit_doc["action"] = "dashboard_export_pdf"
    audit_doc["user_agent"] = request.headers.get("user-agent")
    await db.audit_logs.insert_one(audit_doc)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


async def _build_country_compare_payload(
    db,
    current_user: dict,
    period: str,
    start_date: Optional[str],
    end_date: Optional[str],
    sort_by: Optional[str],
    sort_dir: Optional[str],
    selected_codes: Optional[List[str]],
) -> Dict[str, Any]:
    role = current_user.get("role")
    can_view_finance = role in {"finance", "super_admin"}
    scope = (current_user.get("country_scope") or [])

    period_start, period_end, period_label = _resolve_period_window(period, start_date, end_date)
    start_iso = period_start.isoformat()
    end_iso = period_end.isoformat()

    if selected_codes:
        selected_codes = [code.upper() for code in selected_codes]

    if role == "country_admin":
        if not scope:
            raise HTTPException(status_code=403, detail="Country scope required")
        if selected_codes and not set(selected_codes).issubset(set(scope)):
            raise HTTPException(status_code=403, detail="Country scope violation")
        effective_countries = scope
    else:
        effective_countries = None

    cache_key = _country_compare_cache_key(role, effective_countries, selected_codes, period, start_date, end_date, sort_by, sort_dir)
    cached = _get_cached_country_compare(cache_key)
    if cached:
        return cached

    fx_data = _get_ecb_rates()
    rates = fx_data.get("rates") or {ECB_RATE_BASE: 1.0}
    missing_rates: set[str] = set()

    now = datetime.now(timezone.utc)
    growth_7_start = now - timedelta(days=7)
    growth_14_start = now - timedelta(days=14)
    growth_30_start = now - timedelta(days=30)
    growth_60_start = now - timedelta(days=60)

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_elapsed = (now - month_start).days + 1
    last_month_end = month_start - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_same_end = last_month_start + timedelta(days=days_elapsed)
    if last_month_same_end > month_start:
        last_month_same_end = month_start

    login_since_iso = (now - timedelta(hours=DASHBOARD_MULTI_IP_WINDOW_HOURS)).isoformat()
    login_query: Dict[str, Any] = {
        "event_type": "LOGIN_SUCCESS",
        "created_at": {"$gte": login_since_iso},
    }
    if effective_countries:
        login_query["country_code"] = {"$in": effective_countries}
    login_logs = await db.audit_logs.find(
        login_query,
        {"_id": 0, "user_id": 1, "admin_user_id": 1, "country_code": 1, "metadata": 1, "request_ip": 1},
    ).to_list(length=10000)

    suspicious_by_country: Dict[str, int] = {}
    login_ips: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
    for log in login_logs:
        country_code = (log.get("country_code") or "").upper()
        if not country_code:
            continue
        user_id = log.get("user_id") or log.get("admin_user_id")
        if not user_id:
            continue
        metadata = log.get("metadata") or {}
        ip_address = metadata.get("ip_address") or log.get("request_ip")
        if not ip_address:
            continue
        login_ips[country_code][user_id].add(ip_address)

    for country_code, users in login_ips.items():
        suspicious_by_country[country_code] = len([1 for ips in users.values() if len(ips) >= DASHBOARD_MULTI_IP_THRESHOLD])

    pending_payment_by_country: Dict[str, int] = {}
    if can_view_finance:
        payment_cutoff_iso = (now - timedelta(days=DASHBOARD_PENDING_PAYMENT_DAYS)).isoformat()
        invoice_query: Dict[str, Any] = {"status": "unpaid", "issued_at": {"$lt": payment_cutoff_iso}}
        if effective_countries:
            invoice_query["country_code"] = {"$in": effective_countries}
        invoices = await db.invoices.find(invoice_query, {"_id": 0, "country_code": 1}).to_list(length=10000)
        for inv in invoices:
            code = (inv.get("country_code") or "").upper()
            if not code:
                continue
            pending_payment_by_country[code] = pending_payment_by_country.get(code, 0) + 1

    sla_24_cutoff = (now - timedelta(hours=24)).isoformat()
    sla_48_cutoff = (now - timedelta(hours=48)).isoformat()

    country_query: Dict[str, Any] = {"active_flag": True}
    if effective_countries:
        country_query["$or"] = [
            {"country_code": {"$in": effective_countries}},
            {"code": {"$in": effective_countries}},
        ]
    country_docs = await db.countries.find(country_query, {"_id": 0, "country_code": 1, "code": 1}).to_list(length=200)
    country_codes = [
        (doc.get("country_code") or doc.get("code") or "").upper()
        for doc in country_docs
        if (doc.get("country_code") or doc.get("code"))
    ]

    if selected_codes:
        country_codes = [code for code in country_codes if code in selected_codes]

    async def count_listings(code: str, start: datetime, end: datetime, status: Optional[str] = None) -> int:
        query: Dict[str, Any] = {"country": code, "created_at": {"$gte": start.isoformat(), "$lt": end.isoformat()}}
        if status:
            query["status"] = status
        return await db.vehicle_listings.count_documents(query)

    async def count_dealers(code: str, start: datetime, end: datetime) -> int:
        query: Dict[str, Any] = {
            "country_code": code,
            "role": "dealer",
            "dealer_status": "active",
            "created_at": {"$gte": start.isoformat(), "$lt": end.isoformat()},
        }
        return await db.users.count_documents(query)

    async def sum_revenue(code: str, start: datetime, end: datetime) -> tuple[float, Dict[str, float]]:
        if not can_view_finance:
            return 0.0, {}
        invoice_query = {
            "country_code": code,
            "status": "paid",
            "paid_at": {"$gte": start.isoformat(), "$lt": end.isoformat()},
        }
        invoices = await db.invoices.find(invoice_query, {"_id": 0, "amount_gross": 1, "currency": 1}).to_list(length=10000)
        totals: Dict[str, float] = {}
        eur_total = 0.0
        for inv in invoices:
            currency = (inv.get("currency") or ECB_RATE_BASE).upper()
            amount = float(inv.get("amount_gross") or 0)
            totals[currency] = totals.get(currency, 0.0) + amount
            eur_value = _convert_to_eur(amount, currency, rates)
            if eur_value is None:
                missing_rates.add(currency)
            else:
                eur_total += eur_value
        return round(eur_total, 2), {k: round(v, 2) for k, v in totals.items()}

    items = []
    for code in country_codes:
        total_listings = await count_listings(code, period_start, period_end)
        published_listings = await count_listings(code, period_start, period_end, status="published")
        pending_moderation = await count_listings(code, period_start, period_end, status="pending_moderation")
        active_dealers = await count_dealers(code, period_start, period_end)
        revenue_eur, revenue_local_totals = await sum_revenue(code, period_start, period_end)

        listings_7 = await count_listings(code, growth_7_start, now)
        listings_prev_7 = await count_listings(code, growth_14_start, growth_7_start)
        listings_30 = await count_listings(code, growth_30_start, now)
        listings_prev_30 = await count_listings(code, growth_60_start, growth_30_start)

        published_7 = await count_listings(code, growth_7_start, now, status="published")
        published_prev_7 = await count_listings(code, growth_14_start, growth_7_start, status="published")
        published_30 = await count_listings(code, growth_30_start, now, status="published")
        published_prev_30 = await count_listings(code, growth_60_start, growth_30_start, status="published")

        dealers_7 = await count_dealers(code, growth_7_start, now)
        dealers_prev_7 = await count_dealers(code, growth_14_start, growth_7_start)
        dealers_30 = await count_dealers(code, growth_30_start, now)
        dealers_prev_30 = await count_dealers(code, growth_60_start, growth_30_start)

        revenue_7, _ = await sum_revenue(code, growth_7_start, now)
        revenue_prev_7, _ = await sum_revenue(code, growth_14_start, growth_7_start)
        revenue_30, _ = await sum_revenue(code, growth_30_start, now)
        revenue_prev_30, _ = await sum_revenue(code, growth_60_start, growth_30_start)

        revenue_mtd, _ = await sum_revenue(code, month_start, now)
        revenue_prev_mtd, _ = await sum_revenue(code, last_month_start, last_month_same_end)

        conversion_rate = _safe_ratio(published_listings, total_listings)
        dealer_density = _safe_ratio(active_dealers, total_listings)

        sla_24_count = await db.vehicle_listings.count_documents({
            "country": code,
            "status": "pending_moderation",
            "created_at": {"$lt": sla_24_cutoff},
        })
        sla_48_count = await db.vehicle_listings.count_documents({
            "country": code,
            "status": "pending_moderation",
            "created_at": {"$lt": sla_48_cutoff},
        })

        risk_multi_login = suspicious_by_country.get(code, 0)
        risk_pending_payments = pending_payment_by_country.get(code, 0) if can_view_finance else None

        zero_data = total_listings == 0 and published_listings == 0 and active_dealers == 0 and revenue_eur == 0

        items.append({
            "country_code": code,
            "total_listings": total_listings,
            "published_listings": published_listings,
            "pending_moderation": pending_moderation,
            "active_dealers": active_dealers,
            "revenue_eur": revenue_eur if can_view_finance else None,
            "revenue_local_totals": revenue_local_totals if can_view_finance else None,
            "conversion_rate": round(conversion_rate * 100, 2) if conversion_rate is not None else None,
            "dealer_density": round(dealer_density * 100, 2) if dealer_density is not None else None,
            "growth_total_listings_7d": _growth_pct(listings_7, listings_prev_7),
            "growth_total_listings_30d": _growth_pct(listings_30, listings_prev_30),
            "growth_published_7d": _growth_pct(published_7, published_prev_7),
            "growth_published_30d": _growth_pct(published_30, published_prev_30),
            "growth_active_dealers_7d": _growth_pct(dealers_7, dealers_prev_7),
            "growth_active_dealers_30d": _growth_pct(dealers_30, dealers_prev_30),
            "growth_revenue_7d": _growth_pct(revenue_7, revenue_prev_7) if can_view_finance else None,
            "growth_revenue_30d": _growth_pct(revenue_30, revenue_prev_30) if can_view_finance else None,
            "revenue_mtd_growth_pct": _growth_pct(revenue_mtd, revenue_prev_mtd) if can_view_finance else None,
            "sla_pending_24h": sla_24_count,
            "sla_pending_48h": sla_48_count,
            "risk_multi_login": risk_multi_login,
            "risk_pending_payments": risk_pending_payments,
            "note": "Henüz veri yok" if zero_data else None,
        })

    default_sort_by = "revenue_eur" if can_view_finance else "total_listings"
    default_sort_dir = "desc"
    sort_field = sort_by or default_sort_by
    sort_direction = (sort_dir or default_sort_dir).lower()

    def sort_value(item: Dict[str, Any]) -> float:
        value = item.get(sort_field)
        if value is None:
            return -float("inf") if sort_direction == "desc" else float("inf")
        return float(value)

    items.sort(key=sort_value, reverse=sort_direction == "desc")

    payload = {
        "items": items,
        "finance_visible": can_view_finance,
        "period": period,
        "period_label": period_label,
        "period_start": start_iso,
        "period_end": end_iso,
        "fx": {
            "base": ECB_RATE_BASE,
            "as_of": fx_data.get("last_success_at"),
            "fallback": fx_data.get("fallback", False),
            "missing_currencies": sorted(missing_rates),
        },
        "sort_by": sort_field,
        "sort_dir": sort_direction,
        "default_sort_by": default_sort_by,
        "default_sort_dir": default_sort_dir,
    }

    _set_cached_country_compare(cache_key, payload)
    return payload


@api_router.get("/admin/dashboard/country-compare")
async def admin_dashboard_country_compare(
    request: Request,
    period: str = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
    countries: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    selected_codes = _parse_country_codes(countries)
    return await _build_country_compare_payload(db, current_user, period, start_date, end_date, sort_by, sort_dir, selected_codes)


@api_router.get("/admin/dashboard/country-compare/export/csv")
async def admin_dashboard_country_compare_export_csv(
    request: Request,
    period: str = "30d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
    countries: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support", "finance"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    _enforce_export_rate_limit(request, current_user.get("id"))

    selected_codes = _parse_country_codes(countries)
    payload = await _build_country_compare_payload(db, current_user, period, start_date, end_date, sort_by, sort_dir, selected_codes)
    items = payload.get("items") or []

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Country",
        "Total Listings",
        "Total Growth 7d",
        "Total Growth 30d",
        "Published",
        "Published Growth 7d",
        "Published Growth 30d",
        "Conversion Rate %",
        "Active Dealers",
        "Dealer Growth 7d",
        "Dealer Growth 30d",
        "Dealer Density %",
        "Revenue EUR",
        "Revenue Growth 7d",
        "Revenue Growth 30d",
        "Revenue MTD Growth %",
        "SLA 24h",
        "SLA 48h",
        "Risk Multi Login",
        "Risk Pending Payments",
        "Note",
    ])
    for item in items:
        writer.writerow([
            item.get("country_code"),
            item.get("total_listings"),
            item.get("growth_total_listings_7d"),
            item.get("growth_total_listings_30d"),
            item.get("published_listings"),
            item.get("growth_published_7d"),
            item.get("growth_published_30d"),
            item.get("conversion_rate"),
            item.get("active_dealers"),
            item.get("growth_active_dealers_7d"),
            item.get("growth_active_dealers_30d"),
            item.get("dealer_density"),
            item.get("revenue_eur"),
            item.get("growth_revenue_7d"),
            item.get("growth_revenue_30d"),
            item.get("revenue_mtd_growth_pct"),
            item.get("sla_pending_24h"),
            item.get("sla_pending_48h"),
            item.get("risk_multi_login"),
            item.get("risk_pending_payments"),
            item.get("note"),
        ])

    csv_content = buffer.getvalue().encode("utf-8")
    buffer.close()
    filename = f"country-compare-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"

    audit_doc = await build_audit_entry(
        event_type="country_compare_export_csv",
        actor=current_user,
        target_id="country_compare",
        target_type="dashboard_country_compare",
        country_code=None,
        details={"period": period, "start_date": start_date, "end_date": end_date, "sort_by": sort_by, "sort_dir": sort_dir},
        request=request,
    )
    audit_doc["action"] = "country_compare_export_csv"
    audit_doc["user_agent"] = request.headers.get("user-agent")
    await db.audit_logs.insert_one(audit_doc)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


@api_router.get("/admin/session/health")
async def admin_session_health(request: Request, response: Response, current_user=Depends(get_current_user)):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1] if auth_header.startswith("Bearer ") else None
    expires_at = None
    if token:
        payload = decode_token(token)
        exp = payload.get("exp")
        if exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
    roles = current_user.get("roles") or [current_user.get("role")]
    response.headers["Cache-Control"] = "no-store"
    return {
        "user_id": current_user.get("id"),
        "roles": roles,
        "expires_at": expires_at,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


# =====================
# Public Search v2 (Mongo)
# =====================

@api_router.get("/v2/search")
async def public_search_v2(
    request: Request,
    country: str | None = None,
    q: Optional[str] = None,
    category: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    sort: str = "date_desc",
    page: int = 1,
    limit: int = 20,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
):
    """Mongo-backed search endpoint for Public Portal.

    Contract (minimal, to match existing SearchPage.js):
    - Requires ?country=XX
    - Returns: { items: [], facets: {}, facet_meta: {}, pagination: {total,page,pages} }

    Notes:
    - For v1.0.0 release blocker fix, we search only published vehicle listings.
    - Facets are returned empty for now (UI will still render; facet list stays empty).
    """

    db = request.app.state.db

    country_norm = (country or "").strip().upper()
    if not country_norm:
        raise HTTPException(status_code=400, detail="country is required")

    # Base query: published listings only
    query: Dict = {
        "status": "published",
        "country": country_norm,
    }

    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"vehicle.make_key": {"$regex": q, "$options": "i"}},
            {"vehicle.model_key": {"$regex": q, "$options": "i"}},
        ]

    if category:
        keys = [category]
        cat = await db.categories.find_one(
            {
                "$and": [
                    {
                        "$or": [
                            {"slug": category},
                            {"id": category},
                        ],
                    },
                    {
                        "$or": [
                            {"country_code": None},
                            {"country_code": ""},
                            {"country_code": country_norm},
                        ],
                    },
                    {"active_flag": True},
                ],
            },
            {"_id": 0, "id": 1, "slug": 1},
        )
        if cat:
            if cat.get("id"):
                keys.append(cat["id"])
            slug_value = _pick_label(cat.get("slug"))
            if slug_value:
                keys.append(slug_value)

        query["category_key"] = {"$in": list(set(keys))}

    if make:
        query["vehicle.make_key"] = make
    if model:
        query["vehicle.model_key"] = model

    # Price filters: stored as attributes.price_eur
    if price_min is not None or price_max is not None:
        price_q: Dict = {}
        if price_min is not None:
            price_q["$gte"] = int(price_min)
        if price_max is not None:
            price_q["$lte"] = int(price_max)
        query["attributes.price_eur"] = price_q

    # Pagination guardrails
    page = max(1, int(page))
    limit = min(100, max(1, int(limit)))

    # Sorting
    sort_spec = [("created_at", -1)]
    if sort == "price_asc":
        sort_spec = [("attributes.price_eur", 1), ("created_at", -1)]
    elif sort == "price_desc":
        sort_spec = [("attributes.price_eur", -1), ("created_at", -1)]
    elif sort == "date_asc":
        sort_spec = [("created_at", 1)]

    total = await db.vehicle_listings.count_documents(query)

    cursor = (
        db.vehicle_listings.find(query, {"_id": 0})
        .sort(sort_spec)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)

    items = []
    for d in docs:
        v = d.get("vehicle") or {}
        attrs = d.get("attributes") or {}
        title = (d.get("title") or "").strip()
        if not title:
            title = f"{(v.get('make_key') or '').upper()} {v.get('model_key') or ''} {v.get('year') or ''}".strip()

        media = d.get("media") or []
        cover = next((m for m in media if m.get("is_cover")), media[0] if media else None)
        image_url = None
        if cover and cover.get("file"):
            image_url = f"/media/listings/{d['id']}/{cover['file']}"

        price_data = d.get("price") or {}
        primary_price = price_data.get("amount")
        if primary_price is None:
            primary_price = attrs.get("price_eur")
        items.append(
            {
                "id": d["id"],
                "title": title,
                "price": primary_price,
                "currency": price_data.get("currency_primary") or "EUR",
                "secondary_price": price_data.get("secondary_amount"),
                "secondary_currency": price_data.get("currency_secondary"),
                "image": image_url,
                "city": "",
            }
        )

    pages = (total + limit - 1) // limit if total else 0

    return {
        "items": items,
        "facets": {},
        "facet_meta": {},
        "pagination": {
            "total": total,
            "page": page,
            "pages": pages,
        },
    }



# =====================
# Vehicle Master Data (DB)
# =====================

@api_router.get("/v1/vehicle/makes")
async def public_vehicle_makes(country: str | None = None, request: Request = None):
    if not country:
        raise HTTPException(status_code=400, detail="country is required")
    code = country.upper()
    db = request.app.state.db
    docs = await db.vehicle_makes.find(
        {
            "country_code": code,
            "$or": [{"active_flag": True}, {"active_flag": {"$exists": False}}],
        },
        {"_id": 0, "id": 1, "slug": 1, "name": 1},
    ).sort("name", 1).to_list(length=500)
    items = [
        {"id": doc.get("id"), "key": doc.get("slug"), "label": doc.get("name")}
        for doc in docs
        if doc.get("slug")
    ]
    return {"version": "db", "items": items}


@api_router.get("/v1/vehicle/models")
async def public_vehicle_models(make: str, country: str | None = None, request: Request = None):
    db = request.app.state.db
    make_doc = await db.vehicle_makes.find_one(
        {
            "slug": make,
            "$or": [{"active_flag": True}, {"active_flag": {"$exists": False}}],
        },
        {"_id": 0, "id": 1, "slug": 1, "country_code": 1},
    )
    if not make_doc:
        raise HTTPException(status_code=404, detail="Make not found")
    if country and make_doc.get("country_code") != country.upper():
        raise HTTPException(status_code=404, detail="Make not found")
    models = await db.vehicle_models.find(
        {
            "make_id": make_doc.get("id"),
            "$or": [{"active_flag": True}, {"active_flag": {"$exists": False}}],
        },
        {"_id": 0, "id": 1, "slug": 1, "name": 1},
    ).sort("name", 1).to_list(length=1000)
    items = [
        {"id": doc.get("id"), "key": doc.get("slug"), "label": doc.get("name")}
        for doc in models
        if doc.get("slug")
    ]
    return {"version": "db", "make": make, "items": items}


@api_router.get("/v2/vehicle/makes")
async def public_vehicle_makes_v2(country: str | None = None, request: Request = None):
    return await public_vehicle_makes(country, request)


@api_router.get("/v2/vehicle/models")
async def public_vehicle_models_v2(make_key: str | None = None, make: str | None = None, country: str | None = None, request: Request = None):
    key = make_key or make
    if not key:
        raise HTTPException(status_code=400, detail="make_key is required")
    return await public_vehicle_models(key, country, request)


@api_router.get("/v1/admin/vehicle-master/status")
async def vehicle_master_status_endpoint(current_user=Depends(check_permissions(["super_admin", "country_admin"]))):
    return vehicle_master_status()


@api_router.post("/v1/admin/vehicle-master/validate")
async def vehicle_master_validate_endpoint(request: Request, current_user=Depends(check_permissions(["super_admin", "country_admin"]))):
    form = await request.form()
    upload = form.get("file")
    if upload is None:
        raise HTTPException(status_code=400, detail="file is required")

    raw = await upload.read()
    return validate_upload(upload.filename or "bundle.json", raw)


@api_router.post("/v1/admin/vehicle-master/activate")
async def vehicle_master_activate_endpoint(payload: dict, request: Request, current_user=Depends(check_permissions(["super_admin", "country_admin"]))):
    staging_id = payload.get("staging_id")
    if not staging_id:
        raise HTTPException(status_code=400, detail="staging_id is required")



# =====================
# Vehicle Listings (Stage-4)
# =====================

@api_router.post("/v1/listings/vehicle")
async def create_vehicle_draft(payload: dict, request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db
    doc = await create_vehicle_listing(db, payload, current_user)
    return {"id": doc["id"], "status": doc["status"], "validation_errors": [], "next_actions": ["upload_media", "submit"]}


@api_router.post("/v1/listings/vehicle/{listing_id}/media")
async def upload_vehicle_media(
    listing_id: str,
    request: Request,
    files: list[UploadFile] = File(...),
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("created_by") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if listing.get("status") not in ["draft", "needs_revision"]:
        raise HTTPException(status_code=400, detail="Only draft/needs_revision can accept media")

    stored = []
    for f in files:
        raw = await f.read()
        try:
            filename, w, h = store_image(listing["country"], listing_id, raw, f.filename or "upload.jpg")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        media_item = {
            "media_id": str(uuid.uuid4()),
            "file": filename,
            "width": w,
            "height": h,
            "is_cover": False,
        }
        stored.append(media_item)
        await add_vehicle_media(db, listing_id, media_item)

    # set cover if none
    listing = await get_vehicle_listing(db, listing_id)
    media = listing.get("media", [])
    if media and not any(m.get("is_cover") for m in media):
        media[0]["is_cover"] = True
        await db.vehicle_listings.update_one({"id": listing_id, "media.media_id": media[0]["media_id"]}, {"$set": {"media.$.is_cover": True}})
        listing = await get_vehicle_listing(db, listing_id)
        media = listing.get("media", [])

    resp_media = [
        {
            "media_id": m["media_id"],
            "file": m["file"],
            "width": m["width"],
            "height": m["height"],
            "is_cover": m.get("is_cover", False),
            "preview_url": f"/api/v1/listings/vehicle/{listing_id}/media/{m['media_id']}/preview",
        }
        for m in media
    ]

    return {"id": listing_id, "status": "draft", "media": resp_media}


@api_router.get("/v1/listings/vehicle/{listing_id}/media/{media_id}/preview")
async def preview_vehicle_media(listing_id: str, media_id: str, request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("created_by") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")

    media = next((m for m in (listing.get("media") or []) if m.get("media_id") == media_id), None)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    path = resolve_public_media_path(listing_id, media["file"])
    return FileResponse(path)


def _apply_listing_payload(listing: dict, payload: dict) -> tuple[dict, dict]:
    updates: dict = {}
    if not payload:
        return listing, updates
    core_fields = payload.get("core_fields") or {}
    price_payload = core_fields.get("price") if isinstance(core_fields, dict) else None
    price_payload = price_payload or payload.get("price") or {}
    title = core_fields.get("title") or payload.get("title")
    description = core_fields.get("description") or payload.get("description")
    if title is not None:
        updates["title"] = title.strip()
        updates["title_lower"] = title.strip().lower()
    if description is not None:
        updates["description"] = description.strip()
    if price_payload:
        updates["price"] = {
            "amount": price_payload.get("amount"),
            "currency_primary": price_payload.get("currency_primary"),
            "currency_secondary": price_payload.get("currency_secondary"),
            "secondary_amount": price_payload.get("secondary_amount"),
            "decimal_places": price_payload.get("decimal_places"),
        }
    if core_fields:
        updates["core_fields"] = core_fields

    attributes = dict(listing.get("attributes") or {})
    dynamic_fields = payload.get("dynamic_fields") or {}
    if isinstance(dynamic_fields, dict):
        attributes.update(dynamic_fields)
    extra_attrs = payload.get("attributes")
    if isinstance(extra_attrs, dict):
        attributes.update(extra_attrs)
    price_amount = updates.get("price", {}).get("amount") if updates.get("price") else None
    if price_amount is not None:
        attributes["price_eur"] = price_amount
    updates["attributes"] = attributes

    vehicle_payload = payload.get("vehicle") or {}
    if vehicle_payload:
        vehicle = dict(listing.get("vehicle") or {})
        vehicle.update({k: v for k, v in vehicle_payload.items() if v is not None})
        updates["vehicle"] = vehicle

    if payload.get("detail_groups") is not None:
        updates["detail_groups"] = payload.get("detail_groups")
    if payload.get("modules") is not None:
        updates["modules"] = payload.get("modules")
    if payload.get("payment_options") is not None:
        updates["payment_options"] = payload.get("payment_options")

    updated_listing = dict(listing)
    updated_listing.update(updates)
    return updated_listing, updates


@api_router.post("/v1/listings/vehicle/{listing_id}/submit")
async def submit_vehicle_listing(
    listing_id: str,
    request: Request,
    payload: dict = Body(default={}),
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("created_by") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if listing.get("status") not in ["draft", "needs_revision"]:
        raise HTTPException(status_code=400, detail="Listing not draft/needs_revision")

    listing, updates = _apply_listing_payload(listing, payload)
    if updates:
        now_iso = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now_iso
        await db.vehicle_listings.update_one({"id": listing_id}, {"$set": updates})

    vehicle_master = await _build_vehicle_master_from_db(db, listing.get("country"))
    required_keys = await _get_required_attribute_keys(db, listing.get("category_key"), listing.get("country"))
    errs = validate_publish(
        listing,
        vehicle_master,
        required_attribute_keys=required_keys,
        supported_countries=SUPPORTED_COUNTRIES,
    )
    schema = None
    if listing.get("category_id"):
        category = await db.categories.find_one({"id": listing.get("category_id")})
        if category:
            schema = _normalize_category_schema(category.get("form_schema"))
    if schema:
        errs.extend(validate_listing_schema(listing, schema))
        title_uniqueness = schema.get("title_uniqueness", {})
        if title_uniqueness.get("enabled"):
            title_value = (listing.get("title") or "").strip()
            if title_value:
                query = {
                    "title_lower": title_value.lower(),
                    "category_id": listing.get("category_id"),
                    "id": {"$ne": listing.get("id")},
                    "status": {"$ne": "archived"},
                }
                if title_uniqueness.get("scope") == "category_user":
                    query["created_by"] = listing.get("created_by")
                exists = await db.vehicle_listings.find_one(query, {"_id": 1})
                if exists:
                    errs.append(
                        {
                            "code": "DUPLICATE_TITLE",
                            "field": "title",
                            "message": schema.get("core_fields", {})
                            .get("title", {})
                            .get("messages", {})
                            .get("duplicate", "Bu başlık zaten kullanılıyor."),
                        }
                    )
    if errs:
        raise HTTPException(
            status_code=422,
            detail={"id": listing_id, "status": listing.get("status"), "validation_errors": errs, "next_actions": ["fix_form", "upload_media"]},
        )

    listing = await set_vehicle_status(db, listing_id, "pending_moderation")

    return {
        "id": listing_id,
        "status": "pending_moderation",
        "validation_errors": [],
        "next_actions": ["wait_moderation"],
        "detail_url": f"/ilan/{listing_id}?preview=1",
    }


@api_router.get("/v1/listings/vehicle/{listing_id}")
async def get_vehicle_detail(listing_id: str, request: Request, preview: bool = False):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing or (listing.get("status") != "published" and not preview):
        raise HTTPException(status_code=404, detail="Not found")

    media = listing.get("media") or []
    out_media = [
        {
            "media_id": m["media_id"],
            "url": f"/media/listings/{listing_id}/{m['file']}",
            "is_cover": m.get("is_cover", False),
            "width": m.get("width"),
            "height": m.get("height"),
        }
        for m in media
    ]

    v = listing.get("vehicle") or {}
    attrs = listing.get("attributes") or {}
    title = listing.get("title") or f"{v.get('make_key','').upper()} {v.get('model_key','')} {v.get('year','')}".strip()
    price_data = listing.get("price") or {}
    primary_price = price_data.get("amount")
    if primary_price is None:
        primary_price = attrs.get("price_eur")

    modules = None
    if listing.get("category_id"):
        category = await db.categories.find_one({"id": listing.get("category_id")})
        if category and category.get("form_schema"):
            modules = _normalize_category_schema(category.get("form_schema")).get("modules")

    return {
        "id": listing_id,
        "status": "published",
        "country": listing.get("country"),
        "category_key": listing.get("category_key"),
        "vehicle": v,
        "attributes": attrs,
        "media": out_media,
        "title": title,
        "price": primary_price,
        "currency": price_data.get("currency_primary") or "EUR",
        "secondary_price": price_data.get("secondary_amount"),
        "secondary_currency": price_data.get("currency_secondary"),
        "location": {"city": "", "country": listing.get("country")},
        "description": listing.get("description") or "",
        "seller": {"name": "", "is_verified": False},
        "modules": modules or {},
        "contact_option_phone": listing.get("contact_option_phone", False),
        "contact_option_message": listing.get("contact_option_message", True),
        "contact": {"phone_protected": not listing.get("contact_option_phone", False)},
    }


@app.get("/media/listings/{listing_id}/{file}")
async def public_vehicle_media(listing_id: str, file: str, request: Request):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing or listing.get("status") != "published":
        raise HTTPException(status_code=404, detail="Not found")

    # ensure file belongs to listing
    media = listing.get("media") or []
    if not any(m.get("file") == file for m in media):
        raise HTTPException(status_code=404, detail="Not found")

    path = resolve_public_media_path(listing_id, file)
    return FileResponse(path)


@api_router.post("/v1/admin/vehicle-master/rollback")
async def vehicle_master_rollback_endpoint(payload: dict, request: Request, current_user=Depends(check_permissions(["super_admin", "country_admin"]))):
    target_version = payload.get("target_version")
    current = vehicle_master_rollback(user_id=current_user["id"], target_version=target_version)

    # reload in-memory cache
    request.app.state.vehicle_master = load_current_master(request.app.state.vehicle_master_dir)

    return {"ok": True, "current": current}

app.include_router(api_router)
