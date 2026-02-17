from __future__ import annotations

from typing import Any


SUPPORTED_COUNTRIES = {"DE", "CH", "FR", "AT"}

SEGMENT_REQUIRED_BASE = {
    "mileage_km",
    "price_eur",
    "condition",
    "fuel_type",
    "transmission",
}

SEGMENT_EXTRA_REQUIRED = {
    "motosiklet": {"engine_cc"},
    "ticari-arac": {"body_type"},
}


def _error(field: str, code: str, message: str) -> dict:
    return {"field": field, "code": code, "message": message}


def validate_segment_required(category_key: str, attrs: dict) -> list[dict]:
    required = set(SEGMENT_REQUIRED_BASE)
    required |= SEGMENT_EXTRA_REQUIRED.get(category_key, set())

    errs = []
    for k in required:
        v = attrs.get(k)
        if v is None or v == "":
            errs.append(_error(k, "REQUIRED", f"{k} zorunlu"))
    return errs


def enforce_make_model(vehicle_master: dict, make_key: str, model_key: str) -> list[dict]:
    errs = []

    makes = {m["make_key"]: m for m in vehicle_master.get("makes", [])}
    make = makes.get(make_key)
    if not make:
        return [_error("make_key", "MAKE_NOT_FOUND", "make_key master data’da yok")]
    if not make.get("is_active", True):
        errs.append(_error("make_key", "MAKE_INACTIVE", "make_key pasif"))

    models = vehicle_master.get("models_by_make", {}).get(make_key, [])
    model = next((m for m in models if m.get("model_key") == model_key), None)
    if not model:
        return errs + [_error("model_key", "MODEL_NOT_FOUND", "model_key make altında yok")]
    if not model.get("is_active", True):
        errs.append(_error("model_key", "MODEL_INACTIVE", "model_key pasif"))

    return errs


def enforce_media_policy(media: list[dict]) -> list[dict]:
    errs = []
    if len(media) < 3:
        errs.append(_error("media", "MIN_PHOTOS", "En az 3 fotoğraf zorunlu"))
        return errs

    for m in media:
        w = m.get("width")
        h = m.get("height")
        if not isinstance(w, int) or not isinstance(h, int) or w < 800 or h < 600:
            errs.append(_error("media", "MIN_RESOLUTION", "Minimum çözünürlük 800x600"))
            break

    return errs


def validate_publish(listing: dict, vehicle_master: dict) -> list[dict]:
    errs: list[dict] = []

    country = listing.get("country")
    if not country or country not in SUPPORTED_COUNTRIES:
        errs.append(_error("country", "COUNTRY_INVALID", "country zorunlu (DE/CH/FR/AT)"))

    category_key = listing.get("category_key")
    if not category_key:
        errs.append(_error("category_key", "REQUIRED", "category_key zorunlu"))

    vehicle = listing.get("vehicle") or {}
    make_key = vehicle.get("make_key")
    model_key = vehicle.get("model_key")
    year = vehicle.get("year")

    if not make_key:
        errs.append(_error("make_key", "REQUIRED", "make_key zorunlu"))
    if not model_key:
        errs.append(_error("model_key", "REQUIRED", "model_key zorunlu"))
    if not year:
        errs.append(_error("year", "REQUIRED", "year zorunlu"))

    if make_key and model_key:
        errs.extend(enforce_make_model(vehicle_master, make_key, model_key))

    attrs = listing.get("attributes") or {}
    if category_key:
        errs.extend(validate_segment_required(category_key, attrs))

    errs.extend(enforce_media_policy(listing.get("media") or []))

    return errs
