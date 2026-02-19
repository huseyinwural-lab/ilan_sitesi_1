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


def validate_required_attributes(required_keys: list[str], attrs: dict) -> list[dict]:
    errs = []
    for k in required_keys:
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


def validate_publish(
    listing: dict,
    vehicle_master: dict,
    required_attribute_keys: list[str] | None = None,
    supported_countries: set | None = None,
) -> list[dict]:
    errs: list[dict] = []

    country = listing.get("country")
    supported = supported_countries or SUPPORTED_COUNTRIES
    if not country or country not in supported:
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
    if required_attribute_keys:
        errs.extend(validate_required_attributes(required_attribute_keys, attrs))

    errs.extend(enforce_media_policy(listing.get("media") or []))

    return errs


def validate_listing_schema(listing: dict, schema: dict) -> list[dict]:
    errs: list[dict] = []
    core = schema.get("core_fields") or {}
    title_cfg = core.get("title") or {}
    desc_cfg = core.get("description") or {}
    price_cfg = core.get("price") or {}

    title = (listing.get("title") or "").strip()
    if title_cfg.get("required") and not title:
        errs.append(_error("title", "REQUIRED", title_cfg.get("messages", {}).get("required", "Başlık zorunlu")))
    if title:
        min_len = title_cfg.get("min")
        max_len = title_cfg.get("max")
        if min_len and len(title) < min_len:
            errs.append(_error("title", "MIN", title_cfg.get("messages", {}).get("min", "Başlık çok kısa")))
        if max_len and len(title) > max_len:
            errs.append(_error("title", "MAX", title_cfg.get("messages", {}).get("max", "Başlık çok uzun")))

    description = (listing.get("description") or "").strip()
    if desc_cfg.get("required") and not description:
        errs.append(_error("description", "REQUIRED", desc_cfg.get("messages", {}).get("required", "Açıklama zorunlu")))
    if description:
        min_len = desc_cfg.get("min")
        max_len = desc_cfg.get("max")
        if min_len and len(description) < min_len:
            errs.append(_error("description", "MIN", desc_cfg.get("messages", {}).get("min", "Açıklama çok kısa")))
        if max_len and len(description) > max_len:
            errs.append(_error("description", "MAX", desc_cfg.get("messages", {}).get("max", "Açıklama çok uzun")))

    price_data = listing.get("price") or {}
    price_amount = price_data.get("amount")
    if price_amount is None:
        price_amount = (listing.get("attributes") or {}).get("price_eur")
    if price_cfg.get("required") and (price_amount is None or price_amount == ""):
        errs.append(_error("price", "REQUIRED", price_cfg.get("messages", {}).get("required", "Fiyat zorunlu")))
    if price_amount is not None:
        try:
            price_amount = float(price_amount)
        except (TypeError, ValueError):
            errs.append(_error("price", "NUMERIC", price_cfg.get("messages", {}).get("numeric", "Fiyat sayısal olmalı")))
        else:
            range_cfg = price_cfg.get("range") or {}
            if range_cfg.get("min") is not None and price_amount < range_cfg.get("min"):
                errs.append(_error("price", "RANGE", price_cfg.get("messages", {}).get("range", "Fiyat aralık dışında")))
            if range_cfg.get("max") is not None and price_amount > range_cfg.get("max"):
                errs.append(_error("price", "RANGE", price_cfg.get("messages", {}).get("range", "Fiyat aralık dışında")))
            decimal_places = price_cfg.get("decimal_places")
            if decimal_places == 0 and price_amount % 1 != 0:
                errs.append(_error("price", "DECIMAL", price_cfg.get("messages", {}).get("numeric", "Fiyat ondalık içeremez")))

    attrs = listing.get("attributes") or {}
    for field in schema.get("dynamic_fields", []):
        key = field.get("key")
        if not key:
            continue
        value = attrs.get(key)
        if field.get("required") and (value is None or value == ""):
            errs.append(_error(key, "REQUIRED", field.get("messages", {}).get("required", f"{key} zorunlu")))
            continue
        if value is not None and value != "":
            options = field.get("options") or []
            if options and value not in options:
                errs.append(_error(key, "INVALID", field.get("messages", {}).get("invalid", f"{key} geçersiz")))

    detail_groups = listing.get("detail_groups") or {}
    for group in schema.get("detail_groups", []):
        group_id = group.get("id") or group.get("title")
        selections = detail_groups.get(group_id)
        if group.get("required") and not selections:
            errs.append(_error(group_id, "REQUIRED", group.get("messages", {}).get("required", "Detay grubu zorunlu")))
            continue
        if selections:
            options = group.get("options") or []
            invalid = [s for s in selections if s not in options]
            if invalid:
                errs.append(_error(group_id, "INVALID", group.get("messages", {}).get("invalid", "Detay seçimi geçersiz")))

    return errs
