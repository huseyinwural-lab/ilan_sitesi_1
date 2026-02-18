import uuid
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_vehicle_listing(db, payload: dict, user: dict) -> dict:
    listing_id = str(uuid.uuid4())
    doc = {
        "id": listing_id,
        "type": "vehicle",
        "status": "draft",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "created_by": user.get("id"),
        "country": payload.get("country"),
        "category_key": payload.get("category_key"),
        "vehicle": {
            "make_key": payload.get("make_key"),
            "model_key": payload.get("model_key"),
            "year": payload.get("year"),
            "trim_key": payload.get("trim_key"),
        },
        "attributes": {
            "mileage_km": payload.get("mileage_km"),
            "price_eur": payload.get("price_eur"),
            "fuel_type": payload.get("fuel_type"),
            "transmission": payload.get("transmission"),
            "condition": payload.get("condition"),
            "body_type": payload.get("body_type"),
            "drivetrain": payload.get("drivetrain"),
            "power_hp": payload.get("power_hp"),
            "engine_cc": payload.get("engine_cc"),
        },
        "media": [],
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
