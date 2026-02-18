import os
import re
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import List, Optional, Dict, Any
import time


from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
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
from app.vehicle_publish_guard import validate_publish
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
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


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
        created_at=doc.get("created_at") or datetime.now(timezone.utc).isoformat(),
        last_login=doc.get("last_login"),
    )


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
            "is_active": True,
            "is_verified": True,
            "country_scope": ["DE"],
            "country_code": "DE",
            "preferred_language": "tr",
            "created_at": now_iso,
            "last_login": None,
        }
    )


async def lifespan(app: FastAPI):
    client = get_mongo_client()
    db = client[get_db_name()]

    # Ping
    await db.command("ping")

    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
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

    # Seed countries
    now_iso = datetime.now(timezone.utc).isoformat()
    for c in default_countries(now_iso):
        await db.countries.update_one(
            {"code": c["code"]},
            {"$setOnInsert": c},
            upsert=True,
        )
    existing_countries = await db.countries.find({}, {"_id": 0, "code": 1, "country_code": 1}).to_list(length=500)
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

    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="User account is disabled")


    # successful login: reset failed-login counters
    _failed_login_attempts.pop(rl_key, None)
    _failed_login_blocked_until.pop(rl_key, None)
    _failed_login_block_audited.pop(rl_key, None)

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": now_iso}})
    user["last_login"] = now_iso

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


@api_router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserPayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )
    query: Dict = {}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country
    if role:
        query["role"] = role
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]

    cursor = db.users.find(query, {"_id": 0}).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_user_to_response(d).model_dump() for d in docs]


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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
):
    db = request.app.state.db
    ctx = await resolve_admin_country_context(request, current_user=current_user, db=db, )

    query: Dict = {"role": "dealer"}
    if getattr(ctx, "mode", "global") == "country" and ctx.country:
        query["country_code"] = ctx.country
    if status:
        query["dealer_status"] = status
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    country: Optional[str] = None,
    module: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    _ensure_moderation_rbac(current_user)

    q: Dict = {"status": status}
    if country:
        q["country"] = country.strip().upper()
    if module and module != "vehicle":
        # Only vehicle listings exist in Mongo MVP
        return []

    cursor = db.vehicle_listings.find(q, {"_id": 0}).sort("created_at", -1).skip(int(skip)).limit(int(limit))
    docs = await cursor.to_list(length=int(limit))

    out = []
    for d in docs:
        v = d.get("vehicle") or {}
        attrs = d.get("attributes") or {}
        media = d.get("media") or []
        title = (d.get("title") or "").strip() or f"{(v.get('make_key') or '').upper()} {v.get('model_key') or ''} {v.get('year') or ''}".strip()
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
                "is_dealer_listing": False,
                "is_premium": False,
            }
        )

    return out


@api_router.get("/admin/moderation/queue/count")
async def moderation_queue_count(
    request: Request,
    status: str = "pending_moderation",
    current_user=Depends(get_current_user),
):
    db = request.app.state.db
    _ensure_moderation_rbac(current_user)
    count = await db.vehicle_listings.count_documents({"status": status})
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


