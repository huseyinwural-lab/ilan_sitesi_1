#!/usr/bin/env python3
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.environ.get("ARTIFACT_ROOT", str(ROOT_DIR / "release-artifacts")))
RETENTION_WINDOW_DAYS = int(os.environ.get("RETENTION_WINDOW_DAYS", "21"))
DRY_RUN = str(os.environ.get("DRY_RUN", "true")).strip().lower() in {"1", "true", "yes", "y"}
TRIGGER_SOURCE = os.environ.get("TRIGGER_SOURCE", "manual")
ACTIVE_RELEASE_ID = os.environ.get("ACTIVE_RELEASE_ID", "").strip()
ROLLBACK_RELEASE_ID = os.environ.get("ROLLBACK_RELEASE_ID", "").strip()


def _parse_dt(raw: Optional[str]) -> Optional[datetime]:
    value = str(raw or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_meta(release_dir: Path) -> tuple[Optional[dict], Optional[str]]:
    meta_path = release_dir / "release_meta.json"
    if not meta_path.exists():
        return None, "MISSING_METADATA"
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None, "INVALID_METADATA"
    if not isinstance(raw, dict):
        return None, "INVALID_METADATA"
    return raw, None


def _analyze_release(release_dir: Path, now: datetime) -> dict:
    meta, meta_error = _load_meta(release_dir)
    release_id = str((meta or {}).get("release_id") or release_dir.name)
    created_at = _parse_dt((meta or {}).get("created_at")) if meta else None
    if created_at is None:
        try:
            created_at = datetime.fromtimestamp(release_dir.stat().st_mtime, tz=timezone.utc)
        except Exception:
            created_at = None

    is_active = bool((meta or {}).get("is_active", False)) or (ACTIVE_RELEASE_ID and release_id == ACTIVE_RELEASE_ID)
    is_rollback_candidate = bool((meta or {}).get("is_rollback_candidate", False)) or (
        ROLLBACK_RELEASE_ID and release_id == ROLLBACK_RELEASE_ID
    )
    retention_locked = bool((meta or {}).get("retention_locked", False))

    reason = "WITHIN_RETENTION_WINDOW"
    action = "KEEP"
    if is_active:
        reason = "ACTIVE_RELEASE"
    elif is_rollback_candidate:
        reason = "ROLLBACK_CANDIDATE"
    elif retention_locked:
        reason = "RETENTION_LOCKED"
    elif meta_error == "MISSING_METADATA":
        reason = "MISSING_METADATA"
    elif meta_error == "INVALID_METADATA":
        reason = "INVALID_METADATA"
    elif created_at is None:
        reason = "MISSING_CREATED_AT"
    else:
        cutoff = now - timedelta(days=max(1, RETENTION_WINDOW_DAYS))
        if created_at < cutoff:
            action = "DELETE"
            reason = "OUTSIDE_RETENTION_WINDOW"

    return {
        "release_dir": str(release_dir),
        "release_folder": release_dir.name,
        "release_id": release_id,
        "created_at": created_at.isoformat() if created_at else None,
        "is_active": bool(is_active),
        "is_rollback_candidate": bool(is_rollback_candidate),
        "retention_locked": bool(retention_locked),
        "action": action,
        "reason": reason,
        "meta_error": meta_error,
    }


def main() -> None:
    now = datetime.now(timezone.utc)
    dirs = sorted([item for item in ARTIFACT_ROOT.iterdir() if item.is_dir()]) if ARTIFACT_ROOT.exists() else []
    items = [_analyze_release(item, now) for item in dirs]

    keep_items = [item for item in items if item.get("action") == "KEEP"]
    delete_items = [item for item in items if item.get("action") == "DELETE"]

    output = {
        "trigger_source": TRIGGER_SOURCE,
        "dry_run": bool(DRY_RUN),
        "generated_at": now.isoformat(),
        "retention_window_days": RETENTION_WINDOW_DAYS,
        "total_artifacts": len(items),
        "protected_count": len(keep_items),
        "delete_candidates_count": len(delete_items),
        "keep": keep_items,
        "delete": delete_items,
    }

    if not DRY_RUN:
        deleted_ids = []
        for item in delete_items:
            target = Path(str(item.get("release_dir"))).resolve()
            if not str(target).startswith(str(ARTIFACT_ROOT.resolve())):
                continue
            if target.exists() and target.is_dir():
                shutil.rmtree(target, ignore_errors=False)
                deleted_ids.append(str(item.get("release_id") or target.name))
        output["deleted_artifacts"] = deleted_ids
        output["deleted_count"] = len(deleted_ids)

    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
