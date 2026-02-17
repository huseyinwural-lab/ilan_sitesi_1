import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
from typing import List, Optional, Dict

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
from app.dependencies import get_current_user, check_permissions
from app.countries_seed import default_countries
from app.menu_seed import default_top_menu
from app.categories_seed import vehicle_category_tree


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
from app.vehicle_master_admin_file import validate_upload, activate_staging, rollback as vehicle_master_rollback, get_status as vehicle_master_status


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

SUPPORTED_COUNTRIES = ["DE", "CH", "FR", "AT"]


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

    # Seed admin user
    await _ensure_admin_user(db)

    # Seed countries
    now_iso = datetime.now(timezone.utc).isoformat()
    for c in default_countries(now_iso):
        await db.countries.update_one(
            {"code": c["code"]},
            {"$setOnInsert": c},
            upsert=True,
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
    await db.categories.delete_many({"module": "vehicle", "slug.tr": "elektrikli"})
    for cat in vehicle_category_tree(now_iso):
        await db.categories.update_one(
            {"id": cat["id"]},
            {"$setOnInsert": cat},
            upsert=True,
        )

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

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
async def health_check(request: Request):
    db = request.app.state.db
    await db.command("ping")
    return {"status": "healthy", "supported_countries": SUPPORTED_COUNTRIES, "database": "mongo"}


@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    db = request.app.state.db

    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="User account is disabled")

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


@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return _user_to_response(current_user)


@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db

    users_total = await db.users.count_documents({})
    users_active = await db.users.count_documents({"is_active": True})

    # Minimal response compatible with Dashboard.js usage
    return {
        "users": {"total": users_total, "active": users_active},
        "countries": {"enabled": len(SUPPORTED_COUNTRIES)},
        "feature_flags": {"enabled": 0, "total": 0},
        "users_by_role": {
            "super_admin": await db.users.count_documents({"role": "super_admin"}),
            "country_admin": await db.users.count_documents({"role": "country_admin"}),
            "moderator": await db.users.count_documents({"role": "moderator"}),
            "support": await db.users.count_documents({"role": "support"}),
            "finance": await db.users.count_documents({"role": "finance"}),
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
    query: Dict = {}
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
async def list_categories(request: Request, module: str, current_user=Depends(get_current_user)):
    db = request.app.state.db
    docs = await db.categories.find({"module": module}, {"_id": 0}).to_list(length=500)
    # Stable ordering: sort_order then name
    docs.sort(key=lambda x: (x.get("sort_order", 0), x.get("slug", {}).get("tr", "")))
    return docs



@api_router.get("/countries")
async def list_countries(request: Request, current_user=Depends(get_current_user)):
    db = request.app.state.db
    docs = await db.countries.find({}, {"_id": 0}).to_list(length=200)
    docs.sort(key=lambda x: x.get("code", ""))
    return docs

 


@api_router.patch("/countries/{country_id}")
async def update_country(country_id: str, data: dict, request: Request, current_user=Depends(check_permissions(["super_admin", "country_admin"]))):
    db = request.app.state.db
    allowed = {"is_enabled", "default_currency", "default_language", "support_email"}
    payload = {k: v for k, v in data.items() if k in allowed}
    if not payload:
        return {"ok": True}

    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.countries.update_one({"id": country_id}, {"$set": payload})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Country not found")

    return {"ok": True}


# =====================
# Vehicle Master Data (File-Based) APIs
# =====================

@api_router.get("/v1/vehicle/makes")
async def public_vehicle_makes(country: str | None = None, request: Request = None):
    vm = request.app.state.vehicle_master
    items = [
        {
            "key": m["make_key"],
            "label": m["display_name"],
            "popular_rank": m.get("sort_order"),
        }
        for m in vm["makes"]
        if m.get("is_active", True)
    ]
    return {"version": vm["version"], "items": items}


@api_router.get("/v1/vehicle/models")
async def public_vehicle_models(make: str, country: str | None = None, request: Request = None):
    vm = request.app.state.vehicle_master
    models = vm["models_by_make"].get(make)
    if models is None:
        raise HTTPException(status_code=404, detail="Make not found")

    items = [
        {
            "key": m["model_key"],
            "label": m["display_name"],
            "year_from": m.get("year_from"),
            "year_to": m.get("year_to"),
            "popular_rank": None,
        }
        for m in models
        if m.get("is_active", True)
    ]

    return {"version": vm["version"], "make": make, "items": items}


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
    if listing.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Only draft can accept media")

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
    if listing.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Listing not draft")

    errs = validate_publish(listing, request.app.state.vehicle_master)
    if errs:
        # return normalized 422 payload for FE
        raise HTTPException(status_code=422, detail={"id": listing_id, "status": "draft", "validation_errors": errs, "next_actions": ["fix_form", "upload_media"]})

    listing = await set_vehicle_status(db, listing_id, "published")

    # simplistic slug
    v = listing.get("vehicle") or {}
    slug = f"{v.get('make_key','')}-{v.get('model_key','')}-{v.get('year','')}".strip('-')
    return {
        "id": listing_id,
        "status": "published",
        "validation_errors": [],
        "next_actions": ["view_detail"],
        "detail_url": f"/ilan/vasita/{listing_id}-{slug}",
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
        "contact_option_phone": False,
        "contact_option_message": True,
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
