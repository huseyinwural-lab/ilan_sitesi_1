import json
import os
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_vehicle_master_dir() -> Path:
    return Path(os.environ.get("VEHICLE_MASTER_DATA_DIR", "/data/vehicle_master"))


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_checksum(obj: dict) -> str:
    # checksum excludes the `checksum` field itself
    cloned = json.loads(json.dumps(obj))
    cloned.pop("checksum", None)
    payload = _canonical_json(cloned).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _require_fields(obj: dict, fields: list[str], where: str):
    for f in fields:
        if f not in obj:
            raise ValueError(f"Missing required field '{f}' in {where}")


def validate_file_schema(doc: dict, file_type: str):
    _require_fields(doc, ["version", "generated_at", "source", "checksum", "items"], file_type)
    if not isinstance(doc["items"], list):
        raise ValueError(f"{file_type}.items must be a list")

    expected = compute_checksum(doc)
    if doc.get("checksum") != expected:
        raise ValueError(f"Checksum mismatch for {file_type}: expected {expected} got {doc.get('checksum')}")


def _is_kebab_ascii(s: str) -> bool:
    if not s or s.lower() != s:
        return False
    for ch in s:
        if ch.isalnum() or ch == "-":
            continue
        return False
    return True


def validate_master_data(makes_doc: dict, models_doc: dict) -> dict:
    """Strict validation + dedupe rules.

    Returns: validation_report dict.
    """
    errors: list[dict] = []

    try:
        validate_file_schema(makes_doc, "makes")
    except Exception as e:
        errors.append({"code": "INVALID_MAKES_SCHEMA", "message": str(e)})

    try:
        validate_file_schema(models_doc, "models")
    except Exception as e:
        errors.append({"code": "INVALID_MODELS_SCHEMA", "message": str(e)})

    if errors:
        return {"ok": False, "errors": errors, "summary": {}}

    make_keys: set[str] = set()
    make_aliases_global: set[str] = set()

    for item in makes_doc["items"]:
        for f in ["make_key", "display_name", "aliases", "is_active", "sort_order"]:
            if f not in item:
                errors.append({"code": "MAKES_MISSING_FIELD", "message": f"Missing {f} for make"})
                continue
        mk = item.get("make_key")
        if not isinstance(mk, str) or not _is_kebab_ascii(mk):
            errors.append({"code": "INVALID_MAKE_KEY", "message": f"Invalid make_key: {mk}"})
            continue
        if mk in make_keys:
            errors.append({"code": "DUPLICATE_MAKE_KEY", "message": f"Duplicate make_key: {mk}"})
        make_keys.add(mk)

        aliases = item.get("aliases") or []
        if not isinstance(aliases, list):
            errors.append({"code": "INVALID_ALIASES", "message": f"aliases must be list for make {mk}"})
            continue
        norm_aliases = set()
        for a in aliases:
            if not isinstance(a, str):
                continue
            na = a.strip().lower()
            if not na:
                continue
            if na in norm_aliases:
                errors.append({"code": "DUPLICATE_ALIAS", "message": f"Duplicate alias in make {mk}: {a}"})
            norm_aliases.add(na)

            if na in make_aliases_global:
                errors.append({"code": "ALIAS_COLLISION", "message": f"Alias collision across makes: {a}"})
            make_aliases_global.add(na)

    model_keys_by_make: dict[str, set[str]] = {}
    model_aliases_global: set[str] = set()

    for item in models_doc["items"]:
        for f in ["make_key", "model_key", "display_name", "aliases", "is_active"]:
            if f not in item:
                errors.append({"code": "MODELS_MISSING_FIELD", "message": f"Missing {f} for model"})
                continue

        mk = item.get("make_key")
        mdlk = item.get("model_key")

        if mk not in make_keys:
            errors.append({"code": "UNKNOWN_MAKE_KEY", "message": f"Model references unknown make_key: {mk}"})

        if not isinstance(mdlk, str) or not _is_kebab_ascii(mdlk):
            errors.append({"code": "INVALID_MODEL_KEY", "message": f"Invalid model_key: {mdlk}"})
            continue

        model_keys_by_make.setdefault(mk, set())
        if mdlk in model_keys_by_make[mk]:
            errors.append({"code": "DUPLICATE_MODEL_KEY", "message": f"Duplicate model_key under make {mk}: {mdlk}"})
        model_keys_by_make[mk].add(mdlk)

        aliases = item.get("aliases") or []
        if not isinstance(aliases, list):
            errors.append({"code": "INVALID_ALIASES", "message": f"aliases must be list for model {mk}/{mdlk}"})
            continue
        norm_aliases = set()
        for a in aliases:
            if not isinstance(a, str):
                continue
            na = a.strip().lower()
            if not na:
                continue
            if na in norm_aliases:
                errors.append({"code": "DUPLICATE_ALIAS", "message": f"Duplicate alias in model {mk}/{mdlk}: {a}"})
            norm_aliases.add(na)

            if na in model_aliases_global:
                errors.append({"code": "ALIAS_COLLISION", "message": f"Alias collision across models: {a}"})
            model_aliases_global.add(na)

        yf = item.get("year_from")
        yt = item.get("year_to")
        if yf is not None and (not isinstance(yf, int) or yf < 1885 or yf > 2100):
            errors.append({"code": "INVALID_YEAR", "message": f"Invalid year_from for {mk}/{mdlk}: {yf}"})
        if yt is not None and (not isinstance(yt, int) or yt < 1885 or yt > 2100):
            errors.append({"code": "INVALID_YEAR", "message": f"Invalid year_to for {mk}/{mdlk}: {yt}"})
        if isinstance(yf, int) and isinstance(yt, int) and yf > yt:
            errors.append({"code": "INVALID_YEAR_RANGE", "message": f"year_from > year_to for {mk}/{mdlk}"})

    summary = {
        "make_count": len(makes_doc["items"]),
        "model_count": len(models_doc["items"]),
        "inactive_count": sum(1 for m in makes_doc["items"] if not m.get("is_active", True))
        + sum(1 for m in models_doc["items"] if not m.get("is_active", True)),
        "alias_count": len(make_aliases_global) + len(model_aliases_global),
    }

    return {
        "ok": len(errors) == 0,
        "version": makes_doc.get("version"),
        "errors": errors,
        "summary": summary,
    }


