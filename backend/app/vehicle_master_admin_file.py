import json
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from app.vehicle_master_file import (
    get_vehicle_master_dir,
    read_bundle_bytes,
    validate_master_data,
    compute_checksum,
    now_iso,
)


def _atomic_write(path: Path, content: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _ensure_dirs(data_dir: Path):
    (data_dir / "versions").mkdir(parents=True, exist_ok=True)
    (data_dir / "staging").mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)



def ensure_default_master_data(data_dir: Path):
    """Creates a minimal, valid file-based vehicle master dataset if missing.

    This is required for preview/dev pods where /data volume may start empty.
    """

    _ensure_dirs(data_dir)
    current_path = data_dir / "current.json"
    if current_path.exists():
        return

    version_id = "seed-v1"
    ver_dir = data_dir / "versions" / version_id
    ver_dir.mkdir(parents=True, exist_ok=True)

    makes = {
        "version": version_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "default-seed",
        "items": [
            {"make_key": "audi", "display_name": "Audi", "aliases": ["audi"], "is_active": True, "sort_order": 1},
            {"make_key": "bmw", "display_name": "BMW", "aliases": ["bmw"], "is_active": True, "sort_order": 2},
            {"make_key": "vw", "display_name": "Volkswagen", "aliases": ["volkswagen", "vw"], "is_active": True, "sort_order": 3},
        ],
    }
    makes["checksum"] = compute_checksum(makes)

    models = {
        "version": version_id,
        "generated_at": makes["generated_at"],
        "source": "default-seed",
        "items": [
            {"make_key": "audi", "model_key": "a3", "display_name": "A3", "aliases": ["a3"], "is_active": True, "year_from": 1996, "year_to": None},
            {"make_key": "audi", "model_key": "a4", "display_name": "A4", "aliases": ["a4"], "is_active": True, "year_from": 1994, "year_to": None},
            {"make_key": "bmw", "model_key": "3-series", "display_name": "3 Series", "aliases": ["3 series"], "is_active": True, "year_from": 1975, "year_to": None},
            {"make_key": "vw", "model_key": "golf", "display_name": "Golf", "aliases": ["golf"], "is_active": True, "year_from": 1974, "year_to": None},
        ],
    }
    models["checksum"] = compute_checksum(models)

    report = validate_master_data(makes, models)
    if not report.get("ok"):
        raise RuntimeError("Default vehicle master seed is invalid")

    (ver_dir / "makes.json").write_text(json.dumps(makes, ensure_ascii=False, indent=2), encoding="utf-8")
    (ver_dir / "models.json").write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
    (ver_dir / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "version": version_id,
        "generated_at": makes["generated_at"],
        "source": "default-seed",
        "checksum": makes["checksum"],
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "activated_by": "system",
    }
    (ver_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    current = {
        "active_version": version_id,
        "activated_at": manifest["activated_at"],
        "activated_by": manifest["activated_by"],
        "source": manifest["source"],
        "checksum": manifest["checksum"],
    }
    _atomic_write(current_path, json.dumps(current, ensure_ascii=False, indent=2))

    _append_jsonl(
        data_dir / "logs" / "audit.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "BOOTSTRAP_DEFAULT",
            "user_id": "system",
            "source": "default-seed",
            "version": version_id,
            "checksum": manifest["checksum"],
            "status": "OK",
            "diff_summary": report.get("summary", {}),
        },
    )


def _append_jsonl(log_path: Path, entry: dict):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)

    # simple rotation
    if log_path.stat().st_size > 20 * 1024 * 1024:
        rotated = log_path.with_name(log_path.name.replace(".jsonl", ".1.jsonl"))
        if rotated.exists():
            rotated.unlink()
        log_path.rename(rotated)