class CategoryUpdatePayload(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
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


def _normalize_category_doc(doc: dict) -> dict:
    return {
        "id": doc.get("id"),
        "parent_id": doc.get("parent_id"),
        "name": _pick_label(doc.get("name")) or _pick_label(doc.get("translations", [{}])[0].get("name") if doc.get("translations") else None),
        "slug": _pick_label(doc.get("slug")) or doc.get("segment"),
        "country_code": doc.get("country_code"),
        "active_flag": doc.get("active_flag", doc.get("is_enabled", True)),
        "sort_order": doc.get("sort_order", 0),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


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

    dealer_only_flag = _parse_bool_flag(dealer_only)
    if dealer_only_flag:
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
        v = d.get("vehicle") or {}
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
        listing_map = {l.get("id"): l for l in listings}

    reporter_ids = [d.get("reporter_user_id") for d in docs if d.get("reporter_user_id")]
    seller_ids = [l.get("created_by") for l in listing_map.values() if l.get("created_by")]
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    query: Dict = {}
    if country:
        code = country.upper()
        _assert_country_scope(code, current_user)
        query["country_code"] = code
    docs = await db.categories.find(query, {"_id": 0}).sort("sort_order", 1).to_list(length=1000)
    return {"items": [_normalize_category_doc(doc) for doc in docs]}


@api_router.post("/admin/categories", status_code=201)
async def admin_create_category(
    payload: CategoryCreatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    doc = {
        "id": category_id,
        "parent_id": parent_id,
        "name": payload.name.strip(),
        "slug": slug,
        "country_code": country_code,
        "active_flag": payload.active_flag if payload.active_flag is not None else True,
        "sort_order": payload.sort_order or 0,
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
    return {"category": _normalize_category_doc(doc)}


@api_router.patch("/admin/categories/{category_id}")
async def admin_update_category(
    category_id: str,
    payload: CategoryUpdatePayload,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
):
    # Permission check already handled by dependency
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )

    category = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    updates: Dict = {}
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

    if not updates:
        return {"category": _normalize_category_doc(category)}

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
    return {"category": _normalize_category_doc(category)}


@api_router.delete("/admin/categories/{category_id}")
async def admin_delete_category(
    category_id: str,
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    return {"category": _normalize_category_doc(category)}


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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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
    current_user=Depends(check_permissions(["super_admin", "country_admin"])),
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


async def _dashboard_metrics(db, country_code: str) -> dict:
    total_listings = await db.vehicle_listings.count_documents({"country": country_code})
    published_listings = await db.vehicle_listings.count_documents({"country": country_code, "status": "published"})
    pending_moderation = await db.vehicle_listings.count_documents({"country": country_code, "status": "pending_moderation"})
    active_dealers = await db.users.count_documents({"role": "dealer", "dealer_status": "active", "country_code": country_code})

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_iso = month_start.isoformat()
    invoices = await db.invoices.find({
        "country_code": country_code,
        "status": "paid",
        "paid_at": {"$gte": month_start_iso},
    }, {"_id": 0, "amount_gross": 1, "currency": 1}).to_list(length=10000)
    totals: Dict[str, float] = {}
    for inv in invoices:
        currency = inv.get("currency") or "UNKNOWN"
        totals[currency] = totals.get(currency, 0) + float(inv.get("amount_gross") or 0)
    revenue_mtd = sum(totals.values())

    return {
        "total_listings": total_listings,
        "published_listings": published_listings,
        "pending_moderation": pending_moderation,
        "active_dealers": active_dealers,
        "revenue_mtd": round(revenue_mtd, 2),
        "revenue_currency_totals": {k: round(v, 2) for k, v in totals.items()},
        "month_start_utc": month_start_iso,
    }


@api_router.get("/admin/dashboard/summary")
async def admin_dashboard_summary(
    request: Request,
    country: Optional[str] = None,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    if not country:
        raise HTTPException(status_code=400, detail="country is required")
    country_code = country.upper()
    _assert_country_scope(country_code, current_user)
    metrics = await _dashboard_metrics(db, country_code)
    return {"country_code": country_code, **metrics}


@api_router.get("/admin/dashboard/country-compare")
async def admin_dashboard_country_compare(
    request: Request,
    current_user=Depends(check_permissions(["super_admin", "country_admin", "support"])),
):
    db = request.app.state.db
    await resolve_admin_country_context(request, current_user=current_user, db=db, )
    docs = await db.countries.find({}, {"_id": 0, "country_code": 1, "code": 1, "active_flag": 1, "is_enabled": 1}).to_list(length=200)
    items = []
    for doc in docs:
        code = (doc.get("country_code") or doc.get("code") or "").upper()
        if not code:
            continue
        if current_user.get("role") == "country_admin":
            scope = current_user.get("country_scope") or []
            if "*" not in scope and code not in scope:
                continue
        metrics = await _dashboard_metrics(db, code)
        items.append({"country_code": code, **metrics})
    return {"items": items}


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
                "$or": [
                    {"slug": category},
                    {"id": category},
                ],
                "active_flag": True,
                "$or": [
                    {"country_code": None},
                    {"country_code": ""},
                    {"country_code": country_norm},
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

        items.append(
            {
                "id": d["id"],
                "title": title,
                "price": attrs.get("price_eur"),
                "currency": "EUR",
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


@api_router.post("/v1/listings/vehicle/{listing_id}/submit")
async def submit_vehicle_listing(listing_id: str, request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.get("created_by") != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    if listing.get("status") not in ["draft", "needs_revision"]:
        raise HTTPException(status_code=400, detail="Listing not draft/needs_revision")

    vehicle_master = await _build_vehicle_master_from_db(db, listing.get("country"))
    required_keys = await _get_required_attribute_keys(db, listing.get("category_key"), listing.get("country"))
    errs = validate_publish(
        listing,
        vehicle_master,
        required_attribute_keys=required_keys,
        supported_countries=SUPPORTED_COUNTRIES,
    )
    if errs:
        # return normalized 422 payload for FE
        raise HTTPException(status_code=422, detail={"id": listing_id, "status": listing.get("status"), "validation_errors": errs, "next_actions": ["fix_form", "upload_media"]})

    # If publish guard passes, listing is ready for moderation queue
    listing = await set_vehicle_status(db, listing_id, "pending_moderation")

    return {
        "id": listing_id,
        "status": "pending_moderation",
        "validation_errors": [],
        "next_actions": ["wait_moderation"],
    }


@api_router.get("/v1/listings/vehicle/{listing_id}")
async def get_vehicle_detail(listing_id: str, request: Request):
    db = request.app.state.db
    listing = await get_vehicle_listing(db, listing_id)
    if not listing or listing.get("status") != "published":
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
    title = f"{v.get('make_key','').upper()} {v.get('model_key','')} {v.get('year','')}".strip()

    return {
        "id": listing_id,
        "status": "published",
        "country": listing.get("country"),
        "category_key": listing.get("category_key"),
        "vehicle": v,
        "attributes": attrs,
        "media": out_media,
        "title": title,
        "price": attrs.get("price_eur"),
        "currency": "EUR",
        "location": {"city": "", "country": listing.get("country")},
        "description": "",
        "seller": {"name": "", "is_verified": False},
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
