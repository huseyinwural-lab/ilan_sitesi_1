#!/usr/bin/env python3
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = Path(os.environ.get("ARTIFACT_ROOT", str(ROOT_DIR / "release-artifacts")))
REPORT_PATH = Path(os.environ.get("REPORT_PATH", str(ROOT_DIR / "reports" / "artifact_integrity_report.json")))

REQUIRED_FIELDS = {
    "release_id",
    "created_at",
    "build_commit",
    "artifact_hash",
    "is_active",
    "is_rollback_candidate",
}


def _compute_artifact_hash(release_dir: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted([item for item in release_dir.rglob("*") if item.is_file()]):
        if file_path.name == "release_meta.json":
            continue
        rel_path = file_path.relative_to(release_dir).as_posix()
        digest.update(rel_path.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(file_path.read_bytes())
        digest.update(b"\x01")
    return digest.hexdigest()


def main() -> None:
    scan_started_at = datetime.now(timezone.utc)
    dirs = sorted([item for item in ARTIFACT_ROOT.iterdir() if item.is_dir()]) if ARTIFACT_ROOT.exists() else []

    valid_artifacts = []
    missing_metadata = []
    corrupted_artifacts = []
    items = []

    for release_dir in dirs:
        meta_path = release_dir / "release_meta.json"
        item = {
            "release_folder": release_dir.name,
            "release_id": release_dir.name,
            "meta_exists": meta_path.exists(),
            "missing_required_fields": [],
            "hash_expected": None,
            "hash_actual": None,
            "hash_match": None,
            "status": "valid",
        }

        if not meta_path.exists():
            item["status"] = "missing_metadata"
            missing_metadata.append(item)
            items.append(item)
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            item["status"] = "missing_metadata"
            missing_metadata.append(item)
            items.append(item)
            continue

        if isinstance(meta, dict):
            item["release_id"] = str(meta.get("release_id") or release_dir.name)
            missing_fields = sorted([field for field in REQUIRED_FIELDS if field not in meta])
            if missing_fields:
                item["missing_required_fields"] = missing_fields
                item["status"] = "missing_metadata"
                missing_metadata.append(item)
                items.append(item)
                continue
            expected_hash = str(meta.get("artifact_hash") or "").strip()
            actual_hash = _compute_artifact_hash(release_dir)
            item["hash_expected"] = expected_hash
            item["hash_actual"] = actual_hash
            item["hash_match"] = bool(expected_hash and expected_hash == actual_hash)
            if not item["hash_match"]:
                item["status"] = "corrupted"
                corrupted_artifacts.append(item)
            else:
                valid_artifacts.append(item)
            items.append(item)
            continue

        item["status"] = "missing_metadata"
        missing_metadata.append(item)
        items.append(item)

    report = {
        "generated_at": scan_started_at.isoformat(),
        "artifact_root": str(ARTIFACT_ROOT),
        "required_fields": sorted(REQUIRED_FIELDS),
        "summary": {
            "total_artifacts": len(items),
            "valid_artifacts": len(valid_artifacts),
            "missing_metadata": len(missing_metadata),
            "corrupted_artifacts": len(corrupted_artifacts),
        },
        "valid_artifacts": valid_artifacts,
        "missing_metadata": missing_metadata,
        "corrupted_artifacts": corrupted_artifacts,
        "items": items,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "report_path": str(REPORT_PATH), "summary": report["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
