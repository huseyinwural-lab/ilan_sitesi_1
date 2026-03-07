#!/usr/bin/env python3
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.environ.get("ARTIFACT_ROOT", str(ROOT_DIR / "release-artifacts")))
MAX_RELEASES = int(os.environ.get("MAX_RELEASES", "20"))
TRIGGER_SOURCE = os.environ.get("TRIGGER_SOURCE", "manual")
ACTIVE_RELEASE_ID = os.environ.get("ACTIVE_RELEASE_ID", "").strip()
ROLLBACK_RELEASE_ID = os.environ.get("ROLLBACK_RELEASE_ID", "").strip()


@dataclass
class ReleaseEntry:
    path: Path
    release_id: str
    created_at: Optional[datetime]
    is_active: bool
    is_rollback_candidate: bool
    retention_locked: bool
    has_valid_meta: bool
    meta: dict


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


def _log_cleanup_event(*, deleted_release_id: str, remaining_release_count: int) -> None:
    payload = {
        "deleted_release_id": deleted_release_id,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "trigger_source": TRIGGER_SOURCE,
        "remaining_release_count": remaining_release_count,
    }
    print(json.dumps(payload, ensure_ascii=False))


def _warn(message: str, extra: Optional[dict] = None) -> None:
    payload = {
        "level": "warning",
        "trigger_source": TRIGGER_SOURCE,
        "message": message,
    }
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))


def _collect_entries() -> list[ReleaseEntry]:
    if not ARTIFACT_ROOT.exists():
        return []

    entries: list[ReleaseEntry] = []
    for child in sorted([item for item in ARTIFACT_ROOT.iterdir() if item.is_dir()]):
        meta_path = child / "release_meta.json"
        if not meta_path.exists():
            _warn("release_meta_missing_fail_safe_protected", {"release_path": str(child)})
            entries.append(
                ReleaseEntry(
                    path=child,
                    release_id=child.name,
                    created_at=None,
                    is_active=False,
                    is_rollback_candidate=False,
                    retention_locked=True,
                    has_valid_meta=False,
                    meta={},
                )
            )
            continue

        try:
            raw_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            _warn("release_meta_invalid_fail_safe_protected", {"release_path": str(child)})
            entries.append(
                ReleaseEntry(
                    path=child,
                    release_id=child.name,
                    created_at=None,
                    is_active=False,
                    is_rollback_candidate=False,
                    retention_locked=True,
                    has_valid_meta=False,
                    meta={},
                )
            )
            continue

        release_id = str(raw_meta.get("release_id") or child.name)
        created_at = _parse_dt(raw_meta.get("created_at"))
        is_active = bool(raw_meta.get("is_active", False)) or (ACTIVE_RELEASE_ID and release_id == ACTIVE_RELEASE_ID)
        is_rollback_candidate = bool(raw_meta.get("is_rollback_candidate", False)) or (
            ROLLBACK_RELEASE_ID and release_id == ROLLBACK_RELEASE_ID
        )
        retention_locked = bool(raw_meta.get("retention_locked", False))

        entries.append(
            ReleaseEntry(
                path=child,
                release_id=release_id,
                created_at=created_at,
                is_active=is_active,
                is_rollback_candidate=is_rollback_candidate,
                retention_locked=retention_locked,
                has_valid_meta=True,
                meta=raw_meta,
            )
        )

    return entries


def main() -> None:
    entries = _collect_entries()
    if len(entries) <= MAX_RELEASES:
        print(json.dumps({
            "message": "cleanup_not_required",
            "total_releases": len(entries),
            "max_releases": MAX_RELEASES,
            "trigger_source": TRIGGER_SOURCE,
        }, ensure_ascii=False))
        return

    protected_ids = {
        entry.release_id
        for entry in entries
        if entry.is_active or entry.is_rollback_candidate or entry.retention_locked or not entry.has_valid_meta
    }

    deletable_entries = [
        entry
        for entry in entries
        if entry.release_id not in protected_ids
    ]

    deletable_entries.sort(key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc))

    remaining = len(entries)
    for entry in deletable_entries:
        if remaining <= MAX_RELEASES:
            break
        shutil.rmtree(entry.path, ignore_errors=False)
        remaining -= 1
        _log_cleanup_event(
            deleted_release_id=entry.release_id,
            remaining_release_count=remaining,
        )

    print(json.dumps({
        "message": "cleanup_finished",
        "trigger_source": TRIGGER_SOURCE,
        "remaining_release_count": remaining,
        "max_releases": MAX_RELEASES,
        "protected_release_count": len(protected_ids),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
