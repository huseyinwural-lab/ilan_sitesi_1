import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_vehicle_listing(db, payload: dict, user: dict) -> dict:
    listing_id = str(uuid.uuid4())
    core_fields = payload.get("core_fields") or {}
    price_payload = core_fields.get("price") if isinstance(core_fields, dict) else None
    price_payload = price_payload or payload.get("price") or {}
    title = (core_fields.get("title") or payload.get("title") or "").strip()
    description = (core_fields.get("description") or payload.get("description") or "").strip()
    price_amount = price_payload.get("amount") if isinstance(price_payload, dict) else None
    hourly_rate = price_payload.get("hourly_rate") if isinstance(price_payload, dict) else None
    price_type = (price_payload.get("price_type") if isinstance(price_payload, dict) else None) or ("HOURLY" if hourly_rate else "FIXED")

    if price_type == "HOURLY":
        price_amount = None
    if price_amount is None:
        price_amount = payload.get("price_eur")
    if price_type != "HOURLY":
        hourly_rate = None

    attributes = {
        "mileage_km": payload.get("mileage_km"),
        "price_eur": price_amount,
        "fuel_type": payload.get("fuel_type"),
        "transmission": payload.get("transmission"),
        "condition": payload.get("condition"),
        "body_type": payload.get("body_type"),
        "drivetrain": payload.get("drivetrain"),
        "power_hp": payload.get("power_hp"),
        "engine_cc": payload.get("engine_cc"),
    }
    dynamic_fields = payload.get("dynamic_fields") or {}
    if isinstance(dynamic_fields, dict):
        attributes.update(dynamic_fields)
    doc = {
        "id": listing_id,
        "type": "vehicle",
        "status": "draft",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "created_by": user.get("id"),
        "country": payload.get("country"),
        "category_id": payload.get("category_id"),
        "category_key": payload.get("category_key"),
        "vehicle": {
            "make_key": payload.get("make_key"),
            "model_key": payload.get("model_key"),
            "year": payload.get("year"),
            "trim_key": payload.get("trim_key"),
        },
        "attributes": attributes,
        "media": [],
        "core_fields": core_fields,
        "title": title,
        "title_lower": title.lower() if title else None,
        "description": description,
        "price": {
            "amount": price_amount,
            "hourly_rate": hourly_rate,
            "price_type": price_type,
            "currency_primary": price_payload.get("currency_primary"),
            "currency_secondary": price_payload.get("currency_secondary"),
            "secondary_amount": price_payload.get("secondary_amount"),
            "decimal_places": price_payload.get("decimal_places"),
        },
        "detail_groups": payload.get("detail_groups") or {},
        "modules": payload.get("modules") or {},
        "payment_options": payload.get("payment_options") or {},
    }

    extra_attrs = payload.get("attributes") or {}
    if isinstance(extra_attrs, dict):
        doc["attributes"].update(extra_attrs)

    await db.vehicle_listings.insert_one(doc)
    return doc


async def get_vehicle_listing(db, listing_id: str) -> dict | None:
    return await db.vehicle_listings.find_one({"id": listing_id}, {"_id": 0})


async def add_media(db, listing_id: str, media_item: dict) -> list[dict]:
    await db.vehicle_listings.update_one(
        {"id": listing_id},
        {
            "$push": {"media": media_item},
            "$set": {"updated_at": now_iso()},
        },
    )
    doc = await get_vehicle_listing(db, listing_id)
    return doc.get("media", []) if doc else []


async def set_status(db, listing_id: str, status: str) -> dict | None:
    await db.vehicle_listings.update_one(
        {"id": listing_id},
        {"$set": {"status": status, "updated_at": now_iso()}},
    )
    return await get_vehicle_listing(db, listing_id)