def read_bundle_bytes(filename: str, raw: bytes) -> tuple[dict, dict]:
    """Return (makes_doc, models_doc)."""
    if filename.lower().endswith(".zip"):
        # Use ZipFile on bytes (no FS) - python expects file-like
        import io as _io

        zf = zipfile.ZipFile(_io.BytesIO(raw))
        names = set(zf.namelist())
        if "makes.json" not in names or "models.json" not in names:
            raise ValueError("ZIP must contain makes.json and models.json")
        makes_doc = json.loads(zf.read("makes.json").decode("utf-8"))
        models_doc = json.loads(zf.read("models.json").decode("utf-8"))
        return makes_doc, models_doc

    # single bundle
    bundle = json.loads(raw.decode("utf-8"))
    if not isinstance(bundle, dict) or "makes" not in bundle or "models" not in bundle:
        raise ValueError("Bundle JSON must include 'makes' and 'models'")
    return bundle["makes"], bundle["models"]


def load_current_master(data_dir: Path) -> dict:
    current_path = data_dir / "current.json"
    if not current_path.exists():
        raise RuntimeError(f"Missing current.json in {data_dir}")

    current = json.loads(current_path.read_text(encoding="utf-8"))
    active_version = current.get("active_version")
    if not active_version:
        raise RuntimeError("current.json missing active_version")

    ver_dir = data_dir / "versions" / active_version
    makes_path = ver_dir / "makes.json"
    models_path = ver_dir / "models.json"
    if not makes_path.exists() or not models_path.exists():
        raise RuntimeError(f"Active version files missing: {ver_dir}")

    makes_doc = json.loads(makes_path.read_text(encoding="utf-8"))
    models_doc = json.loads(models_path.read_text(encoding="utf-8"))

    report = validate_master_data(makes_doc, models_doc)
    if not report["ok"]:
        raise RuntimeError(f"Active master data is invalid: {report['errors'][:3]}")

    makes = sorted(
        makes_doc["items"],
        key=lambda x: x.get("sort_order", 0),
    )
    models_by_make: dict[str, list[dict]] = {}
    for m in models_doc["items"]:
        models_by_make.setdefault(m["make_key"], []).append(m)
    for mk in models_by_make:
        models_by_make[mk].sort(key=lambda x: x.get("display_name", ""))

    return {
        "version": active_version,
        "current": current,
        "makes": makes,
        "models_by_make": models_by_make,
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
