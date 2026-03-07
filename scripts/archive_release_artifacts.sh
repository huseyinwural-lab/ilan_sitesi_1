#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELEASE_ID="${RELEASE_ID:-release-$(date +%Y%m%d-%H%M)}"
RELEASE_DATE="${RELEASE_DATE:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
VALIDATED_LOCALES="${VALIDATED_LOCALES:-TR,DE,FR}"
PRESET_BATCH_SIZE="${PRESET_BATCH_SIZE:-100}"
VALIDATED_BY="${VALIDATED_BY:-${GITHUB_ACTOR:-system}}"
IS_ACTIVE="${IS_ACTIVE:-false}"
IS_ROLLBACK_CANDIDATE="${IS_ROLLBACK_CANDIDATE:-false}"
RETENTION_LOCKED="${RETENTION_LOCKED:-false}"
TRIGGER_SOURCE="${TRIGGER_SOURCE:-ci}"
MAX_RELEASES="${MAX_RELEASES:-20}"

SOURCE_PUBLISH_REPORT="${SOURCE_PUBLISH_REPORT:-${ROOT_DIR}/publish_validation_report.md}"
SOURCE_PRESET_REPORT="${SOURCE_PRESET_REPORT:-${ROOT_DIR}/preset_stress_test_report.md}"

TARGET_DIR="${ROOT_DIR}/release-artifacts/${RELEASE_ID}"
mkdir -p "${TARGET_DIR}"

if [[ -f "${SOURCE_PUBLISH_REPORT}" ]]; then
  cp "${SOURCE_PUBLISH_REPORT}" "${TARGET_DIR}/publish_validation_report.md"
fi

if [[ -f "${SOURCE_PRESET_REPORT}" ]]; then
  cp "${SOURCE_PRESET_REPORT}" "${TARGET_DIR}/preset_stress_test_report.md"
fi

python3 - <<PY
import json
from pathlib import Path

target = Path(${TARGET_DIR@Q}) / "release_meta.json"
payload = {
    "release_id": ${RELEASE_ID@Q},
    "created_at": ${RELEASE_DATE@Q},
    "is_active": str(${IS_ACTIVE@Q}).lower() == "true",
    "is_rollback_candidate": str(${IS_ROLLBACK_CANDIDATE@Q}).lower() == "true",
    "retention_locked": str(${RETENTION_LOCKED@Q}).lower() == "true",
    "validated_locales": [item.strip() for item in ${VALIDATED_LOCALES@Q}.split(",") if item.strip()],
    "preset_batch_size": int(${PRESET_BATCH_SIZE@Q}),
    "validated_by": ${VALIDATED_BY@Q},
}
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(str(target))
PY

if [[ -f "${ROOT_DIR}/scripts/cleanup_release_artifacts.py" ]]; then
  MAX_RELEASES="${MAX_RELEASES}" TRIGGER_SOURCE="${TRIGGER_SOURCE}" \
    python3 "${ROOT_DIR}/scripts/cleanup_release_artifacts.py" || true
fi

echo "release artifact archive ready: ${TARGET_DIR}"