def _tail_jsonl(log_path: Path, n: int) -> list[dict]:
    if not log_path.exists():
        return []

    # naive read for v1 (files small)
    lines = log_path.read_text(encoding="utf-8").splitlines()[-n:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def validate_upload(filename: str, raw: bytes) -> dict:
    data_dir = get_vehicle_master_dir()
    _ensure_dirs(data_dir)

    makes_doc, models_doc = read_bundle_bytes(filename, raw)
    report = validate_master_data(makes_doc, models_doc)

    staging_id = hashlib.sha256((filename + now_iso()).encode("utf-8")).hexdigest()[:16]
    staging_dir = data_dir / "staging" / staging_id
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    (staging_dir / "makes.json").write_text(json.dumps(makes_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (staging_dir / "models.json").write_text(json.dumps(models_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (staging_dir / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        **report,
        "staging_id": staging_id,
    }


def activate_staging(staging_id: str, user_id: str, source: str = "admin-upload") -> dict:
    data_dir = get_vehicle_master_dir()
    _ensure_dirs(data_dir)

    staging_dir = data_dir / "staging" / staging_id
    if not staging_dir.exists():
        raise FileNotFoundError("staging not found")

    makes_doc = json.loads((staging_dir / "makes.json").read_text(encoding="utf-8"))
    models_doc = json.loads((staging_dir / "models.json").read_text(encoding="utf-8"))

    report = validate_master_data(makes_doc, models_doc)
    if not report["ok"]:
        raise ValueError("staging data no longer valid")

    version_id = makes_doc.get("version")
    if not version_id:
        raise ValueError("makes.json missing version")

    ver_dir = data_dir / "versions" / version_id
    if ver_dir.exists():
        raise FileExistsError("version already exists")

    ver_dir.mkdir(parents=True)

    (ver_dir / "makes.json").write_text(json.dumps(makes_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (ver_dir / "models.json").write_text(json.dumps(models_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    (ver_dir / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "version": version_id,
        "generated_at": makes_doc.get("generated_at"),
        "source": makes_doc.get("source") or source,
        "checksum": makes_doc.get("checksum"),
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "activated_by": user_id,
    }
    (ver_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    current = {
        "active_version": version_id,
        "activated_at": manifest["activated_at"],
        "activated_by": user_id,
        "source": manifest["source"],
        "checksum": manifest["checksum"],
    }

    _atomic_write(data_dir / "current.json", json.dumps(current, ensure_ascii=False, indent=2))

    _append_jsonl(
        data_dir / "logs" / "audit.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "IMPORT_ACTIVATE",
            "user_id": user_id,
            "source": manifest["source"],
            "version": version_id,
            "checksum": manifest["checksum"],
            "status": "OK",
            "diff_summary": report.get("summary", {}),
        },
    )

    return current


def rollback(user_id: str, target_version: str | None = None) -> dict:
    data_dir = get_vehicle_master_dir()
    _ensure_dirs(data_dir)

    current_path = data_dir / "current.json"
    if not current_path.exists():
        raise FileNotFoundError("current.json missing")
    current = json.loads(current_path.read_text(encoding="utf-8"))
    active = current.get("active_version")

    versions_dir = data_dir / "versions"
    versions = sorted([p.name for p in versions_dir.iterdir() if p.is_dir()])
    if not versions:
        raise RuntimeError("no versions")

    if target_version:
        if target_version not in versions:
            raise FileNotFoundError("target version not found")
        new_version = target_version
    else:
        if active not in versions:
            raise RuntimeError("active version not in versions")
        idx = versions.index(active)
        if idx == 0:
            raise RuntimeError("no previous version")
        new_version = versions[idx - 1]

    manifest_path = versions_dir / new_version / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    new_current = {
        "active_version": new_version,
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "activated_by": user_id,
        "source": manifest.get("source"),
        "checksum": manifest.get("checksum"),
    }

    _atomic_write(data_dir / "current.json", json.dumps(new_current, ensure_ascii=False, indent=2))

    _append_jsonl(
        data_dir / "logs" / "audit.jsonl",
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "ROLLBACK",
            "user_id": user_id,
            "source": manifest.get("source"),
            "version": new_version,
            "checksum": manifest.get("checksum"),
            "status": "OK",
            "diff_summary": {},
        },
    )

    return new_current


def get_status() -> dict:
    data_dir = get_vehicle_master_dir()
    current_path = data_dir / "current.json"
    current = json.loads(current_path.read_text(encoding="utf-8")) if current_path.exists() else None

    audit = _tail_jsonl(data_dir / "logs" / "audit.jsonl", 5)
    audit.reverse()

    return {"current": current, "recent_jobs": audit}
